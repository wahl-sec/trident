#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident: Main Module.

@author: Jacob Wahlman
"""

from dataclasses import dataclass

from typing import Dict, Union, NoReturn

import logging

logger = logging.getLogger("__main__")

from trident.lib.daemon.trident import TridentDaemonConfig, TridentDaemon


@dataclass
class TridentConfig:
    """The config for the :class:`TridentDaemon`.

    :param kwargs: The config values given by the configuration file and the arguments.
    :type kwargs: dict
    """

    trident_config: Dict[str, str]
    trident_daemon_config: Dict[str, Union[str, int]]

    def __init__(self, kwargs: Dict[str, str]):
        self.trident_config = {
            "logging_level": kwargs["args"]["daemon"].get("logging_level"),
            "verbose": kwargs["args"]["daemon"].get("verbose"),
            "quiet": kwargs["args"]["daemon"].get("quiet"),
        }

        self.trident_daemon_config = {
            "plugins": kwargs.get("plugins"),
            "workers": kwargs["args"]["daemon"].get("workers"),
        }

        self._verify_trident_config()
        self._verify_trident_daemon_config()

    def _verify_trident_config(self) -> NoReturn:
        """Verify the validity of the configuration for logging and other optional argument.

        :raises ValueError: If the configuration is not valid.
        """
        if self.trident_config["verbose"] and self.trident_config["quiet"]:
            raise ValueError("Can't both use verbose logging and quiet logging.")

        if self.trident_config["logging_level"] and self.trident_config["quiet"]:
            logger.warning(
                f"Logging level: '{self.trident_config['logging_level']}' was overriden by quiet flag"
            )

        if self.trident_config["logging_level"] and self.trident_config["verbose"]:
            logger.warning(
                f"Logging level: '{self.trident_config['logging_level']}' was overriden by verbose flag"
            )

    def _verify_trident_daemon_config(self) -> NoReturn:
        """Verify the validity of the :class:`TridentDaemonConfig`.

        :raises ValueError: If the configuration is not valid.
        """
        try:
            int(self.trident_daemon_config["workers"])
        except ValueError:
            raise ValueError(f"Value of workers is not a valid positive integer")

        if int(self.trident_daemon_config["workers"]) <= 0:
            raise ValueError(
                f"Invalid amount of workers specified: '{self.trident_daemon_config['workers']}', value must be greater than 0"
            )

        if not self.trident_daemon_config["plugins"]:
            logger.warning("No plugins was specified")


class Trident:
    """The main Trident controller handling the :class:`TridentDaemon`.

    :param trident_config: The configuration for the Trident program.
    :type trident_config: :class:`TridentConfig`
    """

    def __init__(self, trident_config: TridentConfig):
        self.trident_config = trident_config
        self.trident_daemon = self._initialize_trident_daemon()

    def _initialize_trident_daemon(self) -> TridentDaemon:
        """Initialize the :class:`TridentDaemon` from the given configuration.

        :raises Exception: If an error occured when initializing the :class:`TridentDaemon`
        :return: The daemon if initialized.
        :rtype: :class:`TridentDaemon`
        """
        try:
            trident_daemon_config = TridentDaemonConfig(
                **self.trident_config.trident_daemon_config
            )
            return TridentDaemon(trident_daemon_config)
        except Exception as e:
            raise e

    def start_trident_daemon(self) -> NoReturn:
        """Start the :class:`TridentDaemon` by starting each :class:`TridentRunner` and wait for them to end.

        :raises Exception: If any error occurs when starting/waiting for the runners.
        """
        try:
            self.trident_daemon.start_all_runners()
        except Exception as e:
            raise e

    def shut_down_trident_daemon(self) -> NoReturn:
        """Signals all runners to stop execution.

        :raises Exception: If an error occurs when stopping the runners.
        """
        try:
            self.trident_daemon.stop_all_runners()
        except Exception as e:
            raise e
