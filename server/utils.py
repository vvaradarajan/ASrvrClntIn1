import numpy as np
import io, pydub
def pnp(v,label=''):
    if v is None: print(f'{label} is {v}')
    elif isinstance(v,np.ndarray): 
        shape=v.shape
        print(f'{label} => type:{type(v)}, len={len(v)}, shape={shape}, dType={v.dtype}')
    elif isinstance(v,io.BytesIO):
        print(f'{label} => type:{type(v)}, contentLength={v.getbuffer().nbytes}')
    elif isinstance(v,(int,float)):
            print(f'{label} => type:{type(v)},value={v}')
    else: print(f'{label} => type:{type(v)}, **cannot print details**')

debugMp3i=1
def createMp3(f,sr,x,reason):
    global debugMp3i
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
    if debugMp3i:
        song.export(f'/tmp/data/{reason}{str(debugMp3i)}.mp3', format="mp3")
        debugMp3i +=1
    song.export(memoryBuff,format='mp3')
    pnp(memoryBuff,'memoryBuff')
    return memoryBuff