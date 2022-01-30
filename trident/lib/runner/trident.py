#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident: Runner

Runs and controls the execution of a valid plugin.
@author: Jacob Wahlman
"""

from threading import Event
from inspect import signature
from dataclasses import dataclass
from importlib import import_module
import re

from typing import (
    Callable,
    NewType,
    Dict,
    Optional,
    Union,
    List,
    Any,
    NoReturn,
    Generator,
    Tuple,
    AnyStr,
)

Module = NewType("Module", object)
PluginClass = NewType("PluginClass", object)

import logging

logger = logging.getLogger("__main__")

from trident.lib.daemon.data_storage import TridentDataDaemonConfig, TridentDataDaemon
from trident.lib.daemon.notification import (
    TridentNotificationDaemonConfig,
    TridentNotificationDaemon,
)


class _TridentDefaultRunnerConfig:
    """Trident runner configuration class containing common functionality."""

    def _apply_runner_config(self, runner_config: Dict[AnyStr, Any]) -> None:
        """Apply any config parameter passed to this runner config.

        :param runner_config: Config containing the parameters to apply.
        :type runner_config: dict
        """
        if "dont_store_on_error" not in runner_config:
            runner_config["dont_store_on_error"] = False

        if "filter_results" not in runner_config:
            runner_config["filter_results"] = []

        for arg, value in runner_config.items():
            setattr(self, arg, value)

    def _resolve_plugin_name(self) -> AnyStr:
        """Construct the name of the plugin from the plugin path.
        Converts the path to the plugin to the expected name of the class in the plugin module.

        :return: The plugin name.
        :rtype: str
        """
        components = self.plugin_path.split(".")
        component_name = (
            components[0].title() if len(components) == 1 else components[-1].title()
        )
        if "_" in component_name:
            return "".join(component_name.split("_"))

        return component_name

    def _initialize_runner_plugin(
        self, plugin_path: str, plugin_name: str
    ) -> Union[Tuple[PluginClass, Module], None]:
        """Initialize the plugin to be used by the :class:`TridentRunner`.
        Tries to import the module given the path provided and tries to initialize an instance given the plugin name.

        :raises ValueError: If the plugin name is not found in the plugin module.
        :raises Exception: If any unexpected error occured when initializing the plugin.
        :return: The plugin instance and the plugin module if successful otherwise None
        :rtype: (PluginClass, Module)
        """
        try:
            plugin_module, plugin_instance = None, None
            plugin_module = import_module(plugin_path, package=__package__)
            if plugin_name not in dir(plugin_module):
                raise ValueError(
                    f"Failed to find a class named: '{plugin_name}' in module: '{plugin_path}'"
                )
            plugin_instance = getattr(plugin_module, plugin_name)()

            return plugin_instance, plugin_module
        except Exception as e:
            logger.error(
                f"Failed to initialize plugin: '{plugin_path}' with error: {e}"
            )
            raise e

    def _sanitize_parameters(
        self, parameters: Dict[str, Any], method_reference: Callable
    ) -> Dict[str, Any]:
        """Sanitize and filter out any parameters that can't be passed to the given plugin.

        :param parameters: The parameters to be filtered before being passed
        :type parameters: Dict[str, Any]
        :param method_reference: The reference of the method to filter parameters for
        :type method_reference: Callable
        """
        return {
            key: value
            for key, value in parameters.items()
            if key in signature(method_reference).parameters.keys()
        }


@dataclass
class TridentRunnerConfig(_TridentDefaultRunnerConfig):
    """The configuration for the :class:`TridentRunner`.
    Defines the attributes that the runner runs, like plugin instance, module and other info required by the runner.

    :param plugin_path: The path to the plugin used.
    :type plugin_path: str
    :param plugin_name: The name of the plugin used.
    :type plugin_name: Optional[str]
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

    plugin_path: str
    plugin_name: str
    plugin_args: Dict[str, Any]
    plugin_module: object
    plugin_instance: object
    resource_queues: Dict[str, List[str]]
    thread_event: Event

    def __init__(
        self,
        plugin_path: str,
        plugin_name: Optional[str],
        plugin_args: Dict[str, Any],
        store_config: Dict[str, Any],
        checkpoint_config: Dict[str, Any],
        runner_config: Union[Dict[str, Any], None],
        notification_config: Dict[str, Any],
        resource_queues: Dict[str, List[str]],
    ):
        self.plugin_path = plugin_path
        self.plugin_args = plugin_args
        self.store_config = store_config
        self.checkpoint_config = checkpoint_config
        self.notification_config = notification_config
        self.resource_queues = resource_queues

        self.thread_event = Event()

        if runner_config is not None:
            self._apply_runner_config(runner_config)

        self.plugin_name = plugin_name if plugin_name else self._resolve_plugin_name()
        self.plugin_instance, self.plugin_module = self._initialize_runner_plugin(
            self.plugin_path, self.plugin_name
        )


