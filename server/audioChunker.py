import sounddevice as sd
import numpy as np, asyncio
import pydub 
import io
from testRequests import transcribe, aiohttpTranscribe
from utils import pnp, createMp3
import webrtcvad
vad = webrtcvad.Vad()

G={'sampleRate':8000,'chunkTime':0.02,'sampleWidth':2, 'dType': np.int16,
    'duration':5.5}

async  def aWrite(fs,npArr):
    mp3Recording = createMp3('out2.mp3', fs, npArr)
    await aiohttpTranscribe(mp3Recording)

class RingBuf:
    #stores np.ndarray in a circular buffer
    def __init__(self,size):
        self.ndArr=np.zeros((size,),dtype=np.int16)
        self.st=0
        self.end=0
        self.length=size
        self.noOfVads=0
        self.maxExtract=size #extract a max of 5 entries
        self.extract=np.zeros((self.maxExtract,),dtype=np.int16)

    def addAudio(self,monoNdArr):
        #if array fits from st, put it whole, else split
        l=len(monoNdArr)
        fp=l
        if (self.length - self.end) > l:
            self.ndArr[self.end:self.end+l]=monoNdArr
            self.end=self.end+l
        else:
            fp=self.length-self.end
            self.ndArr[self.end:self.end+fp]=monoNdArr[0:fp]
            sp=l-fp
            self.ndArr[0:sp] = monoNdArr[fp:]
            self.end=sp
            if self.end > self.st:
                print(f'**OverRun**')

    def extractAudio(self):
        #For now Go from st to end
        self.extract[:]=0
        if self.end < self.st:
            avl= self.length - (self.st - self.end)
        else: avl=self.end-self.st
        if avl > self.maxExtract: avl=self.maxExtract
        if avl==0:return self.extract
        fp=avl if self.length-self.st > avl else self.length-self.st
        self.extract[0:fp]=self.ndArr[self.st:self.st+fp]
        if fp<avl:
            self.extract[fp:avl]=self.ndArr[0:avl-fp]
            self.st = avl-fp
        else: self.st +=avl
        return self.extract

    def getLength(self):
        if self.end < self.st:
            avl= self.length - (self.st - self.end)
        else: avl=self.end-self.st
        return avl


        
    def writeOut(self):
        print(f'st={self.st}, end={self.end}\n{self.ndArr}')

    @staticmethod
    def test():
        ndArr=np.array([1,2,3,4,5,6,7,8,9], dtype=np.int16)
        mrb=RingBuf(15)
        mrb.addAudio(ndArr)
        mrb.addAudio(ndArr[0:5])
        mrb.writeOut()
        print(f'1st extract = {mrb.extractAudio()}')
        print(f'2nd extract = {mrb.extractAudio()}')
        print(f'3rd extract = {mrb.extractAudio()}')
        mrb.addAudio(ndArr[0:5])
        print(f'4th extract = {mrb.extractAudio()}')

class AudioChunker:
    '''
    This class handles sd-sounddevice and generates blocks of audio
    using an async generator.
    This should be a singleton.
    '''

    def __init__(self):
        blockSize=int(G['sampleRate']*G['chunkTime'])
        sd.default.samplerate=G['sampleRate']
        sd.default.channels = 2
        sd.default.device = 'default'  #use the default
        self.stopEvent=asyncio.Event()

    async def inputstream_generator(self,blocksize=1024,channels=2, **kwargs):
        """Generator that yields blocks of input data as NumPy arrays."""
        q_in = asyncio.Queue()
        loop = asyncio.get_event_loop()
        idx=0
        audioblock=np.zeros((blocksize,channels),dtype=np.int16)
        def callback(indata, frame_count, time_info, status):
            nonlocal audioblock, idx, channels
            #print(f'audioblock length={len(audioblock)}')
            if len(indata)+idx > blocksize:
                #copy portion that fits and remaining put in buffer after copying
                toCopy = blocksize-idx
                audioblock[idx:idx+toCopy]=indata[0:toCopy]   
                loop.call_soon_threadsafe(q_in.put_nowait, (audioblock.copy(), status))
                toCopy1 = len(indata)-toCopy
                audioblock[0:toCopy1]=indata[toCopy:]
                idx=toCopy1
            else:
                audioblock[idx:idx+len(indata)]=indata
                idx +=len(indata)
        stream = sd.InputStream(callback=callback, channels=channels, **kwargs)
        with stream:
            while not self.stopEvent.is_set():
                indata, status = await q_in.get()
                yield indata, status

class TrancribeAudioChunker:
    '''
    This class createa a chunk of Audio to be sent for transcription.
    Essentially this is for whisper which does not have streaming recognition.
    Algorithm:
    1. Use the RingBuffer
    2. Use a state => inAudio (True if in chunk, False otherwise)
    3. inChunk = True if 3 Nvad followed by vad
    4. inChunk transition from True to False:
        a. timeForTranscribe=5 seconds have gone by
        b. chunks in RingBuffer exceeds Y
    5. Do not send chunk to RingBuffer if:
        a. inChunk=False
        b. if the chunk is > nth Nvad
    '''
    def __init__(self):
        #config
        maxChunks=1000
        timeForTranscribe=5
        fs=G['sampleRate']
        framesForTranscribe=timeForTranscribe*fs #can be less
        NvadLead=3
        ringBufSize=50000
        #end config
        #init
        self.inChunk=False
        self.maxChunks=maxChunks
        self.framesForTranscribe=framesForTranscribe
        self.fs=fs
        #self.chunksForTranscribe=chunksForTranscribe #can be less
        self.NvadLead=NvadLead
        self.rb = RingBuf(ringBufSize)
        self.NvadCnt=0
        self.nVadsSkipped=0


    def transcribe():
        aData = self.rb.extractAudio()
        pnp(aData,'aData')
        pnp(self.nVadsSkipped,'nVadsSkipped')
        asyncio.create_task(aWrite(self.fs,aData))

    def putInBuf(self,chunk):
        notVad = not vad.is_speech(chunk.tobytes(),self.fs)
        if self.inChunk and self.NvadCnt < self.NvadLead:
            self.rb.addAudio(chunk)
        else: self.nVadsSkipped +=1
        self.NvadCnt = self.NvadCnt + 1 if notVad else 0
        #print (f'rbLen={self.rb.getLength()}')
        if self.rb.getLength() >=  self.framesForTranscribe:
            self.transcribe()


    @staticmethod
    async def test():
        tac=TrancribeAudioChunker()
        tac.inChunk=True
        ac=AudioChunker()
        async for result,status in ac.inputstream_generator(dtype=np.int16,blocksize=240):
            #pnp(result[:,0],'result')
            tac.putInBuf(result[:,0]) #use mono channel


if __name__=='__main__':
    #RingBuf.test()
    asyncio.run(TrancribeAudioChunker.test())