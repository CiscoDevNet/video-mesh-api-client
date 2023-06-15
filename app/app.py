import datetime
import logging
from logging import config
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request

import utils
from api import APITriggers
from auth import Authentication

from db import APIDatabase
import parser

app = Flask(__name__)


def setup_logging():
    """
    Setup logging file

    :return: None
    """
    if APP_CONFIG["app"].get("logging_config") and (filepath := Path(APP_CONFIG["app"]["logging_config"])).exists():
        config.fileConfig(filepath)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s : %(filename)s - %(funcName)s - %(lineno)d : %(message)s",
            filename="app.log",
            filemode="w",
        )


def execute_api_triggers():
    """
    Execute API triggers to fetch latest data

    :return: None
    """
    global api

    if api is None or api.access_token is None:
        logging.warning("No API object or token found. Skipping API triggers")
        return

    current_time = datetime.datetime.utcnow()
    from_time = current_time - datetime.timedelta(minutes=APP_CONFIG["app"]["time"])
    to_time = current_time
    logging.info(f"Fetching latest data from {from_time} to {to_time}")
    api.trigger_all_api_endpoints(from_time, to_time)
    logging.info(f"Finished fetching latest data from {from_time} to {to_time}")    
    

def execute_auth_renewal_trigger():
    """
    Execute authentication trigger to check for token expiry

    :return: None
    """
    global api
    global auth

    logging.info("Checking for token expiry")
    auth_check = auth.check_authentication_token_expiry(api)
    api = auth_check if auth_check is not None else api


@app.route("/")
def index() -> tuple[str, int]:
    """
    Index route

    :return: A tuple containing the response and the status code
    """
    return "Hello, World", 200


@app.route("/webhooks", methods=['POST'])
def webhooks_listener() :
    """
    Webhooks Listener route
    
    :return: None
    """
    
    webhook_parser = parser.Parser()
    current_time = datetime.datetime.utcnow()
    req_json = request.json["data"]["map"]
    db = APIDatabase(
            connection_url=APP_CONFIG["api"]["database"]["url"],
            create_tables_on_init=True
        )
    webhook_record = webhook_parser.webhook_event_parse(current_time, req_json)
    db.insert_records(webhook_record, "webhook_events")
    
    return "OK"
    

    
@app.route("/oauth")
def oauth() -> tuple[str, int]:
    """
    OAuth route to generate access and refresh tokens

    :return: A tuple containing the response and the status code
    """
    global api
    global auth

    auth_code = request.args.get("code")
    if auth_code is None:
        return "Access denied", 401

    auth_code = request.args.get("code")
    status = auth.generate_authentication_tokens(auth_code)
    if status:
        logging.info(f"Access and Refresh tokens generated successfully at {auth.last_token_refresh_time}")

        api = APITriggers(
            api_config=APP_CONFIG["api"],
            fetch_historical_data_on_init=True,
            create_tables_on_init=True
        )
        return "Access granted! Application is now running!", 200
    else:
        logging.error(f"Failed to generate tokens. Received args: {request.args}")
        return "Failed to generate tokens", 500


if __name__ == "__main__":
    """
    Main function to run the Flask app
    """
    APP_CONFIG: Optional[dict] = utils.load_config("app/conf/config.yaml")
    if APP_CONFIG is None:
        raise ValueError("Invalid configuration file")

    setup_logging()

    api: Optional[APITriggers] = None
    auth = Authentication(APP_CONFIG["api"])
    scheduler = BackgroundScheduler()
    scheduler.add_job(execute_api_triggers, "interval", minutes=APP_CONFIG["app"]["update_interval_minutes"])
    
    scheduler.add_job(execute_auth_renewal_trigger, "interval", hours=APP_CONFIG["app"]["auth_interval_hours"])
    scheduler.start()
    app.run(
        debug=APP_CONFIG["app"]["debug"],
        host=APP_CONFIG["app"]["host"],
        port=APP_CONFIG["app"]["port"],
        use_reloader=False
    )
