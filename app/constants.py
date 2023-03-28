# A mapping of required fields in a configuration file and their expected types
CONFIG_REQUIRED_FIELDS_AND_TYPES = {
    "app": {
        "logging_config": str,
        "host": str,
        "port": int,
        "debug": bool,
        "time": int,
        "update_interval_minutes": int,
        "auth_interval_hours": int
    },
    "api": {
        "host": str,
        "integration": {
            "client_id": str,
            "client_secret": str,
            "redirect_uri": str,
        },
        "database": {
            "url": str
        }
    },
    "grafana": {
        "host": str,
        "key": None,
    },
}

# The default datetime formats used by the Webex API
WEBEX_API_DATETIME_FORMAT_MILLISECOND_PRECISION = "%Y-%m-%dT%H:%M:%S.%fZ"
WEBEX_API_DATETIME_FORMAT_SECOND_PRECISION = "%Y-%m-%dT%H:%M:%SZ"
