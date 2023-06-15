from pydub import AudioSegment
from pydub.playback import play
import glob
import os


def playFolder(dir='/tmp/data',ignore=0):
    files = glob.glob(f"{dir}/*.mp3")
    files.sort(key=os.path.getmtime)
    print("\n".join(files))
    for f in files:
        fileNm='Nvads_15360_51_14.mp3'
        song = AudioSegment.from_mp3(f'{f}')
        play(song)

if __name__=='__main__':
    playFolder()