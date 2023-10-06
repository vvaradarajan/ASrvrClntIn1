//Concept: Runs as a completely different process=>communication is only thru a message Q
import { frameBufferQBRes } from "./queue.js"
//This queue is only for communication between worklet and message via port. The baud rate etc. do not matter
// let samplingRate=8000
// let chunkSizeFor20ms = Math.round(samplingRate*0.02)
// let config =  {
//   'audioConstraints':{sampleSize:8,channelCount:1,sampleRate:samplingRate,echoCancellation:true}
//   ,'qParamsFromSrvrToBrowser':{name: 'toSpkrQ', convType:'Int16ToFloat32', qSizeInSeconds:20
//     , inSampleRate: samplingRate,outSampleRate: samplingRate, outChunkSize: 128}
//   ,'qParamsFromBrowserToSrvr':{name: 'fromMicQ',convType:'Float32ToInt16', qSizeInSeconds:20
//     , inSampleRate: samplingRate,outSampleRate: samplingRate, outChunkSize: chunkSizeFor20ms}
//   ,'timeOut':500
//   ,'outOfBandSignal': 0b01010101
// }
class MicSpkrProcessor extends AudioWorkletProcessor {
  convToQinit(x) {
    const qSize=x.qSizeInSeconds*x.inSampleRate
    const qDataType = x.convType.split("To")[1] //Queue datatype is the destination type
    return {name:x.name,qSize:qSize,outChunkSize:x.outChunkSize,inSampleRate:x.inSampleRate,outSampleRate:x.outSampleRate,qDataType:qDataType,convType:x.convType}
  }
  convToQinitOld(x) {
    const qSize=x.qSizeInSeconds*x.inSampleRate
    const qDataType = x.convType.split("To")[1] //Queue datatype is the destination type
    return {name:x.name,qSize:qSize,outChunkSize:x.outChunkSize,inSampleRate:x.inSampleRate,qDataType:qDataType,convType:x.convType}
  }
  constructor(options) {
      super()
      //console.log(`MicSpkrProcessorAwp is alive with options : ! ${JSON.stringify(options.processorOptions)}`)
      let config = options.processorOptions.config
      let spkrQParams=this.convToQinit(config.qParamsFromSrvrToBrowser)
      this.spkrQ= new frameBufferQBRes(spkrQParams)

      let micQParams=this.convToQinit(config.qParamsFromBrowserToSrvr)
        this.micQ= new frameBufferQBRes(micQParams)
        this.stopImmediateFlag=false
        this.port.onmessage = function (me){
            let tMsg=typeof(me.data)
            //console.log(`Got ${me.data}; type=${tMsg}`)
            if (!(tMsg=='string')) {
                //console.log('putting in Q')
                this.spkrQ.enqueue(me.data)
            }
            else { //process the message
              if (me.data=='stop') {
                console.log(`stop received by awp`)
                this.stopFlag=true;
                this.port.close()
              }
              if (me.data=='stopImmediate') {this.stopImmediateFlag=true;this.stop()}
              if (me.data=='Hello') {
                this.stopFlag=false
                this.port.postMessage('requestToSend');
                }
            }
        }.bind(this)
        this.stTime=Date.now()
        this.prevTime=this.stTime
        this.cycles=0
    }

    stop(){
      //sends a message that this has stopped
      this.port.postMessage('stoppedImmediate')
      this.port.close()
    }
    spkrProcess(outputs) {
      const output = outputs[0]
      let spkrData=this.spkrQ.dequeue()
      output.forEach(channel => {
        let qLen = this.spkrQ.bottom
        //console.log(`Spkr Queue length:${qLen}`)
        let nowTime=Date.now()
        let interval = nowTime-this.prevTime
        this.prevTime=nowTime
        this.cycles +=1
        if (spkrData) {
          //console.log(`spkrData: ${spkrData.length}; type: ${typeof(spkrData)}: ${interval}, avg: ${(this.prevTime-this.stTime)/this.cycles}`) //\n${spkrData}`)
          //console.log(`data type/length/interhttps://developer.mozilla.org/en-US/docs/Web/API/AudioWorkletGlobalScope
          for (let i = 0; i < channel.length; i++) {
            channel[i] = spkrData[i];
          }
        } 
        else {
          //console.log(`spkr Q length: ${this.spkrQ.bottom} - frame skipped1`)
          ;
        }
      })
      //sets stop via command received on port
      if (this.stopFlag){
        //if (!spkrData) this.stop(); //if stopFlag is set and there is no data stop
        return false; 
      } 
      else return true;
    }
    micProcess(inputs) {
      let micData=null
      //stereo or mono input=> just take one channel [0]
      const inpBuf = inputs[0][0]
      //console.log(`mic buffer: ${inpBuf.length}; type: ${typeof(inpBuf)}`) 
      this.micQ.enqueue(inpBuf)
      let qLen = this.micQ.bottom
      //console.log(`Mic Queue length:${qLen}`)
      //send mic data back on port
      if (qLen > this.micQ.outChunkSize) {
        let micAudioToServer=this.micQ.dequeue()
        //console.log(`enqueued msg of ${inpBuf.length} from micSpkrAwp: ${inpBuf }`)
        //console.log(`dequeued msg from micSpkrAwp: ${micAudioToServer}`)
        this.port.postMessage(micAudioToServer)
      }
      return true;
    }
    processFromQueue (inputs, outputs, parameters) {
        let spkrRetval=this.spkrProcess(outputs)
        let micRetval=this.micProcess(inputs)
        //return true
        return spkrRetval
 
      }
    process (inputs, outputs, parameters){
      //console.log(`micSpkrAws - this.stopImmediateFlag ${this.stopImmediateFlag}`)
      if (this.stopImmediateFlag) return false
      let retVal=this.processFromQueue(inputs,outputs,parameters)
      if (!retVal) {
        console.log(`Processor should be dead!`)
        return false
      }
      return true
    }
  }
try{
  registerProcessor('mic-spkr-processor', MicSpkrProcessor)
} catch (err) {
  console.log(`could not register mic-spkr-processor`)
  throw err
}