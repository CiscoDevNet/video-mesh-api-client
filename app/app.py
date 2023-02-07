import logging
import datetime
import argparse
from dotenv import load_dotenv
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

from api import APITriggers
from auth import Authentication

from logging import config
config.fileConfig("app/conf/logging.conf")

load_dotenv()
app = Flask(__name__)
parser = argparse.ArgumentParser(description="Flask app for VideoMesh APIs")
parser.add_argument("--host", default="0.0.0.0", help="Host to listen on")
parser.add_argument("--port", default=2808, help="Port to listen on")
parser.add_argument(
    "-i",
    "--interval-minutes",
    default=10,
    type=int,
    help="Interval in minutes to fetch data"
)
parser.add_argument(
    "-t", "--time", default=30, type=int, help="Time period in minutes to fetch data"
)
parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
args = parser.parse_args()
app.logger.info(f"Starting Flask app with args: {args}")


def execute_api_triggers():
    global api
    if api is None or api.DEVELOPER_HUB_TOKEN is None:
        logging.warn("No API object or token. Skipping API triggers")
        return
    current_time = datetime.datetime.utcnow()
    to_time = current_time
    from_time = current_time - datetime.timedelta(minutes=args.time)
    logging.info(f"Fetching latest data from {from_time} to {to_time}")
    api.trigger_all_endpoints(from_time, to_time)
    logging.info(f"Finished fetching latest data")


def execute_auth_trigger():
    global api
    global auth

    logging.info("Checking for token expiry")
    result = auth.check_authentication_token_expiry(api)
    if result is not None:
        api = result


@app.route("/")
def index():
    return "Hello, World", 200


@app.route("/oauth")
def oauth():
    global api
    global auth

    if "code" in request.args:
        auth_code = request.args.get("code")
        status = auth.generate_authentication_tokens(auth_code)
        if status:
            logging.info(
                f"Access and Refresh tokens generated successfully at {auth.LAST_TOKEN_REFRESH_TIME}")
            api = APITriggers(auth.ACCESS_TOKEN)
            return "Access granted! Application is now running!", 200
        else:
            logging.error("Failed to generate tokens")
            return "Failed to generate tokens", 500
    else:
        return "Access denied", 401


if __name__ == "__main__":
    api: APITriggers = None
    auth = Authentication()
    scheduler = BackgroundScheduler()
    scheduler.add_job(execute_api_triggers, "interval",
                      minutes=args.interval_minutes)
    scheduler.add_job(execute_auth_trigger, "interval", hours=24)
    scheduler.start()
    app.run(
        debug=args.debug,
        host=args.host,
        port=args.port,
        use_reloader=False
    )
