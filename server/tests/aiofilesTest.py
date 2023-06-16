import aiofiles, asyncio
async def test():
    # create a file
    outDir='/tmp/data'
    tFNm=f'{outDir}/transcript.txt'
    handle = await aiofiles.open(tFNm,mode ='a')
    #handle = await aiofiles.open('/tmp/data/test_create.txt', mode='a')
    # ...
    handle.close()

asyncio.run(test())
