import os
import logging
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData, Table, select


load_dotenv()


class TimescaleDB:
    def __init__(self):
        self.DATABASE_URL = os.getenv('DATABASE_URL')
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

        self.setup_tables()

        self.cluster_availability_table = Table(
            'cluster_availability',
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.node_availability_table = Table(
            'node_availability',
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.organizations_table = Table(
            'organizations',
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.cloud_overflow_table = Table(
            'cloud_overflow',
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.call_redirects_table = Table(
            'call_redirects',
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.media_health_monitoring_tool_table = Table(
            'media_health_monitoring_tool',
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.reachability_table = Table(
            'reachability',
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.cluster_utlization_table = Table(
            'cluster_utlization',
            self.metadata,
            autoload=True,
            autoload_with=self.engine
        )

        self.cluster_details_table = Table(
            'cluster_details',
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

    def check_organization_exists(self, organization_id):
        query = self.organizations_table.select().where(
            self.organizations_table.c.organization_id == organization_id
        )
        result = self.connection.execute(query).fetchall()
        return bool(result)

    def add_organization(self, organization_id, organization_name, created_at):
        if not self.check_organization_exists(organization_id):
            query = self.organizations_table.insert().values(
                organization_id=organization_id,
                organization_name=organization_name,
                created_at=created_at
            )
            self.connection.execute(query)

    def check_cluster_availability_exists(
        self,
        organization_id,
        cluster_id,
        num_offline_nodes,
        num_online_nodes,
        availability,
        segment_start_time,
        segment_end_time
    ):
        query = self.cluster_availability_table.select().where(
            self.cluster_availability_table.c.organization_id == organization_id,
            self.cluster_availability_table.c.cluster_id == cluster_id,
            self.cluster_availability_table.c.num_offline_nodes == num_offline_nodes,
            self.cluster_availability_table.c.num_online_nodes == num_online_nodes,
            self.cluster_availability_table.c.availability == availability,
            self.cluster_availability_table.c.segment_start_time == segment_start_time,
            self.cluster_availability_table.c.segment_end_time == segment_end_time
        )
        result = self.connection.execute(query).fetchall()
        return bool(result)

    def add_cluster_availability(
        self,
        current_time,
        organization_id,
        cluster_id,
        cluster_name,
        num_offline_nodes,
        num_online_nodes,
        availability,
        segment_start_time,
        segment_end_time
    ):

        if not self.check_cluster_availability_exists(
            organization_id,
            cluster_id,
            num_offline_nodes,
            num_online_nodes,
            availability,
            segment_start_time,
            segment_end_time
        ):
            query = self.cluster_availability_table.insert().values(
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
            self.connection.execute(query)

    def get_all_cluster_ids(self):
        stmt = select([self.cluster_availability_table.c.cluster_id])
        result = self.connection.execute(stmt).fetchall()
        result = list(map(lambda x: x[0], result))
        result = list(set(result))
        return result

    def check_node_availability_exists(self, organization_id, cluster_id, node_id, segment_start_time, segment_end_time):
        query = self.node_availability_table.select().where(
            self.node_availability_table.c.organization_id == organization_id,
            self.node_availability_table.c.cluster_id == cluster_id,
            self.node_availability_table.c.node_id == node_id,
            self.node_availability_table.c.segment_start_time == segment_start_time,
            self.node_availability_table.c.segment_end_time == segment_end_time
        )
        result = self.connection.execute(query).fetchall()
        return bool(result)

    def add_node_availability(
        self,
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
    ):

        if not self.check_node_availability_exists(
            organization_id,
            cluster_id,
            node_id,
            segment_start_time,
            segment_end_time
        ):
            query = self.node_availability_table.insert().values(
                timestamp=current_time,
                organization_id=organization_id,
                cluster_id=cluster_id,
                cluster_name=cluster_name,
                node_id=node_id,
                host_name=host_name,
                num_offline_nodes=num_offline_nodes,
                num_online_nodes=num_online_nodes,
                availability=availability,
                segment_start_time=segment_start_time,
                segment_end_time=segment_end_time
            )
            self.connection.execute(query)

    def check_cloud_overflow_exists(self, organization_id, overflow_time, reason):
        query = self.cloud_overflow_table.select().where(
            self.cloud_overflow_table.c.organization_id == organization_id,
            self.cloud_overflow_table.c.overflow_time == overflow_time,
            self.cloud_overflow_table.c.reason == reason
        )
        result = self.connection.execute(query).fetchall()
        return bool(result)

    def add_cloud_overflow(
        self,
        current_time,
        organization_id,
        aggregation_interval,
        from_timestamp,
        to_timestamp,
        overflow_time,
        overflow_reason,
        overflow_count,
        remediation
    ):
        if not self.check_cloud_overflow_exists(
            organization_id,
            overflow_time,
            overflow_reason
        ):
            query = self.cloud_overflow_table.insert().values(
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
            self.connection.execute(query)

    def check_call_redirects_exists(self, organization_id, cluster_id, redirect_time, reason):
        query = self.call_redirects_table.select().where(
            self.call_redirects_table.c.organization_id == organization_id,
            self.call_redirects_table.c.cluster_id == cluster_id,
            self.call_redirects_table.c.redirect_time == redirect_time,
            self.call_redirects_table.c.reason == reason
        )
        result = self.connection.execute(query).fetchall()
        return bool(result)

    def add_call_redirects(
        self,
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
    ):
        if not self.check_call_redirects_exists(
            organization_id,
            cluster_id,
            redirect_time,
            redirect_reason
        ):
            query = self.call_redirects_table.insert().values(
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
            self.connection.execute(query)

    def check_media_health_monitoring_tool_exists(self, organization_id, cluster_id, node_id, test_time, test_name):
        query = self.media_health_monitoring_tool_table.select().where(
            self.media_health_monitoring_tool_table.c.organization_id == organization_id,
            self.media_health_monitoring_tool_table.c.cluster_id == cluster_id,
            self.media_health_monitoring_tool_table.c.node_id == node_id,
            self.media_health_monitoring_tool_table.c.test_time == test_time,
            self.media_health_monitoring_tool_table.c.test_name == test_name
        )
        result = self.connection.execute(query).fetchall()
        return bool(result)

    def add_media_health_monitoring_tool(
        self,
        current_time,
        organization_id,
        from_time,
        to_time,
        cluster_id,
        cluster_name,
        node_id,
        host_name,
        test_time,
        test_name,
        test_status,
        test_failure_reason=None
    ):
        if not self.check_media_health_monitoring_tool_exists(
            organization_id,
            cluster_id,
            node_id,
            test_time,
            test_name
        ):
            query = self.media_health_monitoring_tool_table.insert().values(
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
            self.connection.execute(query)

    def check_reachability_exists(self, organization_id, cluster_id, node_id, destination_cluster, test_time, reachability_type, port):
        query = self.reachability_table.select().where(
            self.reachability_table.c.organization_id == organization_id,
            self.reachability_table.c.cluster_id == cluster_id,
            self.reachability_table.c.node_id == node_id,
            self.reachability_table.c.destination_cluster == destination_cluster,
            self.reachability_table.c.test_time == test_time,
            self.reachability_table.c.reachability_type == reachability_type,
            self.reachability_table.c.port == port
        )
        result = self.connection.execute(query).fetchall()
        return bool(result)

    def add_reachability(
        self,
        current_time,
        organization_id,
        from_time,
        to_time,
        cluster_id,
        cluster_name,
        node_id,
        host_name,
        destination_cluster,
        test_time,
        reachability_type,
        port,
        reachability
    ):
        if not self.check_reachability_exists(
            organization_id,
            cluster_id,
            node_id,
            destination_cluster,
            test_time,
            reachability_type,
            port
        ):
            query = self.reachability_table.insert().values(
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
            self.connection.execute(query)

    def check_cluster_utlization_exists(self, organization_id, measure_time, cluster_id):
        query = self.cluster_utlization_table.select().where(
            self.cluster_utlization_table.c.organization_id == organization_id,
            self.cluster_utlization_table.c.measure_time == measure_time,
            self.cluster_utlization_table.c.cluster_id == cluster_id
        )
        result = self.connection.execute(query).fetchall()
        return bool(result)

    def add_cluster_utlization(
        self, 
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
    ):
        if not self.check_cluster_utlization_exists(
            organization_id,
            measure_time,
            cluster_id
        ):
            query = self.cluster_utlization_table.insert().values(
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
            self.connection.execute(query)

    def check_cluster_details_exists(self, organization_id, cluster_id, node_id):
        query = self.cluster_details_table.select().where(
            self.cluster_details_table.c.organization_id == organization_id,
            self.cluster_details_table.c.cluster_id == cluster_id,
            self.cluster_details_table.c.node_id == node_id
        )
        result = self.connection.execute(query).fetchall()
        return bool(result)
    
    def add_cluster_details(
        self,
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
    ):
        if not self.check_cluster_details_exists(
            organization_id,
            cluster_id,
            node_id
        ):
            query = self.cluster_details_table.insert().values(
                organization_id=organization_id,
                cluster_id=cluster_id,
                cluster_name=cluster_name,
                node_id=node_id,
                host_name=host_name,
                release_channel=release_channel,
                upgrade_schedule_days=upgrade_schedule_days,
                upgrade_schedule_time=upgrade_schedule_time,
                upgrade_schedule_timezone=upgrade_schedule_timezone,
                upgrade_pending=upgrade_pending,
                next_upgrade_time=next_upgrade_time
            )
            self.connection.execute(query)