#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import NoReturn, AnyStr, List, Dict, Union
from pathlib import Path
from os import path
import json

from cli.views import View, Back, Option, ChoiceOption
from cli.views.start import StartView
from cli.views.configure import ConfigureView


class TridentCLI:
    history: List[View] = []
    config: Dict[AnyStr, Union[AnyStr, bool]] = {
        "logging_level": "INFO",
        "plugins": {

        },
        "args": {
            "trident": {
                "verbose": False,
                "quiet": False
            },
            "daemon": {
                "workers": 5
            },
            "store": {
                "path_store": "data",
                "no_store": False,
                "global_store": None
            },
            "runner": {
                "dont_store_on_error": False
            }
        }
    }

    def __init__(self):
        config_file = path.join(path.dirname(path.dirname(path.abspath(__file__))), "config", "trident.json")
        if Path(config_file).exists():
            self.config.update(self.read_config(config_file, "TRIDENT"))

        self.display(StartView(self.history, self.config))

    def display(self, view: View) -> NoReturn:
        while True:
            if isinstance(view, Back):
                view = view.history[-1]

            view.display()
            print(f"\33]0;Trident / {view.name}\a", end="")

            choice = view.prompt()
            if isinstance(choice, Option):
                choice = choice.modify()
                if choice is None:
                    continue

            if isinstance(choice, View):  # Already instantiated
                view = choice
            else:
                view = choice(history=view.history.copy(), config=self.config)

    def read_config(self, path: AnyStr, section: AnyStr) -> Dict[AnyStr, Union[AnyStr, bool]]:
        with open(path, "r") as file_obj:
            config = json.load(file_obj)[section]

        config["config"] = Path(path).name
        return config


if __name__ == "__main__":
    trident = TridentCLI()