class _TridentDefaultRunner:
    """Trident runner class containing common functionality."""

    def _initialize_data_daemon(self) -> TridentDataDaemon:
        """Initialize the :class:`TridentDataDaemon` connected to this runner from the :class:`TridentDataDaemonConfig`.

        :raises Exception: If any exceptions occur when initializing the :class:`TridentDataDaemon`
        :return: The initialized :class:`TridentDataDaemon`.
        :rtype: :class:`TridentDataDaemon`
        """
        if self.runner_config.store_config.get(
            "no_store"
        ) and self.runner_config.checkpoint_config.get("no_checkpoint"):
            return None

        if self.runner_config.store_config.get(
            "no_store"
        ) is None or not self.runner_config.store_config.get("no_store"):
            if self.runner_config.store_config.get("global_store"):
                store_path = self.runner_config.store_config.get("global_store")
            else:
                store_path = self.runner_config.store_config.get("path_store")
        else:
            store_path = None

        if self.runner_config.checkpoint_config.get(
            "no_checkpoint"
        ) is None or self.runner_config.checkpoint_config.get("no_checkpoint"):
            if self.runner_config.checkpoint_config.get("checkpoint_path"):
                checkpoint_path = self.runner_config.checkpoint_config.get(
                    "checkpoint_path"
                )
            else:
                checkpoint_path = None

        try:
            trident_data_config = TridentDataDaemonConfig(
                runner=self,
                store_path=store_path,
                store_name=self.runner_id,
                checkpoint_path=checkpoint_path,
            )
            return TridentDataDaemon(daemon_config=trident_data_config)
        except Exception as e:
            logger.error(
                f"Failed to initialize data daemon for runner: '{self.runner_id}'"
            )
            raise e

    def _initialize_notification_daemon(self) -> TridentNotificationDaemon:
        """Initialize the :class:`TridentNotificationDaemon` connected to this runner from the :class:`TridentNotificationDaemonConfig`

        :raises Exception: If any exceptions occur when initializing the :class:`TridentNotificationDaemonConfig`
        :return: The initialized :class:`TridentNotificationDaemon`
        :rtype: :class:`TridentNotificationDaemon`
        """
        try:
            trident_notification_config = TridentNotificationDaemonConfig(
                runner=self,
                notifications=self.runner_config.notification_config,
            )
            return TridentNotificationDaemon(daemon_config=trident_notification_config)
        except Exception as e:
            logger.error(
                f"Failed to initialize the notification daemon for runner: '{self.runner_id}'"
            )
            raise e

    def _start_plugin_runner(
        self,
        runner_config: TridentRunnerConfig,
        variables: Optional[Dict[str, Any]] = None,
        variable_key: Optional[str] = None,
    ) -> NoReturn:
        """Start an initialized plugin by calling the method `execute_plugin` with the provided arguments.
        This method is called when the plugin is a normal runner.

        :param runner_config: The trident plugin runner configuration detailing the plugin to use and more
        :type: :class:`TridentRunnerConfig`
        :param variables: Additional variable map for step runners to use in multiple steps, skips store if `None`, defaults to None
        :type variables: Optional[Dict[str, Any]], optional
        :param variable_key: If a specific variable key is needed to store the results for, if `None` it defaults to the index, defaults to None
        :type variable_key: Optional[str], optional
        :raises Exception: Re-raised exceptions that occurs in the plugin.
        """
        if not hasattr(runner_config.plugin_instance, "execute_plugin"):
            raise RuntimeError("Entry method 'execute_plugin' not defined.")

        if hasattr(runner_config.plugin_instance, "plugin_state"):
            if runner_config.plugin_instance.__class__.plugin_state.fset is None:
                logger.warning(
                    f"Checkpoint data: '{self.data_daemon.daemon_config.checkpoint_path}' was found for runner: '{self.runner_id}' but no load state method was defined"
                )
            else:
                _state = self.data_daemon.load_state_checkpoint()
                if _state is None:
                    logger.warning(
                        f"Checkpoint data: '{self.data_daemon.daemon_config.checkpoint_path}' was empty for runner: '{self.runner_id}'"
                    )
                else:
                    self.runner_state = _state

        try:
            _plugins_args = runner_config._sanitize_parameters(
                parameters=runner_config.plugin_args,
                method_reference=runner_config.plugin_instance.execute_plugin,
            )
            # The thread event is used to allow the daemon to stop already started plugins.
            if (
                "thread_event"
                not in signature(
                    runner_config.plugin_instance.execute_plugin
                ).parameters
            ):
                logger.warning(
                    f"Thread event parameter not specified in 'execute_plugin' method for plugin: '{runner_config.plugin_name}' at '{runner_config.plugin_path}'"
                )
                runner_generator = runner_config.plugin_instance.execute_plugin(
                    **_plugins_args
                )
            else:
                runner_generator = runner_config.plugin_instance.execute_plugin(
                    thread_event=runner_config.thread_event,
                    **_plugins_args,
                )

            if runner_generator is not None:
                try:
                    self._evaluate_plugin(
                        runner_generator, variables=variables, variable_key=variable_key
                    )
                except Exception as e:
                    raise e
            else:
                logger.warning(
                    f"No results were returned from the plugin: '{self.runner_id}'"
                )
        except Exception as e:
            logger.error(f"Runner: '{self.runner_id}' encountered error: {e}")
            raise e

    def _evaluate_result(self, result: Any, result_index: int) -> NoReturn:
        """Evaluate the result yielded/returned from the plugin for each iteration.

        :param result: The result returned from the plugin.
        :type result: Any
        :param result_index: The iteration index that the result was returned.
        :type result_index: int
        :raises Exception: If any error occur when storing the result.
        """
        if self.data_daemon is None or self.runner_config.thread_event.is_set():
            return

        if getattr(self.runner_config, "filter_results"):
            for pattern in getattr(self.runner_config, "filter_results"):
                match = re.match(pattern, result)
                if match is not None and match.group(0):
                    logger.debug(
                        f"Result: '{result}' matched pattern: '{pattern}' for runner: '{self.runner_id}'"
                    )
                    break
            else:
                logger.warning(
                    f"Result: '{result}' did not match any pattern(s) for runner: '{self.runner_id}'"
                )
                return

        try:
            if self.data_daemon.store_data is not None:
                self.data_daemon.store_runner_result({result_index: result})
            self.notification_daemon.send_notification(content={result_index: result})
        except Exception as e:
            raise e

    def _evaluate_plugin(
        self,
        generator: Generator[Any, Any, Any],
        variables: Optional[Dict[str, Any]] = None,
        variable_key: Optional[str] = None,
    ) -> NoReturn:
        """Evaluate the initialized plugin generator for each returned value.

        :param generator: The generator yielded from `start_runner`.
        :type generator: Generator
        :param variables: Stores results in an additional variable map for step runners to use in multiple steps, skips store if `None`, defaults to None
        :type variables: Optional[Dict[str, Any]], optional
        :param variable_key: If a specific variable key is needed to store the results for, if `None` it defaults to the index, defaults to None
        :type variable_key: Optional[str], optional
        :raises StopIteration: If generator did not return any more values from the plugin.
        :raises Exception: If any errors occured when trying to access the next value.
        """
        results_index = 0
        while not self.runner_config.thread_event.is_set():
            try:
                _key = variable_key if variable_key is not None else results_index
                try:
                    result = next(generator)
                    if variables is not None:
                        if _key not in variables:
                            variables[_key] = []

                        variables[_key].append(result)
                except TypeError as e:
                    result = generator
                    if variables is not None:
                        variables[_key] = result

                    self._evaluate_result(result, results_index)
                    raise StopIteration
                except Exception as e:
                    if not isinstance(e, StopIteration):
                        logger.error(
                            f"Runner: '{self.runner_id}' encountered a '{type(e).__name__}' with message: '{e}' at run index: '{results_index}'"
                        )

                    raise e

                self._evaluate_result(result, results_index)
                results_index += 1
            except Exception as e:
                if not isinstance(e, StopIteration):
                    if getattr(self.runner_config, "dont_store_on_error"):
                        raise e

                    if self.data_daemon is not None:
                        logger.info(
                            f"Runner: '{self.runner_id}' exited with error, storing results up until error"
                        )

                if self.data_daemon is not None:
                    if (
                        not self.data_daemon.daemon_config.store_path
                        in self.runner_config.resource_queues
                    ):
                        self.runner_config.resource_queues[
                            self.data_daemon.daemon_config.store_path
                        ] = [self.runner_id]
                    else:
                        self.runner_config.resource_queues[
                            self.data_daemon.daemon_config.store_path
                        ].append(self.runner_id)

                if isinstance(e, StopIteration):
                    break

                raise e


