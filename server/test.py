
import sounddevice as sd
import numpy as np, asyncio
import pydub , webrtcvad
import io
from testRequests import transcribe, aiohttpTranscribe
from audioChunker import AudioChunker,TrancribeAudioChunker
from utils import pnp,createMp3
#config
duration = 5.5  # seconds
fs=8000
vad = webrtcvad.Vad() #10, 20, or 30 ms
blockTime=0.030
blockSize=int(fs*blockTime)
#end config

sd.default.samplerate = fs
sd.default.device = 'default'

def writeToFile(fs,npArr):
    #Store recording in a file
    mp3Recording = createMp3('out2.mp3', fs, npArr)
    transcribe(mp3Recording)

async  def aWrite(fs,npArr):
    mp3Recording = createMp3('out2.mp3', fs, npArr)
    await aiohttpTranscribe(mp3Recording)

async def main(myrecording):
    #test code
    maxTime=5.5 #seconds
    ac=AudioChunker()
    maxBlocks= int(maxTime*sd.default.samplerate/blockSize)
    blockLimitForStop=3
    blockLimitIdx=0
    blockIdx=0
    blockForTranscript=np.zeros((maxBlocks*blockSize,),dtype=np.int16)
    print(f'[asyncGen]Blocksize requested: {blockSize}')
    async for result,status in ac.inputstream_generator(dtype=np.int16,blocksize=blockSize):
	    #extract channel 1 (only 16 bit mono PCM audio for VAD)
        monoAudioBytes = result[:,0].tobytes()
        #pnp(result,'result')
        #pnp(monoAudioBytes,'monoAudioBytes')
        blockForTranscript[blockIdx*blockSize:blockIdx*blockSize+blockSize]=result[:,0]
        if (blockIdx := blockIdx+1)==maxBlocks:
            asyncio.create_task(aWrite(fs,blockForTranscript))
            if (blockLimitIdx := blockLimitIdx+1)==blockLimitForStop:
                ac.stopEvent.set()
            else:blockIdx=0
        if vad.is_speech(monoAudioBytes,fs): 
            pass
            #print(f'Got Speech')
    pnp(myrecording,'myrecording')
    pnp(blockForTranscript,'blockForTranscript')
    #end test code

    if myrecording:
        monoRecording = myrecording[:,0]
        pnp(myrecording)
        await aWrite(fs,monoRecording)
    #asyncio.create_task(aWrite(fs,blockForTranscript))
    await aWrite(fs,blockForTranscript)
    return



    #[[-225  707]
    # [-234  782]
    # [-205  755]
    # ..., 
    # [ 303   89]
    # [ 337   69]
    # [ 274   89]]

    write('out2.mp3', fs, npArr)

    ###############
    

def getRecording():
    print(f'Start Recording..from device {sd.default.device}')
    sd.default.samplerate=fs
    sd.default.channels = 2
    myrecording = sd.rec(int(duration * fs),dtype=np.int16)
    sd.wait()
    pnp(myrecording,'Recording')
    return myrecording

if __name__=='__main__':
    #myrecording=getRecording()
    #exit()
    asyncio.run(main(None))#
    # writeToFile(fs,myrecording)
    exit(0)

# sd.play(myrecording,samplerate=fs)
# sd.wait()
'''
OPENAI_API_KEY='sk-XlupqSvSI071uMeCDPZHT3BlbkFJ8Nnc816dMkZcEUBdM4A4sk-vSD1bhLhBEVLY4rhzrcFT3BlbkFJvXJ6nQ7nopFzcsjH2h47'
curl --request POST \
  --url https://api.openai.com/v1/audio/transcriptions \
  --header "Authorization: Bearer $OPENAI_API_KEY" \
  --header 'Content-Type: multipart/form-data' \
  --form file=@out2.mp3 \
  --form model=whisper-1
'''