#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident: Runner Daemon

Trident daemon that controls all runners and couples itself to it's data storage.
The runners are run in a asynchronous environment controlled by the daemon to allow them to run concurrently.
@author: Jacob Wahlman
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
import concurrent.futures

from typing import List, Dict, Union, NoReturn, NewType
TridentDataDaemonConfig = NewType("TridentDataDaemonConfig", None)

import logging
logger = logging.getLogger("__main__")

from trident.lib.runner.trident import TridentRunnerConfig, TridentRunner


@dataclass
class TridentDaemonConfig:
    """ Config class for the :class:`TridentDaemon` controlling each :class:`TridentRunner`.

    :param workers: The amount of workers that the daemon should use at most.
    :type workers: int
    :param plugins: Dictionary containing the path, optional arguments and descriptors for the plugins.
    :type plugins: dict
    :param data_config: Configuration dictionary for the :class:`TridentDataDaemon`
    :type data_config: dict
    :param dont_store_on_error: Store results if errors occur in runners.
    :type dont_store_on_error: bool
    """
    workers: int
    plugins: Dict[str, str]
    data_config: Dict[str, Union[str, bool]]
    dont_store_on_error: bool


class TridentDaemon:
    """ Main daemon controlling each :class:`TridentRunner` for the program.
    Starts execution of the runners, waits for completion and handles any interrupts to the runners.

    :param daemon_config: The configuration class for the :class:`TridentDaemon`.
    :type daemon_config: :class:`TridentDaemonConfig`
    """
    def __init__(self, daemon_config: TridentDaemonConfig):
        self.daemon_config = daemon_config
        self._runner_resource_queues = {}
        self._future_runners = None
        self.runners = self._initialize_runners()

    def start_all_runners(self) -> NoReturn:
        """ Creates a :class:`concurrent.futures.Future` for each :class:`TridentRunner` and start each runner asynchronously. """
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.daemon_config.workers) as executor:
            self._executor = executor
            self._future_runners = {executor.submit(runner.start_runner): runner for runner in self.runners}

    def wait_for_runners(self) -> NoReturn:
        """ Wait for each runner future to report as completed meaning that each :class:`TridentRunner` has finished.
        Raises exception for each future that encountered an exception while running.

        :raises Exception: The exception raised while the plugin ran in the :class:`TridentRunner`.
        """
        for future in concurrent.futures.as_completed(self._future_runners):
            runner = self._future_runners[future]
            try:
                future.result()
            except Exception as e:
                raise e

            try:
                if runner.runner_id not in self._runner_resource_queues[runner.data_daemon.daemon_config.store_path]:
                    continue
            except (AttributeError, KeyError):
                # Data Daemon not initialized or no store specified
                continue

            if not Path(runner.data_daemon.daemon_config.store_path).exists():
                Path(runner.data_daemon.daemon_config.store_path).touch()
            else:
                runner.data_daemon.merge_store_data()
                
            runner.data_daemon.write_to_store()
            self._runner_resource_queues[runner.data_daemon.daemon_config.store_path].remove(runner.runner_id)

    def stop_all_runners(self) -> NoReturn:
        """ Stop execution for all :class:`TridentRunner`, if it has already started it's execution then it can't be halted
        so a :class:`threading.Event` will be set to signal for the plugin to halt when seen during execution.
        """
        for future, runner in self._future_runners.items():
            logger.debug(f"Sending stop signal to runner: '{runner.runner_id}'")
            runner.runner_config.thread_event.set()
            if not future.cancel():
                logger.warning(f"Runner: '{runner.runner_id}' is in a running state and couldn't be halted immediately")
        
        self._executor.shutdown(wait=False)

    def _initialize_runner(self, runner_config: TridentRunnerConfig, runner_id: str, data_daemon_config: TridentDataDaemonConfig) -> TridentRunner:
        """ Initialize a runner given the config :class:`TridentRunnerConfig`, runner identifier and the data config :class:`TridentDataDaemonConfig`.
        The runner :class:`TridentRunner` controls the execution and handling for each plugin.

        :param runner_config: The config for :class:`TridentRunnerConfig` used to initialize the class.
        :type runner_config: TridentRunnerConfig
        :param runner_id: The unique indentifier for each :class:`TridentRunner`.
        :type runner_id: str
        :param data_daemon_config: The data daemon config used by each :class:`TridentRunner` to control it's data daemon :class:`TridentDataDaemon`.
        :type data_daemon_config: TridentDataDaemonConfig
        :raises Exception: If any issues occurs whilst initializing the :class:`TridentRunner`.
        :return: The :class:`TridentRunner` instance created from the config :class:`TridentRunnerConfig`.
        :rtype: TridentRunner
        """
        logger.info(f"Initializing plugin: '{runner_config.plugin_path}'")
        try:
            return TridentRunner(runner_config, runner_id, data_daemon_config)
        except Exception as e:
            raise e

    def _initialize_runners(self) -> List[TridentRunner]:
        """ Initialize the :class:`TridentRunner` for each plugin given by the :class:`TridentDaemonConfig`.

        :raises ValueError: If the plugin does not exist from the path provided.
        :raises Exception: If any other issue initializing the :class:`TridentRunner` occurs.
        :return: A list of the :class:`TridentRunner` objects representing each plugin.
        :rtype: list
        """
        _initialized_runners = []
        for plugin_id, plugin_config in self.daemon_config.plugins.items():
            if "path" not in plugin_config:
                raise ValueError(f"Missing path to plugin for plugin: '{plugin_id}' in config.")
            else:
                plugin_path = plugin_config["path"]

            if "args" not in plugin_config:
                logger.debug(f"No arguments specified for plugin: '{plugin_id}'")
                plugin_args = {}
            else:
                plugin_args = plugin_config["args"]

            try:
                runner = self._initialize_runner(
                    runner_config=TridentRunnerConfig(
                        plugin_path=plugin_path,
                        plugin_args=plugin_args,
                        resource_queues=self._runner_resource_queues,
                        dont_store_on_error=self.daemon_config.dont_store_on_error
                    ),
                    runner_id=plugin_id,
                    data_daemon_config=self.daemon_config.data_config
                )
                
                _initialized_runners.append(runner)
            except Exception as e:
                logger.error(f"Failed to initialize a trident runner for plugin: '{plugin_id}' due to previous error: {e}")
                raise e

        logger.info(f"Initialized ({len(_initialized_runners)}) out of ({len(self.daemon_config.plugins)}) plugins")
        return _initialized_runners
