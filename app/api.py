import os
import json
import logging
import datetime
import requests
import threading
from db import TimescaleDB
from dotenv import load_dotenv

load_dotenv()


class APITriggers:
    object_count = 0

    def __init__(self, DEVELOPER_HUB_TOKEN=None):
        self.DEVELOPER_HUB_TOKEN = DEVELOPER_HUB_TOKEN
        if DEVELOPER_HUB_TOKEN is None:
            self.DEVELOPER_HUB_TOKEN = os.getenv('DEVELOPER_HUB_TOKEN')
        self.organizations = None
        self.request_header = {
            'Authorization': "Bearer " + self.DEVELOPER_HUB_TOKEN,
            'Content-Type': 'application/json'
        }
        self.db = TimescaleDB()

        self.API_URL_ORGS = os.getenv('WEBEX_API_URL') + "/organizations"
        self.API_URL_CLUSTER_AVAILABILITY = os.getenv(
            'WEBEX_API_URL') + "/videoMesh/clusters/availability"
        self.API_URL_NODE_AVAILABILITY = os.getenv(
            'WEBEX_API_URL') + "/videoMesh/nodes/availability"
        self.API_URL_CLOUD_OVERFLOW = os.getenv(
            'WEBEX_API_URL') + "/videoMesh/cloudOverflow"
        self.API_URL_CALL_REDIRECTS = os.getenv(
            'WEBEX_API_URL') + "/videoMesh/callRedirects"
        self.API_URL_MHM_TOOLS = os.getenv(
            'WEBEX_API_URL') + "/videoMesh/mediaHealthMonitor"
        self.API_URL_REACHABILITY = os.getenv(
            'WEBEX_API_URL') + "/videoMesh/reachabilityTest"
        self.API_URL_CLUSTER_UTILIZATION = os.getenv(
            'WEBEX_API_URL') + "/videoMesh/utilization"
        self.API_URL_CLUSTER_DETAILS = os.getenv(
            'WEBEX_API_URL') + "/videoMesh/clusters"

        if '.object_count' not in os.listdir(os.getcwd()):
            APITriggers.object_count = 1
            with open('.object_count', 'w') as f:
                f.write('1')
        else:
            with open('.object_count', 'r') as f:
                APITriggers.object_count = int(f.read())
                APITriggers.object_count += 1
            with open('.object_count', 'w') as f:
                f.write(str(APITriggers.object_count))   

        if APITriggers.object_count == 1:
            thread = threading.Thread(target=self.fetch_historical_data)
            thread.start()

    def trigger_all_endpoints(self, start_time, end_time, fetch_orgs=True):
        if fetch_orgs:
            self.list_organizations()
        self.list_cluster_details()
        self.list_clusters_availability(start_time, end_time)
        self.list_node_availability(start_time, end_time)
        self.list_cloud_overflow(start_time, end_time)
        self.list_call_redirects(start_time, end_time)
        self.list_media_health_monitoring_tool(start_time, end_time)
        self.list_reachability(start_time, end_time)
        self.list_cluster_utilization(start_time, end_time)

    def fetch_historical_data(self, history="month", fetch_orgs=True):
        end_time = datetime.datetime.utcnow()
        if history == "year":
            start_time = datetime.datetime(end_time.year, 1, 1, 0, 0, 0)
        elif history == "month":
            start_time = end_time - datetime.timedelta(days=31)

        logging.info('Fetching historical data from %s to %s', start_time, end_time)
        while end_time >= start_time:
            self.trigger_all_endpoints(end_time - datetime.timedelta(days=7), end_time, fetch_orgs)
            end_time = end_time - datetime.timedelta(days=7)
        logging.info('Historical data fetching complete')

    def list_organizations(self):
        url = self.API_URL_ORGS
        response = requests.get(url, headers=self.request_header)
        response = response.json()
        logging.debug(response)
        logging.debug(f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes")
        self.organizations = dict()
        for organization_detail in response['items']:
            self.organizations[organization_detail['id']] = {
                'displayName': organization_detail['displayName'],
                'created': datetime.datetime.strptime(organization_detail['created'], "%Y-%m-%dT%H:%M:%S.%fZ")
            }
            self.db.add_organization(
                organization_id=organization_detail['id'],
                organization_name=organization_detail['displayName'],
                created_at=self.organizations[organization_detail['id']]['created']
            )
        return self.organizations

    def get_organization_details(self, organization_id):
        url = f"{self.API_URL_ORGS}/{organization_id}"
        response = requests.get(url, headers=self.request_header)
        response = response.json()
        organization_details = {
            'displayName': response['displayName'],
            'created': datetime.datetime.strptime(response['created'], "%Y-%m-%dT%H:%M:%S.%fZ")
        }
        return organization_details

    def get_cluster_availability(self, organization_id, from_timestamp, to_timestamp):
        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        params = {
            'from': from_timestamp,
            'to': to_timestamp,
            'orgId': organization_id
        }
        url = self.API_URL_CLUSTER_AVAILABILITY
        response = requests.get(
            url, headers=self.request_header, params=params)
        response = response.json()
        return response

    def list_clusters_availability(self, from_timestamp, to_timestamp):
        current_time = datetime.datetime.utcnow()
        for organization_id in self.organizations:
            logging.info(
                f"Fetching cluster availability details for {self.organizations[organization_id]['displayName']} between {from_timestamp} and {to_timestamp}")
            try:
                response = self.get_cluster_availability(
                    organization_id, from_timestamp, to_timestamp)
                logging.debug(response)
                logging.debug(f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes")
                if response:
                    for organization_results in response:
                        for cluster_result in organization_results["items"]:
                            try:
                                cluster_id = cluster_result["clusterId"]
                                cluster_name = cluster_result["clusterName"]
                                for availability_segment in cluster_result["availabilitySegments"]:
                                    try:
                                        num_offline_nodes = availability_segment["noOfOfflineNodes"]
                                        num_online_nodes = availability_segment["noOfOnlineNodes"]
                                        availability = availability_segment["availability"]
                                        segment_start_time = datetime.datetime.strptime(
                                            availability_segment["segmentStartTime"], "%Y-%m-%dT%H:%M:%SZ")
                                        segment_end_time = datetime.datetime.strptime(
                                            availability_segment["segmentEndTime"], "%Y-%m-%dT%H:%M:%SZ")

                                        self.db.add_cluster_availability(
                                            current_time,
                                            organization_id,
                                            cluster_id,
                                            cluster_name,
                                            num_offline_nodes,
                                            num_online_nodes,
                                            availability,
                                            segment_start_time,
                                            segment_end_time
                                        )
                                    except Exception as e:
                                        logging.error(f"Error parsing availability segment: {e}: {availability_segment}:\n{response}")
                            except Exception as e:
                                logging.error(f"Error parsing cluster data: {e} : {cluster_result}:\n{response}")
            except Exception as e:
                logging.error(
                    f"Error fetching cluster availability details for {self.organizations[organization_id]['displayName']} ({organization_id}): {e}")

    def get_node_availability(self, cluster_id, from_timestamp, to_timestamp):
        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        params = {
            'from': from_timestamp,
            'to': to_timestamp,
            'clusterId': cluster_id
        }
        url = self.API_URL_NODE_AVAILABILITY
        response = requests.get(
            url, headers=self.request_header, params=params)
        response = response.json()
        return response

    def list_node_availability(self, from_timestamp, to_timestamp):
        current_time = datetime.datetime.utcnow()
        cluster_ids = self.db.get_all_cluster_ids()
        for cluster_id in cluster_ids:
            logging.info(
                f"Fetching node availability details for {cluster_id} between {from_timestamp} and {to_timestamp}")
            try:
                response = self.get_node_availability(
                    cluster_id, from_timestamp, to_timestamp)
                logging.debug(response)
                logging.debug(f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes")
                if response:
                    for cluster_results in response:
                        try:
                            organization_id = cluster_results["orgId"]
                            for cluster in cluster_results["items"]:
                                try:
                                    cluster_name = cluster["clusterName"]
                                    node_id = cluster["nodeId"]
                                    host_name = cluster["hostNameOrIp"]
                                    for availability_segment in cluster["availabilitySegments"]:
                                        try:
                                            num_offline_nodes = availability_segment["noOfOfflineNodes"]
                                            num_online_nodes = availability_segment["noOfOnlineNodes"]
                                            availability = availability_segment["availability"]
                                            segment_start_time = datetime.datetime.strptime(
                                                availability_segment["segmentStartTime"], "%Y-%m-%dT%H:%M:%SZ")
                                            segment_end_time = datetime.datetime.strptime(
                                                availability_segment["segmentEndTime"], "%Y-%m-%dT%H:%M:%SZ")

                                            self.db.add_node_availability(
                                                current_time,
                                                organization_id,
                                                cluster_id,
                                                cluster_name,
                                                node_id,
                                                host_name,
                                                num_offline_nodes,
                                                num_online_nodes,
                                                availability,
                                                segment_start_time,
                                                segment_end_time
                                            )
                                        except Exception as e:
                                            logging.error(f"Error parsing availability segment: {e}: {availability_segment}:\n{response}")
                                except Exception as e:
                                    logging.error(f"Error parsing cluster: {e} : {cluster}:\n{response}")
                        except Exception as e:
                            logging.error(f"Error parsing cluster results: {e} : {cluster_results}:\n{response}")
            except Exception as e:
                logging.error(
                    f"Error fetching node availability details for {cluster_id}: {e}")

    def get_cloud_overflow(self, organization_id, from_timestamp, to_timestamp):
        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        params = {
            'from': from_timestamp,
            'to': to_timestamp,
            'orgId': organization_id
        }
        url = self.API_URL_CLOUD_OVERFLOW
        response = requests.get(
            url, headers=self.request_header, params=params)
        response = response.json()
        return response

    def list_cloud_overflow(self, from_timestamp, to_timestamp):
        current_time = datetime.datetime.utcnow()
        for organization_id in self.organizations:
            logging.info(
                f"Fetching cloud overflow details for {self.organizations[organization_id]['displayName']} between {from_timestamp} and {to_timestamp}")
            try:
                response = self.get_cloud_overflow(
                    organization_id, from_timestamp, to_timestamp)
                logging.debug(response)
                logging.debug(f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes")
                aggregation_interval = response["aggregationInterval"]
                for overflow_result in response["items"]:
                    try:
                        overflow_time = datetime.datetime.strptime(
                            overflow_result["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
                        overflow_reason = overflow_result["overflowDetails"][0]["overflowReason"]
                        overflow_count = overflow_result["overflowDetails"][0]["overflowCount"]
                        remediation = overflow_result["overflowDetails"][0]["possibleRemediation"]

                        self.db.add_cloud_overflow(
                            current_time,
                            organization_id,
                            aggregation_interval,
                            from_timestamp,
                            to_timestamp,
                            overflow_time,
                            overflow_reason,
                            overflow_count,
                            remediation
                        )
                    except Exception as e:
                        logging.error(f"Error parsing overflow result: {e}: {overflow_result}:\n{response}")
            except Exception as e:
                logging.error(
                    f"Error fetching cloud overflow details for {self.organizations[organization_id]['displayName']} ({organization_id}): {e}")

    def get_call_redirects(self, organization_id, from_timestamp, to_timestamp):
        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        params = {
            'from': from_timestamp,
            'to': to_timestamp,
            'orgId': organization_id
        }
        url = self.API_URL_CALL_REDIRECTS
        response = requests.get(
            url, headers=self.request_header, params=params)
        response = response.json()
        return response

    def list_call_redirects(self, from_timestamp, to_timestamp):
        current_time = datetime.datetime.utcnow()
        for organization_id in self.organizations:
            logging.info(
                f"Fetching call redirect details for {self.organizations[organization_id]['displayName']} between {from_timestamp} and {to_timestamp}")
            try:
                response = self.get_call_redirects(
                    organization_id, from_timestamp, to_timestamp)
                logging.debug(response)
                logging.debug(f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes")
                aggregation_interval = response["aggregationInterval"]
                for organization_results in response["items"]:
                    try:
                        redirect_time = datetime.datetime.strptime(
                            organization_results["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
                        for cluster_result in organization_results["clusters"]:
                            try:
                                cluster_id = cluster_result["clusterId"]
                                cluster_name = cluster_result["clusterName"]
                                redirect_reason = cluster_result["redirectDetails"][0]["redirectReason"]
                                redirect_count = cluster_result["redirectDetails"][0]["redirectCount"]
                                remediation = cluster_result["redirectDetails"][0]["possibleRemediation"]

                                self.db.add_call_redirects(
                                    current_time,
                                    organization_id,
                                    aggregation_interval,
                                    from_timestamp,
                                    to_timestamp,
                                    redirect_time,
                                    cluster_id,
                                    cluster_name,
                                    redirect_reason,
                                    redirect_count,
                                    remediation
                                )
                            except Exception as e:
                                logging.error(f"Error parsing cluster result: {e}: {cluster_result}:\n{response}")
                    except Exception as e:
                        logging.error(f"Error parsing organization result: {e}: {organization_results}:\n{response}")
            except Exception as e:
                logging.error(
                    f"Error fetching call redirect details for {self.organizations[organization_id]['displayName']} ({organization_id}): {e}")

    def get_media_health_monitoring_tool(self, organization_id, from_timestamp, to_timestamp):
        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        params = {
            'from': from_timestamp,
            'to': to_timestamp,
            'orgId': organization_id
        }
        url = self.API_URL_MHM_TOOLS
        response = requests.get(
            url, headers=self.request_header, params=params)
        response = response.json()
        return response

    def list_media_health_monitoring_tool(self, from_timestamp, to_timestamp):
        current_time = datetime.datetime.utcnow()
        for organization_id in self.organizations:
            logging.info(
                f"Fetching media health monitoring tool details for {self.organizations[organization_id]['displayName']} between {from_timestamp} and {to_timestamp}")
            try:
                response = self.get_media_health_monitoring_tool(
                    organization_id, from_timestamp, to_timestamp)
                logging.debug(response)
                logging.debug(f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes")
                for cluster in response["items"]:
                    for cluster_result in cluster["clusters"]:
                        try:
                            cluster_id = cluster_result["clusterId"]
                            cluster_name = cluster_result["clusterName"]
                            for node_result in cluster_result["nodes"]:
                                try:
                                    node_id = node_result["nodeId"]
                                    host_name = node_result["hostName"]
                                    for test_results in node_result["mhmTestResults"]:
                                        test_time = datetime.datetime.strptime(
                                            test_results["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
                                        for test in test_results["testResults"]:
                                            test_name = test["testName"]
                                            test_status = test["testResult"]
                                            test_failure_reason = None
                                            if test_status == "Failed":
                                                test_failure_reason = test["failureReason"]

                                            self.db.add_media_health_monitoring_tool(
                                                current_time,
                                                organization_id,
                                                from_timestamp,
                                                to_timestamp,
                                                cluster_id,
                                                cluster_name,
                                                node_id,
                                                host_name,
                                                test_time,
                                                test_name,
                                                test_status,
                                                test_failure_reason
                                            )
                                except Exception as e:
                                    logging.error(f"Error parsing node results: {e}: {node_result}:\n{response}")
                        except Exception as e:
                            logging.error(f"Error parsing cluster results: {e}: {cluster_result}:\n{response}")
            except Exception as e:
                logging.error(
                    f"Error fetching media health monitoring tool details for {self.organizations[organization_id]['displayName']} ({organization_id}): {e}")

    def get_reachability(self, organization_id, from_timestamp, to_timestamp):
        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        params = {
            'from': from_timestamp,
            'to': to_timestamp,
            'orgId': organization_id
        }
        url = self.API_URL_REACHABILITY
        response = requests.get(
            url, headers=self.request_header, params=params)
        response = response.json()
        return response
    
    def list_reachability(self, from_timestamp, to_timestamp):
        current_time = datetime.datetime.utcnow()
        for organization_id in self.organizations:
            logging.info(
                f"Fetching reachability details for {self.organizations[organization_id]['displayName']} between {from_timestamp} and {to_timestamp}")
            try:
                response = self.get_reachability(
                    organization_id, from_timestamp, to_timestamp)
                logging.debug(response)
                logging.debug(f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes")
                for cluster_result in response["items"]["clusters"]:
                    try:
                        cluster_id = cluster_result["clusterId"]
                        cluster_name = cluster_result["clusterName"]
                        for node_result in cluster_result["nodes"]:
                            try:
                                node_id = node_result["nodeId"]
                                host_name = node_result["hostNameOrIp"]
                                for test_results in node_result["testResults"]:
                                    destination_cluster = test_results["destinationCluster"]
                                    for result in test_results["stunResults"]:
                                        test_time = datetime.datetime.strptime(
                                            result["timestamp"], "%Y-%m-%d %H:%M:%S.%f")

                                        for udp_results in result["udp"]:
                                            port = udp_results["port"]
                                            reachability = udp_results["reachable"]
                                            self.db.add_reachability(
                                                current_time,
                                                organization_id,
                                                from_timestamp,
                                                to_timestamp,
                                                cluster_id,
                                                cluster_name,
                                                node_id,
                                                host_name,
                                                destination_cluster,
                                                test_time,
                                                "udp",
                                                port,
                                                reachability
                                            )

                                        for tcp_results in result["tcp"]:
                                            port = tcp_results["port"]
                                            reachability = tcp_results["reachable"]
                                            self.db.add_reachability(
                                                current_time,
                                                organization_id,
                                                from_timestamp,
                                                to_timestamp,
                                                cluster_id,
                                                cluster_name,
                                                node_id,
                                                host_name,
                                                destination_cluster,
                                                test_time,
                                                "tcp",
                                                port,
                                                reachability
                                            )

                            except Exception as e:
                                logging.error(f"Error parsing node results: {e}: {node_result}:\n{response}")
                    except Exception as e:
                        logging.error(f"Error parsing cluster results: {e}: {cluster_result}:\n{response}")
            except Exception as e:
                logging.error(
                    f"Error fetching reachability details for {self.organizations[organization_id]['displayName']} ({organization_id}): {e}")

    def get_cluster_utlization(self, organization_id, from_timestamp, to_timestamp):
        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        params = {
            'from': from_timestamp,
            'to': to_timestamp,
            'orgId': organization_id
        }
        url = self.API_URL_CLUSTER_UTILIZATION
        response = requests.get(
            url, headers=self.request_header, params=params)
        response = response.json()
        return response

    def list_cluster_utilization(self, from_timestamp, to_timestamp):
        current_time = datetime.datetime.utcnow()
        for organization_id in self.organizations:
            logging.info(
                f"Fetching cluster utilization details for {self.organizations[organization_id]['displayName']} between {from_timestamp} and {to_timestamp}")
            try:
                response = self.get_cluster_utlization(
                    organization_id, from_timestamp, to_timestamp)
                logging.debug(response)
                logging.debug(f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes")
                aggregation_interval = response["aggregationInterval"]
                for cluster_result in response["items"]:
                    try:
                        measure_time = cluster_result['timestamp']
                        for cluster in cluster_result['clusters']:
                            try:
                                cluster_id = cluster['clusterId']
                                cluster_name = cluster['clusterName']
                                peak_cpu = cluster['utilizationMetrics']['peakCpu']
                                avg_cpu = cluster['utilizationMetrics']['avgCpu']
                                active_calls = cluster['utilizationMetrics']['activeCalls']

                                self.db.add_cluster_utlization(
                                    current_time,
                                    organization_id,
                                    from_timestamp,
                                    to_timestamp,
                                    aggregation_interval,
                                    measure_time,
                                    cluster_id,
                                    cluster_name,
                                    peak_cpu,
                                    avg_cpu,
                                    active_calls
                                )

                            except Exception as e:
                                logging.error(f"Error parsing cluster results: {e}: {cluster}:\n{response}")
                    except Exception as e:
                        logging.error(f"Error parsing cluster results: {e}: {cluster_result}:\n{response}")
            except Exception as e:
                logging.error(
                    f"Error fetching cluster utilization details for {self.organizations[organization_id]['displayName']} ({organization_id}): {e}")

    def get_cluster_details(self, organization_id):
        params = {'orgId': organization_id}
        url = self.API_URL_CLUSTER_DETAILS
        response = requests.get(url, headers=self.request_header, params=params)
        response = response.json()
        return response

    def list_cluster_details(self):
        for organization_id in self.organizations:
            logging.info(
                f"Fetching cluster details for {self.organizations[organization_id]['displayName']}")
            try:
                response = self.get_cluster_details(organization_id)
                logging.debug(response)
                logging.debug(f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes")
                for cluster_result in response["items"]:
                    try:
                        cluster_id = cluster_result["clusterId"]
                        cluster_name = cluster_result["clusterName"]
                        release_channel = cluster_result["releaseChannel"]
                        upgrade_schedule_days = cluster_result["upgradeSchedule"]["scheduleDays"]
                        upgrade_schedule_days = ",".join(upgrade_schedule_days)
                        upgrade_schedule_time = cluster_result["upgradeSchedule"]["scheduleTime"] + ":00"
                        upgrade_schedule_timezone = cluster_result["upgradeSchedule"]["scheduleTimeZone"]
                        upgrade_pending = cluster_result["upgradeSchedule"]["upgradePending"]
                        next_upgrade_time = cluster_result["upgradeSchedule"]["nextUpgradeTime"]
                        next_upgrade_time = datetime.datetime.strptime(next_upgrade_time, "%Y-%m-%dT%H:%M:%SZ")
                        for node_result in cluster_result["nodes"]:
                            try:
                                node_id = node_result["nodeId"]
                                host_name = node_result["hostNameOrIp"]

                                self.db.add_cluster_details(
                                    organization_id,
                                    cluster_id,
                                    cluster_name, 
                                    node_id,
                                    host_name,
                                    release_channel,
                                    upgrade_schedule_days,
                                    upgrade_schedule_time,
                                    upgrade_schedule_timezone,
                                    upgrade_pending,
                                    next_upgrade_time
                                )

                            except Exception as e:
                                logging.error(f"Error parsing node results: {e}: {node_result}:\n{response}")
                    except Exception as e:
                        logging.error(f"Error parsing cluster results: {e}: {cluster_result}:\n{response}")
            except Exception as e:
                logging.error(
                    f"Error fetching cluster details for {self.organizations[organization_id]['displayName']} ({organization_id}): {e}")