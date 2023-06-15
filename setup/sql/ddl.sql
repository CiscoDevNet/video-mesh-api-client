CREATE TABLE IF NOT EXISTS ORGANIZATIONS(
    organization_id VARCHAR NOT NULL,
    organization_name VARCHAR NOT NULL,
    create_timestamp TIMESTAMP NOT NULL,
    PRIMARY KEY (organization_id)
);

CREATE TABLE IF NOT EXISTS CLUSTER_AVAILABILITY(
    timestamp TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    cluster_id VARCHAR NOT NULL,
    cluster_name VARCHAR NOT NULL,
    online_nodes INTEGER NOT NULL,
    offline_nodes INTEGER NOT NULL,
    availability VARCHAR NOT NULL,
    start_timestamp TIMESTAMP NOT NULL,
    end_timestamp TIMESTAMP NOT NULL,
    PRIMARY KEY (organization_id, cluster_id, start_timestamp, end_timestamp)
);

CREATE TABLE IF NOT EXISTS NODE_AVAILABILITY(
    timestamp TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    cluster_id VARCHAR NOT NULL,
    cluster_name VARCHAR NOT NULL,
    node_id VARCHAR NOT NULL,
    host_name VARCHAR NOT NULL,
    availability VARCHAR NOT NULL,
    start_timestamp TIMESTAMP NOT NULL,
    end_timestamp TIMESTAMP NOT NULL,
    PRIMARY KEY (organization_id, cluster_id, node_id, start_timestamp, end_timestamp)
);

CREATE TABLE IF NOT EXISTS CLOUD_OVERFLOW(
    timestamp TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    aggregation_interval VARCHAR NOT NULL,
    from_timestamp TIMESTAMP NOT NULL,
    to_timestamp TIMESTAMP NOT NULL,
    overflow_timestamp TIMESTAMP NOT NULL,
    overflow_reason VARCHAR NOT NULL,
    overflow_count INTEGER NOT NULL,
    remediation VARCHAR NOT NULL,
    PRIMARY KEY (organization_id, overflow_timestamp, overflow_reason)
);

CREATE TABLE IF NOT EXISTS CALL_REDIRECTS(
    timestamp TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    aggregation_interval VARCHAR NOT NULL,
    from_timestamp TIMESTAMP NOT NULL,
    to_timestamp TIMESTAMP NOT NULL,
    redirect_timestamp TIMESTAMP NOT NULL,
    cluster_id VARCHAR NOT NULL,
    cluster_name VARCHAR NOT NULL,
    redirect_reason VARCHAR NOT NULL,
    redirect_count INTEGER NOT NULL,
    remediation VARCHAR NOT NULL,
    PRIMARY KEY (organization_id, cluster_id, redirect_timestamp, redirect_reason)
);

CREATE TABLE IF NOT EXISTS CLUSTER_UTILIZATION(
    timestamp TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    from_timestamp TIMESTAMP NOT NULL,
    to_timestamp TIMESTAMP NOT NULL,
    aggregation_interval VARCHAR NOT NULL,
    measure_timestamp TIMESTAMP NOT NULL,
    cluster_id VARCHAR NOT NULL,
    cluster_name VARCHAR NOT NULL,
    peak_cpu FLOAT NOT NULL,
    avg_cpu FLOAT NOT NULL,
    active_calls INTEGER NOT NULL,
    PRIMARY KEY (organization_id, measure_timestamp, cluster_id)
);

CREATE TABLE IF NOT EXISTS CLUSTER_DETAILS(
    timestamp TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    cluster_id VARCHAR NOT NULL,
    cluster_name VARCHAR NOT NULL,
    node_id VARCHAR NOT NULL,
    release_channel VARCHAR NOT NULL,
    upgrade_schedule_days VARCHAR NOT NULL,
    upgrade_schedule_time TIME NOT NULL,
    upgrade_schedule_timezone VARCHAR NOT NULL,
    upgrade_pending VARCHAR NOT NULL,
    next_upgrade_timestamp TIMESTAMP NOT NULL,
    PRIMARY KEY (organization_id, cluster_id, node_id)
);

