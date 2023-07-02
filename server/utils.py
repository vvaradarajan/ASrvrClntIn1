import numpy as np
import io, pydub,json
import aiohttp,requests
from globals import G

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


class LeftBuf:
    #stores np.ndarray in a buffer from left to right
    def __init__(self,size):
        self.ndArr=np.zeros((size,),dtype=np.int16)
        self.end=0
        self.length=size
        self.noOfVads=0
        self.maxExtract=100000 #size #extract only this or less

    def addAudio(self,monoNdArr):
        #if array fits from st, put it whole, else split
        l=len(monoNdArr)
        endBuf=self.end+ l
        if endBuf > self.length: 
            print(f'**OverRun**')
            l=self.length - self.end
            self.ndArr[self.end:self.end+l] = monoNdArr[0:l] 
            self.end=self.length
        else:
            self.ndArr[self.end:self.end+l] = monoNdArr[0:l] 
            self.end +=l

    def extractAudio(self,noToExtract=None):
        #For now Go till end or self.maxExtract
        noRequested = noToExtract if noToExtract else self.maxExtract
        if self.end > noRequested:
            retval=self.ndArr[0:noRequested].copy()
            print(f'move to:0:{self.end-noRequested}; from:{noRequested}:{self.end}')
            self.ndArr[0:self.end-noRequested]=self.ndArr[noRequested:self.end]
            self.end -= noRequested
        else:
            retval=self.ndArr[0:self.end].copy()
            self.end=0
        return retval
        
    def writeOut(self):
        print(f'buf: st=0; end={self.end}, content= {self.ndArr}')

    @staticmethod
    def test():
        ndArr=np.array([1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5], dtype=np.int16)
        mrb=LeftBuf(15)
        #test overrun
        for i in range(10):
            mrb.addAudio(ndArr[i*4 % 20 :i*4 % 20 + 4])
        #extract entire buf
        mrb.writeOut()
        print(f'1st extract = end:{mrb.end}; content={mrb.extractAudio(noToExtract=10)}')
        mrb.writeOut()
        # print(f'2nd extract = st:{mrb.st}; avl:{mrb.avl},content={mrb.extractAudio()}')
        # print(f'3rd extract = st:{mrb.st}; avl:{mrb.avl},content={mrb.extractAudio()}')
        # mrb.addAudio(ndArr[4:9])
        # print(f'4th extract = st:{mrb.st}; avl:{mrb.avl},content={mrb.extractAudio()}')

if __name__=='__main__':
    LeftBuf.test()