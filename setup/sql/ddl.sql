CREATE TABLE IF NOT EXISTS ORGANIZATIONS(
    organization_id VARCHAR NOT NULL,
    organization_name VARCHAR NOT NULL,
    CREATED_AT TIMESTAMP NOT NULL,
    PRIMARY KEY (organization_id)
);

CREATE TABLE IF NOT EXISTS CLUSTER_AVAILABILITY(
    timestamp TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    cluster_id VARCHAR NOT NULL,
    cluster_name VARCHAR NOT NULL,
    num_online_nodes INTEGER NOT NULL,
    num_offline_nodes INTEGER NOT NULL,
    availability VARCHAR NOT NULL,
    segment_start_time TIMESTAMP NOT NULL,
    segment_end_time TIMESTAMP NOT NULL,
    PRIMARY KEY (organization_id, cluster_id, segment_start_time, segment_end_time)
);

CREATE TABLE IF NOT EXISTS NODE_AVAILABILITY(
    timestamp TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    cluster_id VARCHAR NOT NULL,
    cluster_name VARCHAR NOT NULL,
    node_id VARCHAR NOT NULL,
    host_name VARCHAR NOT NULL,
    availability VARCHAR NOT NULL,
    segment_start_time TIMESTAMP NOT NULL,
    segment_end_time TIMESTAMP NOT NULL,
    PRIMARY KEY (organization_id, cluster_id, node_id, segment_start_time, segment_end_time)
);

CREATE TABLE IF NOT EXISTS CLOUD_OVERFLOW(
    timestamp TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    aggregation_interval VARCHAR NOT NULL,
    from_time TIMESTAMP NOT NULL,
    to_time TIMESTAMP NOT NULL,
    overflow_time TIMESTAMP NOT NULL,
    reason VARCHAR NOT NULL,
    overflow_count INTEGER NOT NULL,
    remediation VARCHAR NOT NULL,
    PRIMARY KEY (organization_id, overflow_time, reason)
);

CREATE TABLE IF NOT EXISTS CALL_REDIRECTS(
    timestamp TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    aggregation_interval VARCHAR NOT NULL,
    from_time TIMESTAMP NOT NULL,
    to_time TIMESTAMP NOT NULL,
    redirect_time TIMESTAMP NOT NULL,
    cluster_id VARCHAR NOT NULL,
    cluster_name VARCHAR NOT NULL,
    reason VARCHAR NOT NULL,
    redirect_count INTEGER NOT NULL,
    remediation VARCHAR NOT NULL,
    PRIMARY KEY (organization_id, cluster_id, redirect_time, reason)
);

CREATE TABLE IF NOT EXISTS MEDIA_HEALTH_MONITORING_TOOL(
    timestamp TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    from_time TIMESTAMP NOT NULL,
    to_time TIMESTAMP NOT NULL,
    cluster_id VARCHAR NOT NULL,
    cluster_name VARCHAR NOT NULL,
    node_id VARCHAR NOT NULL,
    host_name VARCHAR NOT NULL,
    test_time TIMESTAMP NOT NULL,
    test_name VARCHAR NOT NULL,
    test_result VARCHAR NOT NULL,
    failure_reason VARCHAR,
    PRIMARY KEY (organization_id, cluster_id, node_id, test_time, test_name)
);

CREATE TABLE IF NOT EXISTS REACHABILITY(
    timestamp TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    from_time TIMESTAMP NOT NULL,
    to_time TIMESTAMP NOT NULL,
    cluster_id VARCHAR NOT NULL,
    cluster_name VARCHAR NOT NULL,
    node_id VARCHAR NOT NULL,
    host_name VARCHAR NOT NULL,
    destination_cluster VARCHAR NOT NULL,
    test_time TIMESTAMP NOT NULL,
    reachability_type VARCHAR NOT NULL,
    port INTEGER NOT NULL,
    reachability VARCHAR NOT NULL,
    PRIMARY KEY(organization_id, cluster_id, node_id, destination_cluster, test_time, reachability_type, port)
);

CREATE TABLE IF NOT EXISTS CLUSTER_UTLIZATION(
    timestamp TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    from_time TIMESTAMP NOT NULL,
    to_time TIMESTAMP NOT NULL,
    aggregation_interval VARCHAR NOT NULL,
    measure_time TIMESTAMP NOT NULL,
    cluster_id VARCHAR NOT NULL,
    cluster_name VARCHAR NOT NULL,
    peak_cpu FLOAT NOT NULL,
    avg_cpu FLOAT NOT NULL,
    active_calls INTEGER NOT NULL,
    PRIMARY KEY (organization_id, measure_time, cluster_id)
);

CREATE TABLE IF NOT EXISTS CLUSTER_DETAILS(
    last_updated_timestamp TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    cluster_id VARCHAR NOT NULL,
    cluster_name VARCHAR NOT NULL,
    node_id VARCHAR NOT NULL,
    release_channel VARCHAR NOT NULL,
    upgrade_schedule_days VARCHAR NOT NULL,
    upgrade_schedule_time TIME NOT NULL,
    upgrade_schedule_timezone VARCHAR NOT NULL,
    upgrade_pending VARCHAR NOT NULL,
    next_upgrade_time TIMESTAMP NOT NULL,
    PRIMARY KEY (organization_id, cluster_id, node_id)
);

