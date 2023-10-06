/**
 * @author Created by vasan on 19-10-23.
 * @email   vsvconsult@gmailcom
 */
'use strict';
class Resampler {
    constructor(fromSampleRate, toSampleRate, lastValue,d,returnType) {
      
      this.resampler       = null;
      this.fromSampleRate  = fromSampleRate;
      this.toSampleRate    = toSampleRate;
      this.lastValue       = lastValue || 0;
      this.d=d //max distance between outSamples before an input sample occurs
      this.maxU  = toSampleRate/fromSampleRate // number of output samples per input sample (upSampling > 1)
      this.maxD = fromSampleRate/toSampleRate // number of input samples per output sample (downSampling - > 1)
      this.returnType=returnType
      //determine up/down sampling and point ratio
      if (this.maxU > 1) {
          this.sampleMethod='UP';
          this.resample =this.resampleUp;
          this.sampleRatio = this.maxU
      } else if (this.maxD > 1) {
        this.sampleMethod='DN';
        this.resample =this.resampleDown;
        this.sampleRatio = this.maxD
          
      } else {
            console.log('Resampling rates are same. Simple conversion Int16 or Float32 directly!')
            this.sampleMethod='NR';
            this.resample = this.noResample;
            //this.sampleRatio = 1;
          }   
       
    }
    calcOutputLength(inpLength,maxU,d) {
        //find the number of output points given above
        //The last input point is not included
        //Ex: maxU=2.5, inpLength=3 =>5
        let n=(inpLength-1)*maxU-1
    }

    //resample(inpBuf){
    //    if (this.maxU > 1) return this.resampleUp(inpBuf);
   //     else if (this.maxD > 1) return this.resampleDown(inpBuf)
    //    else console.log('Resampling rates are same. Pls do the Array conversion Int16 or Float32 directly!')
    //}

    noResample (inpBuf) {
        return new Float32Array(inpBuf);
    }

    resampleUp(inpBuf){
        let oS=[]
        let lhs=this.lastValue; //lhs-left value, rhs=right value, d = distance from lhs
        let rhs=null
        for (let i=0;i<inpBuf.length;i++) {
            while (this.d <= this.maxU) {
                //console.log(`debug: maxU: ${this.maxU}, d:${this.d}, inpBuf[1]:${inpBuf[i]}`)
                rhs=inpBuf[i]
                oS.push(((this.maxU-this.d)*lhs + this.d*rhs)/this.maxU) //linear interpolation
                this.d++;
            }
            this.d -=this.maxU
            lhs=rhs
        }
        this.lastValue= rhs //This is the lhs saved for the next call
        return new Float32Array(oS)
    }
    resampleDown(inpBuf){
        let oS=[]
        let lhs=this.lastValue; //lhs-left value, rhs=right value, d = distance from lhs
        let rhs=null
        let il=inpBuf.length
        for (let i=0;i<inpBuf.length;i++) {
            if (this.d > this.maxD) {
                if (i==0) lhs=this.lastValue
                else lhs=inpBuf[i-1]
                rhs=inpBuf[i]
                this.d -=this.maxD
                //console.log(`lhs: ${lhs}; rhs: ${rhs}; d: ${this.d}`)
                oS.push((1.0-this.d)*lhs+this.d*rhs)
            }
            this.d +=1
        }
        this.lastValue=inpBuf[il-1]
        return new Float32Array(oS)  //scaling => do everything in float32 and convert outside!
    }
    toString(){
        return `Resampler: from:${this.fromSampleRate}, to:${this.toSampleRate}, method: ${this.sampleMethod}, ptRadio: ${this.sampleRatio}, lastValue: ${this.lastValue}, maxdistance: ${this.d}`
    }

    static tester(){
        let rs=new Resampler(8000,8000,6,0)
        rs.toString()
        let inpSample=[1,1,1,1,1,1,1,2,2,2,2,2,3,2,3,3,3,3] //two imput samples
        let oS=rs.resample(inpSample)
        console.log(`oS=${oS}\nlastvalue=${rs.lastValue}; d=${rs.d}`)

    }
}

export {Resampler}
//Test via node (v12.13.1 or more ) using: node --experimental-modules src/cResampler.js using the code below
//console.log("Hello")
//Resampler.tester()