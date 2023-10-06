import { AudioWithAwp } from './nexmoRtc.js'
import { Remarkable } from 'remarkable'
import { getConfig } from './config.js'
//import './AudioContextMonkeyPatch.js'
class nexmoProxy {

    static get randomPhoneNo() {
        //Get a random number starting with 1555
        return  (Math.floor((Math.random())*10000000) + 15550000000).toString()
    }
    static async sentInitialCallerEvent(ws) {
        let nexmoInitialMsg={
            "event":"websocket:connected",
            "content-type":"audio/l16;rate=8000",
            "prop1": "value1",
            "prop2": "value2"
          }
          //console.log(`hostWs state during nexmoInitialMsg=${ws.readyState}=> should be ${ws.OPEN}`)
          await ws.send(JSON.stringify(nexmoInitialMsg)) // Required by cx member to start stt
    }
    static async getNexmoProxy(storeConfig) {
        //async factory to create the nexmoProxy object
        //storeConfig must have from, to, urlPrefix (https://slashcom.app:8008: 8008 for av, 8006 for pre1),dcPath ()
        //Get the webRtc stream and the ws to the cyborgOps
        async function getStream(samplingRate) {
            //Get the stream here
            let webRtcStream=null
            while (webRtcStream == null) {
                try {webRtcStream=await webAudioUtils.getWebrtcStream(samplingRate)}
                //try {webRtcStream=await webAudioUtils.getWebrtcStream()}
                catch(err) {
                    ; //alert(err)
                }
            }
            return webRtcStream;
        }
        async function getWs() {
            //getWsUrl from server, connect to it, get the user Media and start the webRtc
            let data={'from':storeConfig.from,'to':storeConfig.to} //,'filterData':this.shadowRoot.querySelector('filter-form').getJson()}
            let rUrl=`${storeConfig.urlPrefix}${storeConfig.dcPath}`
            console.log(`rUrl:${rUrl}, postData: ${JSON.stringify(data)}`)
            let resp=await fetch(rUrl,{method:'post',body:JSON.stringify(data)}).then(res => res.json()) // parse async response as JSON (can be res.text() for plain response) and return it
            console.log(`${JSON.stringify(resp)}`)
            let wsUrl=resp.wsUrl
            if (wsUrl==null) {
                alert (`wsUrl connection not made: ${JSON.stringify(resp)}! Server is down..`);
                return null
            } else return await webAudioUtils.wsConnect(wsUrl)
        }
        let stream=await getStream(storeConfig.samplingRate) //getStream(config.samplingRate)
        let ws = await getWs()
        if (!ws) return null //websocket to connect to on host not available. (check if agent is available)
        let np=new nexmoProxy(stream,ws,storeConfig.samplingRate) //,config.samplingRate)
        np.wl= await AudioWithAwp.factory(np.stream,ws,storeConfig.samplingRate)  //Get ref to AudioWorklet. 
        np.wl.restartFlag=true
        if (np != null)
            await nexmoProxy.sentInitialCallerEvent(ws); //Initial connect event - required by members.py to start STT
        return np;
    }
    constructor(stream,ws,samplingRate) {
        function adjustQParams(params) {
            //Determine parameters for Q's => qSize and qDatatype
            if (params.convType.endsWith("Int16")) {params.qDataType='Int16'} else {params.qDataType='Float32'}
            params.qSize = (params.outSampleRate > params.inSampleRate)?params.outSampleRate*params.qSizeInSeconds:params.inSampleRate*params.qSizeInSeconds
            return params
        }
        function isSampleRateSupported(rate) {
            //This is not supported in firefox
            
            try {
                let ac=new AudioContext({'sampleRate':rate})
                if (ac.sampleRate == rate ) return true
            } catch(err) {
                console.log(`Error in isSampleRateSupported ${err.message} `)
                return false
            }
            return false
        }


        this.stream=stream
        this.ws=ws //websocket to server. This is used to transfer mic input to server and receive spkr output from srvr
        this.config=getConfig(samplingRate)
        //Find the default audioContext settings and get the default sampleRate and create the bufferQ's
        let defaultSampleRate=(new AudioContext()).sampleRate
        let desiredRate=samplingRate
        if (isSampleRateSupported(desiredRate)) {
             console.log(`Sample rate of ${desiredRate} supported.. using ${desiredRate}`)
             defaultSampleRate =  desiredRate
        }
        this.audioSettings = stream.getAudioTracks()[0].getSettings() //ignore the returned actual settings. You can still set AudioContext to rates within
        let qParamsFromBrowserToSrvr = this.config.qParamsFromBrowserToSrvr
        let qParamsFromSrvrToBrowser = this.config.qParamsFromSrvrToBrowser
        qParamsFromBrowserToSrvr.inSampleRate=defaultSampleRate
        qParamsFromSrvrToBrowser.outSampleRate=qParamsFromBrowserToSrvr.inSampleRate
        //Determine parameters for Q's
        qParamsFromSrvrToBrowser=adjustQParams(qParamsFromSrvrToBrowser)
        qParamsFromBrowserToSrvr=adjustQParams(qParamsFromBrowserToSrvr)
    }
    async terminate() {
        //remove the nexmoProxy gracefully
        await this.wl.sendStopToAwp(false)
        this.wl=null
        if ( !(this.ws == null) && this.ws.readyState==1) {
            this.ws.close()
            console.log('ws closed')
            } else {
            console.log(`ws not operational: ${this.ws.readyState}`)
            }
        //The audioworklet etc. will terminate when the host websocket is closed
    }

}

