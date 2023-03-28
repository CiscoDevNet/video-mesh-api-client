import requests
from utils import load_config

config = load_config("config.yaml")
api_config = config["api"]
grafana_config = config["grafana"]
grafana_host_url = grafana_config["host"]
grafana_api_key = grafana_config["key"]
database_connection_url = api_config["database"]["url"]
database_connection_url_components = database_connection_url.split("/")
database_user_password_host_port = database_connection_url_components[2]
database_user_password, database_host_port = database_user_password_host_port.split("@")
database_user, database_password = database_user_password.split(":")
database_host, database_port = database_host_port.split(":")
database_name = database_connection_url_components[3]
grafana_datasource_url = f"{grafana_host_url}/api/datasources"

payload = {
    "id": 1,
    "uid": "uid_timescaledb",
    "name": "TimescaleDB",
    "type": "postgres",
    "isDefault": True,
    "url": f"{database_host}:{database_port}",
    "database": database_name,
    "access": "proxy",
    "jsonData": {
        "postgresVersion": 1500,
        "sslmode": "disable",
        "timescaledb": True,
        "tlsAuth": False,
        "tlsAuthWithCACert": False,
        "tlsConfigurationMethod": "file-path",
        "tlsSkipVerify": True
    },
    "user": database_user,
    "secureJsonData": {
        "password": database_password
    },
    "basicAuth": False
}

response = requests.post(
    grafana_datasource_url,
    headers={'Authorization': 'Bearer ' + grafana_api_key},
    json=payload
)

if response.status_code != 200:
    print('Failed to add TimescaleDB datasource')
    print(response.text)
else:
    print('Successfully Added TimescaleDB datasource')
