#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import NoReturn, Dict, AnyStr, NewType, List, Union
from os import name, system
import termios
import sys
import tty

PROMPT = ">>> "
OPTION_PROMPT = "{key} = {value}"
PADDING = 2
TRIDENT = """
    ████████╗██████╗ ██╗██████╗ ███████╗███╗   ██╗████████╗
    ╚══██╔══╝██╔══██╗██║██╔══██╗██╔════╝████╗  ██║╚══██╔══╝
       ██║   ██████╔╝██║██║  ██║█████╗  ██╔██╗ ██║   ██║
       ██║   ██╔══██╗██║██║  ██║██╔══╝  ██║╚██╗██║   ██║
       ██║   ██║  ██║██║██████╔╝███████╗██║ ╚████║   ██║
       ╚═╝   ╚═╝  ╚═╝╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝

    @author: Jacob Wahlman
    @version: 1.0.0
    @config: {config}
"""


class View:
    def display(self) -> NoReturn:
        print("\n" * PADDING, TRIDENT.format(config=self.config.get("config", "No Config Selected")))

    def clear(self) -> NoReturn:
        #system("cls" if name == "nt" else "clear")
        pass


class Exit:
    name: AnyStr = "Exit"

    def __init__(self, history: List[View], config: Dict[AnyStr, Union[AnyStr, bool]]):
        pass

    def display(self) -> NoReturn:
        exit(0)


class Back:
    name: AnyStr = "Back"

    def __init__(self, history: List[View], config: Dict[AnyStr, Union[AnyStr, bool]]):
        self.history = history[:-1]

    def prompt(self) -> NoReturn:
        pass

    def display(self) -> NoReturn:
        pass


class ListView(View):
    def __init__(self, views: Dict[AnyStr, AnyStr]):
        pass

    def display(self) -> NoReturn:
        super(ListView, self).clear()
        super(ListView, self).display()
        if hasattr(self, "options"):
            for section, config in self.options.items():
                print(f"Section - {section}")
                for key, value in config.items():
                    if hasattr(value, "value"):
                        print(f"({key}) - {value.key} = {value.value}")
                    else:
                        print(f"({key}) - {value.key}")

        for key, value in self.views.items():
            print(f"({key}) - {value.name}")

    def prompt(self) -> AnyStr:
        choice: AnyStr = None
        while choice not in self.views:
            if hasattr(self, "options"):
                for config in self.options.values():
                    if choice in config:
                        return config[choice]

            choice = input(PROMPT)

        return self.views[choice]


class TableView(View):
    def __init__(self, views: Dict[AnyStr, AnyStr]):
        pass

    def display(self) -> NoReturn:
        pass


class Option:
    pass


class BoolOption(Option):
    def __init__(self, key: AnyStr, value: bool, config: Dict[AnyStr, Union[AnyStr, bool]]):
        self.key, self.value, self.config = key, value, config

    def modify(self) -> NoReturn:
        self.value = not self.value
        self.config[self.key] = self.value


class IntOption(Option):
    def __init__(self, key: AnyStr, value: bool, config: Dict[AnyStr, Union[AnyStr, bool]]):
        self.key, self.value, self.config = key, value, config

    def modify(self) -> NoReturn:
        try:
            self.value = int(input(OPTION_PROMPT.format(key=self.key, value="")))
            if self.value <= 0:
                return self.modify()
        except ValueError:
            return self.modify()
        finally:
            self.config[self.key] = self.value


class TextOption(Option):
    def __init__(self, key: AnyStr, value: bool, config: Dict[AnyStr, Union[AnyStr, bool]]):
        self.key, self.value, self.config = key, value, config

    def modify(self) -> NoReturn:
        self.value = input(OPTION_PROMPT.format(key=self.key, value=""))
        self.config[self.key] = self.value if self.value else None


class ChoiceOption(Option):
    def __init__(self, key: AnyStr, value: AnyStr, options: Dict[AnyStr, AnyStr], config: Dict[AnyStr, Union[AnyStr, bool]]):
        self.key, self.value, self.options, self.config = key, value, options, config

    def modify(self) -> NoReturn:
        print("OPTIONS:")
        for key, value in self.options.items():
            print(OPTION_PROMPT.format(key=key, value=value))
        print()

        self.value = input(OPTION_PROMPT.format(key=self.key, value=""))
        while self.value not in self.options:
            self.value = input(OPTION_PROMPT.format(key=self.key, value=""))

        self.config[self.key] = self.value


class TransitionOption(Option):
    def __init__(self, key: AnyStr, view: View, history: List[View], config: Dict[AnyStr, Union[AnyStr, bool]], options_config: Dict[AnyStr, Union[AnyStr, bool]], options: Dict[AnyStr, Option]):
        self.key, self.view, self.history, self.config, self.options_config, self.options = key, view, history, config, options_config, options

    def modify(self) -> NoReturn:
        return self.view(history=self.history, config=self.config, options=self.options, options_config=self.options_config)


class ListOption(Option):
    pass

