#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident: Runner

Runs and controls the execution of a valid plugin.
@author: Jacob Wahlman
"""

from pathlib import Path
from threading import Event
from inspect import signature
from dataclasses import dataclass
from importlib import import_module

from typing import NewType, Dict, Union, List, Any, NoReturn, Generator, Tuple, AnyStr
Module = NewType("Module", object)
PluginClass = NewType("PluginClass", object)

import logging
logger = logging.getLogger("__main__")

from trident.lib.daemon.data_storage import TridentDataDaemonConfig, TridentDataDaemon


@dataclass
class TridentRunnerConfig:
    """ The configuration for the :class:`TridentRunner`.
    Defines the attributes that the runner runs, like plugin instance, module and other info required by the runner.

    :param plugin_path: The path to the plugin used.
    :type plugin_path: str
    :param plugin_name: The name of the plugin used.
    :type plugin_name: str
    :param plugin_args: The arguments that should be passed to the plugin when executing.
    :type plugin_args: dict
    :param plugin_module: The module object given by `import_module` from the `importlib` library.
    :type plugin_module: object
    :param plugin_instance: An instance of the plugin class found in the module.
    :type plugin_instance: object
    :param resource_queues: Queue used to register access to a resource shared between runners to avoid conflicts.
    :type resource_queues: dict
    :param dont_store_on_error: If the runner should store the results accumulated before exiting if an error occured.
    :type dont_store_on_error: bool
    :param thread_event: The event flag used to signal to the plugin that it should exit.
    :type thread_event: :class:`threading.Event`
    """
    plugin_path: AnyStr
    plugin_name: AnyStr
    plugin_args: Dict[AnyStr, Any]
    plugin_module: object
    plugin_instance: object
    resource_queues: Dict[AnyStr, List[AnyStr]]
    thread_event: Event

    def __init__(self, plugin_path: AnyStr, plugin_args: Dict[AnyStr, Any], store_config: Dict[AnyStr, Any], runner_config: Dict[AnyStr, Any], resource_queues: Dict[AnyStr, List[AnyStr]]):
        self.plugin_path = plugin_path
        self.plugin_args = plugin_args
        self.store_config = store_config
        self.resource_queues = resource_queues

        self.thread_event = Event()
        self._apply_runner_config(runner_config)
        self.plugin_name = self._resolve_plugin_name()
        self.plugin_instance, self.plugin_module = self._initialize_runner_plugin()

    def _apply_runner_config(self, runner_config: Dict[AnyStr, Any]) -> None:
        """ Apply any config parameter passed to this runner config.

        :param runner_config: Config containing the parameters to apply.
        :type runner_config: dict
        """
        for arg, value in runner_config.items():
            setattr(self, arg, value)

    def _resolve_plugin_name(self) -> AnyStr:
        """ Construct the name of the plugin from the plugin path.
        Converts the path to the plugin to the expected name of the class in the plugin module.

        :return: The plugin name.
        :rtype: str
        """
        components = self.plugin_path.split(".")
        component_name = components[0].title() if len(components) == 1 else components[-1].title()
        if "_" in component_name:
            return "".join(component_name.split("_"))

        return component_name

    def _initialize_runner_plugin(self) -> Union[Tuple[PluginClass, Module], None]:
        """ Initialize the plugin to be used by the :class:`TridentRunner`.
        Tries to import the module given the path provided and tries to initialize an instance given the plugin name.

        :raises ValueError: If the plugin name is not found in the plugin module.
        :raises Exception: If any unexpected error occured when initializing the plugin. 
        :return: The plugin instance and the plugin module if successful otherwise None
        :rtype: (PluginClass, Module)
        """
        try:
            plugin_module, plugin_instance = None, None
            plugin_module = import_module(self.plugin_path, package=__package__)
            if self.plugin_name not in dir(plugin_module):
                raise ValueError(f"Failed to find a class named: '{self.plugin_name}' in module: '{self.plugin_path}'")
            plugin_instance = getattr(plugin_module, self.plugin_name)()

            return plugin_instance, plugin_module
        except Exception as e:
            logger.error(f"Failed to initialize plugin: '{self.plugin_path}' with error: {e}")
            raise e


class TridentRunner:
    """ The :class:`TridentRunner` used to control the execution of each plugin.
    Starts initialized plugins, evaluates results and calls for storage by the :class:`TridentDataDaemon` attached to this runner.

    :param runner_config: The configuration used to define the behavior of this runner.
    :type runner_config: :class:`TridentRunnerConfig`
    :param runner_id: The unique identifier for this runner.
    :type runner_id: str
    """
    def __init__(self, runner_config: TridentRunnerConfig, runner_id: AnyStr):
        self.runner_config = runner_config
        self.runner_id = runner_id

        self.data_daemon = self._initialize_data_daemon()

    def start_runner(self) -> NoReturn:
        """ Start the initialized :class:`TridentRunner` by calling the plugin method `execute_plugin` with the provided arguments.

        :raises Exception: Re-raised exceptions that occurs in the plugin.
        """
        logger.info(f"Starting runner: '{self.runner_id}' ...")
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
        """ Initialize the :class:`TridentDataDaemon` connected to this runner from the :class:`TridentDataDaemonConfig`.

        :raises Exception: If any exceptions occur when initializing the :class:`TridentDataDaemon`
        :return: The initialized :class:`TridentDataDaemon`.
        :rtype: :class:`TridentDataDaemon`
        """
        if self.runner_config.store_config.get("no_store"):
            return None

        if self.runner_config.store_config.get("global_store"):
            store_path = self.runner_config.store_config.get("global_store")
        else:
            store_path = self.runner_config.store_config.get("path_store")

        try:
            trident_data_config = TridentDataDaemonConfig(
                runner=self,
                store_path=store_path,
                store_name=self.runner_id
            )
            return TridentDataDaemon(daemon_config=trident_data_config)
        except Exception as e:
            logger.error(f"Failed to initialize data daemon for runner: '{self.runner_id}'")
            raise e

    def _evaluate_result(self, result: Any, result_index: int) -> NoReturn:
        """ Evaluate the result yielded/returned from the plugin for each iteration.

        :param result: The result returned from the plugin.
        :type result: Any
        :param result_index: The iteration index that the result was returned.
        :type result_index: int
        :raises Exception: If any error occur when storing the result.
        """
        if self.data_daemon is None or self.runner_config.thread_event.is_set():
            return

        try:
            self.data_daemon.store_runner_result({result_index: result})
        except Exception as e:
            raise e

    def _evaluate_plugin(self, generator: Generator[Any, Any, Any]) -> NoReturn:
        """ Evaluate the initialized plugin generator for each returned value.
        
        :param generator: The generator yielded from `start_runner`.
        :type generator: Generator
        :raises StopIteration: If generator did not return any more values from the plugin.
        :raises Exception: If any errors occured when trying to access the next value. 
        """
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
                    if self.runner_config.get("dont_store_on_error"):
                        raise e

                    if self.data_daemon is not None:
                        logger.info(f"Runner: '{self.runner_id}' exited with error, storing results up until error")

                if self.data_daemon is not None:
                    if not self.data_daemon.daemon_config.store_path in self.runner_config.resource_queues:
                        self.runner_config.resource_queues[self.data_daemon.daemon_config.store_path] = [self.runner_id]
                    else:
                        self.runner_config.resource_queues[self.data_daemon.daemon_config.store_path].append(self.runner_id)
                break
