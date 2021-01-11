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
    runner: object
    store_path: Path
    store_name: str

    def __init__(self, runner: TridentRunner, store_path: str, store_name: str):
        self.runner = runner
        self.store_name = store_name
        self.store_path = self._determine_store_path(store_path)

    def _determine_store_path(self, store_path: str) -> Path:
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
        try:
            store_path_n = Path(store_path)
        except Exception as e:
            logger.fatal(f"Failed to normalize path due to unexpected error: {e}")
            raise e

        return store_path_n


class TridentDataDaemon:
    def __init__(self, daemon_config: TridentDataDaemonConfig):
        self.daemon_config = daemon_config
        self.store_data = self._initialize_daemon()
        self.run_index = self._get_run_index()
        logger.debug(f"Trident data daemon initialized for runner: '{self.daemon_config.runner.runner_id}'")

    def store_runner_result(self, result: Any) -> NoReturn:
        logger.debug(f"Updating store with: '{result}' for runner: '{self.daemon_config.runner.runner_id}'")
        try:
            self._update_store_content(result)
        except Exception as e:
            raise e

    def write_to_store(self) -> NoReturn:
        logger.debug(f"Writing to store at path: '{self.daemon_config.store_path}'")
        try:
            with open(self.daemon_config.store_path, "r+") as store_obj:
                store_obj.seek(0)
                store_obj.write(json.dumps(self.store_data))
                store_obj.truncate()
        except Exception as e:
            logger.error(f"Failed to write to store: '{self.daemon_config.store_path}'")

    def merge_store_data(self) -> NoReturn:
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
            pass
        except Exception as e:
            raise e

    def _update_store_content(self, result: Any) -> NoReturn:
        try:
            results = self._get_runner_results()
            if self.run_index not in results:
                results[self.run_index] = {}

            results[self.run_index].update(result)
            self.store_data["runners"][self.daemon_config.runner.runner_id]["results"].update(results)
        except Exception as e:
            logger.error(f"Failed to read from store: '{self.daemon_config.store_path}'")
            raise e

    def _initialize_daemon(self) -> Dict[str, Dict[str, Dict[str, Dict]]]:
        if not path.exists(self.daemon_config.store_path):
            logger.debug(f"Initializing store at: '{self.daemon_config.store_path}'")
            try:
                return {"runners": {self.daemon_config.runner.runner_id: {"results": {}}}}
            except Exception as e:
                raise e

        return self._get_store_data()

    def _get_runner_content(self) -> Dict[str, Dict[int, Dict[int, Any]]]:
        try:
            if "runners" not in self.store_data or self.daemon_config.runner.runner_id not in self.store_data["runners"]:
                raise ValueError(f"Store: '{self.daemon_config.store_path}' has not been initialized yet")

            return self.store_data["runners"][self.daemon_config.runner.runner_id]
        except Exception as e:
            logger.error(f"Failed to get runner content for store: '{self.daemon_config.store_path}'")
            raise e

    def _get_runner_results(self) -> Dict[int, Dict[int, Any]]:
        content = self._get_runner_content()
        try:
            return content["results"]
        except Exception as e:
            logger.error(f"Failed to get result for runner: '{self.daemon_config.runner.runner_id}'")
            raise e

    def _get_run_index(self) -> str:
        try:
            content = self._get_runner_results()
            if not content.keys():
                return str(0)

            return str(max([int(index) for index in content.keys()]) + 1)
        except Exception as e:
            logger.error(f"Failed to get the run index for store: '{self.daemon_config.store_path}'")
            raise e

    def _get_store_data(self) -> Dict[str, Dict[str, Dict[str, Dict[str, str]]]]:
        try:
            with open(self.daemon_config.store_path, "r") as store_obj:
                return json.load(store_obj)
        except Exception as e:
            raise e