CREATE TABLE IF NOT EXISTS NODE_DETAILS(
    last_updated_timestamp_node TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    cluster_id VARCHAR NOT NULL,
    node_id VARCHAR NOT NULL,
    host_name VARCHAR NOT NULL,
    deployment_type VARCHAR NOT NULL,
    country_code VARCHAR NOT NULL,
    city VARCHAR NOT NULL,
    timezone VARCHAR NOT NULL,
    PRIMARY KEY (node_id),
    CONSTRAINT fk_cluster
        FOREIGN KEY (organization_id, cluster_id, node_id)
            REFERENCES CLUSTER_DETAILS(organization_id, cluster_id, node_id)
);

CREATE TABLE IF NOT EXISTS REACHABILITY_TEST_RESULTS(
    timestamp TIMESTAMP NOT NULL,
    from_time TIMESTAMP NOT NULL,
    to_time TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    cluster_id VARCHAR NOT NULL,
    cluster_name VARCHAR NOT NULL,
    node_id VARCHAR NOT NULL,
    host_name VARCHAR NOT NULL,
    ip_address VARCHAR NOT NULL,
    destination_cluster VARCHAR NOT NULL,
    test_timestamp TIMESTAMP NOT NULL,
    test_id VARCHAR NOT NULL,
    trigger_type VARCHAR NOT NULL,
    reachability_type VARCHAR NOT NULL,
    port INTEGER NOT NULL,
    reachability BOOLEAN NOT NULL,
    PRIMARY KEY(organization_id, cluster_id, node_id, destination_cluster, test_id, test_timestamp, reachability_type, port)
);

CREATE TABLE IF NOT EXISTS MEDIA_HEALTH_MONITORING_TEST_RESULTS(
    timestamp TIMESTAMP NOT NULL,
    from_time TIMESTAMP NOT NULL,
    to_time TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    cluster_id VARCHAR NOT NULL,
    cluster_name VARCHAR NOT NULL,
    node_id VARCHAR NOT NULL,
    host_name VARCHAR NOT NULL,
    ip_address VARCHAR NOT NULL,
    test_timestamp TIMESTAMP NOT NULL,
    test_id VARCHAR NOT NULL,
    trigger_type VARCHAR NOT NULL,
    test_name VARCHAR NOT NULL,
    test_result VARCHAR NOT NULL,
    failure_reason VARCHAR,
    PRIMARY KEY (organization_id, cluster_id, node_id, test_id, test_timestamp, test_name)
);

CREATE TABLE IF NOT EXISTS CONNECTIVITY_TEST_RESULTS(
    timestamp TIMESTAMP NOT NULL,
    from_time TIMESTAMP NOT NULL,
    to_time TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    cluster_id VARCHAR NOT NULL,
    cluster_name VARCHAR NOT NULL,
    node_id VARCHAR NOT NULL,
    host_name VARCHAR NOT NULL,
    ip_address VARCHAR NOT NULL,
    test_timestamp TIMESTAMP NOT NULL,
    test_id VARCHAR NOT NULL,
    trigger_type VARCHAR NOT NULL,
    test_type VARCHAR NOT NULL,
    service_type VARCHAR NOT NULL,
    test_result VARCHAR NOT NULL,
    failure_reason VARCHAR,
    possible_remediation VARCHAR,
    PRIMARY KEY (organization_id, cluster_id, node_id, test_id, test_timestamp, test_type, service_type)
);

CREATE TABLE IF NOT EXISTS CITY_COORDINATES(
    continent_name VARCHAR NOT NULL,
    city_name VARCHAR NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    PRIMARY KEY (continent_name, city_name)
);

SELECT create_hypertable('CLUSTER_AVAILABILITY', 'segment_start_time', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('CLUSTER_AVAILABILITY', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('NODE_AVAILABILITY', 'segment_start_time', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('NODE_AVAILABILITY', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('CLOUD_OVERFLOW', 'overflow_time', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('CLOUD_OVERFLOW', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('CALL_REDIRECTS', 'redirect_time', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('CALL_REDIRECTS', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('MEDIA_HEALTH_MONITORING_TOOL', 'test_time', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('MEDIA_HEALTH_MONITORING_TOOL', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('REACHABILITY', 'test_time', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('REACHABILITY', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('CLUSTER_UTLIZATION', 'measure_time', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('CLUSTER_UTLIZATION', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('REACHABILITY_TEST_RESULTS', 'test_timestamp', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('REACHABILITY_TEST_RESULTS', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('MEDIA_HEALTH_MONITORING_TEST_RESULTS', 'test_timestamp', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('MEDIA_HEALTH_MONITORING_TEST_RESULTS', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('CONNECTIVITY_TEST_RESULTS', 'test_timestamp', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('CONNECTIVITY_TEST_RESULTS', INTERVAL '30 days', if_not_exists => TRUE);

COMMIT;