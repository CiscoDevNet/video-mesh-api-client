import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
GRAFANA_URL = os.getenv('GRAFANA_URL') + "/api/folders"
GRAFANA_API_KEY = os.getenv('GRAFANA_API_KEY')

try:
    print('*' * 50)
    print('Importing folder structure to GRAFANA')
    print('*' * 50)
    with open('./setup/grafana/config/grafana-folders.json', "r") as f:
        folder_list = json.load(f)
    for each in folder_list:
        print('Importing folder :', each)
        r = requests.post(
            GRAFANA_URL, 
            data=json.dumps(each), 
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GRAFANA_API_KEY}
        )
        if r.status_code != 200:
            print('r.status_cod + r.reason :', r.status_code, r.reason)
except Exception as e:
    print('Folder import raised the following exception :', e)