CREATE TABLE IF NOT EXISTS NODE_DETAILS(
    timestamp TIMESTAMP NOT NULL,
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
    from_timestamp TIMESTAMP NOT NULL,
    to_timestamp TIMESTAMP NOT NULL,
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
    protocol VARCHAR NOT NULL,
    port INTEGER NOT NULL,
    reachability BOOLEAN NOT NULL,
    destination_ip_address VARCHAR,
    PRIMARY KEY(organization_id, cluster_id, node_id, destination_cluster, test_id, test_timestamp, protocol, port, destination_ip_address)
);

CREATE TABLE IF NOT EXISTS MEDIA_HEALTH_MONITORING_TEST_RESULTS(
    timestamp TIMESTAMP NOT NULL,
    from_timestamp TIMESTAMP NOT NULL,
    to_timestamp TIMESTAMP NOT NULL,
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

CREATE TABLE IF NOT EXISTS NETWORK_TEST_RESULTS(
    timestamp TIMESTAMP NOT NULL,
    from_timestamp TIMESTAMP NOT NULL,
    to_timestamp TIMESTAMP NOT NULL,
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
    continent VARCHAR NOT NULL,
    city VARCHAR NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    PRIMARY KEY (continent, city)
);

CREATE TABLE IF NOT EXISTS CLIENT_TYPE_DISTRIBUTION(
    timestamp TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    aggregation_interval VARCHAR NOT NULL,
    from_timestamp TIMESTAMP NOT NULL,
    to_timestamp TIMESTAMP NOT NULL,
    distribution_timestamp TIMESTAMP NOT NULL,
    cluster_id VARCHAR NOT NULL,
    cluster_name VARCHAR NOT NULL,
    device_type VARCHAR NOT NULL,
    device_count INTEGER NOT NULL,
    device_description VARCHAR NOT NULL,
    PRIMARY KEY (organization_id, cluster_id, distribution_timestamp, device_type)
);

CREATE TABLE IF NOT EXISTS WEBHOOK_EVENTS(
    timestamp TIMESTAMP NOT NULL,
    organization_id VARCHAR NOT NULL,
    cluster_id VARCHAR,
    alert_id VARCHAR NOT NULL,
    alert_name VARCHAR NOT NULL,
    alert_type VARCHAR NOT NULL,
    total_calls INTEGER NOT NULL,
    metric_count INTEGER NOT NULL,
    threshold_name VARCHAR NOT NULL,
    threshold INTEGER NOT NULL,
    absolute_percentage_over_threshold FLOAT NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    PRIMARY KEY (organization_id, alert_name, event_timestamp, alert_id)
);


SELECT create_hypertable('CLUSTER_AVAILABILITY', 'start_timestamp', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('CLUSTER_AVAILABILITY', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('NODE_AVAILABILITY', 'start_timestamp', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('NODE_AVAILABILITY', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('CLOUD_OVERFLOW', 'overflow_timestamp', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('CLOUD_OVERFLOW', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('CALL_REDIRECTS', 'redirect_timestamp', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('CALL_REDIRECTS', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('CLUSTER_UTILIZATION', 'measure_timestamp', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('CLUSTER_UTILIZATION', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('REACHABILITY_TEST_RESULTS', 'test_timestamp', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('REACHABILITY_TEST_RESULTS', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('MEDIA_HEALTH_MONITORING_TEST_RESULTS', 'test_timestamp', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('MEDIA_HEALTH_MONITORING_TEST_RESULTS', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('NETWORK_TEST_RESULTS', 'test_timestamp', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('NETWORK_TEST_RESULTS', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('CLIENT_TYPE_DISTRIBUTION', 'distribution_timestamp', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('CLIENT_TYPE_DISTRIBUTION', INTERVAL '30 days', if_not_exists => TRUE);

SELECT create_hypertable('WEBHOOK_EVENTS', 'event_timestamp', chunk_time_interval => INTERVAL '24 hours', if_not_exists => TRUE);

SELECT add_retention_policy('WEBHOOK_EVENTS', INTERVAL '30 days', if_not_exists => TRUE);

COMMIT;