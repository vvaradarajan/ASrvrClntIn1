from sanic import Sanic, response
from sanic.response import json
import os

app = Sanic(name='AsrvrClntIn1')
clientDir = f'{os.path.dirname(os.path.dirname(__file__))}/client/deploy'
#clientDir = '/home/vv/git/ASrvrClntIn1/client/deploy'

app.static('/client', clientDir)


@app.route("/")
async def test(request):
    return response.json({"hello": "world"})

@app.route("/client")
async def clientSPA(request):
    with open(f'{clientDir}/index.html','r') as f:
        clientHtml = f.read()
    #put in the brand and userId into the order board and into the menu
    brandUser = {
        'wsUrl':'localhost:8009/'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)