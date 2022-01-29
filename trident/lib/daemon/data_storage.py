#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident: Data Storage

Trident daemon handling the data collected by all runners under a Trident daemon.
@author: Jacob Wahlman
"""

import json
from os import path
from pathlib import Path
from dataclasses import dataclass

from typing import Dict, NewType, Any, NoReturn, AnyStr, Optional, Union

TridentRunner = NewType("TridentRunner", None)

import logging

logger = logging.getLogger("__main__")


@dataclass
class TridentDataDaemonConfig:
    """Config class for :class:`TridentDataDaemon` controlling the data handling for each :class:`TridentRunner`.

    :param runner: Reference to the runner belonging to this daemon :class:`TridentRunner`
    :type runner: class:`TridentRunner`
    :param store_path: Given path to the store location on disk.
    :type store_path: str
    :param store_name: Name of the store on the disk if the store path does not include file, default behavior is using the id of the runner :class:`TridentRunner`.
    :type store_name: str
    """

    runner: TridentRunner
    store_path: Path
    store_name: str
    checkpoint_path: Optional[Path]

    def __init__(
        self,
        runner: TridentRunner,
        store_name: str,
        store_path: str,
        checkpoint_path: Optional[str] = None,
    ):
        self.runner = runner
        self.store_name = store_name

        if store_path is not None:
            self.store_path = self._determine_store_path(store_path)
        else:
            self.store_path = None

        if checkpoint_path is not None or self.store_path:
            self.checkpoint_path = self._determine_checkpoint_path(
                checkpoint_path, store_path
            )
        else:
            self.checkpoint_path = None

    def _determine_store_path(self, store_path: str) -> Path:
        """Verifies that the store path is a valid path that exists and is normalizable, returns the normalized path if valid.
        Raises `FileNotFoundError` if the normalized store path does not exist.

        :param store_path: The store path to verify and normalize.
        :type store_path: str
        :raises FileNotFoundError: The store path does not exist on the system.
        :return: The :class:`pathlib.Path` object of the store on the system.
        :rtype: :class:`pathlib.Path`
        """
        store_path_n = self._normalize_store_path(store_path)
        if store_path_n.is_file():
            logger.debug(
                f"Using existing store path: '{store_path_n}' for runner: '{self.runner.runner_id}'"
            )
            return store_path_n
        elif store_path_n.is_dir() or store_path_n.exists():
            logger.debug(
                f"Creating store in path: '{store_path_n}' for runner: '{self.runner.runner_id}'"
            )
            if store_path_n.suffix == ".json":
                return store_path_n

            return self._normalize_store_path(f"{store_path}/{self.store_name}.json")
        else:
            raise FileNotFoundError(
                f"Store path: '{store_path_n}' does not exist for runner: '{self.runner.runner_id}'"
            )

    def _determine_checkpoint_path(
        self, checkpoint_path: Union[str, None], store_path: str
    ) -> Path:
        """Returns the path to where the checkpoint for the runner should be stored if it was enabled
        By default it will place next to the store path named as `[RUNNER_ID]_CHECKPOINT.json`

        :param checkpoint_path: The checkpoint path if provided
        :type checkpoint_path: Union[str, None]
        :param store_path: The store path to base the checkpoint path on.
        :type store_path: str
        :return: The :class:`pathlib.Path` object of the checkpoint on the system.
        :rtype: :class:`pathlib.Path`
        """
        if checkpoint_path is not None:
            path_n = self._normalize_store_path(checkpoint_path)
        else:
            path_n = self._normalize_store_path(store_path)

        if path_n.suffix:
            checkpoint_path_n = self._normalize_store_path(
                f"{path_n.parent}/{self.runner.runner_id}_CHECKPOINT.json"
            )
        if path_n.is_dir() or path_n.exists():
            checkpoint_path_n = self._normalize_store_path(
                f"{path_n}/{self.runner.runner_id}_CHECKPOINT.json"
            )
        else:
            checkpoint_path_n = self._normalize_store_path(
                f"{path_n}/{self.runner.runner_id}_CHECKPOINT.json"
            )

        logger.debug(
            f"Creating checkpoint at: '{checkpoint_path_n}' for runner: '{self.runner.runner_id}'"
        )
        return checkpoint_path_n

    def _normalize_store_path(self, store_path: str) -> Path:
        """Normalizes the path to the store by using the :class:`Path` object.

        :param store_path: The path to the store to normalize.
        :type store_path: str
        :return: The normalized :class:`Path`.
        :rtype: :class:`Path`
        """
        try:
            store_path_n = Path(store_path)
        except Exception as e:
            logger.fatal(
                f"Failed to normalize path due to unexpected error: {e}", exc_info=e
            )

        return store_path_n


class TridentDataDaemon:
    """Daemon handling all the reading/writing to the stores used by each :class:`TridentRunner`.
    All access goes through this daemon in order to verify that no conflicts occur when writing to the store
    and that all file handlers are properly opened/closed.

    :param daemon_config: The config for this data daemon.
    :type daemon_config: :class:`TridentDataDaemonConfig`
    """

    def __init__(self, daemon_config: TridentDataDaemonConfig):
        self.daemon_config = daemon_config

        if self.daemon_config.store_path is not None:
            self.store_data = self._initialize_store()
            self.run_index = self._get_run_index()
        else:
            self.store_data, self.run_index = None, 0

        logger.debug(
            f"Trident data daemon initialized for runner: '{self.daemon_config.runner.runner_id}'"
        )

    def store_runner_result(self, result: Dict) -> NoReturn:
        """Store the results given in the initialized store. This updates the store in the program and does not
        write the store to the disk.

        :param result: The result to update the store with in the form of a dictionary.
        :type result: dict
        """
        logger.debug(
            f"Updating store with: '{result}' for runner: '{self.daemon_config.runner.runner_id}'"
        )
        try:
            _result = {}
            for key, value in result.items():
                if hasattr(value, "__dict__"):
                    _result[key] = value.__dict__
                else:
                    _result[key] = value

            self._update_store_content(_result)
        except TypeError:
            logger.warning(
                f"Result: '{result}' is not JSON serializable for runner: '{self.daemon_config.runner.runner_id}'"
            )
        except Exception as e:
            raise e

    def write_to_store(self) -> NoReturn:
        """Writes the current initialized store to the disk on the system for the given store path."""
        logger.debug(
            f"Writing to store at path: '{self.daemon_config.store_path}' for runner: '{self.daemon_config.runner.runner_id}'"
        )
        try:
            with open(self.daemon_config.store_path, "r+") as store_obj:
                store_obj.seek(0)
                store_obj.write(json.dumps(self.store_data))
                store_obj.truncate()
        except Exception as e:
            logger.error(
                f"Failed to write to store: '{self.daemon_config.store_path}' for runner: '{self.daemon_config.runner.runner_id}'",
                exc_info=e,
            )

    def create_state_checkpoint(self) -> NoReturn:
        """Creates the checkpoint representing the current state of the plugin and stores it in the path given by `checkpoint_path` in :class:`TridentDataDaemonConfig`"""
        logger.debug(
            f"Writing to checkpoint at path: '{self.daemon_config.checkpoint_path}' for runner: '{self.daemon_config.runner.runner_id}'"
        )

        _state = self.daemon_config.runner.runner_state
        if _state is not None:
            try:
                with open(self.daemon_config.checkpoint_path, "r+") as checkpoint_obj:
                    checkpoint_obj.seek(0)
                    checkpoint_obj.write(json.dumps(_state))
                    checkpoint_obj.truncate()
            except Exception as e:
                logger.fatal(
                    f"Failed to write to checkpoint: '{self.daemon_config.checkpoint_path}' for runner: '{self.daemon_config.runner.runner_id}'",
                    exc_info=e,
                )

    def merge_store_data(self) -> NoReturn:
        """Merges the store data with the existing store data available in the written store.
        This is used when the store has results written to it from previous iterations.

        :raises JSONDecodeError: Raises JSONDecodeError if the JSON data is not parseable.
        """
        logger.debug(
            f"Merging store data with existing store at: '{self.daemon_config.store_path}'"
        )
        try:

            def _merge(runner, store):
                for k in store.keys():
                    if k not in runner:
                        runner[k] = store[k]

                    if isinstance(store[k], dict):
                        runner[k] = _merge(runner[k], store[k])

                return runner

            self.store_data = _merge(self.store_data, self._get_store_data())
        except json.JSONDecodeError as e:
            logger.warning(
                f"Failed to parse the JSON data read from the store: '{self.daemon_config.store_path}'"
            )
            raise e
        except Exception as e:
            logger.fatal(
                f"Failed to read state from store path: '{self.daemon_config.checkpoint_path}' for runner: '{self.daemon_config.runner.runner_id}'",
                exc_info=e,
            )

    def load_state_checkpoint(self) -> Dict[Union[str, int], Any]:
        """Load the checkpoint state for the current plugin from the path given by `checkpoint_path` in :class:`TridentDataDaemonConfig`"""
        logger.debug(
            f"Reading from the checkpoint at path: '{self.daemon_config.checkpoint_path}' for runner: '{self.daemon_config.runner.runner_id}'"
        )

        try:
            with open(self.daemon_config.checkpoint_path, "r") as checkpoint_obj:
                return json.load(checkpoint_obj)
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(
                f"Failed to read state from checkpoint path: '{self.daemon_config.checkpoint_path}' for runner: '{self.daemon_config.runner.runner_id}'",
                exc_info=e,
            )
        return {}

    def _initialize_store(self) -> Dict[str, Dict[str, Dict[str, Dict]]]:
        """Initialize the store structure if the store does not exist, otherwise read the existing store data and return.

        :return: The store structure in the form of {"runners": {"[RUNNER]": {"results": {...}}}}
        :rtype: dict
        """
        try:
            if not path.exists(self.daemon_config.store_path):
                logger.debug(
                    f"Initializing store at: '{self.daemon_config.store_path}'"
                )
                return {
                    "runners": {self.daemon_config.runner.runner_id: {"results": {}}}
                }

            return self._get_store_data()
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse the JSON data from the store: '{self.daemon_config.store_path}'"
            )
            raise e
        except Exception as e:
            logger.error(
                f"Failed to initialize store: '{self.daemon_config.store_path}' for runner: '{self.daemon_config.runner.runner_id}'",
                exc_info=e,
            )
            raise e

    def _update_store_content(self, result: Dict) -> NoReturn:
        """Update the initialized store values with the given result values.

        :param result: The result structure to update the store from.
        :type result: dict
        :raises JSONDecodeError: Raises JSONDecodeError if the JSON data is not parseable.
        :raises Exception: Raises exception if failed to read from the store.
        """
        try:
            results = self._get_runner_results()
            if self.run_index not in results:
                results[self.run_index] = {}

            results[self.run_index].update(result)
            self.store_data["runners"][self.daemon_config.runner.runner_id][
                "results"
            ].update(results)
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse the JSON data from the store: '{self.daemon_config.store_path}'"
            )
            raise e
        except Exception as e:
            logger.error(
                f"Failed to read from store: '{self.daemon_config.store_path}' for runner: '{self.daemon_config.runner.runner_id}'",
                exc_info=e,
            )
            raise e

    def _get_runner_content(self) -> Dict[str, Dict[int, Dict[int, Any]]]:
        """Get the part of the store relating to the runner connected to this daemon.
        Used when multiple runners are using the same store.

        :raises Exception: Raises Exception if the store data is of an unexpected format.
        :return: Dictionary of the format {"results": {0: {0: ...}}}
        :rtype: dict
        """
        try:
            if (
                "runners" not in self.store_data
                or self.daemon_config.runner.runner_id not in self.store_data["runners"]
            ):
                raise ValueError(
                    f"Store: '{self.daemon_config.store_path}' has not been initialized yet"
                )

            return self.store_data["runners"][self.daemon_config.runner.runner_id]
        except Exception as e:
            logger.error(
                f"Failed to get runner content for store: '{self.daemon_config.store_path}' for runner: '{self.daemon_config.runner.runner_id}'",
                exc_info=e,
            )
            raise e

    def _get_runner_results(self) -> Dict[int, Dict[int, Any]]:
        """Get the results part of the store relating to the runner connected to this daemon.

        :return: The results for the runner connected to this daemon.
        :rtype: dict
        """
        try:
            content = self._get_runner_content()
            return content["results"]
        except Exception as e:
            logger.error(
                f"Failed to get result for runner: '{self.daemon_config.runner.runner_id}'",
                exc_info=e,
            )
            raise e

    def _get_run_index(self) -> AnyStr:
        """Determine the run index for this run given the latest index in the store.
        If no runs have been made then return 0 as first index.

        :return: The index of this run.
        :rtype: str
        """
        try:
            content = self._get_runner_results()
            if not content.keys():
                return str(0)

            return str(max([int(index) for index in content.keys()]) + 1)
        except Exception as e:
            logger.error(
                f"Failed to get the run index for store: '{self.daemon_config.store_path}' for runner: '{self.daemon_config.runner.runner_id}'",
                exc_info=e,
            )
            raise e

    def _get_store_data(self) -> Dict[str, Dict[str, Dict[str, Dict[str, str]]]]:
        """Read from the store written to the disk and parse using the JSON library.

        :raises Exception: If unable to read from the store.
        :return: Returns the dictionary representation of the results written to the store on the disk.
        :rtype: dict
        """
        try:
            with open(self.daemon_config.store_path, "r") as store_obj:
                return json.load(store_obj)
        except Exception as e:
            logger.error(
                f"Failed to get the store data at: '{self.daemon_config.store_path}' for runner: '{self.daemon_config.runner.runner_id}'",
                exc_info=e,
            )
            raise e
