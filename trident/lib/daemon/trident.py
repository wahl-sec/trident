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
    workers: int
    plugins: Dict[str, str]
    data_config: Dict[str, Union[str, bool]]
    dont_store_on_error: bool


class TridentDaemon:
    def __init__(self, daemon_config: TridentDaemonConfig):
        self.daemon_config = daemon_config
        self._runner_resource_queues = {}
        self._future_runners = None
        self.runners = self._initialize_runners()

    def start_all_runners(self) -> NoReturn:
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.daemon_config.workers) as executor:
            self._executor = executor
            self._future_runners = {executor.submit(runner.start_runner): runner for runner in self.runners}

    def wait_for_runners(self) -> NoReturn:
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

            runner.data_daemon.merge_store_data()
            runner.data_daemon.write_to_store()
            self._runner_resource_queues[runner.data_daemon.daemon_config.store_path].remove(runner.runner_id)

    def stop_all_runners(self) -> NoReturn:
        for future, runner in self._future_runners.items():
            logger.debug(f"Sending stop signal to runner: '{runner.runner_id}'")
            runner.runner_config.thread_event.set()
            if not future.cancel():
                logger.warning(f"Runner: '{runner.runner_id}' is in a running state and couldn't be halted immediately")
        
        self._executor.shutdown(wait=False)

    def _initialize_runner(self, runner_config: TridentRunnerConfig, runner_id: str, data_daemon_config: TridentDataDaemonConfig) -> TridentRunner:
        logger.info(f"Initializing plugin: '{runner_config.plugin_path}'")
        try:
            return TridentRunner(runner_config, runner_id, data_daemon_config)
        except Exception as e:
            raise e

    def _initialize_runners(self) -> List[TridentRunner]:
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
                logger.error(f"Failed to initialize a trident runner for plugin: '{plugin}' due to previous error: {e}")
                raise e

        logger.info(f"Initialized ({len(_initialized_runners)}) out of ({len(self.daemon_config.plugins)}) plugins")
        return _initialized_runners
