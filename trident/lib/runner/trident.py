#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident: Runner
Runs and controls the execution of a valid plugin.
@author: Jacob Wahlman
"""

import logging
logger = logging.getLogger("__main__")

from pathlib import Path
from threading import Event
from inspect import signature
from dataclasses import dataclass
from importlib import import_module
from typing import NewType, Dict, Union, List, Any

from trident.lib.daemon.data_storage import TridentDataDaemonConfig, TridentDataDaemon

Module = NewType("Module", object)
PluginClass = NewType("PluginClass", object)


@dataclass
class TridentRunnerConfig:
    plugin_path: str
    plugin_name: str
    plugin_args: Dict[str, Any]
    plugin_module: object
    plugin_instance: object
    resource_queues: Dict[str, List[str]]
    dont_store_on_error: bool
    thread_event: Event

    def __init__(self, plugin_path, plugin_args, resource_queues, dont_store_on_error):
        self.plugin_path = plugin_path
        self.plugin_args = plugin_args
        self.resource_queues = resource_queues
        self.dont_store_on_error = dont_store_on_error
        self.thread_event = Event()
        self.plugin_name = self._resolve_plugin_name()
        self.plugin_instance, self.plugin_module = self._initialize_runner_config()

    def _resolve_plugin_name(self) -> str:
        components = self.plugin_path.split(".")
        component_name = components[0].title() if len(components) == 1 else components[-1].title()
        if "_" in component_name:
            return "".join(component_name.split("_"))
        return component_name

    def _initialize_runner_config(self) -> (PluginClass, Module):
        try:
            plugin_module, plugin_instance = None, None
            plugin_module = import_module(self.plugin_path, package=__package__)
            if self.plugin_name not in dir(plugin_module):
                raise ValueError(f"Failed to find a class named: '{self.plugin_name}' in module: '{self.plugin_path}'")
            plugin_instance = getattr(plugin_module, self.plugin_name)()

            return plugin_instance, plugin_module
        except Exception as e:
            logger.error(f"Failed to initialize plugin: {self.plugin_path} with error: {e}")
            raise e


class TridentRunner:
    def __init__(self, runner_config, runner_id, data_daemon_config):
        self.runner_config = runner_config
        self.runner_id = runner_id

        self.data_daemon_config = data_daemon_config
        self.data_daemon = self._initialize_data_daemon()

    def start_runner(self) -> None:
        logger.info(f"Starting runner: {self.runner_id} ...")
        try:
            # The thread event is used to allow the daemon to stop already started plugins.
            if "thread_event" not in signature(self.runner_config.plugin_instance.execute_plugin).parameters:
                logger.warning(f"Thread event parameter not specified in 'execute_plugin' method for plugin: '{self.runner_config.plugin_name}' at '{self.runner_config.plugin_path}'")
                runner_generator = self.runner_config.plugin_instance.execute_plugin(**self.runner_config.plugin_args)
            else:
                runner_generator = self.runner_config.plugin_instance.execute_plugin(thread_event=self.runner_config.thread_event, **self.runner_config.plugin_args)

        except Exception as e:
            logger.error(f"Runner: '{self.runner_id}' encountered error: {e}")
            raise e

        if runner_generator is not None:
            try:
                self._evaluate_plugin(runner_generator)
            except Exception as e:
                raise e
        else:
            logger.warning(f"No results were returned from the plugin: '{self.runner_id}'")

    def _initialize_data_daemon(self) -> TridentDataDaemon:
        if self.data_daemon_config["no_store"]:
            return None

        if self.data_daemon_config["global_store"]:
            store_path = f"{self.data_daemon_config['path_store']}/{self.data_daemon_config['global_store']}"
        else:
            store_path = self.data_daemon_config["path_store"]

        try:
            trident_data_config = TridentDataDaemonConfig(
                runner=self,
                store_path=store_path,
                store_name=self.runner_id
            )
            return TridentDataDaemon(trident_data_config)
        except Exception as e:
            logger.error(f"Failed to initialize data daemon for runner: {self.runner_id}")
            raise e

    def _evaluate_result(self, result, result_index) -> None:
        if self.data_daemon is None or self.runner_config.thread_event.is_set():
            return

        try:
            self.data_daemon.store_runner_result({result_index: result})
        except Exception as e:
            raise e

    def _evaluate_plugin(self, generator) -> None:
        results_index = 0
        while not self.runner_config.thread_event.is_set():
            try:
                try:
                    result = next(generator)
                except TypeError:
                    result = generator
                    self._evaluate_result(result, results_index)
                    raise StopIteration
                except Exception as e:
                    if not isinstance(e, StopIteration):
                        logger.error(f"Runner: '{self.runner_id}' encountered a '{type(e).__name__}' with message: '{e}' at run index: '{results_index}'")

                    raise e

                self._evaluate_result(result, results_index)
                results_index += 1
            except Exception as e:
                if not isinstance(e, StopIteration):
                    if self.runner_config.dont_store_on_error:
                        raise e

                    if self.data_daemon is not None:
                        logger.info(f"Runner: '{self.runner_id}' exited with error, storing results up until error")

                if self.data_daemon is not None:
                    if not self.data_daemon.daemon_config.store_path in self.runner_config.resource_queues:
                        self.runner_config.resource_queues[self.data_daemon.daemon_config.store_path] = [self.runner_id]
                    else:
                        self.runner_config.resource_queues[self.data_daemon.daemon_config.store_path].append(self.runner_id)
                break