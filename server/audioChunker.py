import sounddevice as sd
import numpy as np, asyncio
import pydub 
import io
from testRequests import transcribe, aiohttpTranscribe

G={'sampleRate':8000,'chunkTime':0.02,'sampleWidth':2, 'dType': np.int16,
    'duration':5.5}

class RingBuf:
    #stores np.ndarray in a circular buffer
    def __init__(self,size):
        self.ndArr=np.zeros((size,),dtype=np.int16)
        self.st=0
        self.end=0
        self.length=size
        self.noOfVads=0
        self.maxExtract=5 #extract a max of 5 entries
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

    if __name__=='__main__':
        RingBuf.test()