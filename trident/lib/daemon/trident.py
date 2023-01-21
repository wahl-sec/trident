#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident: Runner Daemon

Trident daemon that controls all runners and couples itself to it's data storage.
The runners are run in a asynchronous environment controlled by the daemon to allow them to run concurrently.
@author: Jacob Wahlman
"""

from dataclasses import dataclass
from pathlib import Path
import concurrent.futures

from typing import List, Dict, NoReturn, NewType, AnyStr, Optional

TridentDataDaemonConfig = NewType("TridentDataDaemonConfig", None)

import logging

logger = logging.getLogger("__main__")

from trident.lib.interface.trident import (
    TridentInterface,
    TridentInterfaceConfig,
    TridentInterfaceReceiverConfig,
    TridentInterfaceSenderConfig,
    TridentReceiver,
    TridentSender,
)
from trident.lib.runner.trident import (
    TridentRunnerConfig,
    TridentRunner,
    TridentStepsRunner,
    TridentStepsRunnerConfig,
    _TridentDefaultRunnerConfig,
)


@dataclass
class TridentDaemonConfig:
    """Config class for :class:`TridentDaemon` controlling each :class:`TridentRunner`.

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
    interface: Dict[str, str]


class TridentDaemon:
    """Main daemon controlling each :class:`TridentRunner` for the program.
    Starts execution of the runners, waits for completion and handles any interrupts to the runners.

    :param daemon_config: The configuration class for the :class:`TridentDaemon`.
    :type daemon_config: :class:`TridentDaemonConfig`
    """

    def __init__(self, daemon_config: TridentDaemonConfig):
        self.daemon_config = daemon_config
        self._runner_resource_queues = {}
        self._future_runners = None
        self.runners = self._initialize_runners()
        self.interface = self._initialize_interface()

    def start_all_runners(self) -> NoReturn:
        """Creates a :class:`concurrent.futures.Future` for each :class:`TridentRunner` and start each runner asynchronously."""
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.daemon_config.workers
        ) as executor:
            self._executor = executor
            self._future_runners = {
                executor.submit(runner.start_runner): runner for runner in self.runners
            }

            self.wait_for_runners()

    def wait_for_runners(self) -> NoReturn:
        """Wait for each runner future to report as completed meaning that each :class:`TridentRunner` has finished.
        Raises exception for each future that encountered an exception while running.

        :raises Exception: The exception raised while the plugin ran in the :class:`TridentRunner`.
        """
        for future in concurrent.futures.as_completed(self._future_runners):
            runner = self._future_runners[future]
            try:
                future.result()
            except Exception as e:
                raise e

            logger.info(
                f"Runner: '{runner.runner_id}' finished execution for plugin: '{runner.runner_config.plugin_name}'"
            )

            try:
                if (
                    runner.runner_id
                    not in self._runner_resource_queues[
                        runner.data_daemon.daemon_config.store_path
                    ]
                ):
                    continue
            except (AttributeError, KeyError):
                # Data Daemon not initialized or no store specified
                continue

            if runner.data_daemon.daemon_config.store_path:
                if not Path(runner.data_daemon.daemon_config.store_path).exists():
                    Path(runner.data_daemon.daemon_config.store_path).touch()
                else:
                    runner.data_daemon.merge_store_data()

                logger.info(
                    f"Writing output from plugin '{runner.runner_config.plugin_name}' for runner: '{runner.runner_id}' at: '{runner.data_daemon.daemon_config.store_path}'"
                )
                runner.data_daemon.write_to_store()

            self._runner_resource_queues[
                runner.data_daemon.daemon_config.store_path
            ].remove(runner.runner_id)

    def stop_all_runners(self) -> NoReturn:
        """Stop execution for all :class:`TridentRunner`, if it has already started it's execution then it can't be halted
        so a :class:`threading.Event` will be set to signal for the plugin to halt when seen during execution.
        """
        for future, runner in self._future_runners.items():
            logger.debug(f"Sending stop signal to runner: '{runner.runner_id}'")
            runner.runner_config.thread_event.set()
            if not future.cancel():
                logger.warning(
                    f"Runner: '{runner.runner_id}' is in a running state and couldn't be halted immediately"
                )

            if runner.data_daemon.store_data is not None:
                logger.info(
                    f"Saving current data store to disk for runner: '{runner.runner_id}' at: '{runner.data_daemon.daemon_config.store_path}'"
                )
                if not Path(runner.data_daemon.daemon_config.store_path).exists():
                    Path(runner.data_daemon.daemon_config.store_path).touch()
                else:
                    runner.data_daemon.merge_store_data()

                runner.data_daemon.write_to_store()

            if isinstance(runner, TridentRunner) and hasattr(
                runner.runner_config.plugin_instance, "plugin_state"
            ):
                logger.info(
                    f"Saving current progress for runner: '{runner.runner_id}' in a checkpoint at: {runner.data_daemon.daemon_config.checkpoint_path}'"
                )
                Path(runner.data_daemon.daemon_config.checkpoint_path).touch(
                    exist_ok=True
                )
                runner.data_daemon.create_state_checkpoint()

        self._executor.shutdown(wait=False)

    def start_listen_interface(self) -> None:
        """Start the :class:`TridentInterface` to open up for receiving messages to other
        :class:`TridentDaemon` instances.
        """
        self.interface.listen()

    def _initialize_interface(self) -> TridentInterface:
        """Initialize the :class:`TridentInterface` for :class:`TridentDaemon`.

        :raises ValueError: If the interface cannot be initialized.
        :raises Exception: If any other issue initializing the :class:`TridentInterface` occurs.
        :return: The initialized :class:`TridentInterface`
        :rtype: :class:`TridentInterface`
        """
        # Initialize the listener config
        _receiver: Optional[TridentReceiver] = None
        if self.daemon_config.interface.get("receiver"):
            _receiver_config = TridentInterfaceReceiverConfig(
                port=self.daemon_config.interface["receiver"]["port"]
            )
            _receiver = TridentReceiver(receiver_config=_receiver_config)

        # Initialize the sender config
        _senders: List[TridentSender] = []
        if self.daemon_config.interface.get("sender"):
            for _sender in self.daemon_config.interface.get("sender"):
                _sender_config = TridentInterfaceSenderConfig(
                    ip=_sender["ip"], port=_sender["port"]
                )
                _senders.append(TridentSender(sender_config=_sender_config))

        return TridentInterface(
            TridentInterfaceConfig(senders=_senders, receiver=_receiver)
        )

    def _initialize_runner(
        self, runner_config: _TridentDefaultRunnerConfig, runner_id: AnyStr
    ) -> TridentRunner:
        """Initialize a runner given the config :class:`TridentRunnerConfig`, runner identifier and the data config :class:`TridentDataDaemonConfig`.
        The runner :class:`TridentRunner` controls the execution and handling for each plugin.

        :param runner_config: The config for :class:`TridentRunnerConfig` or :class:`TridentStepsRunnerConfig` used to initialize the class.
        :type runner_config: _TridentDefaultRunnerConfig
        :param runner_id: The unique indentifier for each :class:`TridentRunner`.
        :type runner_id: str
        :raises Exception: If any issues occurs whilst initializing the :class:`TridentRunner`.
        :return: The :class:`TridentRunner` instance created from the config :class:`TridentRunnerConfig` or :class:`TridentStepsRunnerConfig`.
        :rtype: :class:`TridentRunner`
        """
        logger.info(f"Initializing runner for plugin: '{runner_config.plugin_name}'")
        try:
            if isinstance(runner_config, TridentRunnerConfig):
                return TridentRunner(runner_config, runner_id)
            elif isinstance(runner_config, TridentStepsRunnerConfig):
                return TridentStepsRunner(runner_config, runner_id)

        except Exception as e:
            raise e

    def _initialize_runners(self) -> List[TridentRunner]:
        """Initialize the :class:`TridentRunner` for each plugin given by the :class:`TridentDaemonConfig`.

        :raises ValueError: If the plugin does not exist from the path provided.
        :raises Exception: If any other issue initializing the :class:`TridentRunner` occurs.
        :return: A list of the :class:`TridentRunner` objects representing each plugin.
        :rtype: List[:class:`TridentRunner`]
        """
        _initialized_runners = []
        for plugin_id, plugin_config in self.daemon_config.plugins.items():
            if "disabled" in plugin_config and plugin_config["disabled"]:
                continue

            if "path" in plugin_config:
                plugin_name = plugin_config["name"] if "name" in plugin_config else None

                if "plugin_args" not in plugin_config:
                    logger.debug(f"No arguments specified for plugin: '{plugin_id}'")
                    plugin_args = {}
                else:
                    plugin_args = plugin_config["plugin_args"]

                try:
                    runner = self._initialize_runner(
                        runner_config=TridentRunnerConfig(
                            plugin_path=plugin_config["path"],
                            plugin_name=plugin_name,
                            plugin_args=plugin_args,
                            store_config=plugin_config["args"]["store"],
                            checkpoint_config=plugin_config["args"]["checkpoint"],
                            runner_config=plugin_config["args"]["runner"],
                            notification_config=plugin_config["args"]["notification"],
                            resource_queues=self._runner_resource_queues,
                        ),
                        runner_id=plugin_id,
                    )

                    _initialized_runners.append(runner)
                except Exception as e:
                    logger.error(
                        f"Failed to initialize a trident runner for plugin: '{plugin_id}' due to previous error: {e}"
                    )
                    raise e
            elif "steps" in plugin_config:
                plugin_name = plugin_config["name"] if plugin_config["name"] else None

                if "plugin_args" not in plugin_config:
                    logger.debug(f"No arguments specified for plugin: '{plugin_id}'")
                    plugin_args = {}
                else:
                    plugin_args = plugin_config["plugin_args"]

                try:
                    runner = self._initialize_runner(
                        runner_config=TridentStepsRunnerConfig(
                            plugin_name=plugin_name,
                            plugin_args=plugin_args,
                            plugin_steps=plugin_config["steps"],
                            store_config=plugin_config["args"]["store"],
                            checkpoint_config=plugin_config["args"]["checkpoint"],
                            runner_config=plugin_config["args"]["runner"],
                            notification_config=plugin_config["args"]["notification"],
                            resource_queues=self._runner_resource_queues,
                        ),
                        runner_id=plugin_id,
                    )

                    _initialized_runners.append(runner)
                except Exception as e:
                    logger.error(
                        f"Failed to initialize a trident steps runner for plugin: '{plugin_id}' due to previous error: {e}"
                    )
                    raise e
            else:
                raise ValueError(
                    f"Failed to initialize plugin: '{plugin_id}' due to missing the 'path' or 'steps' keyword"
                )

            logger.info(
                f"Initialized ({len(_initialized_runners)}) out of ({len(self.daemon_config.plugins)}) plugins"
            )
        return _initialized_runners