class TridentRunner(_TridentDefaultRunner):
    """The :class:`TridentRunner` used to control the execution of each plugin.
    Starts initialized plugins, evaluates results and calls for storage by the :class:`TridentDataDaemon` attached to this runner.

    :param runner_config: The configuration used to define the behavior of this runner.
    :type runner_config: :class:`TridentRunnerConfig`
    :param runner_id: The unique identifier for this runner.
    :type runner_id: str
    """

    def __init__(self, runner_config: TridentRunnerConfig, runner_id: str):
        self.runner_config = runner_config
        self.runner_id = runner_id

        self.data_daemon = self._initialize_data_daemon()
        self.notification_daemon = self._initialize_notification_daemon()
        logger.debug(f"Trident runner: '{self.runner_id}' initialized")

    @property
    def runner_state(self) -> Optional[Dict[Union[str, int], Any]]:
        """Get the current runner state used to restore the runner to a previous run of the plugin.

        :return: The state for the runner if it exists, otherwise `None`
        :rtype: Optional[Dict[Union[str, int], Any]]
        """
        if hasattr(self.runner_config.plugin_instance, "plugin_state"):
            return self.runner_config.plugin_instance.plugin_state

        return None

    @runner_state.setter
    def runner_state(self, state: Dict[Union[str, int], Any]):
        """Set the initial state for a runner based on previous checkpoint data.

        :param state: The state to load in the runner as an initial state
        :type state: Dict[Union[str, int], Any]
        """
        self.runner_config.plugin_instance.plugin_state = state

    def start_runner(self) -> NoReturn:
        """Start the initialized :class:`TridentRunner` by calling the plugin method `execute_plugin` with the provided arguments.
        This method is called when the plugin is a normal runner.

        :raises Exception: Re-raised exceptions that occurs in the plugin.
        """
        logger.info(f"Starting runner: '{self.runner_id}' ...")
        self._start_plugin_runner(self.runner_config)


