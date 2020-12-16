#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident: Config Parser
Parses and validates the required config file passed to the program.
@author: Jacob Wahlman
"""

import logging
logger = logging.getLogger("__main__")

from pathlib import Path
from configparser import ConfigParser
from typing import Dict


class TridentConfigParser:
    def __init__(self, config_file_path, config_file_section):
        self.args = self._setup_parser(config_file_path, config_file_section)

    @property
    def valid_config(self) -> bool:
        if self.config_file_path is None:
            return False

        return True

    def _setup_parser(self, config_file_path, config_file_section) -> Dict[str, str]:
        config_file_path_n = self._normalize_config_file_path(config_file_path)
        parser = ConfigParser()

        if not parser.read(config_file_path):
            raise FileNotFoundError(f"Failed to find a config file at: '{config_file_path}'")

        if not parser.has_section(config_file_section):
            raise ValueError(f"Section: '{config_file_section}' does not exist for config file: '{config_file_path}'")

        if not self._verify_config_file_section(parser[config_file_section]):
            raise ValueError(f"Config file is not valid due to previous error.")

        return dict(parser[config_file_section])

    def _normalize_config_file_path(self, config_file_path) -> None:
        try:
            normalized_path = Path(config_file_path)
        except Exception as e:
            logger.fatal(f"Failed to normalize path due to unexpected error: {e}")
            raise e

        return normalized_path

    def _verify_config_file_section(self, config_section_args) -> bool:
        for key in ["logging_level"]:
            if key not in config_section_args:
                logger.warning(f"Couldn't read value from config value with key: '{key}'")
                break
        else:
            return True

        return False