class webAudioUtils {
    //Helper class containing useful collection for getUserMedia and wsConnect

    static async wsConnect(wsUrl) {
        //makes ws connection to wsUrl
        let wsPromise=new Promise(function(resolve,reject){
            let ws = new WebSocket(wsUrl);
            ws.binaryType = 'arraybuffer';
            ws.name='Gazebo'
            ws.onopen=(e) => {//no need for this in arrow fcn (takes on the enclosing context!)
                console.log('ws is connected!'+e.currentTarget.name)
                resolve(ws); //this is the enclosing contexrt
            }
            ws.onerror = (e) => {
                console.log('ws is rejected!')
                reject('Rejected!')
            }
        })
        let ws=await wsPromise;
        return ws
    }
    static async getWebrtcStream(samplingRate){
        let config = getConfig(samplingRate)
        let myStream = await navigator.mediaDevices.getUserMedia({ audio: config.audioConstraints, video: false }) //audio means audio source = microphone - returns mediastream
        return myStream;
    }

    static async wsJoin(confId,stream,agentNm,wsUrl){
        let ws=await this.wsConnect(wsUrl);
        let wa=new webAudio(stream,ws)
        wa.bport=resp.bport //b port used for instance specific api calls (/csapi)
        let thisConv=new confProcess(ws,wa) //put any recv data to speaker (need to re-write to be anonymous)
        return wa //return this object
    }

    static isSampleRateSupported(rate) {
        //Check if rate is supported (ex: This is not supported in firefox, but chrome works)
        try {
            let ac=new AudioContext({'sampleRate':rate})
            if (ac.sampleRate == rate ) return true
        } catch(err) {
            console.log(`Error in isSampleRateSupported ${err.message} `)
            return false
        }
        return false
    }

    static adjustQParams(params) {
        //Determine parameters for Q's => qSize and qDatatype
        if (params.convType.endsWith("Int16")) {params.qDataType='Int16'} else {params.qDataType='Float32'}
        params.qSize = (params.outSampleRate > params.inSampleRate)?params.outSampleRate*params.qSizeInSeconds:params.inSampleRate*params.qSizeInSeconds
        return params
    }

}
export {nexmoProxy}
export {webAudioUtils}