@dataclass
class TridentStepInstructionConfig(_TridentDefaultRunnerConfig):
    """The configuration for the instruction for each step config."""

    name: str
    ref: str
    type: str
    args: Dict[str, Any]
    out: str

    def __init__(self, name: str, ref: str, type: str, args: Dict[str, Any], out: str):
        self.name = name
        self.ref = ref
        self.type = type
        self.args = args
        self.out = out


@dataclass
class TridentStepConfig:
    """The configuration for the individual step run by the :class:`TridentStepsRunner`
    Defines the attributes that specify the instruction to run for the step.

    :param plugin_name: The plugin identifier that the step belongs to.
    :type plugin_name: str
    :param step_name: The name of the step.
    :type step_name: str
    :param step_instruction: The instruction configuration specifying the instruction to use and type.
    :type step_instruction: :class:`TridentStepInstructionConfig`
    :param method_reference: The reference to the method to call when using a 'method' step
    :type method_reference: Callable
    """

    plugin_name: str
    step_name: str
    step_instruction: TridentStepInstructionConfig
    method_reference: Callable = None

    def __init__(
        self, plugin_name: str, step_name: str, step_instruction: Dict[str, Any]
    ):
        self.plugin_name = plugin_name
        self.step_name = step_name

        self.step_instruction = self._initialize_step_instruction(step_instruction)

        if self.step_instruction.type == "method":
            self.method_reference = self._initialize_step_method(
                method_path=self.step_instruction.ref
            )

    def _initialize_step_instruction(
        self, step_instruction: Dict[str, Any]
    ) -> TridentStepInstructionConfig:
        """Initialize the step instruction config.
        Validates and parses the config, if valid the configuration object is returned.

        :raises ValueError: If the configuration is missing values or is otherwise misconfigured.

        :param step_instruction: The dictionary containing the instruction reference, type, arguments and any potential output variable.
        :type step_instruction: Dict[str, Any]
        :return: The step instruction config object
        :rtype: :class:`TridentStepInstructionConfig`
        """
        if "ref" not in step_instruction or not isinstance(
            step_instruction["ref"], str
        ):
            raise ValueError(
                f"Step instruction: '{self.step_name}' for plugin: '{self.plugin_name}' did not contain necessary 'ref' or was otherwise malformed"
            )

        if "type" not in step_instruction or not isinstance(
            step_instruction["type"], str
        ):
            raise ValueError(
                f"Step instruction: '{self.step_name}' for plugin: '{self.plugin_name}' did not contain necessary 'type' or was otherwise malformed"
            )

        if step_instruction["type"] not in ["plugin", "method"]:
            raise ValueError(
                f"Step instruction: '{self.step_name}' for plugin: '{self.plugin_name}' was not of type 'plugin' or 'method'"
            )

        return TridentStepInstructionConfig(
            name=self.step_name,
            ref=step_instruction["ref"],
            type=step_instruction["type"],
            args=step_instruction["args"] if "args" in step_instruction else {},
            out=step_instruction["out"] if "out" in step_instruction else None,
        )

    def _initialize_step_method(self, method_path: str) -> Union[Callable, None]:
        """Initialize the method to be used by the :class:`TridentStepsRunner`.
        Tries to import the module given the path provided and tries to initialize a reference to the method provided.

        :param method_path: The path to the method to initialize a reference to
        :type method_path: str
        :raises ValueError: If the method name is not found in the module.
        :raises Exception: If any unexpected error occured when importing the method.
        :return: The method reference if successful otherwise None
        :rtype: (PluginClass, Module)
        """
        try:
            _result = method_path.split(".")
            method_module, method_name = ".".join(_result[:-1]), _result[-1]
            method_module = import_module(method_module, package=__package__)
            method_reference = getattr(method_module, method_name)
            return method_reference
        except Exception as e:
            logger.error(
                f"Failed to initialize plugin: '{method_path}' with error: {e}"
            )
            raise e


