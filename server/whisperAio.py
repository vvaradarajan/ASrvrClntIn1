import sys,io,json,requests
import aiohttp, asyncio,numpy as np
from globals import G
from utils import pnp
import pydub
GA=G['audio']
GO=G['openai']
GW=G['whisperApiAlg']

class WhisperAio:
    '''
    Transcribes mp3 audio in transQ (and asyncio.Queue)
    '''
    def __init__(self):
        self.audioInQ = asyncio.Queue()
        self.transOutQ = asyncio.Queue()
        self.debugMp3i = 1 if GW['debugMp3i'] else None
        self.taskList = []

    def createMp3(self,f,sr,x,reason):
        """numpy array to MP3"""
        channels = 2 if (x.ndim == 2 and x.shape[1] == 2) else 1
        #pydub takes int16 audio => convert if needed
        if x.dtype==np.int16: normalized=False
        if normalized:  # normalized array - each item should be a float in [-1, 1)
            y = np.int16(x * 2 ** 15)
        else:
            y = np.int16(x)
        song = pydub.AudioSegment(y.tobytes(), frame_rate=sr, sample_width=2, channels=channels)
        memoryBuff = io.BytesIO()
        song.export(memoryBuff,format='mp3')
        pnp(memoryBuff,'memoryBuff')
        return memoryBuff
    
    def transcribe(self,audio,myurl='https://api.openai.com/v1/audio/transcriptions'):
        OPENAI_API_KEY='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'
        headers = {"Authorization":f'Bearer {OPENAI_API_KEY}'}
        fields = {
            "model":"whisper-1"
            }
        #files = {'file': ("out2.mp3",open('out2.mp3', 'rb').read())}
        files = {'file': ("out2.mp3",audio)}
        getdata = requests.post(myurl,data=fields,files=files,headers=headers)
        print(getdata.text) 

    async def aiohttpTranscribe(self,audio,myurl='https://api.openai.com/v1/audio/transcriptions',reason='None'):
        print(f'Using AioHttp')
        OPENAI_API_KEY=GO['whisperKey']
        headers = {"Authorization":f'Bearer {OPENAI_API_KEY}'}
        data=aiohttp.FormData()
        data.add_field('model','whisper-1',content_type='multipart/form-data')
        data.add_field('language','en',content_type='multipart/form-data')
        data.add_field('file', audio, filename='abc.mp3',
                            content_type='multipart/form-data')
        pnp(audio,'audio')
        if GO['openAiStub']: 
            txt=json.dumps({'text':'No Whisper'})
        else:
            async with aiohttp.ClientSession() as session:
                getdata = await session.post(myurl,data=data,headers=headers)
                txt=await getdata.text()
        print(f'{reason}: {txt}') 
        return txt

    async  def aWrite(self,fs,npArr,reason='None'):
        mp3Recording = self.createMp3('out2.mp3', fs, npArr,reason)
        pnp(npArr,'mp3Recording')
        if self.debugMp3i:
            with open(f'{GW["debugDir"]}/data/{str(self.debugMp3i)}_{reason}.mp3','wb') as f:
                f.write(mp3Recording.getvalue())
            self.debugMp3i +=1
        txt = json.loads(await self.aiohttpTranscribe(mp3Recording,reason=reason))
        await self.transcriptFile.write(f'{str(self.debugMp3i)}:{txt["text"]}\n')

    async def processQ(self):
        while True:
            print(f'Extracted Audio')
            reason,audio = await self.audioInQ.get()
            pnp(audio,'getData')
            await self.aWrite(GA['sampleRate'],audio,reason=reason)

    def start(self):
        self.taskList.append(
            asyncio.create_task(self.processQ(),name='whis-process')
        )
            
    def stop(self):
        for t in self.taskList:
            t.cancel()



if __name__=='__main__':
    args=sys.argv
    myurl='https://httpbin.org/post'
    #myurl = 'https://api.openai.com/v1/audio/transcriptions'
    print(f'args={args}')
    wsAio = WhisperAio(None)
    if len(args)>1:
        if args[1]=='aio':
            asyncio.run(aiohttpTest('abc',myurl))
    else: wsAio.transcribe('abc',myurl)
    exit(0)
    transcribe(open('out2.mp3', 'rb').read())