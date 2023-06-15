import datetime
import logging
from typing import Union

import constants


class Parser:
    def __init__(self):
        """
        Parser class to parse data from API responses
        """
        pass

    @staticmethod
    def trim_whitespaces(records: Union[list[dict], dict]) -> Union[list[dict], dict]:
        """
        Trim whitespaces from a collection of dictionary values

        :param records: Dictionary containing records or an iterable of dictionaries
        :return: Dictionary with trimmed values or a list of dictionaries with trimmed values
        """
        if isinstance(records, dict):
            return {
                key: value.strip() if isinstance(value, str) else value
                for key, value in records.items()
            }
        elif isinstance(records, list):
            return [
                {
                    key: value.strip() if isinstance(value, str) else value
                    for key, value in record.items()
                }
                for record in records
            ]
        else:
            raise TypeError("Records must be either a dictionary or a list of dictionaries")

    @staticmethod
    def parse_organizations(response: dict) -> tuple[dict, list[dict]]:
        """
        Parse organizations from API response

        :param response: API response
        :return: A tuple containing a dictionary of organizations and a list of organization records
        """
        organizations = dict()
        organization_records = list()
        for organization_detail in response["items"]:
            organizations[organization_detail["id"]] = {
                "displayName": organization_detail["displayName"],
                "created": datetime.datetime.strptime(
                    organization_detail["created"], constants.WEBEX_API_DATETIME_FORMAT_MILLISECOND_PRECISION
                )
            }

            organization_records.append(
                {
                    "organization_id": organization_detail["id"],
                    "organization_name": organization_detail["displayName"],
                    "create_timestamp": organizations[organization_detail["id"]]["created"]
                }
            )
        organization_records = Parser.trim_whitespaces(organization_records)
        return organizations, organization_records

    @staticmethod
    def parse_cluster_availability(response: dict, current_time: Union[str, datetime.datetime], organization_id: str) -> \
            list[dict]:
        """
        Parse cluster availability from API response

        :param response: Cluster Availability API response
        :param current_time: Current time
        :param organization_id: Organization ID
        :return: A list of cluster availability records
        """
        cluster_availability_records = list()
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
                                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
                            )
                            segment_end_time = datetime.datetime.strptime(
                                availability_segment["segmentEndTime"],
                                constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
                            )

                            cluster_availability_records.append(
                                {
                                    "timestamp": current_time,
                                    "organization_id": organization_id,
                                    "cluster_id": cluster_id,
                                    "cluster_name": cluster_name,
                                    "offline_nodes": num_offline_nodes,
                                    "online_nodes": num_online_nodes,
                                    "availability": availability,
                                    "start_timestamp": segment_start_time,
                                    "end_timestamp": segment_end_time
                                }
                            )

                        except Exception as e:
                            logging.error(
                                f"Error parsing availability segment: {e}: {availability_segment}:\n{response}")
                except Exception as e:
                    logging.error(f"Error parsing cluster data: {e} : {cluster_result}:\n{response}")

        cluster_availability_records = Parser.trim_whitespaces(cluster_availability_records)
        return cluster_availability_records

    @staticmethod
    def parse_node_availability(response: dict, current_time: Union[str, datetime.datetime], cluster_id: str) -> \
            list[dict]:
        """
        Parse node availability from API response

        :param response: Node availability API response
        :param current_time: Current time
        :param cluster_id: Cluster ID
        :return: A list of node availability records
        """
        node_availability_records = list()
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
                                        constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
                                    )
                                )
                                segment_end_time = (
                                    datetime.datetime.strptime(
                                        availability_segment[
                                            "segmentEndTime"
                                        ],
                                        constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
                                    )
                                )

                                node_availability_records.append(
                                    {
                                        "timestamp": current_time,
                                        "organization_id": organization_id,
                                        "cluster_id": cluster_id,
                                        "cluster_name": cluster_name,
                                        "node_id": node_id,
                                        "host_name": host_name,
                                        "availability": availability,
                                        "start_timestamp": segment_start_time,
                                        "end_timestamp": segment_end_time
                                    }
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

        node_availability_records = Parser.trim_whitespaces(node_availability_records)
        return node_availability_records

    @staticmethod
    def parse_cloud_overflow(response: dict, current_time: Union[str, datetime.datetime], organization_id: str,
                             from_timestamp: Union[str, datetime.datetime],
                             to_timestamp: Union[str, datetime.datetime]) -> list[dict]:
        """
        Parse cloud overflow from API response

        :param response: Cloud overflow API response
        :param current_time: Current time
        :param organization_id: Organization ID
        :param from_timestamp: From timestamp
        :param to_timestamp: To timestamp
        :return: A list of cloud overflow records
        """
        cloud_overflow_records = list()
        aggregation_interval = response["aggregationInterval"]
        for overflow_result in response["items"]:
            try:
                overflow_time = datetime.datetime.strptime(
                    overflow_result["timestamp"], constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
                )
                overflow_details = overflow_result["overflowDetails"]
                for overflow_detail in overflow_details:
                    try:
                        overflow_reason = overflow_detail["overflowReason"]
                        overflow_count = overflow_detail["overflowCount"]
                        remediation = overflow_detail["possibleRemediation"]

                        cloud_overflow_records.append(
                            {
                                "timestamp": current_time,
                                "organization_id": organization_id,
                                "aggregation_interval": aggregation_interval,
                                "from_timestamp": from_timestamp,
                                "to_timestamp": to_timestamp,
                                "overflow_timestamp": overflow_time,
                                "overflow_reason": overflow_reason,
                                "overflow_count": overflow_count,
                                "remediation": remediation
                            }
                        )

                    except Exception as e:
                        logging.error(
                            f"Error parsing overflow detail: {e}: {overflow_detail}:\n{response}"
                        )
            except Exception as e:
                logging.error(
                    f"Error parsing overflow result: {e}: {overflow_result}:\n{response}"
                )

        cloud_overflow_records = Parser.trim_whitespaces(cloud_overflow_records)
        return cloud_overflow_records

    @staticmethod
    def parse_call_redirects(response: dict, current_time: Union[str, datetime.datetime], organization_id: str,
                             from_timestamp: Union[str, datetime.datetime],
                             to_timestamp: Union[str, datetime.datetime]) -> list[dict]:
        """
        Parse call redirects from API response

        :param response: Call redirects API response
        :param current_time: Current time
        :param organization_id: Organization ID
        :param from_timestamp: From timestamp
        :param to_timestamp: To timestamp
        :return: A list of call redirects records
        """
        call_redirects_records = list()
        aggregation_interval = response["aggregationInterval"]
        for organization_results in response["items"]:
            try:
                redirect_time = datetime.datetime.strptime(
                    organization_results["timestamp"], constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
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

                                call_redirects_records.append(
                                    {
                                        "timestamp": current_time,
                                        "organization_id": organization_id,
                                        "aggregation_interval": aggregation_interval,
                                        "from_timestamp": from_timestamp,
                                        "to_timestamp": to_timestamp,
                                        "redirect_timestamp": redirect_time,
                                        "cluster_id": cluster_id,
                                        "cluster_name": cluster_name,
                                        "redirect_reason": redirect_reason,
                                        "redirect_count": redirect_count,
                                        "remediation": remediation
                                    }
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

        call_redirects_records = Parser.trim_whitespaces(call_redirects_records)
        return call_redirects_records

    @staticmethod
    def parse_cluster_utilization(response: dict, current_time: Union[str, datetime.datetime],
                                  organization_id: str,
                                  from_timestamp: Union[str, datetime.datetime],
                                  to_timestamp: Union[str, datetime.datetime]) -> list[dict]:
        """
        Parse cluster utilization from API response

        :param response: Cluster utilization API response
        :param current_time: Current time
        :param organization_id: Organization ID
        :param from_timestamp: From timestamp
        :param to_timestamp: To timestamp
        :return: A list of cluster utilization records
        """
        cluster_utilization_records = list()
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

                        cluster_utilization_records.append(
                            {
                                "timestamp": current_time,
                                "organization_id": organization_id,
                                "from_timestamp": from_timestamp,
                                "to_timestamp": to_timestamp,
                                "aggregation_interval": aggregation_interval,
                                "measure_timestamp": measure_time,
                                "cluster_id": cluster_id,
                                "cluster_name": cluster_name,
                                "peak_cpu": peak_cpu,
                                "avg_cpu": avg_cpu,
                                "active_calls": active_calls
                            }
                        )

                    except Exception as e:
                        logging.error(
                            f"Error parsing cluster results: {e}: {cluster}:\n{response}"
                        )
            except Exception as e:
                logging.error(
                    f"Error parsing cluster results: {e}: {cluster_result}:\n{response}"
                )

        cluster_utilization_records = Parser.trim_whitespaces(cluster_utilization_records)
        return cluster_utilization_records

    @staticmethod
    def parse_cluster_details(response: dict, current_time: Union[str, datetime.datetime],
                              organization_id: str) -> tuple[list[dict], list[dict]]:
        """
        Parse cluster details from API response

        :param response: Cluster details API response
        :param current_time: Current time
        :param organization_id: Organization ID
        :return: A tuple of cluster details records and node details records
        """
        cluster_details_records = list()
        node_details_records = list()
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
                    next_upgrade_time, constants.WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION
                )
                for node_result in cluster_result["nodes"]:
                    try:
                        node_id = node_result["nodeId"]
                        host_name = node_result["hostNameOrIp"]
                        deployment_type = node_result["deploymentType"]
                        country_code = node_result["location"]["countryCode"]
                        city = node_result["location"]["city"]
                        timezone = node_result["location"]["timeZone"]

                        cluster_details_records.append(
                            {
                                "timestamp": current_time,
                                "organization_id": organization_id,
                                "cluster_id": cluster_id,
                                "cluster_name": cluster_name,
                                "node_id": node_id,
                                "release_channel": release_channel,
                                "upgrade_schedule_days": upgrade_schedule_days,
                                "upgrade_schedule_time": upgrade_schedule_time,
                                "upgrade_schedule_timezone": upgrade_schedule_timezone,
                                "upgrade_pending": upgrade_pending,
                                "next_upgrade_timestamp": next_upgrade_time
                            }
                        )

                        node_details_records.append(
                            {
                                "timestamp": current_time,
                                "organization_id": organization_id,
                                "cluster_id": cluster_id,
                                "node_id": node_id,
                                "host_name": host_name,
                                "deployment_type": deployment_type,
                                "country_code": country_code,
                                "city": city,
                                "timezone": timezone
                            }
                        )

                    except Exception as e:
                        logging.error(
                            f"Error parsing node results: {e}: {node_result}:\n{response}"
                        )
            except Exception as e:
                logging.error(
                    f"Error parsing cluster results: {e}: {cluster_result}:\n{response}"
                )

        cluster_details_records = Parser.trim_whitespaces(cluster_details_records)
        node_details_records = Parser.trim_whitespaces(node_details_records)
        return cluster_details_records, node_details_records

    @staticmethod
    def parse_reachability_test_results(
            response: dict,
            current_time: Union[str, datetime.datetime],
            organization_id: str,
            from_timestamp: Union[str, datetime.datetime],
            to_timestamp: Union[str, datetime.datetime],
    ) -> list[dict]:
        """
        Parse reachability test results from API response

        :param response: Reachability test results API response
        :param current_time: Current time
        :param organization_id: Organization ID
        :param from_timestamp: From timestamp
        :param to_timestamp: To timestamp
        :return: A list of reachability test results records
        """
        reachability_test_results_records = list()
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
                                    tcp_destination_ip_address = tcp_result["ipAddress"]

                                    reachability_test_results_records.append(
                                        {
                                            "timestamp": current_time,
                                            "from_timestamp": from_timestamp,
                                            "to_timestamp": to_timestamp,
                                            "organization_id": organization_id,
                                            "cluster_id": cluster_id,
                                            "cluster_name": cluster_name,
                                            "node_id": node_id,
                                            "host_name": host_name,
                                            "ip_address": ip_address,
                                            "destination_cluster": destination_cluster,
                                            "test_timestamp": test_timestamp,
                                            "test_id": test_id,
                                            "trigger_type": test_trigger_type,
                                            "protocol": "tcp",
                                            "port": tcp_port,
                                            "reachability": tcp_status,
                                            "destination_ip_address": tcp_destination_ip_address
                                        }
                                    )

                            if "udp" in stun_result:
                                for udp_result in stun_result["udp"]:
                                    udp_port = udp_result["port"]
                                    udp_status = udp_result["reachable"]
                                    udp_destination_ip_address = udp_result["ipAddress"]

                                    reachability_test_results_records.append(
                                        {
                                            "timestamp": current_time,
                                            "from_timestamp": from_timestamp,
                                            "to_timestamp": to_timestamp,
                                            "organization_id": organization_id,
                                            "cluster_id": cluster_id,
                                            "cluster_name": cluster_name,
                                            "node_id": node_id,
                                            "host_name": host_name,
                                            "ip_address": ip_address,
                                            "destination_cluster": destination_cluster,
                                            "test_timestamp": test_timestamp,
                                            "test_id": test_id,
                                            "trigger_type": test_trigger_type,
                                            "protocol": "udp",
                                            "port": udp_port,
                                            "reachability": udp_status,
                                            "destination_ip_address": udp_destination_ip_address
                                        }
                                    )

            except Exception as e:
                logging.error(
                    f"Error parsing reachability test results: {e}: {reachability_test_result}:\n{response}"
                )

        reachability_test_results_records = Parser.trim_whitespaces(reachability_test_results_records)
        return reachability_test_results_records

    @staticmethod
    def parse_media_health_monitoring_test_results(
            response: dict,
            current_time: Union[str, datetime.datetime],
            organization_id: str,
            from_timestamp: Union[str, datetime.datetime],
            to_timestamp: Union[str, datetime.datetime],
    ) -> list[dict]:
        """
        Parse media health monitoring test results from API response

        :param response: Media health monitoring test results API response
        :param current_time: Current time
        :param organization_id: Organization ID
        :param from_timestamp: From timestamp
        :param to_timestamp: To timestamp
        :return: A list of media health monitoring test results records
        """
        media_health_monitoring_test_results_records = list()
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

                                media_health_monitoring_test_results_records.append(
                                    {
                                        "timestamp": current_time,
                                        "from_timestamp": from_timestamp,
                                        "to_timestamp": to_timestamp,
                                        "organization_id": organization_id,
                                        "cluster_id": cluster_id,
                                        "cluster_name": cluster_name,
                                        "node_id": node_id,
                                        "host_name": host_name,
                                        "ip_address": ip_address,
                                        "test_timestamp": test_timestamp,
                                        "test_id": test_id,
                                        "trigger_type": test_trigger_type,
                                        "test_name": test_name,
                                        "test_result": test_result,
                                        "failure_reason": failure_reason
                                    }
                                )

            except Exception as e:
                logging.error(
                    f"Error parsing media health monitoring test results: {e}: {media_health_monitoring_test_result}:\n{response}"
                )

        media_health_monitoring_test_results_records = Parser.trim_whitespaces(
            media_health_monitoring_test_results_records)
        return media_health_monitoring_test_results_records

    @staticmethod
    def parse_network_test_results(
            response: dict,
            current_time: Union[str, datetime.datetime],
            organization_id: str,
            from_timestamp: Union[str, datetime.datetime],
            to_timestamp: Union[str, datetime.datetime],
    ) -> list[dict]:
        """
        Parse network test results from API response

        :param response: Network test results API response
        :param current_time: Current time
        :param organization_id: Organization ID
        :param from_timestamp: From timestamp
        :param to_timestamp: To timestamp
        :return: A list of network test results records
        """
        network_test_results_records = list()
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
                                        possible_remediation = result["failureDetails"]["possibleRemediation"][
                                            0]
                                    else:
                                        failure_reason = None
                                        possible_remediation = None

                                    network_test_results_records.append(
                                        {
                                            "timestamp": current_time,
                                            "from_timestamp": from_timestamp,
                                            "to_timestamp": to_timestamp,
                                            "organization_id": organization_id,
                                            "cluster_id": cluster_id,
                                            "cluster_name": cluster_name,
                                            "node_id": node_id,
                                            "host_name": host_name,
                                            "ip_address": ip_address,
                                            "test_timestamp": test_timestamp,
                                            "test_id": test_id,
                                            "trigger_type": test_trigger_type,
                                            "test_type": test_type,
                                            "service_type": service_type,
                                            "test_result": service_test_result,
                                            "failure_reason": failure_reason,
                                            "possible_remediation": possible_remediation
                                        }
                                    )

            except Exception as e:
                logging.error(
                    f"Error parsing connectivity test results: {e}: {connectivity_test_result}:\n{response}"
                )

        network_test_results_records = Parser.trim_whitespaces(network_test_results_records)
        return network_test_results_records
    
    @staticmethod
    def client_type_distribution_results(
            response: dict,
            current_time: Union[str, datetime.datetime],
            organization_id: str,
            from_timestamp: Union[str, datetime.datetime],
            to_timestamp: Union[str, datetime.datetime],
    ) -> list[dict]:
        """
        Parse Client type distribution results from API response

        :param response:Client type distribution results API response
        :param current_time: Current time
        :param organization_id: Organization ID
        :param from_timestamp: From timestamp
        :param to_timestamp: To timestamp
        :return: A list of client type distribution results records
        """
        client_type_distribution_test_results_records = list()
        aggregation_interval = response["aggregationInterval"]
        for client_type_distribution_test_result in response["items"]:
            try:
                distribution_timestamp = client_type_distribution_test_result["timestamp"]
                for cluster in client_type_distribution_test_result["clusters"]:
                    cluster_id = cluster["clusterId"]
                    cluster_name = cluster["clusterName"]
                    for distr in cluster["clientTypeDistributionDetails"]:
                        
                        device_type = distr["deviceType"]
                        device_description = distr["description"]
                        device_count = distr["count"]

                        client_type_distribution_test_results_records.append(
                            {
                                "timestamp": current_time,
                                "organization_id": organization_id,
                                "aggregation_interval": aggregation_interval,
                                "distribution_timestamp": distribution_timestamp,
                                "from_timestamp": from_timestamp,
                                "to_timestamp": to_timestamp,
                                "cluster_id": cluster_id,
                                "cluster_name": cluster_name,
                                "device_type": device_type,
                                "device_count": device_count,
                                "device_description": device_description
                            }
                        )

            except Exception as e:
                logging.error(
                    f"Error parsing client_type_distribution results: {e}: {client_type_distribution_test_result}:\n{response}"
                )

        client_type_distribution_test_results_records = Parser.trim_whitespaces(client_type_distribution_test_results_records)
        return client_type_distribution_test_results_records
            