#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident: Main Module.
@author: Jacob Wahlman
"""

from dataclasses import dataclass
from json import loads

from typing import Dict, Union, NoReturn

import logging
logger = logging.getLogger("__main__")

from trident.lib.daemon.trident import TridentDaemonConfig, TridentDaemon


@dataclass
class TridentConfig:
    trident_config: Dict[str, str]
    trident_daemon_config: Dict[str, Union[str, int]]
    trident_data_daemon_config: Dict[str, Union[str, bool]]

    def __init__(self, kwargs: Dict[str, str]):
        self.trident_config = {
            "logging_level": kwargs.get("logging_level"),
            "verbose": kwargs.get("verbose"),
            "quiet": kwargs.get("quiet"),
        }

        self.trident_daemon_config = {
            "plugins": loads(kwargs.get("plugins")),
            "workers": kwargs.get("workers"),
            "dont_store_on_error": kwargs.get("dont_store_on_error")
        }

        self.trident_data_daemon_config = {
            "path_store": kwargs.get("path_store"),
            "no_store": kwargs.get("no_store"),
            "global_store": kwargs.get("global_store"),
        }

        self._verify_trident_config()
        self._verify_trident_daemon_config()
        self._verify_trident_data_daemon_config()

    def _verify_trident_config(self) -> NoReturn:
        if self.trident_config["verbose"] and self.trident_config["quiet"]:
            raise ValueError("Can't both use verbose logging and quiet logging.")

        if self.trident_config["logging_level"] and self.trident_config["quiet"]:
            logger.warning(f"Logging level: '{self.trident_config['logging_level']}' was overriden by quiet flag")

        if self.trident_config["logging_level"] and self.trident_config["verbose"]:
            logger.warning(f"Logging level: '{self.trident_config['logging_level']}' was overriden by verbose flag")

    def _verify_trident_daemon_config(self) -> NoReturn:
        try:
            int(self.trident_daemon_config["workers"])
        except ValueError:
            raise ValueError(f"Value of workers is not a valid positive integer")

        if int(self.trident_daemon_config["workers"]) <= 0:
            raise ValueError(f"Invalid amount of workers specified: '{self.trident_daemon_config['workers']}', value must be greater than 0")

        if not self.trident_daemon_config["plugins"]:
            logger.warning("No plugins was specified")

    def _verify_trident_data_daemon_config(self) -> NoReturn:
        if not self.trident_data_daemon_config["path_store"]:
            logger.warning("No path was given for stores, will use the working directory")

        if self.trident_data_daemon_config["no_store"] and self.trident_data_daemon_config["global_store"]:
            raise ValueError(f"Can't both use global store and no store options")


class Trident:
    def __init__(self, trident_config: TridentConfig):
        self.trident_config = trident_config
        self.trident_daemon = self._initialize_trident_daemon()

    def _initialize_trident_daemon(self) -> TridentDaemon:
        try:
            trident_daemon_config = TridentDaemonConfig(
                **self.trident_config.trident_daemon_config,
                data_config=self.trident_config.trident_data_daemon_config,
            )
            return TridentDaemon(trident_daemon_config)
        except Exception as e:
            raise e

    def start_trident_daemon(self) -> NoReturn:
        try:
            self.trident_daemon.start_all_runners()
            self.trident_daemon.wait_for_runners()
        except Exception as e:
            raise e

    def shut_down_trident_daemon(self) -> NoReturn:
        try:
            self.trident_daemon.stop_all_runners()
        except Exception as e:
            raise e
