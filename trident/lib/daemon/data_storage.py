#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident: Data Storage

Trident daemon handling the data collected by all runners under a Trident daemon.
@author: Jacob Wahlman
"""

import json
from os import path, rename
from pathlib import Path
from dataclasses import dataclass
from functools import reduce

from typing import Dict, NewType, Any, NoReturn
TridentRunner = NewType("TridentRunner", None)

import logging
logger = logging.getLogger("__main__")


@dataclass
class TridentDataDaemonConfig:
    """ Config class for :class:`TridentDataDaemon` controlling the data handling for each :class:`TridentRunner`.

    :param runner: Reference to the runner belonging to this daemon :class:`TridentRunner`
    :type runner: class:`TridentRunner`
    :param store_path: Given path to the store location on disk.
    :type store_path: str
    :param store_name: Name of the store on the disk if the store path does not include file, default behavior is using the id of the runner :class:`TridentRunner`.
    :type store_name: str
    """
    runner: object
    store_path: Path
    store_name: str

    def __init__(self, runner: TridentRunner, store_path: str, store_name: str):
        self.runner = runner
        self.store_name = store_name
        self.store_path = self._determine_store_path(store_path)

    def _determine_store_path(self, store_path: str) -> Path:
        """ Verifies that the store path is a valid path that exists and is normalizable, returns the normalized path if valid.
        Raises `FileNotFoundError` if the normalized store path does not exist.

        :param store_path: The store path to verify and normalize.
        :type store_path: str 
        :raises FileNotFoundError: The store path does not exist on the system.
        :return: The :class:`Path` object of the store on the system.
        :rtype: :class:`Path`
        """
        store_path_n = self._normalize_store_path(store_path)
        if path.isfile(store_path_n):
            logger.debug(f"Using existing store path: '{store_path_n}' for runner: '{self.runner.runner_id}'")
            return store_path_n
        elif path.isdir(store_path_n) or path.exists(path.dirname(store_path_n)):
            logger.debug(f"Creating store in path: '{store_path_n}' for runner: '{self.runner.runner_id}'")
            if store_path_n.suffix == ".json":
                return store_path_n

            return self._normalize_store_path(f"{store_path}/{self.store_name}.json")
        else:
            raise FileNotFoundError(f"Store path: {store_path_n} does not exist for runner: '{self.runner.runner_id}'")

    def _normalize_store_path(self, store_path: str) -> Path:
        """ Normalizes the path to the store by using the :class:`Path` object.

        :param store_path: The path to the store to normalize.
        :type store_path: str
        :return: The normalized :class:`Path`.
        :rtype: :class:`Path`
        """
        try:
            store_path_n = Path(store_path)
        except Exception as e:
            logger.fatal(f"Failed to normalize path due to unexpected error: {e}")
            raise e

        return store_path_n


class TridentDataDaemon:
    """ Daemon handling all the reading/writing to the stores used by each :class:`TridentRunner`.
    All access goes through this daemon in order to verify that no conflicts occur when writing to the store
    and that all file handlers are properly opened/closed.

    :param daemon_config: The config for this data daemon.
    :type daemon_config: :class:`TridentDataDaemonConfig`
    """
    def __init__(self, daemon_config: TridentDataDaemonConfig):
        self.daemon_config = daemon_config
        self.store_data = self._initialize_store()
        self.run_index = self._get_run_index()
        logger.debug(f"Trident data daemon initialized for runner: '{self.daemon_config.runner.runner_id}'")

    def store_runner_result(self, result: Dict) -> NoReturn:
        """ Store the results given in the initialized store. This updates the store in the program and does not
        write the store to the disk.

        :param result: The result to update the store with in the form of a dictionary.
        :type result: dict
        """
        logger.debug(f"Updating store with: '{result}' for runner: '{self.daemon_config.runner.runner_id}'")
        try:
            self._update_store_content(result)
        except Exception as e:
            raise e

    def write_to_store(self) -> NoReturn:
        """ Writes the current initialized store to the disk on the system for the given store path. """
        logger.debug(f"Writing to store at path: '{self.daemon_config.store_path}'")
        try:
            with open(self.daemon_config.store_path, "r+") as store_obj:
                store_obj.seek(0)
                store_obj.write(json.dumps(self.store_data))
                store_obj.truncate()
        except Exception as e:
            logger.error(f"Failed to write to store: '{self.daemon_config.store_path}'")

    def merge_store_data(self) -> NoReturn:
        """ Merges the store data with the existing store data available in the written store.
        This is used when the store has results written to it from previous iterations.

        :raises JSONDecodeError: Raises JSONDecodeError if the JSON data is not parseable.
        """
        logger.debug(f"Merging store data with existing store at: '{self.daemon_config.store_path}'")
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
            logger.warning(f"Failed to parse the JSON data read from the store: '{self.daemon_config.store_path}'")
            raise e
        except Exception as e:
            raise e

    def _initialize_store(self) -> Dict[str, Dict[str, Dict[str, Dict]]]:
        """ Initialize the store structure if the store does not exist, otherwise read the existing store data and return.

        :return: The store structure in the form of {"runners": {"[RUNNER]": {"results": {...}}}}
        :rtype: dict
        """
        try:
            if not path.exists(self.daemon_config.store_path):
                logger.debug(f"Initializing store at: '{self.daemon_config.store_path}'")
                return {"runners": {self.daemon_config.runner.runner_id: {"results": {}}}}

            return self._get_store_data()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse the JSON data from the store: '{self.daemon_config.store_path}'")
            raise e
        except Exception:
            raise e

    def _update_store_content(self, result: Dict) -> NoReturn:
        """ Update the initialized store values from the given result values.

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
            self.store_data["runners"][self.daemon_config.runner.runner_id]["results"].update(results)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse the JSON data from the store: '{self.daemon_config.store_path}'")
            raise e
        except Exception as e:
            logger.error(f"Failed to read from store: '{self.daemon_config.store_path}'")
            raise e

    def _get_runner_content(self) -> Dict[str, Dict[int, Dict[int, Any]]]:
        """ Get the part of the store relating to the runner connected to this daemon.
        Used when multiple runners are using the same store.

        :raises Exception: Raises Exception if the store data is of an unexpected format.
        :return: Dictionary of the format {"results": {0: {0: ...}}}
        :rtype: dict
        """
        try:
            if "runners" not in self.store_data or self.daemon_config.runner.runner_id not in self.store_data["runners"]:
                raise ValueError(f"Store: '{self.daemon_config.store_path}' has not been initialized yet")

            return self.store_data["runners"][self.daemon_config.runner.runner_id]
        except Exception as e:
            logger.error(f"Failed to get runner content for store: '{self.daemon_config.store_path}'")
            raise e

    def _get_runner_results(self) -> Dict[int, Dict[int, Any]]:
        """ Get the results part of the store relating to the runner connected to this daemon.

        :return: The results for the runner connected to this daemon.
        :rtype: dict
        """
        try:
            content = self._get_runner_content()
            return content["results"]
        except Exception as e:
            logger.error(f"Failed to get result for runner: '{self.daemon_config.runner.runner_id}'")
            raise e

    def _get_run_index(self) -> str:
        """ Determine the run index for this run given the latest index in the store.
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
            logger.error(f"Failed to get the run index for store: '{self.daemon_config.store_path}'")
            raise e

    def _get_store_data(self) -> Dict[str, Dict[str, Dict[str, Dict[str, str]]]]:
        """ Read from the store written to the disk and parse using the JSON library.

        :raises Exception: If unable to read from the store.
        :return: Returns the dictionary representation of the results written to the store on the disk.
        :rtype: dict
        """
        try:
            with open(self.daemon_config.store_path, "r") as store_obj:
                return json.load(store_obj)
        except Exception as e:
            raise e
