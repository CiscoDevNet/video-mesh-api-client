import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
GRAFANA_URL_FOLDER = os.getenv('GRAFANA_URL') + "/api/folders"
GRAFANA_URL_DASHBOARD = os.getenv('GRAFANA_URL') + "/api/dashboards/db"
GRAFANA_API_KEY = os.getenv('GRAFANA_API_KEY')

grafana_folders = next(os.walk('./setup/grafana/config'))[1]
for grafana_folder in grafana_folders:
    import_folder = f"./setup/grafana/config/{grafana_folder}"
    print('*' * 50)
    print(f'Importing all the dashboard from {grafana_folder}')
    print('*' * 50)
    try:
        rd = requests.get(
            GRAFANA_URL_FOLDER, 
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GRAFANA_API_KEY}
        )
        if rd.status_code != 200:
            raise Exception(rd.status_code, rd.text)
        folder_list_dst = rd.json()
        dirdict_id = {}
        for key in folder_list_dst:
            dirdict_id[key['uid']] = key['id']

    except Exception as e:
        print('dashboard_import() exception: ', e)
        exit(0)

    try:
        grafana_dashboard_files = [dsh_file for dsh_file in os.listdir(import_folder) if os.path.isfile(os.path.join(import_folder, dsh_file))]
    except Exception as e:
        print('Error found when listing json files in folder {0}'.format(grafana_folder))
        exit(0)

    for eachfile in grafana_dashboard_files:
        try:
            filename = os.path.join(import_folder, eachfile)
            print('Importing file :', filename)
            with open(filename, "r") as f:
                dashboard_definition = json.load(f)
                folder_uid = dashboard_definition['folderUid']
                if folder_uid in dirdict_id.keys():
                    dashboard_definition['folderId'] = dirdict_id[folder_uid]
                else:
                    dashboard_definition['folderId'] = 0
                    print('Folder uid not found for the dashboard {0}'.format(eachfile))
                del dashboard_definition['folderUid']
                r = requests.post(
                    GRAFANA_URL_DASHBOARD, 
                    data=json.dumps(dashboard_definition), 
                    headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GRAFANA_API_KEY}
                )
                if r.status_code != 200:
                    print('r.status_cod + r.reason :', r.status_code, r.reason)

        except Exception as e:
            print('error :', e)
