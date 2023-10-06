//import './AudioContextMonkeyPatch.js'
import { getConfig } from './config.js'

function copyTypedArrays(inpBuf,outBuf){
    for (let i = 0; i < inpBuf.length; i++) {
        outBuf[i] = inpBuf[i];
    }
}

function zeroArray(inpArray) {
    return inpArray.every(function (e) {
        return e == 0;
    });
}

class AudioWithAwp{
    //Mic data => comes via inputBuffer -> put in audioMicQ (transforms it to proper sampling rate)->send to srvr on ws
    //Spkr data => to be put in outputBuffer -> get it from audioSpkrQ, if empty otherwise send silence
    constructor(stream,hostWs,sampleRate){
        this.stream=stream   //stream is required to extract the microphone input
        this.hostWs=hostWs   //required to send mic output back to host
        this.sampleRate=sampleRate
      }

    async restartAwp(){
        if (this.restartFlag) {
            if (this.awN) this.awN.disconnect()
            console.log('restarting')
            this.awN=new AudioWorkletNode(this.audioContext, 'mic-spkr-processor',{'processorOptions':{'config':getConfig(this.sampleRate)}}) //mic-spkr-processor is the previous line awp (exported from there)
            // Now this is the way to
            // connect our microphone to
            // the AudioWorkletNode and it should passed on as input to AWP
            this.microphone.connect(this.awN)
            //Get the port to communicate with awP
            this.awPPort=this.awN.port
            this.awPPort.postMessage('Hello')
            let msg = await this.recvDataFromAwp()  //indicates that the processor has started
            this.awPPort.addEventListener("message", this.awpRecieveLoop.bind(this));
            this.awN.connect(this.audioContext.destination) //connect this to the destination (spkr)
        }
    }
    
    async sendDataToAwp(d){
        if (this.awpStatus=='stopped') {
            await this.restartAwp()
            this.awpStatus='active'
        }
        this.awPPort.postMessage(d)
    }
    
    recvDataFromAwp() {
        return new Promise(function(resolve, reject) {
            this.awPPort.onmessage = function(evt) {
                resolve(evt.data);
            }
        }.bind(this))
    }
    
    async sendStopToAwp(restartFlag) {
        //requests awp to stop
        if (this.awN){
            this.restartFlag = restartFlag
            this.awN.disconnect()
            await this.awPPort.postMessage('stop') //send stop to the Awp
            this.awN=null
        } else console.log('Waiting for awp to stop calling back after death!')
    }

    async awpRecieveLoop(evt){
        let msgFromAwp = evt.data
        //console.log(`Received from micSpkrAwp: ${msgFromAwp}`);
        let tMsg=typeof(msgFromAwp)
        if (!(tMsg=='string')) {//audio data
            
            if (this.hostWs.readyState == this.hostWs.OPEN)
            { await this.hostWs.send(msgFromAwp)
            console.log(`sending audio data to host..${tMsg}, Length=${msgFromAwp.length}`)
            }
            else {
            //backend host is not alive so stop processsor
            console.log(`backend host websocket is not open: ${this.hostWs.readyState}. AWP stopped`)
            await this.sendStopToAwp(false) //send stop to the Awp
            }
        }
        else { //process the message
            if (msgFromAwp == 'stopped') {
                this.awpStatus='stopped'
                console.log(`Received "${msgFromAwp}" from Awp`)
                this.awN.disconnect()
            }
            else {
            console.log(`Error: unknow msg: ${msgFromAwp} received from Awp!`)
            }
        }
    }
    
    //***Start the audio Worklet with the micSpkrAwp processor */
    static async factory(stream,hostWs,sampleRate) {
        const aw=new AudioWithAwp(stream,hostWs,sampleRate)
        // configure the AudioContext and register the Awp
        aw.audioContext = new AudioContext({sampleRate: sampleRate})  //This also sets how often the audio-worklet-processor is called
        // //get the microphone as a MediaStreamSource
        aw.microphone = aw.audioContext.createMediaStreamSource(stream)
        const pName='src/micSpkrAwp.js'
        try {
            aw.awP = await aw.audioContext.audioWorklet.addModule(pName) //micSpkrAwp is the audio-worklet-processor running in different process. That 
        } catch (e) {
            console.log(`could not add processor ${pName} to audioworklet`)
            throw e;
        }
        aw.awpStatus='stopped'  //The processor is stopped, and can be started with 'Hello' on the port
        aw.hostWs.onmessage = function(evt) {
            //console.log("WebSocket message received and put in audioSpeakerQ:", evt);
            aw.sendDataToAwp(evt.data) //async function
          }.bind(aw);
        return aw
    }
}

export {AudioWithAwp};