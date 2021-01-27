#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident: Config Parser

Parses and validates the required config file (JSON) passed to the program.
@author: Jacob Wahlman
"""

import json
from pathlib import Path

from typing import Dict, Union, Any, AnyStr

import logging
logger = logging.getLogger("__main__")


class TridentConfigParser:
    """ Parses the configuration file used by Trident to define plugins and arguments.
    
    :param config_file_path: The path to the config file on the host.
    :type config_file_path: str
    :param config_file_section: The section in the config file that should be used.
    :type config_file_section: str
    """
    def __init__(self, config_file_path: AnyStr, config_file_section: AnyStr):
        self.args = self._setup_parser(config_file_path, config_file_section)

    def _setup_parser(self, config_file_path: AnyStr, config_file_section: AnyStr) -> Dict[AnyStr, AnyStr]:
        """ Setup the config file parser from the given path and section.

        :param config_file_path: The path to the config file on the host.
        :type config_file_path: str
        :param config_file_section: The section in the config file that should be used.
        :type config_file_section: str
        :return: Section in configuration file read to dictionary.
        :rtype: dict
        """
        config_file_path_n = self._normalize_config_file_path(config_file_path)

        try:
            with open(config_file_path_n, "r") as config:
                data = json.load(config)
        except Exception as e:
            logger.error(f"Failed to read config file at: '{config_file_path_n}'.")
            raise e

        if not config_file_section in data:
            raise ValueError(f"Section: '{config_file_section}' does not exist for config file: '{config_file_path}'")

        data[config_file_section] = self._convert_data_section(data[config_file_section])
        if not self._verify_config_file_section(data[config_file_section]):
            raise ValueError(f"Config file is not valid due to previous error.")

        return data[config_file_section]

    def _normalize_config_file_path(self, config_file_path: AnyStr) -> Path:
        """ Normalize the path to the config file using the convention of the platform that Trident is run on.

        :param config_file_path: The path to the config file path to normalize.
        :type config_file_path: str
        :return: The platform normalized path.
        :rtype: :class:`Path`
        """
        try:
            normalized_path = Path(config_file_path)
        except Exception as e:
            logger.fatal(f"Failed to normalize path due to unexpected error: {e}")
            raise e

        return normalized_path
    
    def _convert_data_section(self, config_data_section: Dict[AnyStr, Union[Dict[AnyStr, Any], AnyStr]]) -> Dict[AnyStr, Union[Dict[AnyStr, Any], AnyStr]]:
        """ Convert all the argument keys in the config dictionary to lowercase.
        Ignores the plugin arguments keys since the arguments might be meant to be in any other case.

        :param config_data_section: The section of the config file to convert.
        :type config_data_section: dict
        :return: The converted config dictionary.
        :rtype: dict
        """
        def _convert(data, converted):
            for k in data.keys():
                if k in ["plugin_args"]:
                    converted[k] = data[k]
                elif isinstance(data[k], dict):
                    converted[k.lower()] = _convert(data[k], {})
                else:
                    converted[k.lower()] = data[k]

            return converted
        
        return _convert(config_data_section, {})

    def _verify_config_file_section(self, config_section_args: Dict[AnyStr, AnyStr]) -> bool:
        """ Verify the validity of the keys given in the config file section.
        Ensures that the required arguments are provided in the section.

        :param config_section_args: The configuration read from the section.
        :type config_section_args: dict
        :return: If the configuration files are valid.
        :rtype: bool
        """
        for key in ["logging_level"]:
            if key not in config_section_args:
                logger.warning(f"Couldn't read value from config value with key: '{key}'")
                break
        else:
            return True

        return False
