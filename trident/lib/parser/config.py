#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident: Config Parser

Parses and validates the required config file passed to the program.
@author: Jacob Wahlman
"""

from pathlib import Path
from configparser import ConfigParser

from typing import Dict

import logging
logger = logging.getLogger("__main__")


class TridentConfigParser:
    """ Parses the configuration file used by Trident to define plugins and arguments.
    
    :param config_file_path: The path to the config file on the host.
    :type config_file_path: str
    :param config_file_section: The section in the config file that should be used.
    :type config_file_section: str
    """
    def __init__(self, config_file_path: str, config_file_section: str):
        self.args = self._setup_parser(config_file_path, config_file_section)

    def _setup_parser(self, config_file_path: str, config_file_section: str) -> Dict[str, str]:
        """ Setup the config file parser from the given path and section.

        :param config_file_path: The path to the config file on the host.
        :type config_file_path: str
        :param config_file_section: The section in the config file that should be used.
        :type config_file_section: str
        :return: Section in configuration file read to dictionary.
        :rtype: dict
        """
        config_file_path_n = self._normalize_config_file_path(config_file_path)
        parser = ConfigParser()

        if not parser.read(config_file_path):
            raise FileNotFoundError(f"Failed to find a config file at: '{config_file_path}'")

        if not parser.has_section(config_file_section):
            raise ValueError(f"Section: '{config_file_section}' does not exist for config file: '{config_file_path}'")

        if not self._verify_config_file_section(parser[config_file_section]):
            raise ValueError(f"Config file is not valid due to previous error.")

        return dict(parser[config_file_section])

    def _normalize_config_file_path(self, config_file_path) -> Path:
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

    def _verify_config_file_section(self, config_section_args: Dict[str, str]) -> bool:
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