@dataclass
class TridentStepsRunnerConfig(_TridentDefaultRunnerConfig):
    """The configuration for the :class:`TridentStepsRunner`.
    Defines the attributes that the runner runs, like plugin instructions, module and other info required by the steps runner.

    :param plugin_name: The name of the plugin used.
    :type plugin_name: Optional[str]
    :param plugin_steps: The steps included in the plugin.
    :type plugin_steps: List[:class:`TridentStepConfig`]
    :param plugin_args: The arguments that should be passed to the plugin when executing.
    :type plugin_args: dict
    :param resource_queues: Queue used to register access to a resource shared between runners to avoid conflicts.
    :type resource_queues: dict
    :param dont_store_on_error: If the runner should store the results accumulated before exiting if an error occured.
    :type dont_store_on_error: bool
    :param thread_event: The event flag used to signal to the plugin that it should exit.
    :type thread_event: :class:`threading.Event`
    """

    plugin_name: str
    plugin_args: Dict[str, Any]
    plugin_steps: List[Dict[str, Any]]
    resource_queues: Dict[str, List[str]]
    thread_event: Event

    def __init__(
        self,
        plugin_name: Optional[str],
        plugin_args: Dict[str, Any],
        plugin_steps: List[Dict[str, Any]],
        store_config: Dict[str, Any],
        checkpoint_config: Dict[str, Any],
        runner_config: Dict[str, Any],
        notification_config: Dict[str, Any],
        resource_queues: Dict[str, List[str]],
    ):
        self.plugin_name = plugin_name
        self.plugin_args = plugin_args
        self.store_config = store_config
        self.checkpoint_config = checkpoint_config
        self.notification_config = notification_config
        self.resource_queues = resource_queues

        self.thread_event = Event()
        self._apply_runner_config(runner_config)
        self.plugin_steps = self._initialize_plugin_steps(plugin_steps)

    def _initialize_plugin_steps(
        self, plugin_steps: List[Dict[str, Any]]
    ) -> List[TridentStepConfig]:
        """Initialize each step in a list of steps for plugins.

        :param plugin_steps: The list of step configuration to initialize
        :type plugin_steps: List[Dict[str, Any]]
        :return: The initialized list of step configuration objects
        :rtype: List[:class:`TridentStepConfig`]
        """
        _initialized_steps = []
        for step in plugin_steps:
            if "name" not in step:
                raise ValueError(
                    f"Failed to initialize plugin step configuration for plugin: {self.plugin_name}, missing 'name' keyword"
                )

            if "instruction" not in step:
                raise ValueError(
                    f"Failed to initialize plugin step configuration for plugin: {self.plugin_name}, missing 'instruction' keyword"
                )

            _initialized_steps.append(
                TridentStepConfig(
                    plugin_name=self.plugin_name,
                    step_name=step["name"]
                    if "name" not in step["instruction"]
                    else step["instruction"]["name"],
                    step_instruction=step["instruction"],
                )
            )

        logger.debug(
            f"Initialized ({len(_initialized_steps)}) steps for plugin: {self.plugin_name}"
        )
        return _initialized_steps


