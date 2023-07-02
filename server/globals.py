import json,numpy as np

import yaml
import os,json

configFile = os.path.join(os.path.dirname(__file__), 'etc/config.yml')

with open(configFile, 'r') as file:
    G = yaml.safe_load(file)
print(json.dumps(G,indent=4))