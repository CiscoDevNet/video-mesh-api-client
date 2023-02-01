import os
import logging
import datetime
from typing import List, Union
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData, Table, select


load_dotenv()


class TimescaleDB:
    def __init__(self, setup_tables=True):
        self.DATABASE_URL = os.getenv("DATABASE_URL")
        self.base = declarative_base()
        self.engine = create_engine(self.DATABASE_URL)
        self.metadata = MetaData()

        while True:
            try:
                self.connection = self.engine.connect()
                self.session = sessionmaker(bind=self.engine)()
                self.connection.execute("SELECT 1")
            except Exception as e:
                logging.error(f"Error connecting to database: {e}")
                continue
            else:
                break

        if setup_tables:
            self.setup_tables()

        self.cluster_availability_table = Table(
            "cluster_availability",
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.node_availability_table = Table(
            "node_availability",
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.organizations_table = Table(
            "organizations",
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.cloud_overflow_table = Table(
            "cloud_overflow",
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.call_redirects_table = Table(
            "call_redirects",
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.media_health_monitoring_tool_table = Table(
            "media_health_monitoring_tool",
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.reachability_table = Table(
            "reachability",
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.cluster_utlization_table = Table(
            "cluster_utlization",
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.cluster_details_table = Table(
            "cluster_details",
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.node_details_table = Table(
            "node_details",
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.reachability_test_results_table = Table(
            "reachability_test_results",
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.media_health_monitoring_test_results_table = Table(
            "media_health_monitoring_test_results",
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.connectivity_test_results_table = Table(
            "connectivity_test_results",
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

    def setup_tables(self):
        queries = list()
        
        with open("setup/sql/ddl.sql") as f:
            queries = f.read().split("\n\n")
        for query in queries:
            try:
                self.connection.execute(query)
            except Exception as e:
                logging.error(f"Error creating table: {e}")
                exit(1)

        with open("setup/sql/city_coordinates.sql") as f:
            queries = f.read().split("\n")
        for query in queries:
            try:
                self.connection.execute(query)
            except Exception as e:
                logging.error(f"Error inserting city coordinates: {e}")

    def check_organization_exists(self, organization_id: str) -> bool:
        query = self.organizations_table.select().where(
            self.organizations_table.c.organization_id == organization_id
        )
        result = self.connection.execute(query).fetchall()
        return bool(result)

    def add_organization(self, organization_id: str, organization_name: str, created_at: str):
        if not self.check_organization_exists(organization_id):
            query = self.organizations_table.insert().values(
                organization_id=organization_id,
                organization_name=organization_name,
                created_at=created_at
            )
            self.connection.execute(query)

    def add_cluster_availability(
        self,
        current_time: datetime.datetime,
        organization_id: str,
        cluster_id: str,
        cluster_name: str,
        num_offline_nodes: int,
        num_online_nodes: int,
        availability: bool,
        segment_start_time: datetime.datetime,
        segment_end_time: datetime.datetime,
    ):
        query = postgresql.insert(self.cluster_availability_table).values(
            timestamp=current_time,
            organization_id=organization_id,
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            num_offline_nodes=num_offline_nodes,
            num_online_nodes=num_online_nodes,
            availability=availability,
            segment_start_time=segment_start_time,
            segment_end_time=segment_end_time
        )
        query = query.on_conflict_do_update(
            index_elements=[
                "organization_id",
                "cluster_id",
                "segment_start_time",
                "segment_end_time"
            ],
            set_={
                "timestamp": query.excluded.timestamp,
                "cluster_name": query.excluded.cluster_name,
                "num_offline_nodes": query.excluded.num_offline_nodes,
                "num_online_nodes": query.excluded.num_online_nodes,
                "availability": query.excluded.availability
            }
        )
        self.connection.execute(query)

    def get_all_cluster_ids(self) -> List[str]:
        stmt = select([self.cluster_availability_table.c.cluster_id])
        result = self.connection.execute(stmt).fetchall()
        result = list(map(lambda x: x[0], result))
        result = list(set(result))
        return result

    def add_node_availability(
        self,
        current_time: datetime.datetime,
        organization_id: str,
        cluster_id: str,
        cluster_name: str,
        node_id: str,
        host_name: str,
        availability: bool,
        segment_start_time: datetime.datetime,
        segment_end_time: datetime.datetime,
    ):
        query = postgresql.insert(self.node_availability_table).values(
            timestamp=current_time,
            organization_id=organization_id,
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            node_id=node_id,
            host_name=host_name,
            availability=availability,
            segment_start_time=segment_start_time,
            segment_end_time=segment_end_time
        )
        query = query.on_conflict_do_update(
            index_elements=[
                "organization_id",
                "cluster_id",
                "node_id",
                "segment_start_time",
                "segment_end_time"
            ],
            set_={
                "timestamp": query.excluded.timestamp,
                "cluster_name": query.excluded.cluster_name,
                "host_name": query.excluded.host_name,
                "availability": query.excluded.availability
            }
        )
        self.connection.execute(query)

    def add_cloud_overflow(
        self,
        current_time: datetime.datetime,
        organization_id: str,
        aggregation_interval: str,
        from_timestamp: datetime.datetime,
        to_timestamp: datetime.datetime,
        overflow_time: datetime.datetime,
        overflow_reason: str,
        overflow_count: int,
        remediation: str,
    ):
        query = postgresql.insert(self.cloud_overflow_table).values(
            timestamp=current_time,
            organization_id=organization_id,
            aggregation_interval=aggregation_interval,
            from_time=from_timestamp,
            to_time=to_timestamp,
            overflow_time=overflow_time,
            reason=overflow_reason,
            overflow_count=overflow_count,
            remediation=remediation
        )
        query = query.on_conflict_do_update(
            index_elements=["organization_id", "overflow_time", "reason"],
            set_={
                "timestamp": query.excluded.timestamp,
                "aggregation_interval": query.excluded.aggregation_interval,
                "from_time": query.excluded.from_time,
                "to_time": query.excluded.to_time,
                "overflow_count": query.excluded.overflow_count,
                "remediation": query.excluded.remediation
            }
        )
        self.connection.execute(query)

    def add_call_redirects(
        self,
        current_time: datetime.datetime,
        organization_id: str,
        aggregation_interval: str,
        from_timestamp: datetime.datetime,
        to_timestamp: datetime.datetime,
        redirect_time: datetime.datetime,
        cluster_id: str,
        cluster_name: str,
        redirect_reason: str,
        redirect_count: int,
        remediation: str,
    ):
        query = postgresql.insert(self.call_redirects_table).values(
            timestamp=current_time,
            organization_id=organization_id,
            aggregation_interval=aggregation_interval,
            from_time=from_timestamp,
            to_time=to_timestamp,
            redirect_time=redirect_time,
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            reason=redirect_reason,
            redirect_count=redirect_count,
            remediation=remediation
        )
        query = query.on_conflict_do_update(
            index_elements=["organization_id",
                            "cluster_id", "redirect_time", "reason"],
            set_={
                "timestamp": query.excluded.timestamp,
                "aggregation_interval": query.excluded.aggregation_interval,
                "from_time": query.excluded.from_time,
                "to_time": query.excluded.to_time,
                "cluster_name": query.excluded.cluster_name,
                "redirect_count": query.excluded.redirect_count,
                "remediation": query.excluded.remediation
            }
        )
        self.connection.execute(query)

    def add_media_health_monitoring_tool(
        self,
        current_time: datetime.datetime,
        organization_id: str,
        from_time: datetime.datetime,
        to_time: datetime.datetime,
        cluster_id: str,
        cluster_name: str,
        node_id: str,
        host_name: str,
        test_time: datetime.datetime,
        test_name: str,
        test_status: str,
        test_failure_reason: str = None
    ):
        query = postgresql.insert(self.media_health_monitoring_tool_table).values(
            timestamp=current_time,
            organization_id=organization_id,
            from_time=from_time,
            to_time=to_time,
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            node_id=node_id,
            host_name=host_name,
            test_time=test_time,
            test_name=test_name,
            test_result=test_status,
            failure_reason=test_failure_reason
        )
        query = query.on_conflict_do_update(
            index_elements=[
                "organization_id",
                "cluster_id",
                "node_id",
                "test_time",
                "test_name"
            ],
            set_={
                "timestamp": query.excluded.timestamp,
                "from_time": query.excluded.from_time,
                "to_time": query.excluded.to_time,
                "cluster_name": query.excluded.cluster_name,
                "host_name": query.excluded.host_name,
                "test_result": query.excluded.test_result,
                "failure_reason": query.excluded.failure_reason
            }
        )
        self.connection.execute(query)

    def add_reachability(
        self,
        current_time: datetime.datetime,
        organization_id: str,
        from_time: datetime.datetime,
        to_time: datetime.datetime,
        cluster_id: str,
        cluster_name: str,
        node_id: str,
        host_name: str,
        destination_cluster: str,
        test_time: datetime.datetime,
        reachability_type: str,
        port: int,
        reachability: bool,
    ):
        query = postgresql.insert(self.reachability_table).values(
            timestamp=current_time,
            organization_id=organization_id,
            from_time=from_time,
            to_time=to_time,
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            node_id=node_id,
            host_name=host_name,
            destination_cluster=destination_cluster,
            test_time=test_time,
            reachability_type=reachability_type,
            port=port,
            reachability=reachability
        )
        query = query.on_conflict_do_update(
            index_elements=[
                "organization_id",
                "cluster_id",
                "node_id",
                "destination_cluster",
                "test_time",
                "reachability_type",
                "port"
            ],
            set_={
                "timestamp": query.excluded.timestamp,
                "from_time": query.excluded.from_time,
                "to_time": query.excluded.to_time,
                "cluster_name": query.excluded.cluster_name,
                "host_name": query.excluded.host_name,
                "reachability": query.excluded.reachability
            }
        )
        self.connection.execute(query)

    def add_cluster_utlization(
        self,
        current_time: datetime.datetime,
        organization_id: str,
        from_timestamp: datetime.datetime,
        to_timestamp: datetime.datetime,
        aggregation_interval: str,
        measure_time: datetime.datetime,
        cluster_id: str,
        cluster_name: str,
        peak_cpu: float,
        avg_cpu: float,
        active_calls: int,
    ):
        query = postgresql.insert(self.cluster_utlization_table).values(
            timestamp=current_time,
            organization_id=organization_id,
            from_time=from_timestamp,
            to_time=to_timestamp,
            aggregation_interval=aggregation_interval,
            measure_time=measure_time,
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            peak_cpu=peak_cpu,
            avg_cpu=avg_cpu,
            active_calls=active_calls
        )
        query = query.on_conflict_do_update(
            index_elements=["organization_id", "measure_time", "cluster_id"],
            set_={
                "timestamp": query.excluded.timestamp,
                "from_time": query.excluded.from_time,
                "to_time": query.excluded.to_time,
                "aggregation_interval": query.excluded.aggregation_interval,
                "cluster_name": query.excluded.cluster_name,
                "peak_cpu": query.excluded.peak_cpu,
                "avg_cpu": query.excluded.avg_cpu,
                "active_calls": query.excluded.active_calls
            }
        )
        self.connection.execute(query)

    def add_cluster_details(
        self,
        current_time: datetime.datetime,
        organization_id: str,
        cluster_id: str,
        cluster_name: str,
        node_id: str,
        release_channel: str,
        upgrade_schedule_days: str,
        upgrade_schedule_time: str,
        upgrade_schedule_timezone: str,
        upgrade_pending: bool,
        next_upgrade_time: datetime.datetime,
    ):
        query = postgresql.insert(self.cluster_details_table).values(
            last_updated_timestamp=current_time,
            organization_id=organization_id,
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            node_id=node_id,
            release_channel=release_channel,
            upgrade_schedule_days=upgrade_schedule_days,
            upgrade_schedule_time=upgrade_schedule_time,
            upgrade_schedule_timezone=upgrade_schedule_timezone,
            upgrade_pending=upgrade_pending,
            next_upgrade_time=next_upgrade_time
        )
        query = query.on_conflict_do_update(
            index_elements=["organization_id", "cluster_id", "node_id"],
            set_={
                "last_updated_timestamp": query.excluded.last_updated_timestamp,
                "cluster_name": query.excluded.cluster_name,
                "release_channel": query.excluded.release_channel,
                "upgrade_schedule_days": query.excluded.upgrade_schedule_days,
                "upgrade_schedule_time": query.excluded.upgrade_schedule_time,
                "upgrade_schedule_timezone": query.excluded.upgrade_schedule_timezone,
                "upgrade_pending": query.excluded.upgrade_pending,
                "next_upgrade_time": query.excluded.next_upgrade_time
            }
        )
        self.connection.execute(query)

    def add_node_details(
        self,
        current_time: datetime.datetime,
        organization_id: str,
        cluster_id: str,
        node_id: str,
        host_name: str,
        deployment_type: str,
        country_code: str,
        city: str,
        timezone: str,
    ):
        query = postgresql.insert(self.node_details_table).values(
            last_updated_timestamp_node=current_time,
            organization_id=organization_id,
            cluster_id=cluster_id,
            node_id=node_id,
            host_name=host_name,
            deployment_type=deployment_type,
            country_code=country_code,
            city=city,
            timezone=timezone
        )
        query = query.on_conflict_do_update(
            index_elements=["node_id"],
            set_={
                "last_updated_timestamp_node": query.excluded.last_updated_timestamp_node,
                "organization_id": query.excluded.organization_id,
                "cluster_id": query.excluded.cluster_id,
                "host_name": query.excluded.host_name,
                "deployment_type": query.excluded.deployment_type,
                "country_code": query.excluded.country_code,
                "city": query.excluded.city,
                "timezone": query.excluded.timezone
            }
        )
        self.connection.execute(query)

    def add_reachability_test_results(
        self,
        current_time: datetime.datetime,
        from_timestamp: datetime.datetime,
        to_timestamp: datetime.datetime,
        organization_id: str,
        cluster_id: str,
        cluster_name: str,
        node_id: str,
        host_name: str,
        ip_address: str,
        destination_cluster: str,
        test_time: datetime.datetime,
        test_id: str,
        test_trigger_type: str,
        reachability_type: str,
        port: int,
        reachability_status: bool
    ):
        query = postgresql.insert(self.reachability_test_results_table).values(
            timestamp=current_time,
            from_time=from_timestamp,
            to_time=to_timestamp,
            organization_id=organization_id,
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            node_id=node_id,
            host_name=host_name,
            ip_address=ip_address,
            destination_cluster=destination_cluster,
            test_timestamp=test_time,
            test_id=test_id,
            trigger_type=test_trigger_type,
            reachability_type=reachability_type,
            port=port,
            reachability=reachability_status
        )
        query = query.on_conflict_do_update(
            index_elements=[
                "organization_id",
                "cluster_id",
                "node_id",
                "destination_cluster",
                "test_id",
                "test_timestamp",
                "reachability_type",
                "port"
            ],
            set_={
                "timestamp": query.excluded.timestamp,
                "from_time": query.excluded.from_time,
                "to_time": query.excluded.to_time,
                "cluster_name": query.excluded.cluster_name,
                "host_name": query.excluded.host_name,
                "trigger_type": query.excluded.trigger_type,
                "reachability": query.excluded.reachability
            }
        )
        self.connection.execute(query)

    def add_media_health_monitoring_test_results(
        self,
        current_time: datetime.datetime,
        from_timestamp: datetime.datetime,
        to_timestamp: datetime.datetime,
        organization_id: str,
        cluster_id: str,
        cluster_name: str,
        node_id: str,
        host_name: str,
        ip_address: str,
        test_timestamp: datetime.datetime,
        test_id: str,
        test_trigger_type: str,
        test_name: str,
        test_result: str,
        failure_reason: Union[str, None],
    ):
        query = postgresql.insert(self.media_health_monitoring_test_results_table).values(
            timestamp=current_time,
            from_time=from_timestamp,
            to_time=to_timestamp,
            organization_id=organization_id,
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            node_id=node_id,
            host_name=host_name,
            ip_address=ip_address,
            test_timestamp=test_timestamp,
            test_id=test_id,
            trigger_type=test_trigger_type,
            test_name=test_name,
            test_result=test_result,
            failure_reason=failure_reason
        )
        query = query.on_conflict_do_update(
            index_elements=[
                "organization_id",
                "cluster_id",
                "node_id",
                "test_id",
                "test_timestamp",
                "test_name"
            ],
            set_={
                "timestamp": query.excluded.timestamp,
                "from_time": query.excluded.from_time,
                "to_time": query.excluded.to_time,
                "cluster_name": query.excluded.cluster_name,
                "host_name": query.excluded.host_name,
                "trigger_type": query.excluded.trigger_type,
                "test_result": query.excluded.test_result,
                "failure_reason": query.excluded.failure_reason
            }
        )
        self.connection.execute(query)

    def add_connectivity_test_results(
        self,
        current_time: datetime.datetime,
        from_timestamp: datetime.datetime,
        to_timestamp: datetime.datetime,
        organization_id: str,
        cluster_id: str,
        cluster_name: str,
        node_id: str,
        host_name: str,
        ip_address: str,
        test_timestamp: datetime.datetime,
        test_id: str,
        test_trigger_type: str,
        test_type: str,
        service_type: str,
        test_result: str,
        failure_reason: str,
        possible_remediation: str
    ):
        query = postgresql.insert(self.connectivity_test_results_table).values(
            timestamp=current_time,
            from_time=from_timestamp,
            to_time=to_timestamp,
            organization_id=organization_id,
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            node_id=node_id,
            host_name=host_name,
            ip_address=ip_address,
            test_timestamp=test_timestamp,
            test_id=test_id,
            trigger_type=test_trigger_type,
            test_type=test_type,
            service_type=service_type,
            test_result=test_result,
            failure_reason=failure_reason,
            possible_remediation=possible_remediation
        )
        query = query.on_conflict_do_update(
            index_elements=[
                "organization_id",
                "cluster_id",
                "node_id",
                "test_id",
                "test_timestamp",
                "test_type",
                "service_type"
            ],
            set_={
                "timestamp": query.excluded.timestamp,
                "from_time": query.excluded.from_time,
                "to_time": query.excluded.to_time,
                "cluster_name": query.excluded.cluster_name,
                "host_name": query.excluded.host_name,
                "trigger_type": query.excluded.trigger_type,
                "test_result": query.excluded.test_result,
                "failure_reason": query.excluded.failure_reason,
                "possible_remediation": query.excluded.possible_remediation
            }
        )
        self.connection.execute(query)
