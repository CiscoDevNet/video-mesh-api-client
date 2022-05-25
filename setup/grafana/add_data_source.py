import os
import requests
from dotenv import load_dotenv

load_dotenv()

GRAFANA_URL = os.getenv('GRAFANA_URL') + '/api/datasources'
GRAFANA_API_KEY = os.getenv('GRAFANA_API_KEY')

DATABASE_HOST_TIMESCALE = os.getenv('DATABASE_HOST')
DATABASE_PORT_TIMESCALE = os.getenv('DATABASE_PORT')
DATABASE_USER_TIMESCALE = os.getenv('DATABASE_USER')
DATABASE_PASSWORD_TIMESCALE = os.getenv('DATABASE_PASSWORD')
DATABASE_NAME_TIMESCALE = os.getenv('DATABASE_NAME')

payload = {
    "name": "TimescaleDB",
    "type": "postgres",
    "isDefault": True,
    "url": f"{DATABASE_HOST_TIMESCALE}:{DATABASE_PORT_TIMESCALE}",
    "database": DATABASE_NAME_TIMESCALE,
    "access": "proxy",
    "jsonData": {
        "postgresVersion": 1200,
        "sslmode": "disable",
        "timescaledb": True,
        "tlsAuth": False,
        "tlsAuthWithCACert": False,
        "tlsConfigurationMethod": "file-path",
        "tlsSkipVerify": True
    },
    "user": DATABASE_USER_TIMESCALE,
    "secureJsonData": {
        "password": DATABASE_PASSWORD_TIMESCALE
    },
    "basicAuth": False
}

response = requests.post(
    GRAFANA_URL,
    headers={'Authorization': 'Bearer ' + GRAFANA_API_KEY},
    json=payload
)

if response.status_code != 200:
    print('Failed to add TimescaleDB datasource')
    print(response.text)
else:
    print('Added TimescaleDB datasource')