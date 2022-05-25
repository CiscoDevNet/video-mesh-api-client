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
    num_online_nodes INTEGER NOT NULL,
    num_offline_nodes INTEGER NOT NULL,
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
    organization_id VARCHAR NOT NULL,
    cluster_id VARCHAR NOT NULL,
    cluster_name VARCHAR NOT NULL,
    node_id VARCHAR NOT NULL,
    host_name VARCHAR NOT NULL,
    release_channel VARCHAR NOT NULL,
    upgrade_schedule_days VARCHAR NOT NULL,
    upgrade_schedule_time TIME NOT NULL,
    upgrade_schedule_timezone VARCHAR NOT NULL,
    upgrade_pending VARCHAR NOT NULL,
    next_upgrade_time TIMESTAMP NOT NULL,
    PRIMARY KEY (organization_id, cluster_id, node_id)
);

CREATE TABLE IF NOT EXISTS CITY_COORDINATES(
    continent_name VARCHAR NOT NULL,
    city_name VARCHAR NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    PRIMARY KEY (continent_name, city_name)
);