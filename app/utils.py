import logging
from pathlib import Path
from typing import Optional, Union

import yaml

import constants


def load_config(filepath: str) -> Optional[dict]:
    """
    Load configuration from YAML file

    :param filepath: Path to configuration file
    :return: Configuration dictionary
    """
    config = None
    config_filepath = Path(filepath)
    if config_filepath.exists() and config_filepath.is_file():
        with open(config_filepath, "r") as f:
            config = yaml.safe_load(f)
            if not verify_config(config):
                config = None
                logging.error("Configuration file is invalid")
            else:
                logging.info("Configuration file loaded successfully")
    else:
        logging.error("Configuration file not found")
    return config


def verify_config(config: dict) -> bool:
    """
    Verifies if all required fields and correct data types are present in the configuration dictionary

    :param config: Configuration parameters
    :return: True if all required fields and correct data types are present in the configuration dictionary, False otherwise
    """
    return check_config_field_and_type_recursively(constants.CONFIG_REQUIRED_FIELDS_AND_TYPES, config)


def check_config_field_and_type_recursively(
        expected_config_root: Union[dict, type],
        loaded_config_root: Union[dict, type]
) -> bool:
    """
    Recursively check if the loaded configuration dictionary matches the expected configuration dictionary

    :param expected_config_root: Expected configuration dictionary
    :param loaded_config_root: Loaded configuration dictionary
    :return: True if the loaded configuration dictionary matches the expected configuration dictionary, False otherwise
    """
    if isinstance(expected_config_root, dict):
        for key, value in expected_config_root.items():
            if key not in loaded_config_root:
                logging.error(f"Required Key {key} not found in config")
                return False
            if not check_config_field_and_type_recursively(value, loaded_config_root[key]):
                logging.error(f"Key {key} failed check")
                return False
    elif expected_config_root is not None and not isinstance(loaded_config_root, expected_config_root):
        logging.error(f"Type {type(loaded_config_root)} does not match expected type {expected_config_root}")
        return False

    return True
