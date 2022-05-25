import json
import logging
import datetime
import argparse
from auth import *
from api import APITriggers
from dotenv import load_dotenv
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

from logging import config
config.fileConfig('app/conf/logging.conf')

api = None
ACCESS_TOKEN = None
REFRESH_TOKEN = None
TOKEN_SET_TIME = None

load_dotenv()
app = Flask(__name__)
parser = argparse.ArgumentParser(description='Flask app for VideoMesh APIs')
parser.add_argument('--host', default='0.0.0.0', help='Host to listen on')
parser.add_argument('-p', '--port', default=2808, help='Port to listen on')
parser.add_argument('-i', '--interval-minutes', default=10, type=int, help='Interval in minutes to fetch data')
parser.add_argument('-t', '--time', default=30, type=int, help='Time period in minutes to fetch data')
parser.add_argument('-d', '--debug', action='store_true', help='Debug mode')
args = parser.parse_args()
app.logger.info('Starting Flask app with args: %s', args)


@app.route('/')
def index():
    return "Hello, World"


@app.route("/organizations")
def list_organizations():
    return api.list_organizations()


@app.route("/organizations/<organization_id>")
def get_organization_details(organization_id):
    return api.get_organization_details(organization_id)


@app.route("/clusterAvailability/<organization_id>/<from_timestamp>/<to_timestamp>")
def get_cluster_availability(organization_id, from_timestamp, to_timestamp):
    return json.dumps(api.get_cluster_availability(organization_id, from_timestamp, to_timestamp))


@app.route("/clusterAvailability/<organization_id>/<from_timestamp>/<to_timestamp>")
def get_node_availability(cluster_id, from_timestamp, to_timestamp):
    return api.get_node_availability(cluster_id, from_timestamp, to_timestamp)


@app.route("/cloudOverflow/<organization_id>/<from_timestamp>/<to_timestamp>")
def get_cloud_overflow(organization_id, from_timestamp, to_timestamp):
    return json.dumps(api.get_cloud_overflow(organization_id, from_timestamp, to_timestamp))


@app.route("/callRedirects/<organization_id>/<from_timestamp>/<to_timestamp>")
def get_call_redirects(organization_id, from_timestamp, to_timestamp):
    return json.dumps(api.get_call_redirects(organization_id, from_timestamp, to_timestamp))


@app.route("/mediaHealthMonitor/<organization_id>/<from_timestamp>/<to_timestamp>")
def get_media_health_monitor(organization_id, from_timestamp, to_timestamp):
    return json.dumps(api.get_media_health_monitoring_tool(organization_id, from_timestamp, to_timestamp))

@app.route("/reachability/<organization_id>/<from_timestamp>/<to_timestamp>")
def get_reachability(organization_id, from_timestamp, to_timestamp):
    return json.dumps(api.get_reachability(organization_id, from_timestamp, to_timestamp))

@app.route("/utlization/<organization_id>/<from_timestamp>/<to_timestamp>")
def get_cluster_utlization(organization_id, from_timestamp, to_timestamp):
    return json.dumps(api.get_cluster_utlization(organization_id, from_timestamp, to_timestamp))

@app.route("/clusters/<organization_id>")
def get_cluster_details(organization_id):
    return json.dumps(api.get_cluster_details(organization_id))


@app.route("/oauth")
def oauth():
    global api
    global ACCESS_TOKEN
    global REFRESH_TOKEN
    global TOKEN_SET_TIME

    if "code" in request.args:
        auth_code = request.args.get("code")
        ACCESS_TOKEN, REFRESH_TOKEN = generate_tokens(auth_code)
        TOKEN_SET_TIME = datetime.datetime.utcnow()
        logging.info(
            "Access and Refresh tokens generated successfully at %s", TOKEN_SET_TIME)
        api = APITriggers(ACCESS_TOKEN)
        return "Access granted! Application is now running!", 200
    else:
        return "Access denied", 401


def execute_api_triggers():
    global api
    if api is None or api.DEVELOPER_HUB_TOKEN is None:
        return

    current_time = datetime.datetime.utcnow()
    to_time = current_time
    from_time = current_time - datetime.timedelta(minutes=args.time)
    logging.info('Fetching latest data from %s to %s', from_time, current_time)
    api.trigger_all_endpoints(from_time, to_time)
    logging.info('Finished fetching latest data from %s to %s', from_time, current_time)


def execute_auth_trigger():
    global api
    global ACCESS_TOKEN
    global REFRESH_TOKEN
    global TOKEN_SET_TIME

    logging.info("Checking for token expiry")
    result = check_token_expiry(api, TOKEN_SET_TIME)
    if result is not None:
        api, TOKEN_SET_TIME, ACCESS_TOKEN, REFRESH_TOKEN = result


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(execute_api_triggers, 'interval', minutes=args.interval_minutes)
    scheduler.add_job(execute_auth_trigger, 'interval', hours=24)
    scheduler.start()
    app.run(
        debug=args.debug, 
        host=args.host, 
        port=args.port, 
        use_reloader=False
    )
