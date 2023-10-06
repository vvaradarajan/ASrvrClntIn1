
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
export {webAudioUtils}
