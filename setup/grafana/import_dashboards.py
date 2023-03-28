import os
import json
import requests

from utils import load_config

config = load_config("config.yaml")
grafana_config = config["grafana"]
grafana_host_url = grafana_config["host"]
grafana_api_key = grafana_config["key"]
grafana_folders_url = f"{grafana_host_url}/api/folders"
grafana_dashboard_url = f"{grafana_host_url}/api/dashboards/db"

grafana_folders = next(os.walk('./setup/grafana/config'))[1]
for grafana_folder in grafana_folders:
    import_folder = f"./setup/grafana/config/{grafana_folder}"
    print('*' * 50)
    print(f'Importing all the dashboards from {grafana_folder}')
    print('*' * 50)
    try:
        rd = requests.get(
            grafana_folders_url,
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + grafana_api_key}
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
        grafana_dashboard_files = [dsh_file for dsh_file in os.listdir(import_folder) if
                                   os.path.isfile(os.path.join(import_folder, dsh_file))]
    except Exception as e:
        print('Error found when listing json files in folder {0}'.format(grafana_folder))
        exit(0)

    for eachfile in grafana_dashboard_files:
        try:
            filename = os.path.join(import_folder, eachfile)
            print('Importing file :', filename)
            with open(filename, "r") as f:
                dashboard_definition = json.load(f)

                for i, panel in enumerate(dashboard_definition["dashboard"]["panels"]):
                    dashboard_definition["dashboard"]["panels"][i]["datasource"]["uid"] = "uid_timescaledb"

                for i, template in enumerate(dashboard_definition["dashboard"]["templating"]["list"]):
                    dashboard_definition["dashboard"]["templating"]["list"][i]["datasource"]["uid"] = "uid_timescaledb"

                folder_uid = dashboard_definition['folderUid']
                if folder_uid in dirdict_id.keys():
                    dashboard_definition['folderId'] = dirdict_id[folder_uid]
                else:
                    dashboard_definition['folderId'] = 0
                    print('Folder uid not found for the dashboard {0}'.format(eachfile))
                del dashboard_definition['folderUid']
                r = requests.post(
                    grafana_dashboard_url,
                    data=json.dumps(dashboard_definition),
                    headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + grafana_api_key}
                )
                if r.status_code != 200:
                    print('r.status_cod + r.reason :', r.status_code, r.reason)

        except Exception as e:
            print('error :', e)
