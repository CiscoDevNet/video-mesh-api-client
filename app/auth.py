import os
import json
import logging
import requests
import datetime
from typing import Union
from api import APITriggers
from dotenv import load_dotenv

load_dotenv()


class Authentication:
    def __init__(self):
        self.API_URL_ACCESS_TOKEN = os.getenv(
            "WEBEX_API_URL") + "/access_token"
        self.INTEGRATION_CLIENT_ID = os.getenv("INTEGRATION_CLIENT_ID")
        self.INTEGRATION_CLIENT_SECRET = os.getenv("INTEGRATION_CLIENT_SECRET")
        self.REDIRECT_URI = os.getenv("REDIRECT_URI")
        self.ACCESS_TOKEN = None
        self.REFRESH_TOKEN = None

    def generate_authentication_tokens(self, auth_code: str):
        headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded"
        }
        payload = (
            "grant_type=authorization_code&client_id={0}&client_secret={1}&"
            "code={2}&redirect_uri={3}"
        ).format(self.INTEGRATION_CLIENT_ID, self.INTEGRATION_CLIENT_SECRET, auth_code, self.REDIRECT_URI)
        response = requests.post(
            url=self.API_URL_ACCESS_TOKEN, data=payload, headers=headers)
        response_data = json.loads(response.text)
        if "access_token" not in response_data or "refresh_token" not in response_data:
            logging.error(
                f"Response did not return Authentication Tokens: {response_data}")
            return False
        self.ACCESS_TOKEN = response_data["access_token"]
        self.REFRESH_TOKEN = response_data["refresh_token"]
        self.LAST_TOKEN_REFRESH_TIME = datetime.datetime.utcnow()
        return True

    def renew_authentication_tokens(self):
        headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded"
        }
        payload = (
            "grant_type=refresh_token&client_id={0}&client_secret={1}&" "refresh_token={2}"
        ).format(self.INTEGRATION_CLIENT_ID, self.INTEGRATION_CLIENT_SECRET, self.REFRESH_TOKEN)
        response = requests.post(
            url=self.API_URL_ACCESS_TOKEN, data=payload, headers=headers)
        response_data = json.loads(response.text)
        if "access_token" not in response_data or "refresh_token" not in response_data:
            logging.error(
                f"Response did not return Authentication Tokens: {response_data}")
            return False
        self.ACCESS_TOKEN = response_data["access_token"]
        self.REFRESH_TOKEN = response_data["refresh_token"]
        self.LAST_TOKEN_REFRESH_TIME = datetime.datetime.utcnow()
        return True

    def check_authentication_token_expiry(self, api: Union[APITriggers, None]):
        if api is None or api.DEVELOPER_HUB_TOKEN is None:
            logging.error(
                "API object is not initialized or Developer Hub Token is not set")
            return
        current_time = datetime.datetime.utcnow()
        if (current_time - self.LAST_TOKEN_REFRESH_TIME).days >= 12:
            logging.info("Token expired. Refreshing token")
            status = self.renew_authentication_tokens(self.REFRESH_TOKEN)
            if status == False:
                logging.error("Failed to refresh token")
                return
            api = APITriggers(self.ACCESS_TOKEN, False, False)
        return api
