import sounddevice as sd
import numpy as np, asyncio
import pydub 
import io, atexit, os
import aiofiles
from whisperAio import WhisperAio
from utils import pnp, LeftBuf
from sdAudioChunker import AudioChunker
from globals import G
import webrtcvad
vad = webrtcvad.Vad()
GA=G['audio']
GW=G['whisperApiAlg']


class TrancribeAudioChunker:
    '''
    This class createa a chunk of Audio to be sent for transcription.
    Essentially this is for whisper which does not have streaming recognition.
    Algorithm:
    1. Use the LeftBuffer
    2. Use a state => inAudio (True if in chunk, False otherwise)
    3. inChunk = True if 3 Nvad followed by vad
    4. inChunk transition from True to False:
        a. timeForTranscribe=5 seconds have gone by
        b. chunks in LeftBuffer exceeds Y
    5. Do not send chunk to LeftBuffer if:
        a. inChunk=False
        b. if the chunk is > nth Nvad
    '''
    def __init__(self,wio):
        #config

        timeForTranscribe=GW['duration']
        fs=GA['sampleRate']
        framesForTranscribe=timeForTranscribe*fs #can be less
        NvadLead = GW['NvadLead']  #if there is a sequence of Nvad's more than this they are not sent to transcibe
        NvadTimeForTranscribe = 1.5 # Transcribe is triggered if this occurs
        LeftBufTime=GW['BufferTime'] #Max seconds of audio is kept in buffer
        ignoreShortAudioTime=GW['ignoreShortAudioTime'] #ignore audio segements less that this seconds
        NvadSeparationForTranscribe=0 #Nvads to separation of transcribe requests
        outDir=GW['debugDir']
        #end config
        #init
        self.wio=wio
        self.inChunk=False
        self.framesForTranscribe=framesForTranscribe
        self.fs=fs
        #self.chunksForTranscribe=chunksForTranscribe #can be less
        self.NvadLead=NvadLead
        self.rb = LeftBuf(LeftBufTime*self.fs)
        self.NvadsForTranscribe=int(NvadTimeForTranscribe*self.fs*GA['chunkTime'])
        self.NvadSeparationForTranscribe = int(NvadSeparationForTranscribe*self.fs)
        self.NvadCnt=0
        self.nVadsSkipped=0
        self.forceTranscribeCount=0
        self.NvadsForTranscribeCount=0
        self.NvadSeparationForTranscribeCnt=0
        self.ignoreShortAudioBlocks = int(ignoreShortAudioTime*self.fs)
        self.outDir = outDir
        print(self)

    async def asyncInit(self):
        if not os.path.exists(f'{self.outDir}/data'): os.makedirs(f'{self.outDir}/data')
        tFNm=f'{self.outDir}/transcript.txt'
        self.transcriptFile = await aiofiles.open(tFNm,mode ='a')
        self.wio.transcriptFile=self.transcriptFile
        print(f'TranscriptFile: {tFNm} created')
        self.transcriptFile.close()
        atexit.register(self.transcriptFile.close)

    def __str__(self):
        return (f'TranscribeAudioChunker:\nsamplerate={self.fs}, NvadsForTranscribe= {self.NvadsForTranscribe}, NvadsForTranscribeCount= {self.NvadsForTranscribeCount}\n'
                f'framesForTranscribe= {self.framesForTranscribe}, forceTranscribeCount= {self.forceTranscribeCount} ')

    def putInBuf(self,chunk):
        self.forceTranscribeCount +=len(chunk)
        notVad = not vad.is_speech(chunk.tobytes(),self.fs)
        if notVad:
            self.NvadsForTranscribeCount +=1
            self.NvadSeparationForTranscribeCnt +=1
        else: 
            self.NvadsForTranscribeCount = 0
            self.NvadSeparationForTranscribeCnt = 0
            self.inChunk=True
        if self.inChunk and self.NvadCnt < self.NvadLead:
            self.rb.addAudio(chunk)
        else: 
            self.nVadsSkipped +=1
        self.NvadCnt = self.NvadCnt + 1 if notVad else 0
        length=self.rb.end
        reason = ('length' if ( length >=  self.framesForTranscribe)
                  else 'time' if (self.forceTranscribeCount >= self.framesForTranscribe and self.NvadSeparationForTranscribeCnt > self.NvadSeparationForTranscribe)
                  else f'Nvads_{length}_{self.NvadsForTranscribeCount}_' if (self.NvadsForTranscribeCount > self.NvadsForTranscribe)
                  else None)
        if reason:
            print(f'length: current: {length}, limit: {self.framesForTranscribe} {"****" if reason=="length" else ""}\n'
                  f'time: current: {self.forceTranscribeCount}, limit: {self.framesForTranscribe},'
                    f' NvadSep:{self.NvadSeparationForTranscribeCnt}, NvadSepLmt: {self.NvadSeparationForTranscribe} {"****" if reason=="time" else ""}\n'
                  f'Nvads: current: {self.NvadsForTranscribeCount}, limit: {self.NvadsForTranscribe}  {"****" if reason.startswith("Nvad") else ""}'
                  )
            data = self.rb.extractAudio()
            if len(data) > self.ignoreShortAudioBlocks:
                #asyncio.create_task(self.wio.aWrite(GA['sampleRate'],data,reason))
                pnp(data,'putData')
                asyncio.ensure_future(self.wio.audioInQ.put((reason,data)))
            else:
                print(f'***Audio too short - {len(data)} not > {self.ignoreShortAudioBlocks} - ignored')
            self.forceTranscribeCount=0
            self.NvadsForTranscribeCount=0
            self.inChunk=False


    @staticmethod
    async def test():
        wio = WhisperAio()
        tac=TrancribeAudioChunker(wio)
        await tac.asyncInit()
        tac.inChunk=True
        ac=AudioChunker()
        blocksize=int(tac.fs*GA['chunkTime'])
        print(f'tac blocksize= {blocksize}')
        wio.start()
        async for result,status in ac.inputstream_generator(dtype=np.int16,blocksize=blocksize):
            #pnp(result[:,0],'result')
            tac.putInBuf(result[:,0]) #use mono channel


if __name__=='__main__':
    #LeftBuf.test()
    asyncio.run(TrancribeAudioChunker.test())