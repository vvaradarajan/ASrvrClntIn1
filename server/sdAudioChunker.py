import sounddevice as sd
import numpy as np, asyncio
from globals import G
import webrtcvad
vad = webrtcvad.Vad()
GA=G['audio']

class AudioChunker:
    '''
    This class handles sd-sounddevice and generates blocks of audio
    using an async generator.
    This should be a singleton.
    '''

    def __init__(self):
        blockSize=int(GA['sampleRate']*GA['chunkTime'])
        sd.default.samplerate=GA['sampleRate']
        sd.default.channels = GA['channels']
        sd.default.device = 'default'  #use the default
        self.stopEvent=asyncio.Event()

    async def inputstream_generator(self,blocksize,channels=2, **kwargs):
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

if __name__ == '__main__':
    pass