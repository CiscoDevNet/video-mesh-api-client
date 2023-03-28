import logging
from pathlib import Path

from sqlalchemy import create_engine, MetaData, Table, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker, declarative_base


class APIDatabase:
    def __init__(self, connection_url: str, create_tables_on_init: bool = True):
        """
        Initialize APIDatabase object

        :param connection_url: Database connection URL
        :param create_tables_on_init: Whether to create tables on initialization
        """

        self.base = declarative_base()
        self.engine = create_engine(connection_url)
        self.metadata = MetaData()

        while True:
            try:
                self.connection = self.engine.connect()
                self.session = sessionmaker(bind=self.engine)()
                query = select(1)
                self.connection.execute(query)
            except Exception as e:
                logging.error(f"Error connecting to database: {e}")
                continue
            else:
                break

        if create_tables_on_init:
            self.create_tables()

        self.cluster_availability_table = Table(
            "cluster_availability",
            self.metadata,
            autoload_with=self.engine
        )

        self.node_availability_table = Table(
            "node_availability",
            self.metadata,
            autoload_with=self.engine
        )

        self.organizations_table = Table(
            "organizations",
            self.metadata,
            autoload_with=self.engine
        )

        self.cloud_overflow_table = Table(
            "cloud_overflow",
            self.metadata,
            autoload_with=self.engine
        )

        self.call_redirects_table = Table(
            "call_redirects",
            self.metadata,
            autoload_with=self.engine
        )

        self.cluster_utilization_table = Table(
            "cluster_utilization",
            self.metadata,
            autoload_with=self.engine
        )

        self.cluster_details_table = Table(
            "cluster_details",
            self.metadata,
            autoload_with=self.engine
        )

        self.node_details_table = Table(
            "node_details",
            self.metadata,
            autoload_with=self.engine
        )

        self.reachability_test_results_table = Table(
            "reachability_test_results",
            self.metadata,
            autoload_with=self.engine
        )

        self.media_health_monitoring_test_results_table = Table(
            "media_health_monitoring_test_results",
            self.metadata,
            autoload_with=self.engine
        )

        self.network_test_results_table = Table(
            "network_test_results",
            self.metadata,
            autoload_with=self.engine
        )

        self.tables = {
            "organizations": {
                "table": self.organizations_table,
                "index_elements": ["organization_id"],
            },
            "cluster_availability": {
                "table": self.cluster_availability_table,
                "index_elements": [
                    "organization_id",
                    "cluster_id",
                    "start_timestamp",
                    "end_timestamp"
                ],
            },
            "node_availability": {
                "table": self.node_availability_table,
                "index_elements": [
                    "organization_id",
                    "cluster_id",
                    "node_id",
                    "start_timestamp",
                    "end_timestamp"
                ],
            },
            "cloud_overflow": {
                "table": self.cloud_overflow_table,
                "index_elements": [
                    "organization_id",
                    "overflow_timestamp",
                    "overflow_reason"
                ]
            },
            "call_redirects": {
                "table": self.call_redirects_table,
                "index_elements": [
                    "organization_id",
                    "cluster_id",
                    "redirect_timestamp",
                    "redirect_reason"
                ],
            },
            "cluster_utilization": {
                "table": self.cluster_utilization_table,
                "index_elements": [
                    "organization_id",
                    "measure_timestamp",
                    "cluster_id"
                ]
            },
            "cluster_details": {
                "table": self.cluster_details_table,
                "index_elements": [
                    "organization_id",
                    "cluster_id",
                    "node_id"
                ]
            },
            "node_details": {
                "table": self.node_details_table,
                "index_elements": [
                    "node_id"
                ]
            },
            "reachability_test_results": {
                "table": self.reachability_test_results_table,
                "index_elements": [
                    "organization_id",
                    "cluster_id",
                    "node_id",
                    "destination_cluster",
                    "test_id",
                    "test_timestamp",
                    "protocol",
                    "port",
                    "destination_ip_address"
                ],
            },
            "media_health_monitoring_test_results": {
                "table": self.media_health_monitoring_test_results_table,
                "index_elements": [
                    "organization_id",
                    "cluster_id",
                    "node_id",
                    "test_id",
                    "test_timestamp",
                    "test_name"
                ]
            },
            "network_test_results": {
                "table": self.network_test_results_table,
                "index_elements": [
                    "organization_id",
                    "cluster_id",
                    "node_id",
                    "test_id",
                    "test_timestamp",
                    "test_type",
                    "service_type"
                ],
            }
        }

    def execute_queries_from_sql_file(self, sql_filepath: str):
        """
        Execute queries from sql file

        :param sql_filepath: Path to sql file
        :return: None
        """
        sql_filepath = Path(sql_filepath)
        if not sql_filepath.exists():
            logging.error(f"File {sql_filepath} does not exist")
            return
        with open(sql_filepath) as f:
            queries = f.read().split("\n\n")
        for query in queries:
            try:
                statement = text(query)
                self.connection.execute(statement)
            except Exception as e:
                logging.error(f"Error executing query: {e}")

    def create_tables(self):
        """
        Create tables in database

        :return: None
        """
        self.execute_queries_from_sql_file("setup/sql/ddl.sql")
        self.execute_queries_from_sql_file("setup/sql/city_coordinates.sql")

    def insert_records(self, records: list[dict], table_name: str):
        """
        Insert records into table

        :param records: Records to insert
        :param table_name: Table name
        :return: None
        """
        # TODO: Rarely, a record fails to get inserted. Exception is thrown but no error stack is displayed
        logging.info(f"Inserting {len(records)} records into {table_name} table")
        try:
            table = self.tables[table_name]["table"]
            index_elements = self.tables[table_name]["index_elements"]
            for record in records:
                try:
                    query = insert(table).values(record). \
                        on_conflict_do_update(
                        index_elements=index_elements,
                        set_=record
                    )
                    logging.debug(f"Executing query: {query}")
                    self.connection.execute(query)
                    self.connection.commit()
                except Exception as e:
                    logging.error(f"Error inserting record into table {table_name}: {e}: {record}")
        except KeyError:
            logging.error(f"Table {table_name} does not exist")
        except Exception as e:
            logging.error(f"Unknown Error inserting records into table {table_name}: {e}")

    def get_all_cluster_ids(self) -> list[str]:
        """
        Get all cluster IDs in database

        :return: List of cluster IDs
        """
        result = list()
        try:
            query = select(self.cluster_details_table.c.cluster_id).distinct()
            result = self.connection.execute(query).fetchall()
            result = list(set(map(lambda x: x[0], result)))
        except Exception as e:
            logging.error(f"Error getting cluster IDs: {e}")
        return result
