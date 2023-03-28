import datetime
import json
import logging
from typing import Optional

import requests

from api import APITriggers


class Authentication:
    def __init__(self, api_config: dict):
        """
        Initialize Authentication object

        :param api_config: API configuration parameters
        """
        self.api_config = api_config
        self.access_token_endpoint = f'{api_config["host"]}/access_token'
        self.integration_client_id = api_config["integration"]["client_id"]
        self.integration_client_secret = api_config["integration"]["client_secret"]
        self.redirect_uri = api_config["integration"]["redirect_uri"]

        self.access_token = None
        self.refresh_token = None
        self.last_token_refresh_time = None
        self.update_config_with_access_tokens()

        self.default_request_headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded"
        }

    def update_config_with_access_tokens(self) -> None:
        """
        Update API configuration with access tokens

        :return: None
        """
        self.api_config["access_token"] = self.access_token
        self.api_config["refresh_token"] = self.refresh_token
        self.api_config["last_token_refresh_time"] = self.last_token_refresh_time

    def generate_authentication_tokens(self, auth_code: str) -> bool:
        """
        Generate access and refresh tokens

        :param auth_code: Authorization code
        :return: True if tokens were generated successfully, False otherwise
        """
        payload = f"grant_type=authorization_code&client_id={self.integration_client_id}&" \
                  f"client_secret={self.integration_client_secret}&" \
                  f"code={auth_code}&" \
                  f"redirect_uri={self.redirect_uri}"

        response = requests.post(
            url=self.access_token_endpoint,
            data=payload,
            headers=self.default_request_headers
        )
        logging.debug(f"Authentication Response: {response.text}")
        response_data = json.loads(response.text)

        if "access_token" not in response_data or "refresh_token" not in response_data:
            logging.error(f"Response did not return Authentication Tokens: {response_data}")
            return False

        self.access_token = response_data["access_token"]
        self.refresh_token = response_data["refresh_token"]
        self.last_token_refresh_time = datetime.datetime.utcnow()
        self.update_config_with_access_tokens()
        return True

    def renew_authentication_tokens(self) -> bool:
        """
        Renew access and refresh tokens

        :return: True if tokens were renewed successfully, False otherwise
        """
        payload = f"grant_type=refresh_token&client_id={self.integration_client_id}&" \
                  f"client_secret={self.integration_client_secret}&" \
                  f"refresh_token={self.refresh_token}"

        response = requests.post(
            url=self.access_token_endpoint,
            data=payload,
            headers=self.default_request_headers
        )
        logging.debug(f"Renewal Authentication Response: {response.text}")
        response_data = json.loads(response.text)

        if "access_token" not in response_data or "refresh_token" not in response_data:
            logging.error(f"Response did not return Authentication Tokens: {response_data}")
            return False

        self.access_token = response_data["access_token"]
        self.refresh_token = response_data["refresh_token"]
        self.last_token_refresh_time = datetime.datetime.utcnow()
        self.update_config_with_access_tokens()
        return True

    def check_authentication_token_expiry(self, api: Optional[APITriggers]) -> Optional[APITriggers]:
        """
        Check if the authentication token has expired and renew it if it has

        :param api: API object
        :return: API object if token was renewed successfully, None otherwise
        """
        if api is None or api.access_token is None:
            logging.error("API object is not initialized or Developer Hub Token is not set")
            return None

        current_time = datetime.datetime.utcnow()
        if (current_time - self.last_token_refresh_time).days >= 12:
            logging.info(f"Token expired. Refreshing token at {current_time}")
            status = self.renew_authentication_tokens()
            if not status:
                logging.error("Failed to refresh token")
                return None

            api = APITriggers(
                api_config=self.api_config,
                fetch_historical_data_on_init=False,
                create_tables_on_init=False
            )
        return api
