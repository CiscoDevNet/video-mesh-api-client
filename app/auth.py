import os
import json
import logging
import requests
import datetime
from api import APITriggers
from dotenv import load_dotenv

load_dotenv()


def generate_tokens(auth_code):
    url = os.getenv('WEBEX_API_URL') + "/access_token"
    client_id = os.getenv('INTEGRATION_CLIENT_ID')
    client_secret = os.getenv('INTEGRATION_CLIENT_SECRET')
    redirect_uri = os.getenv('REDIRECT_URI')
    headers = {'accept': 'application/json',
               'content-type': 'application/x-www-form-urlencoded'}
    payload = ("grant_type=authorization_code&client_id={0}&client_secret={1}&"
               "code={2}&redirect_uri={3}").format(client_id, client_secret, auth_code, redirect_uri)
    req = requests.post(url=url, data=payload, headers=headers)
    results = json.loads(req.text)
    access_token = results["access_token"]
    logging.debug('Access token: ' + access_token)
    refresh_token = results["refresh_token"]
    return access_token, refresh_token


def renew_tokens(refresh_token):
    url = os.getenv('WEBEX_API_URL') + "/access_token"
    client_id = os.getenv('INTEGRATION_CLIENT_ID')
    client_secret = os.getenv('INTEGRATION_CLIENT_SECRET')
    headers = {'accept': 'application/json',
               'content-type': 'application/x-www-form-urlencoded'}
    payload = ("grant_type=refresh_token&client_id={0}&client_secret={1}&"
               "refresh_token={2}").format(client_id, client_secret, refresh_token)
    req = requests.post(url=url, data=payload, headers=headers)
    results = json.loads(req.text)
    access_token = results["access_token"]
    logging.debug('Access token: ' + access_token)
    refresh_token = results["refresh_token"]
    return access_token, refresh_token


def check_token_expiry(api, token_set_time):
    if api is None or api.DEVELOPER_HUB_TOKEN is None:
        return

    current_time = datetime.datetime.utcnow()
    if (current_time - token_set_time).days >= 12:
        logging.info('Token expired. Refreshing token')
        ACCESS_TOKEN, REFRESH_TOKEN = renew_tokens(REFRESH_TOKEN)
        TOKEN_SET_TIME = current_time
        api = APITriggers(ACCESS_TOKEN)
        return api, TOKEN_SET_TIME, ACCESS_TOKEN, REFRESH_TOKEN
