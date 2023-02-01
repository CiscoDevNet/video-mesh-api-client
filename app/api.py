import os
import time
import json
import logging
import datetime
import requests
import threading
from typing import Dict
from db import TimescaleDB
from dotenv import load_dotenv

load_dotenv()


class APITriggers:
    object_count = 0

    def __init__(
        self, DEVELOPER_HUB_TOKEN: str = None, fetch_historical_data: bool = True, setup_tables: bool = True
    ):
        self.DEVELOPER_HUB_TOKEN = DEVELOPER_HUB_TOKEN
        if DEVELOPER_HUB_TOKEN is None:
            self.DEVELOPER_HUB_TOKEN = os.getenv("DEVELOPER_HUB_TOKEN")
        self.organizations = None
        self.request_header = {
            "Authorization": "Bearer " + self.DEVELOPER_HUB_TOKEN,
            "Content-Type": "application/json"
        }
        self.db = TimescaleDB(setup_tables)

        self.API_URL_ORGS = os.getenv("WEBEX_API_URL") + "/organizations"
        self.API_URL_CLUSTER_AVAILABILITY = (
            os.getenv("WEBEX_API_URL") + "/videoMesh/clusters/availability"
        )
        self.API_URL_NODE_AVAILABILITY = (
            os.getenv("WEBEX_API_URL") + "/videoMesh/nodes/availability"
        )
        self.API_URL_CLOUD_OVERFLOW = (
            os.getenv("WEBEX_API_URL") + "/videoMesh/cloudOverflow"
        )
        self.API_URL_CALL_REDIRECTS = (
            os.getenv("WEBEX_API_URL") + "/videoMesh/callRedirects"
        )
        self.API_URL_MHM_TOOLS = (
            os.getenv("WEBEX_API_URL") + "/videoMesh/mediaHealthMonitor"
        )
        self.API_URL_REACHABILITY = (
            os.getenv("WEBEX_API_URL") + "/videoMesh/reachabilityTest"
        )
        self.API_URL_CLUSTER_UTILIZATION = (
            os.getenv("WEBEX_API_URL") + "/videoMesh/utilization"
        )
        self.API_URL_CLUSTER_DETAILS = (
            os.getenv("WEBEX_API_URL") + "/videoMesh/clusters"
        )
        self.API_URL_REACHABILITY_TEST_RESULTS = (
            os.getenv("WEBEX_API_URL") +
            "/videoMesh/testResults/reachabilityTest"
        )
        self.API_URL_MEDIA_HEALTH_MONITORING_TEST_RESULTS = (
            os.getenv("WEBEX_API_URL") +
            "/videoMesh/testResults/mediaHealthMonitorTest"
        )
        self.API_URL_CONNECTIVITY_TEST_RESULTS = (
            os.getenv("WEBEX_API_URL") +
            "/videoMesh/testResults/networkTest"
        )

        if ".object_count" not in os.listdir(os.getcwd()):
            APITriggers.object_count = 1
            with open(".object_count", "w") as f:
                f.write("1")
        else:
            with open(".object_count", "r") as f:
                APITriggers.object_count = int(f.read())
                APITriggers.object_count += 1
            with open(".object_count", "w") as f:
                f.write(str(APITriggers.object_count))

        if APITriggers.object_count == 1 and fetch_historical_data:
            thread = threading.Thread(target=self.fetch_historical_data)
            thread.start()

    def call_availability_apis(self, start_time: datetime.datetime, end_time: datetime.datetime):
        self.list_clusters_availability(start_time, end_time)
        self.list_node_availability(start_time, end_time)

    def trigger_all_endpoints(self, start_time: datetime.datetime, end_time: datetime.datetime, fetch_orgs: bool = True):
        if fetch_orgs:
            self.list_organizations()

        thread_list_cluster_details = threading.Thread(
            target=self.list_cluster_details)
        thread_call_availability_apis = threading.Thread(
            target=self.call_availability_apis, args=(start_time, end_time)
        )
        thread_list_cloud_overflow = threading.Thread(
            target=self.list_cloud_overflow, args=(start_time, end_time)
        )
        thread_list_call_redirects = threading.Thread(
            target=self.list_call_redirects, args=(start_time, end_time)
        )
        thread_list_media_health_monitoring_tool = threading.Thread(
            target=self.list_media_health_monitoring_tool, args=(
                start_time, end_time)
        )
        thread_list_reachability = threading.Thread(
            target=self.list_reachability, args=(start_time, end_time)
        )
        thread_list_cluster_utilization = threading.Thread(
            target=self.list_cluster_utilization, args=(start_time, end_time)
        )
        thread_list_reachability_test_results = threading.Thread(
            target=self.list_reachability_test_results, args=(
                start_time, end_time)
        )
        thread_list_media_health_monitoring_test_results = threading.Thread(
            target=self.list_media_health_monitoring_test_results, args=(
                start_time, end_time)
        )
        thread_list_connectivity_test_results = threading.Thread(
            target=self.list_connectivity_test_results, args=(
                start_time, end_time)
        )

        api_threads = [
            thread_list_cluster_details,
            thread_call_availability_apis,
            thread_list_cloud_overflow,
            thread_list_call_redirects,
            thread_list_media_health_monitoring_tool,
            thread_list_reachability,
            thread_list_cluster_utilization,
            thread_list_reachability_test_results,
            thread_list_media_health_monitoring_test_results,
            thread_list_connectivity_test_results
        ]

        [api_thread.start() for api_thread in api_threads]
        [api_thread.join() for api_thread in api_threads]

    def fetch_historical_data(self, history: str = "month", fetch_orgs: bool = True):
        end_time = datetime.datetime.utcnow()
        start_time = end_time - datetime.timedelta(days=31)
        if history == "year":
            start_time = datetime.datetime(end_time.year, 1, 1, 0, 0, 0)
        elif history == "week":
            start_time = end_time - datetime.timedelta(days=7)
        elif history == "month":
            start_time = end_time - datetime.timedelta(days=31)
        elif history == "day":
            start_time = end_time - datetime.timedelta(days=1)
        else:
            pass

        logging.info("Fetching historical data from %s to %s",
                     start_time, end_time)
        while end_time >= start_time:
            logging.info(
                f"Fetching data for dates between {end_time - datetime.timedelta(days=7)} and {end_time}")
            self.trigger_all_endpoints(
                end_time - datetime.timedelta(days=7), end_time, fetch_orgs
            )
            end_time = end_time - datetime.timedelta(days=7)
        logging.info("Historical data fetching complete")

    def list_organizations(self) -> Dict:
        url = self.API_URL_ORGS
        response = requests.get(url, headers=self.request_header)
        tracking_id = response.headers["trackingid"]
        logging.debug(f"Tracking ID: {tracking_id}")
        response = response.json()
        logging.debug(response)
        logging.debug(
            f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes"
        )
        self.organizations = dict()
        for organization_detail in response["items"]:
            self.organizations[organization_detail["id"]] = {
                "displayName": organization_detail["displayName"],
                "created": datetime.datetime.strptime(
                    organization_detail["created"], "%Y-%m-%dT%H:%M:%S.%fZ"
                )
            }
            self.db.add_organization(
                organization_id=organization_detail["id"],
                organization_name=organization_detail["displayName"],
                created_at=self.organizations[organization_detail["id"]]["created"]
            )
        return self.organizations

    def get_organization_details(self, organization_id: str) -> Dict:
        url = f"{self.API_URL_ORGS}/{organization_id}"
        response = requests.get(url, headers=self.request_header)
        logging.debug(f"Request URL: {response.url}")
        tracking_id = response.headers["trackingid"]
        logging.debug(f"Tracking ID: {tracking_id}")
        response = response.json()
        logging.debug(response)
        organization_details = {
            "displayName": response["displayName"],
            "created": datetime.datetime.strptime(
                response["created"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
        }
        return organization_details

    def get_cluster_availability(self, organization_id: str, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime) -> Dict:
        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        params = {"from": from_timestamp,
                  "to": to_timestamp, "orgId": organization_id}
        url = self.API_URL_CLUSTER_AVAILABILITY
        response = requests.get(
            url, headers=self.request_header, params=params)
        logging.debug(f"Request URL: {response.url}")
        tracking_id = response.headers["trackingid"]
        logging.debug(f"Tracking ID: {tracking_id}")
        response = response.json()
        return response

    def list_clusters_availability(self, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime):
        current_time = datetime.datetime.utcnow()
        for organization_id in self.organizations:
            logging.info(
                f"Fetching cluster availability details for {self.organizations[organization_id]['displayName']} between {from_timestamp} and {to_timestamp}"
            )
            try:
                response = self.get_cluster_availability(
                    organization_id, from_timestamp, to_timestamp
                )
                logging.debug(response)
                logging.debug(
                    f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes"
                )
                if response:
                    for organization_results in response:
                        for cluster_result in organization_results["items"]:
                            try:
                                cluster_id = cluster_result["clusterId"]
                                cluster_name = cluster_result["clusterName"]
                                for availability_segment in cluster_result[
                                    "availabilitySegments"
                                ]:
                                    try:
                                        num_offline_nodes = availability_segment[
                                            "noOfOfflineNodes"
                                        ]
                                        num_online_nodes = availability_segment[
                                            "noOfOnlineNodes"
                                        ]
                                        availability = availability_segment[
                                            "availability"
                                        ]
                                        segment_start_time = datetime.datetime.strptime(
                                            availability_segment["segmentStartTime"],
                                            "%Y-%m-%dT%H:%M:%SZ"
                                        )
                                        segment_end_time = datetime.datetime.strptime(
                                            availability_segment["segmentEndTime"],
                                            "%Y-%m-%dT%H:%M:%SZ"
                                        )

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
                                        logging.error(
                                            f"Error parsing availability segment: {e}: {availability_segment}:\n{response}"
                                        )
                            except Exception as e:
                                logging.error(
                                    f"Error parsing cluster data: {e} : {cluster_result}:\n{response}"
                                )
            except Exception as e:
                logging.error(
                    f"Error fetching cluster availability details for {self.organizations[organization_id]['displayName']} ({organization_id}): {e}"
                )

    def get_node_availability(self, cluster_id: str, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime) -> Dict:
        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        params = {"from": from_timestamp,
                  "to": to_timestamp, "clusterId": cluster_id}
        url = self.API_URL_NODE_AVAILABILITY
        response = requests.get(
            url, headers=self.request_header, params=params)
        logging.debug(f"Request URL: {response.url}")
        tracking_id = response.headers["trackingid"]
        logging.debug(f"Tracking ID: {tracking_id}")
        response = response.json()
        return response

    def list_node_availability(self, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime):
        current_time = datetime.datetime.utcnow()
        cluster_ids = self.db.get_all_cluster_ids()
        for cluster_id in cluster_ids:
            logging.info(
                f"Fetching node availability details for {cluster_id} between {from_timestamp} and {to_timestamp}"
            )
            try:
                response = self.get_node_availability(
                    cluster_id, from_timestamp, to_timestamp
                )
                logging.debug(response)
                logging.debug(
                    f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes"
                )
                if response:
                    for cluster_results in response:
                        try:
                            organization_id = cluster_results["orgId"]
                            for cluster in cluster_results["items"]:
                                try:
                                    cluster_name = cluster["clusterName"]
                                    node_id = cluster["nodeId"]
                                    host_name = cluster["hostNameOrIp"]
                                    for availability_segment in cluster[
                                        "availabilitySegments"
                                    ]:
                                        try:
                                            availability = availability_segment[
                                                "availability"
                                            ]
                                            segment_start_time = (
                                                datetime.datetime.strptime(
                                                    availability_segment[
                                                        "segmentStartTime"
                                                    ],
                                                    "%Y-%m-%dT%H:%M:%SZ"
                                                )
                                            )
                                            segment_end_time = (
                                                datetime.datetime.strptime(
                                                    availability_segment[
                                                        "segmentEndTime"
                                                    ],
                                                    "%Y-%m-%dT%H:%M:%SZ"
                                                )
                                            )

                                            self.db.add_node_availability(
                                                current_time,
                                                organization_id,
                                                cluster_id,
                                                cluster_name,
                                                node_id,
                                                host_name,
                                                availability,
                                                segment_start_time,
                                                segment_end_time
                                            )
                                        except Exception as e:
                                            logging.error(
                                                f"Error parsing availability segment: {e}: {availability_segment}:\n{response}"
                                            )
                                except Exception as e:
                                    logging.error(
                                        f"Error parsing cluster: {e} : {cluster}:\n{response}"
                                    )
                        except Exception as e:
                            logging.error(
                                f"Error parsing cluster results: {e} : {cluster_results}:\n{response}"
                            )
            except Exception as e:
                logging.error(
                    f"Error fetching node availability details for {cluster_id}: {e}"
                )

    def get_cloud_overflow(self, organization_id: str, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime) -> Dict:
        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        params = {"from": from_timestamp,
                  "to": to_timestamp, "orgId": organization_id}
        url = self.API_URL_CLOUD_OVERFLOW
        response = requests.get(
            url, headers=self.request_header, params=params)
        logging.debug(f"Request URL: {response.url}")
        tracking_id = response.headers["trackingid"]
        logging.debug(f"Tracking ID: {tracking_id}")
        response = response.json()
        return response

    def list_cloud_overflow(self, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime):
        current_time = datetime.datetime.utcnow()
        for organization_id in self.organizations:
            logging.info(
                f"Fetching cloud overflow details for {self.organizations[organization_id]['displayName']} between {from_timestamp} and {to_timestamp}"
            )
            try:
                response = self.get_cloud_overflow(
                    organization_id, from_timestamp, to_timestamp
                )
                logging.debug(response)
                logging.debug(
                    f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes"
                )
                aggregation_interval = response["aggregationInterval"]
                for overflow_result in response["items"]:
                    try:
                        overflow_time = datetime.datetime.strptime(
                            overflow_result["timestamp"], "%Y-%m-%dT%H:%M:%SZ"
                        )
                        overflow_details = overflow_result["overflowDetails"]
                        for overflow_detail in overflow_details:
                            try:
                                overflow_reason = overflow_detail["overflowReason"]
                                overflow_count = overflow_detail["overflowCount"]
                                remediation = overflow_detail["possibleRemediation"]

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
                                logging.error(
                                    f"Error parsing overflow detail: {e}: {overflow_detail}:\n{response}"
                                )
                    except Exception as e:
                        logging.error(
                            f"Error parsing overflow result: {e}: {overflow_result}:\n{response}"
                        )
            except Exception as e:
                logging.error(
                    f"Error fetching cloud overflow details for {self.organizations[organization_id]['displayName']} ({organization_id}): {e}"
                )

    def get_call_redirects(self, organization_id: str, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime) -> Dict:
        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        params = {"from": from_timestamp,
                  "to": to_timestamp, "orgId": organization_id}
        url = self.API_URL_CALL_REDIRECTS
        response = requests.get(
            url, headers=self.request_header, params=params)
        logging.debug(f"Request URL: {response.url}")
        tracking_id = response.headers["trackingid"]
        logging.debug(f"Tracking ID: {tracking_id}")
        response = response.json()
        return response

    def list_call_redirects(self, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime):
        current_time = datetime.datetime.utcnow()
        for organization_id in self.organizations:
            logging.info(
                f"Fetching call redirect details for {self.organizations[organization_id]['displayName']} between {from_timestamp} and {to_timestamp}"
            )
            try:
                response = self.get_call_redirects(
                    organization_id, from_timestamp, to_timestamp
                )
                logging.debug(response)
                logging.debug(
                    f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes"
                )
                aggregation_interval = response["aggregationInterval"]
                for organization_results in response["items"]:
                    try:
                        redirect_time = datetime.datetime.strptime(
                            organization_results["timestamp"], "%Y-%m-%dT%H:%M:%SZ"
                        )
                        for cluster_result in organization_results["clusters"]:
                            try:
                                cluster_id = cluster_result["clusterId"]
                                cluster_name = cluster_result["clusterName"]
                                redirect_details = cluster_result["redirectDetails"]
                                for redirect_detail in redirect_details:
                                    try:
                                        redirect_reason = redirect_detail[
                                            "redirectReason"
                                        ]
                                        redirect_count = redirect_detail[
                                            "redirectCount"
                                        ]
                                        remediation = redirect_detail[
                                            "possibleRemediation"
                                        ]

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
                                        logging.error(
                                            f"Error parsing redirect detail: {e}: {redirect_detail}:\n{response}"
                                        )
                            except Exception as e:
                                logging.error(
                                    f"Error parsing cluster result: {e}: {cluster_result}:\n{response}"
                                )
                    except Exception as e:
                        logging.error(
                            f"Error parsing organization result: {e}: {organization_results}:\n{response}"
                        )
            except Exception as e:
                logging.error(
                    f"Error fetching call redirect details for {self.organizations[organization_id]['displayName']} ({organization_id}): {e}"
                )

    def get_media_health_monitoring_tool(
        self, organization_id, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime
    ) -> Dict:
        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        params = {"from": from_timestamp,
                  "to": to_timestamp, "orgId": organization_id}
        url = self.API_URL_MHM_TOOLS
        response = requests.get(
            url, headers=self.request_header, params=params)
        logging.debug(f"Request URL: {response.url}")
        tracking_id = response.headers["trackingid"]
        logging.debug(f"Tracking ID: {tracking_id}")
        response = response.json()
        return response

    def list_media_health_monitoring_tool(self, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime):
        current_time = datetime.datetime.utcnow()
        for organization_id in self.organizations:
            logging.info(
                f"Fetching media health monitoring tool details for {self.organizations[organization_id]['displayName']} between {from_timestamp} and {to_timestamp}"
            )
            try:
                response = self.get_media_health_monitoring_tool(
                    organization_id, from_timestamp, to_timestamp
                )
                logging.debug(response)
                logging.debug(
                    f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes"
                )
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
                                            test_results["timestamp"],
                                            "%Y-%m-%dT%H:%M:%SZ"
                                        )
                                        for test in test_results["testResults"]:
                                            test_name = test["testName"]
                                            test_status = test["testResult"]
                                            test_failure_reason = None
                                            if test_status == "Failed":
                                                test_failure_reason = test[
                                                    "failureReason"
                                                ]

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
                                    logging.error(
                                        f"Error parsing node results: {e}: {node_result}:\n{response}"
                                    )
                        except Exception as e:
                            logging.error(
                                f"Error parsing cluster results: {e}: {cluster_result}:\n{response}"
                            )
            except Exception as e:
                logging.error(
                    f"Error fetching media health monitoring tool details for {self.organizations[organization_id]['displayName']} ({organization_id}): {e}{response}"
                )

    def get_reachability(self, organization_id: str, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime) -> Dict:
        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        params = {"from": from_timestamp,
                  "to": to_timestamp, "orgId": organization_id}
        url = self.API_URL_REACHABILITY
        response = requests.get(
            url, headers=self.request_header, params=params)
        logging.debug(f"Request URL: {response.url}")
        tracking_id = response.headers["trackingid"]
        logging.debug(f"Tracking ID: {tracking_id}")
        response = response.json()
        return response

    def list_reachability(self, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime):
        current_time = datetime.datetime.utcnow()
        for organization_id in self.organizations:
            logging.info(
                f"Fetching reachability details for {self.organizations[organization_id]['displayName']} between {from_timestamp} and {to_timestamp}"
            )
            try:
                response = self.get_reachability(
                    organization_id, from_timestamp, to_timestamp
                )
                logging.debug(response)
                logging.debug(
                    f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes"
                )
                for cluster_result in response["items"]["clusters"]:
                    try:
                        cluster_id = cluster_result["clusterId"]
                        cluster_name = cluster_result["clusterName"]
                        for node_result in cluster_result["nodes"]:
                            try:
                                node_id = node_result["nodeId"]
                                host_name = node_result["hostNameOrIp"]
                                for test_results in node_result["testResults"]:
                                    destination_cluster = test_results[
                                        "destinationCluster"
                                    ]
                                    for result in test_results["stunResults"]:
                                        test_time = datetime.datetime.strptime(
                                            result["timestamp"], "%Y-%m-%d %H:%M:%S.%f"
                                        )

                                        if "udp" in result.keys():
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
                                        if "tcp" in result.keys():
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
                                logging.error(
                                    f"Error parsing node results: {e}: {node_result}:\n{response}"
                                )
                    except Exception as e:
                        logging.error(
                            f"Error parsing cluster results: {e}: {cluster_result}:\n{response}"
                        )
            except Exception as e:
                logging.error(
                    f"Error fetching reachability details for {self.organizations[organization_id]['displayName']} ({organization_id}): {e}{response}"
                )

    def get_cluster_utlization(self, organization_id: str, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime) -> Dict:
        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        params = {"from": from_timestamp,
                  "to": to_timestamp, "orgId": organization_id}
        url = self.API_URL_CLUSTER_UTILIZATION
        response = requests.get(
            url, headers=self.request_header, params=params)
        logging.debug(f"Request URL: {response.url}")
        tracking_id = response.headers["trackingid"]
        logging.debug(f"Tracking ID: {tracking_id}")
        response = response.json()
        return response

    def list_cluster_utilization(self, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime):
        current_time = datetime.datetime.utcnow()
        for organization_id in self.organizations:
            logging.info(
                f"Fetching cluster utilization details for {self.organizations[organization_id]['displayName']} between {from_timestamp} and {to_timestamp}"
            )
            try:
                response = self.get_cluster_utlization(
                    organization_id, from_timestamp, to_timestamp
                )
                logging.debug(response)
                logging.debug(
                    f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes"
                )
                aggregation_interval = response["aggregationInterval"]
                for cluster_result in response["items"]:
                    try:
                        measure_time = cluster_result["timestamp"]
                        for cluster in cluster_result["clusters"]:
                            try:
                                cluster_id = cluster["clusterId"]
                                cluster_name = cluster["clusterName"]
                                peak_cpu = cluster["utilizationMetrics"]["peakCpu"]
                                avg_cpu = cluster["utilizationMetrics"]["avgCpu"]
                                active_calls = cluster["utilizationMetrics"][
                                    "activeCalls"
                                ]

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
                                logging.error(
                                    f"Error parsing cluster results: {e}: {cluster}:\n{response}"
                                )
                    except Exception as e:
                        logging.error(
                            f"Error parsing cluster results: {e}: {cluster_result}:\n{response}"
                        )
            except Exception as e:
                logging.error(
                    f"Error fetching cluster utilization details for {self.organizations[organization_id]['displayName']} ({organization_id}): {e}"
                )

    def get_cluster_details(self, organization_id: str) -> Dict:
        params = {"orgId": organization_id}
        url = self.API_URL_CLUSTER_DETAILS
        response = requests.get(
            url, headers=self.request_header, params=params)
        logging.debug(f"Request URL: {response.url}")
        tracking_id = response.headers["trackingid"]
        logging.debug(f"Tracking ID: {tracking_id}")
        response = response.json()
        return response

    def list_cluster_details(self):
        current_time = datetime.datetime.utcnow()
        for organization_id in self.organizations:
            logging.info(
                f"Fetching cluster details for {self.organizations[organization_id]['displayName']}"
            )
            try:
                response = self.get_cluster_details(organization_id)
                logging.debug(response)
                logging.debug(
                    f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes"
                )
                for cluster_result in response["items"]:
                    try:
                        cluster_id = cluster_result["clusterId"]
                        cluster_name = cluster_result["clusterName"]
                        release_channel = cluster_result["releaseChannel"]
                        upgrade_schedule_days = cluster_result["upgradeSchedule"][
                            "scheduleDays"
                        ]
                        upgrade_schedule_days = ",".join(upgrade_schedule_days)
                        upgrade_schedule_time = (
                            cluster_result["upgradeSchedule"]["scheduleTime"] + ":00"
                        )
                        upgrade_schedule_time = (
                            datetime.datetime.strptime(
                                upgrade_schedule_time, "%H:%M:%S"
                            )
                            .astimezone()
                            .time()
                        )
                        upgrade_schedule_timezone = cluster_result["upgradeSchedule"][
                            "scheduleTimeZone"
                        ]
                        upgrade_pending = cluster_result["upgradeSchedule"][
                            "upgradePending"
                        ]
                        next_upgrade_time = cluster_result["upgradeSchedule"][
                            "nextUpgradeTime"
                        ]
                        next_upgrade_time = datetime.datetime.strptime(
                            next_upgrade_time, "%Y-%m-%dT%H:%M:%SZ"
                        )
                        for node_result in cluster_result["nodes"]:
                            try:
                                node_id = node_result["nodeId"]
                                host_name = node_result["hostNameOrIp"]
                                deployment_type = node_result["deploymentType"]
                                country_code = node_result["location"]["countryCode"]
                                city = node_result["location"]["city"]
                                timezone = node_result["location"]["timeZone"]

                                self.db.add_cluster_details(
                                    current_time,
                                    organization_id,
                                    cluster_id,
                                    cluster_name,
                                    node_id,
                                    release_channel,
                                    upgrade_schedule_days,
                                    upgrade_schedule_time,
                                    upgrade_schedule_timezone,
                                    upgrade_pending,
                                    next_upgrade_time
                                )

                                self.db.add_node_details(
                                    current_time,
                                    organization_id,
                                    cluster_id,
                                    node_id,
                                    host_name,
                                    deployment_type,
                                    country_code,
                                    city,
                                    timezone
                                )

                            except Exception as e:
                                logging.error(
                                    f"Error parsing node results: {e}: {node_result}:\n{response}"
                                )
                    except Exception as e:
                        logging.error(
                            f"Error parsing cluster results: {e}: {cluster_result}:\n{response}"
                        )
            except Exception as e:
                logging.error(
                    f"Error fetching cluster details for {self.organizations[organization_id]['displayName']} ({organization_id}): {e}"
                )

    def get_reachability_test_results(self, organization_id: str, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime) -> Dict:
        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        params = {
            "orgId": organization_id,
            "from": from_timestamp,
            "to": to_timestamp,
            "triggerType": "All"
        }
        url = self.API_URL_REACHABILITY_TEST_RESULTS
        response = requests.get(
            url, headers=self.request_header, params=params)
        logging.debug(f"Request URL: {response.url}")
        tracking_id = response.headers["trackingid"]
        logging.debug(f"Tracking ID: {tracking_id}")
        response = response.json()
        return response

    def list_reachability_test_results(self, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime):
        current_time = datetime.datetime.utcnow()
        for organization_id in self.organizations:
            logging.info(
                f"Fetching reachability test results for {self.organizations[organization_id]['displayName']} between {from_timestamp} and {to_timestamp}"
            )
            try:
                response = self.get_reachability_test_results(
                    organization_id, from_timestamp, to_timestamp
                )
                logging.debug(response)
                logging.debug(
                    f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes"
                )
                for reachability_test_result in response["items"]["clusters"]:
                    try:
                        cluster_id = reachability_test_result["clusterId"]
                        cluster_name = reachability_test_result["clusterName"]
                        for node_result in reachability_test_result["nodes"]:
                            node_id = node_result["nodeId"]
                            host_name = node_result["hostName"]
                            ip_address = node_result["ipAddress"]
                            for test_result in node_result["testResults"]:
                                destination_cluster = test_result["destinationCluster"]
                                for stun_result in test_result["stunResults"]:
                                    test_timestamp = stun_result["timestamp"]
                                    test_id = stun_result["id"]
                                    test_trigger_type = stun_result["triggerType"]
                                    if "tcp" in stun_result:
                                        for tcp_result in stun_result["tcp"]:
                                            tcp_port = tcp_result["port"]
                                            tcp_status = tcp_result["reachable"]

                                            self.db.add_reachability_test_results(
                                                current_time,
                                                from_timestamp,
                                                to_timestamp,
                                                organization_id,
                                                cluster_id,
                                                cluster_name,
                                                node_id,
                                                host_name,
                                                ip_address,
                                                destination_cluster,
                                                test_timestamp,
                                                test_id,
                                                test_trigger_type,
                                                "tcp",
                                                tcp_port,
                                                tcp_status
                                            )

                                    if "udp" in stun_result:
                                        for udp_result in stun_result["udp"]:
                                            udp_port = udp_result["port"]
                                            udp_status = udp_result["reachable"]

                                            self.db.add_reachability_test_results(
                                                current_time,
                                                from_timestamp,
                                                to_timestamp,
                                                organization_id,
                                                cluster_id,
                                                cluster_name,
                                                node_id,
                                                host_name,
                                                ip_address,
                                                destination_cluster,
                                                test_timestamp,
                                                test_id,
                                                test_trigger_type,
                                                "udp",
                                                udp_port,
                                                udp_status
                                            )
                    except Exception as e:
                        logging.error(
                            f"Error parsing reachability test results: {e}: {reachability_test_result}:\n{response}"
                        )
            except Exception as e:
                logging.error(
                    f"Error fetching reachability test results for {self.organizations[organization_id]['displayName']} ({organization_id}): {e}"
                )

    def get_media_health_monitoring_test_results(self, organization_id: str, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime) -> Dict:
        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        params = {
            "orgId": organization_id,
            "from": from_timestamp,
            "to": to_timestamp,
            "triggerType": "All"
        }
        url = self.API_URL_MEDIA_HEALTH_MONITORING_TEST_RESULTS
        response = requests.get(
            url, headers=self.request_header, params=params)
        logging.debug(f"Request URL: {response.url}")
        tracking_id = response.headers["trackingid"]
        logging.debug(f"Tracking ID: {tracking_id}")
        response = response.json()
        return response

    def list_media_health_monitoring_test_results(self, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime):
        current_time = datetime.datetime.utcnow()
        for organization_id in self.organizations:
            logging.info(
                f"Fetching media health monitoring test results for {self.organizations[organization_id]['displayName']} between {from_timestamp} and {to_timestamp}"
            )
            try:
                response = self.get_media_health_monitoring_test_results(
                    organization_id, from_timestamp, to_timestamp
                )
                logging.debug(response)
                logging.debug(
                    f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes"
                )
                for media_health_monitoring_test_result in response["items"]:
                    try:
                        for cluster in media_health_monitoring_test_result["clusters"]:
                            cluster_id = cluster["clusterId"]
                            cluster_name = cluster["clusterName"]
                            for node in cluster["nodes"]:
                                node_id = node["nodeId"]
                                host_name = node["hostName"]
                                ip_address = node["ipAddress"]
                                for mhm_test in node["mhmTestResults"]:
                                    test_timestamp = mhm_test["timestamp"]
                                    test_id = mhm_test["id"]
                                    test_trigger_type = mhm_test["triggerType"]
                                    for mhm_test_result in mhm_test["testResults"]:
                                        test_name = mhm_test_result["testName"]
                                        test_result = mhm_test_result["testResult"]
                                        failure_reason = mhm_test_result.get(
                                            "failureReason", None)

                                        self.db.add_media_health_monitoring_test_results(
                                            current_time,
                                            from_timestamp,
                                            to_timestamp,
                                            organization_id,
                                            cluster_id,
                                            cluster_name,
                                            node_id,
                                            host_name,
                                            ip_address,
                                            test_timestamp,
                                            test_id,
                                            test_trigger_type,
                                            test_name,
                                            test_result,
                                            failure_reason
                                        )

                    except Exception as e:
                        logging.error(
                            f"Error parsing media health monitoring test results: {e}: {media_health_monitoring_test_result}:\n{response}"
                        )
            except Exception as e:
                logging.error(
                    f"Error fetching media health monitoring test results for {self.organizations[organization_id]['displayName']} ({organization_id}): {e}"
                )

    def get_connectivity_test_results(self, organization_id: str, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime) -> Dict:
        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )
        params = {
            "orgId": organization_id,
            "from": from_timestamp,
            "to": to_timestamp,
            "triggerType": "All"
        }
        url = self.API_URL_CONNECTIVITY_TEST_RESULTS
        response = requests.get(
            url, headers=self.request_header, params=params)
        logging.debug(f"Request URL: {response.url}")
        tracking_id = response.headers["trackingid"]
        logging.debug(f"Tracking ID: {tracking_id}")
        response = response.json()
        return response

    def list_connectivity_test_results(self, from_timestamp: datetime.datetime, to_timestamp: datetime.datetime):
        current_time = datetime.datetime.utcnow()
        for organization_id in self.organizations:
            logging.info(
                f"Fetching connectivity test results for {self.organizations[organization_id]['displayName']} between {from_timestamp} and {to_timestamp}"
            )
            try:
                response = self.get_connectivity_test_results(
                    organization_id, from_timestamp, to_timestamp
                )
                logging.debug(response)
                logging.debug(
                    f"Size of response: {len(json.dumps(response).encode('utf-8'))} bytes"
                )
                for connectivity_test_result in response["items"]:
                    try:
                        for cluster in connectivity_test_result["clusters"]:
                            cluster_id = cluster["clusterId"]
                            cluster_name = cluster["clusterName"]
                            for node in cluster["nodes"]:
                                node_id = node["nodeId"]
                                host_name = node["hostName"]
                                ip_address = node["ipAddress"]
                                for test in node["testResults"]:
                                    test_timestamp = test["timestamp"]
                                    test_id = test["id"]
                                    test_trigger_type = test["triggerType"]
                                    for test_result in test["results"]:
                                        test_type = test_result["type"]
                                        for result in test_result["results"]:
                                            service_type = result["serviceType"]
                                            service_test_result = result["testResult"]
                                            if "failureDetails" in result:
                                                failure_reason = result["failureDetails"]["possibleFailureReason"][0]
                                                possible_remediation = result["failureDetails"]["possibleRemediation"][0]
                                            else:
                                                failure_reason = None
                                                possible_remediation = None

                                            self.db.add_connectivity_test_results(
                                                current_time,
                                                from_timestamp,
                                                to_timestamp,
                                                organization_id,
                                                cluster_id,
                                                cluster_name,
                                                node_id,
                                                host_name,
                                                ip_address,
                                                test_timestamp,
                                                test_id,
                                                test_trigger_type,
                                                test_type,
                                                service_type,
                                                service_test_result,
                                                failure_reason,
                                                possible_remediation
                                            )
                    except Exception as e:
                        logging.error(
                            f"Error parsing connectivity test results: {e}: {connectivity_test_result}:\n{response}"
                        )

            except Exception as e:
                logging.error(
                    f"Error fetching connectivity test results for {self.organizations[organization_id]['displayName']} ({organization_id}): {e}"
                )