class TridentStepsRunner(_TridentDefaultRunner):
    """The :class:`TridentStepsRunner` used to control the execution of each steps plugin.
    Starts initialized steps plugins, evaluates results and calls for storage by the :class:`TridentDataDaemon` attached to this runner.

    :param runner_config: The configuration used to define the behavior of this runner.
    :type runner_config: :class:`TridentStepsRunnerConfig`
    :param runner_id: The unique identifier for this runner.
    :type runner_id: str
    """

    def __init__(self, runner_config: TridentStepsRunnerConfig, runner_id: str):
        self.runner_config = runner_config
        self.runner_id = runner_id
        self.variables = {}

        self.data_daemon = self._initialize_data_daemon()
        self.notification_daemon = self._initialize_notification_daemon()
        logger.debug(f"Trident steps runner: '{self.runner_id}' initialized")

    def _start_method_runner(
        self,
        step: TridentStepConfig,
        variable_key: Optional[str] = None,
    ) -> NoReturn:
        """Start a method by calling the method directly with the provided arguments.
        This method is called as part of a steps runner.

        :param step: The step configuration to execute
        :type: :class:`TridentStepConfig`
        :param variables: Additional variable map for step runners to use in multiple steps, skips store if `None`, defaults to None
        :type variables: Optional[Dict[str, Any]], optional
        :param variable_key: If a specific variable key is needed to store the results for, if `None` it defaults to the index, defaults to None
        :type variable_key: Optional[str], optional
        :raises Exception: Re-raised exceptions that occurs in the plugin.
        """
        if step.method_reference is None:
            raise RuntimeError(
                f"Step method was not properly initialized for step: '{step.step_name}' for runner: '{self.runner_id}'"
            )

        # TODO: Investigate if possible to introduce some sort of checkpoint state loading for steps

        try:
            _method_args = self.runner_config._sanitize_parameters(
                parameters={
                    **self.runner_config.plugin_args,
                    **step.step_instruction.args,
                    **self.variables,
                },
                method_reference=step.method_reference,
            )

            # TODO: Investigate how we can use the thread event parameter for functions
            runner_generator = step.method_reference(**_method_args)

            if runner_generator is not None:
                try:
                    self._evaluate_plugin(
                        runner_generator,
                        variables=self.variables,
                        variable_key=variable_key,
                    )
                except Exception as e:
                    raise e
            else:
                if step.step_instruction.out is not None:
                    logger.warning(
                        f"No results were returned from the method: '{self.runner_id}' and an output was expected: '{step.step_instruction.out}' for step: '{step.step_name}'"
                    )
        except Exception as e:
            logger.error(f"Runner: '{self.runner_id}' encountered error: {e}")
            raise e

    def start_runner(self) -> NoReturn:
        """Execute a step and evaluate the results for that step instruction.

        :param step: The step to execute and evaluate the results for
        :type step: :class:`TridentStepInstructionConfig`
        """
        logger.info(f"Starting steps runner: '{self.runner_id}' ...")
        for step in self.runner_config.plugin_steps:
            logger.info(
                f"Executing step: '{step.step_name}' for plugin: '{step.plugin_name}' and runner: '{self.runner_id}'"
            )
            logger.debug(
                f"Passing variables: '{str(self.variables)}' for step: '{step.step_name}' ('{step.step_instruction.type}') for plugin: '{step.plugin_name}' and runner: '{self.runner_id}'"
            )

            if step.step_instruction.type == "plugin":
                self._start_plugin_runner(
                    runner_config=TridentRunnerConfig(
                        plugin_path=step.step_instruction.ref,
                        plugin_name=step.step_instruction.name
                        if hasattr(step.step_instruction, "name")
                        else self.runner_config._resolve_plugin_name(),
                        plugin_args={**step.step_instruction.args, **self.variables},
                        store_config=self.runner_config.store_config,
                        checkpoint_config=self.runner_config.checkpoint_config,
                        notification_config=self.notification_daemon.daemon_config,
                        resource_queues=self.runner_config.resource_queues,
                        runner_config=None,
                    ),
                    variables=self.variables,
                    variable_key=step.step_instruction.out
                    if hasattr(step.step_instruction, "out")
                    else None,
                )
            elif step.step_instruction.type == "method":
                self._start_method_runner(
                    step=step,
                    variable_key=step.step_instruction.out
                    if hasattr(step.step_instruction, "out")
                    else None,
                )
