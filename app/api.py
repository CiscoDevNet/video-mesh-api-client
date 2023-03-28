import datetime
import json
import logging
import os
import re
import threading
from typing import Optional, Union, Literal

import requests

import constants
import parser
from db import APIDatabase


class APITriggers:
    INSTANCE_COUNT = 0

    def __init__(
            self,
            api_config: dict,
            fetch_historical_data_on_init: bool = True,
            create_tables_on_init: bool = True,
            **kwargs
    ):
        """
        Initialize APITriggers object

        :param api_config: API configuration parameters
        :param access_token: Webex Developer API access token
        :param fetch_historical_data_on_init: Fetch historical data once the APITriggers object is initialized
        :param setup_tables_on_init: Set up the database tables once the APITriggers object is initialized
        """
        self.access_token = api_config.get("access_token", None)
        if self.access_token is None:
            logging.error("Developer Hub Token not set")
            return None

        self.organizations = None
        self.developer_hub_host_url = api_config["host"]
        self.default_request_header = {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type": "application/json"
        }

        self.db = APIDatabase(
            connection_url=api_config["database"]["url"],
            create_tables_on_init=create_tables_on_init
        )
        self.parser = parser.Parser()

        self.api_endpoint_map = {
            "organizations": {
                "url": f"{self.developer_hub_host_url}/organizations",
                "method": "GET",
                "headers": self.default_request_header,
            },
            "cluster_availability": {
                "url": f"{self.developer_hub_host_url}/videoMesh/clusters/availability",
                "method": "GET",
                "headers": self.default_request_header,
            },
            "node_availability": {
                "url": f"{self.developer_hub_host_url}/videoMesh/nodes/availability",
                "method": "GET",
                "headers": self.default_request_header,
            },
            "cloud_overflow": {
                "url": f"{self.developer_hub_host_url}/videoMesh/cloudOverflow",
                "method": "GET",
                "headers": self.default_request_header,
            },
            "call_redirects": {
                "url": f"{self.developer_hub_host_url}/videoMesh/callRedirects",
                "method": "GET",
                "headers": self.default_request_header,
            },
            "cluster_utilization": {
                "url": f"{self.developer_hub_host_url}/videoMesh/utilization",
                "method": "GET",
                "headers": self.default_request_header,
            },
            "cluster_details": {
                "url": f"{self.developer_hub_host_url}/videoMesh/clusters",
                "method": "GET",
                "headers": self.default_request_header,
            },
            "reachability_test_results": {
                "url": f"{self.developer_hub_host_url}/videoMesh/testResults/reachabilityTest",
                "method": "GET",
                "headers": self.default_request_header,
            },
            "media_health_monitoring_test_results": {
                "url": f"{self.developer_hub_host_url}/videoMesh/testResults/mediaHealthMonitorTest",
                "method": "GET",
                "headers": self.default_request_header,
            },
            "network_test_results": {
                "url": f"{self.developer_hub_host_url}/videoMesh/testResults/networkTest",
                "method": "GET",
                "headers": self.default_request_header,
            }
        }

        if ".INSTANCE_COUNT" not in os.listdir(os.getcwd()):
            APITriggers.INSTANCE_COUNT = 1
            with open(".INSTANCE_COUNT", "w") as f:
                f.write("1")
        else:
            with open(".INSTANCE_COUNT", "r") as f:
                APITriggers.INSTANCE_COUNT = int(f.read()) + 1
            with open(".INSTANCE_COUNT", "w") as f:
                f.write(str(APITriggers.INSTANCE_COUNT))

        if APITriggers.INSTANCE_COUNT == 1 and fetch_historical_data_on_init:
            logging.info(f"First initialization of APITriggers object. Fetching historical data")
            thread = threading.Thread(
                target=self.fetch_historical_data,
                args=(
                    kwargs.get("period", "month"),
                    kwargs.get("fetch_organizations", True)
                )
            )
            thread.start()

    def trigger_all_api_endpoints(
            self,
            start_time: datetime.datetime,
            end_time: datetime.datetime,
            fetch_organizations: bool = True
    ):
        """
        Trigger all API endpoints

        :param start_time: Start time for the API call
        :param end_time: End time for the API call
        :param fetch_organizations: Fetch organizations before triggering the API endpoints
        :return:
        """

        logging.info(f"Triggering all API endpoints between {start_time} and {end_time}")

        functions = [
            func for func in dir(self)
            if callable(getattr(self, func)) \
               and not func.startswith("__") \
               and re.match(r"list_.*_api", func) \
               and func != "list_organizations_api"
        ]

        functions.remove("list_cluster_details_api")
        functions.insert(0, "list_cluster_details_api")

        if fetch_organizations:
            self.list_organizations_api()

        threads = list()
        for function in functions:
            function_callable = getattr(self, function)
            if function == "list_cluster_details_api":
                thread = threading.Thread(target=function_callable, name="list_cluster_details_api")
            else:
                thread = threading.Thread(target=function_callable, args=(start_time, end_time), name=function)
            threads.append(thread)
            thread.start()

        [thread.join() for thread in threads]

    def fetch_historical_data(self, period: Literal["month", "year"], fetch_organizations: bool = True):
        """
        Fetch historical data for all APIs

        :param period: Time period to fetch data for
        :param fetch_organizations: Fetch organizations before triggering the API endpoints
        :return:
        """
        end_time = datetime.datetime.utcnow()
        if period == "year":
            start_time = datetime.datetime(end_time.year, 1, 1, 0, 0, 0)
        elif period == "week":
            start_time = end_time - datetime.timedelta(days=7)
        elif period == "month":
            start_time = end_time - datetime.timedelta(days=31)
        elif period == "day":
            start_time = end_time - datetime.timedelta(days=1)
        else:
            start_time = end_time - datetime.timedelta(days=31)

        logging.info(f"Fetching historical data for period {period} from {start_time} to {end_time}")

        while end_time >= start_time:
            time_range_start_time = end_time - datetime.timedelta(days=6)
            time_range_end_time = end_time
            logging.info(f"Fetching data for time range {time_range_start_time} to {time_range_end_time}")
            self.trigger_all_api_endpoints(time_range_start_time, time_range_end_time, fetch_organizations)
            end_time = end_time - datetime.timedelta(days=6)

        logging.info("Finished fetching historical data")

    def make_api_call(self, endpoint: str, **kwargs) -> Optional[dict]:
        """
        Make API call to the specified endpoint

        :param endpoint: Endpoint to make the API call to
        :param kwargs: Keyword arguments to pass to the API call
        :return:
        """
        logging.info(f"Making API call to /{endpoint} with params {kwargs}")
        api = self.api_endpoint_map[endpoint]
        url = api["url"]
        method = api["method"]
        headers = api["headers"]

        if "params" in kwargs:
            params = kwargs["params"]
        else:
            params = None

        try:
            request_function = getattr(requests, method.lower())
        except AttributeError:
            raise Exception(f"Invalid method {method} for API {endpoint}")

        try:
            response = request_function(url, headers=headers, params=params)
            tracking_id = response.headers["trackingid"]
            logging.info(f"Made request to URL: {response.url} with tracking ID: {tracking_id}")
            response = response.json()
            response_size_bytes = len(json.dumps(response).encode('utf-8'))
            logging.debug(f"Response: {response}")
            logging.debug(f"Response size: {response_size_bytes} bytes")
            return response
        except Exception as e:
            logging.error(f"Error while making API request to /{endpoint}: {e}")
            return None

    def list_organizations_api(self) -> dict:
        """
        List all the organizations

        :return: Dictionary of organizations
        """
        response = self.make_api_call("organizations")
        if response is None:
            return dict()
        try:
            self.organizations, organization_records = self.parser.parse_organizations(response)
            self.db.insert_records(organization_records, "organizations")
            return self.organizations
        except Exception as e:
            logging.error(f"Error in organizations: {e}")
            return dict()

    def list_cluster_availability_api(self, from_timestamp: Union[str, datetime.datetime],
                                      to_timestamp: Union[str, datetime.datetime]):
        """
        List cluster availability API

        :param from_timestamp: From timestamp
        :param to_timestamp: To timestamp
        :return: Dictionary of cluster availability
        """
        current_time = datetime.datetime.utcnow()
        if from_timestamp > to_timestamp:
            logging.error("From timestamp cannot be greater than to timestamp")
            return

        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp,
                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp,
                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
            )

        for organization_id in self.organizations:
            params = {
                "orgId": organization_id,
                "from": from_timestamp,
                "to": to_timestamp
            }
            response = self.make_api_call("cluster_availability", params=params)
            if response is None:
                return
            try:
                cluster_availability_records = self.parser.parse_cluster_availability(
                    response,
                    current_time=current_time,
                    organization_id=organization_id
                )
                self.db.insert_records(cluster_availability_records, "cluster_availability")
            except Exception as e:
                logging.error(f"Error in cluster availability: {e}")

    def list_node_availability_api(self, from_timestamp: Union[str, datetime.datetime],
                                   to_timestamp: Union[str, datetime.datetime]):
        """
        List node availability API

        :param from_timestamp: From timestamp
        :param to_timestamp: To timestamp
        :return: None
        """
        current_time = datetime.datetime.utcnow()
        if from_timestamp > to_timestamp:
            logging.error("From timestamp cannot be greater than to timestamp")
            return

        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp,
                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp,
                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
            )

        cluster_ids = self.db.get_all_cluster_ids()

        for cluster_id in cluster_ids:
            params = {
                "clusterId": cluster_id,
                "from": from_timestamp,
                "to": to_timestamp
            }
            response = self.make_api_call("node_availability", params=params)
            if response is None:
                return
            try:
                node_availability_records = self.parser.parse_node_availability(
                    response,
                    current_time=current_time,
                    cluster_id=cluster_id
                )
                self.db.insert_records(node_availability_records, "node_availability")
            except Exception as e:
                logging.error(f"Error in node availability: {e}")
                return

    def list_cloud_overflow_api(self, from_timestamp: Union[str, datetime.datetime],
                                to_timestamp: Union[str, datetime.datetime]):
        """
        List cloud overflow API

        :return: None
        """
        current_time = datetime.datetime.utcnow()
        if from_timestamp > to_timestamp:
            logging.error("From timestamp cannot be greater than to timestamp")
            return

        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp,
                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp,
                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
            )

        for organization_id in self.organizations:
            params = {
                "orgId": organization_id,
                "from": from_timestamp,
                "to": to_timestamp
            }
            response = self.make_api_call("cloud_overflow", params=params)
            if response is None:
                return
            try:
                cloud_overflow_records = self.parser.parse_cloud_overflow(
                    response,
                    current_time=current_time,
                    organization_id=organization_id,
                    from_timestamp=from_timestamp,
                    to_timestamp=to_timestamp
                )
                self.db.insert_records(cloud_overflow_records, "cloud_overflow")
            except Exception as e:
                logging.error(f"Error in cloud overflow: {e}")
                return

    def list_call_redirects_api(self, from_timestamp: Union[str, datetime.datetime],
                                to_timestamp: Union[str, datetime.datetime]):
        """
        List call redirects API

        :return: None
        """
        current_time = datetime.datetime.utcnow()
        if from_timestamp > to_timestamp:
            logging.error("From timestamp cannot be greater than to timestamp")
            return

        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp,
                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp,
                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
            )

        for organization_id in self.organizations:
            params = {
                "orgId": organization_id,
                "from": from_timestamp,
                "to": to_timestamp
            }
            response = self.make_api_call("call_redirects", params=params)
            if response is None:
                return
            try:
                call_redirects_records = self.parser.parse_call_redirects(
                    response,
                    current_time=current_time,
                    organization_id=organization_id,
                    from_timestamp=from_timestamp,
                    to_timestamp=to_timestamp
                )
                self.db.insert_records(call_redirects_records, "call_redirects")
            except Exception as e:
                logging.error(f"Error in call redirects: {e}")
                return

    def list_cluster_utilization_api(self, from_timestamp: Union[str, datetime.datetime],
                                     to_timestamp: Union[str, datetime.datetime]):
        """
        List cluster utilization API

        :return: None
        """
        current_time = datetime.datetime.utcnow()
        if from_timestamp > to_timestamp:
            logging.error("From timestamp cannot be greater than to timestamp")
            return

        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp,
                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp,
                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
            )

        for organization_id in self.organizations:
            params = {
                "orgId": organization_id,
                "from": from_timestamp,
                "to": to_timestamp
            }
            response = self.make_api_call("cluster_utilization", params=params)
            if response is None:
                return
            try:
                cluster_utilization_records = self.parser.parse_cluster_utilization(
                    response,
                    current_time=current_time,
                    organization_id=organization_id,
                    from_timestamp=from_timestamp,
                    to_timestamp=to_timestamp
                )
                self.db.insert_records(cluster_utilization_records, "cluster_utilization")
            except Exception as e:
                logging.error(f"Error in cluster utilization: {e}")
                return

    def list_cluster_details_api(self):
        """
        List cluster details API

        :return: None
        """
        current_time = datetime.datetime.utcnow()

        for organization_id in self.organizations:
            params = {"orgId": organization_id}
            response = self.make_api_call("cluster_details", params=params)
            if response is None:
                return
            try:
                cluster_details_records, node_details_records = self.parser.parse_cluster_details(
                    response,
                    current_time=current_time,
                    organization_id=organization_id,
                )
                self.db.insert_records(cluster_details_records, "cluster_details")
                self.db.insert_records(node_details_records, "node_details")
            except Exception as e:
                logging.error(f"Error in cluster details: {e}")
                return

    def list_reachability_test_results_api(self, from_timestamp: Union[str, datetime.datetime],
                                           to_timestamp: Union[str, datetime.datetime]):
        """
        List reachability test result API

        :param from_timestamp: Union[str, datetime.datetime]
        :param to_timestamp: Union[str, datetime.datetime]
        :return:
        """
        current_time = datetime.datetime.utcnow()

        if from_timestamp > to_timestamp:
            logging.error("From timestamp cannot be greater than to timestamp")
            return

        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp,
                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp,
                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
            )

        for organization_id in self.organizations:
            params = {
                "orgId": organization_id,
                "from": from_timestamp,
                "to": to_timestamp,
                "triggerType": "All"
            }
            response = self.make_api_call("reachability_test_results", params=params)
            if response is None:
                return
            try:
                reachability_test_result_records = self.parser.parse_reachability_test_results(
                    response,
                    current_time=current_time,
                    organization_id=organization_id,
                    from_timestamp=from_timestamp,
                    to_timestamp=to_timestamp
                )
                self.db.insert_records(reachability_test_result_records, "reachability_test_results")
            except Exception as e:
                logging.error(f"Error in reachability test results: {e}")
                return

    def list_media_health_monitoring_test_results_api(self, from_timestamp: Union[str, datetime.datetime],
                                                      to_timestamp: Union[str, datetime.datetime]):
        """
        List reachability test result API

        :param from_timestamp: Union[str, datetime.datetime]
        :param to_timestamp: Union[str, datetime.datetime]
        :return:
        """
        current_time = datetime.datetime.utcnow()

        if from_timestamp > to_timestamp:
            logging.error("From timestamp cannot be greater than to timestamp")
            return

        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp,
                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp,
                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
            )

        for organization_id in self.organizations:
            params = {
                "orgId": organization_id,
                "from": from_timestamp,
                "to": to_timestamp,
                "triggerType": "All"
            }
            response = self.make_api_call("media_health_monitoring_test_results", params=params)
            if response is None:
                return
            try:
                media_health_monitoring_test_result_records = self.parser.parse_media_health_monitoring_test_results(
                    response,
                    current_time=current_time,
                    organization_id=organization_id,
                    from_timestamp=from_timestamp,
                    to_timestamp=to_timestamp
                )
                self.db.insert_records(
                    media_health_monitoring_test_result_records,
                    "media_health_monitoring_test_results"
                )
            except Exception as e:
                logging.error(f"Error in reachability test results: {e}")
                return

    def list_network_test_results_api(self, from_timestamp: Union[str, datetime.datetime],
                                      to_timestamp: Union[str, datetime.datetime]):
        """
        List reachability test result API

        :param from_timestamp: Union[str, datetime.datetime]
        :param to_timestamp: Union[str, datetime.datetime]
        :return:
        """
        current_time = datetime.datetime.utcnow()

        if from_timestamp > to_timestamp:
            logging.error("From timestamp cannot be greater than to timestamp")
            return

        if isinstance(from_timestamp, datetime.datetime):
            from_timestamp = datetime.datetime.strftime(
                from_timestamp,
                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
            )
        if isinstance(to_timestamp, datetime.datetime):
            to_timestamp = datetime.datetime.strftime(
                to_timestamp,
                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
            )

        for organization_id in self.organizations:
            params = {
                "orgId": organization_id,
                "from": from_timestamp,
                "to": to_timestamp,
                "triggerType": "All"
            }
            response = self.make_api_call("network_test_results", params=params)
            if response is None:
                return
            try:
                network_test_result_records = self.parser.parse_network_test_results(
                    response,
                    current_time=current_time,
                    organization_id=organization_id,
                    from_timestamp=from_timestamp,
                    to_timestamp=to_timestamp
                )
                self.db.insert_records(network_test_result_records, "network_test_results")
            except Exception as e:
                logging.error(f"Error in reachability test results: {e}")
                return
