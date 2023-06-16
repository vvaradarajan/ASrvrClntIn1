import requests,json,sys,io
import aiohttp

def transcribe(audio,myurl='https://api.openai.com/v1/audio/transcriptions'):
    OPENAI_API_KEY='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'
    headers = {"Authorization":f'Bearer {OPENAI_API_KEY}'}
    fields = {
        "model":"whisper-1"
        }
    #files = {'file': ("out2.mp3",open('out2.mp3', 'rb').read())}
    files = {'file': ("out2.mp3",audio)}
    getdata = requests.post(myurl,data=fields,files=files,headers=headers)
    print(getdata.text) 

async def aiohttpTranscribe(audio,myurl='https://api.openai.com/v1/audio/transcriptions',reason='None'):
    print(f'Using AioHttp')
    OPENAI_API_KEY='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'
    headers = {"Authorization":f'Bearer {OPENAI_API_KEY}'}
    data=aiohttp.FormData()
    data.add_field('model','whisper-1',content_type='multipart/form-data')
    data.add_field('language','en',content_type='multipart/form-data')
    data.add_field('file', audio, filename='abc.mp3',
                        content_type='multipart/form-data')
    async with aiohttp.ClientSession() as session:
        getdata = await session.post(myurl,data=data,headers=headers)
        txt=await getdata.text()
        print(f'{reason}: {txt}') 
        return txt

if __name__=='__main__':
    args=sys.argv
    myurl='https://httpbin.org/post'
    #myurl = 'https://api.openai.com/v1/audio/transcriptions'
    print(f'args={args}')
    if len(args)>1:
        if args[1]=='aio':
            asyncio.run(aiohttpTest('abc',myurl))
    else: transcribe('abc',myurl)
    exit(0)
    transcribe(open('out2.mp3', 'rb').read())