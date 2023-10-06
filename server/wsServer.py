from dataclasses import dataclass
import websockets, asyncio, json, os
from globals import G
class RunWsServer:
    ''' websocket server in com. All wsClients (tasks) connect to this with a path.
    The last part of the path is the port to which Agents will connect to.  The number of wsClients
    is limited by maxClients (about equal to number of processors)
    '''
    def __init__(self,name,jsonDataQ,wsServerPort):
        self.prevSocket=None
        self.name=name
        self.jsonDataQ = jsonDataQ
        self.wsServerPort = wsServerPort
        self.wsClientSet = set()
        self.rcSet = set()
    
    async def getLoopVoltages(self,ws):
        while True:
            data= await ws.recv()
            try:
                lvDataArr = json.loads(data)
                #print(f'[vasan] lvData: {lvDataArr}')
                await G['dbServiceWriteQ'].put({'LoopVoltages':lvDataArr})
                #put them into Queue for display
                for lvData in lvDataArr:
                    if lvData["restaurant_id"] in self.rcSet: await self.jsonDataQ.put(lvData)
            except Exception as E:
                print(f'[loopVoltage] Invalid loop Data received: {data}:\n{str(E)}')
                if not ws.open: break

    def createRcSet(self):
        self.rcSet=set()
        for wsx in self.wsClientSet:
            self.rcSet.add(wsx.rc)
        print(f'[sensors] Current clients: {self.rcSet}')
    async def hello(self,ws,path):
        if path.endswith('loopVoltage'):
            await self.getLoopVoltages(ws) #store loop voltages into db
            return
        #attach restaurant_code to ws and store in array
        rc= os.path.basename(os.path.normpath(path))
        ws.rc = rc
        self.wsClientSet.add(ws)
        print(f'[vasan] {ws.rc} added for loop display')
        self.createRcSet()
        print(f'send data to js client task started: ws.open = {ws.open}')
        while True:
            data = await self.jsonDataQ.get()
            delset=set()
            for wsx in self.wsClientSet:
                if wsx.rc == data['restaurant_id']:  
                    try:
                        await wsx.send(json.dumps(data))
                        #print(f'[commreporter]Sending loop data to client..')
                    except:
                        print(f'Unable to send {self.name} data on ws: ws.open = {ws.open} .. closing..')
                        delset.add(wsx)
            if delset:
                self.wsClientSet = self.wsClientSet - delset
                self.createRcSet()

    async def run(self):
        print(f'wsServer running with name: {self.name}, accepting connections on {self.wsServerPort}')
        try:
            async with websockets.serve(self.hello,"localhost",self.wsServerPort):
                await asyncio.Future() # run forever
        except Exception as E:
            print(f'[Sensor] ws server aborted unexpectedly! Restart commreporter..')

if __name__=='__main__':
    tQ=asyncio.Queue()
    tQ.put_nowait('NutCase')
    rws = RunWsServer('loop',tQ,8009)
    asyncio.run(rws.run())


#593898877, 13-nov-2028



