import json
import requests

from utils import load_config

config = load_config("config.yaml")
grafana_config = config["grafana"]
grafana_host_url = grafana_config["host"]
grafana_api_key = grafana_config["key"]
grafana_folders_url = f"{grafana_host_url}/api/folders"

try:
    print('*' * 50)
    print('Importing folder structure to Grafana')
    print('*' * 50)
    with open('./setup/grafana/config/grafana-folders.json', "r") as f:
        folder_list = json.load(f)
    for each in folder_list:
        print('Importing folder :', each)
        r = requests.post(
            grafana_folders_url,
            data=json.dumps(each),
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + grafana_api_key}
        )
        if r.status_code != 200:
            print('r.status_cod + r.reason :', r.status_code, r.reason)
except Exception as e:
    print('Folder import raised the following exception :', e)
