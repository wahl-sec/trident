#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, AnyStr, List, Union

from cli.views import ListView, Back, View, TextOption, BoolOption, TransitionOption, Option
from cli.adapter.adapter import TridentAdapter, PluginsAdapter


class GlobalConfigurePluginsView(ListView):
    name: AnyStr = "Global Configure Plugins"

    def __init__(self, history: List[View], config: Dict[AnyStr, Union[AnyStr, bool]]):
        self.options: Dict[AnyStr, AnyStr] = {}
        self.views: Dict[AnyStr, AnyStr] = {
            "0": Back
        }

        super(GlobalConfigurePluginsView, self).__init__(views=self.views)
        self.history, self.config = history + [self], config
        self.options.update({
            "store": {
                "1": TextOption(key="path_store", value=self.config["args"]["store"]["path_store"], config=self.config["args"]["store"]),
                "2": BoolOption(key="no_store", value=self.config["args"]["store"]["no_store"], config=self.config["args"]["store"]),
                "3": TextOption(key="global_store", value=self.config["args"]["store"]["global_store"], config=self.config["args"]["store"])
            },
            "runner": {
                "4": BoolOption(key="dont_store_on_error", value=self.config["args"]["runner"]["dont_store_on_error"], config=self.config["args"]["runner"])
            }
        })


class ConfigurePluginsView(ListView):
    name: AnyStr = "Configure Plugins"

    def __init__(self, history: List[View], config: Dict[AnyStr, Union[AnyStr, bool]]):
        self.history, self.config = history + [self], config
        self.views: Dict[AnyStr, AnyStr] = {}

        super(ConfigurePluginsView, self).__init__(views=self.views)

        for count, plugin in enumerate(self.config["plugins"]):
            self.config["plugins"][plugin]["name"] = plugin
            self.views[str(count + 1)] = ConfigurePluginView(history=self.history.copy(), config=self.config, plugin=self.config["plugins"][plugin])

        self.views["0"] = Back  # Ensure that it is the last entry


class ConfigurePluginView(ListView):
    name: AnyStr = "Configure: {plugin} - {path}"

    def __init__(self, history: List[View], config: Dict[AnyStr, Union[AnyStr, bool]], plugin: Dict[AnyStr, AnyStr]):
        self.options: Dict[AnyStr, AnyStr] = {}
        self.views: Dict[AnyStr, AnyStr] = {
            "0": Back
        }

        super(ConfigurePluginView, self).__init__(views=self.views)
        self.history, self.config = history + [self], config
        self.name = self.name.format(plugin=plugin["name"], path=plugin["path"])

        self.config["plugins"][plugin["name"]].setdefault("args", {})
        self.config["plugins"][plugin["name"]]["args"].update({
            "store": {
                "path_store": self.config["args"]["store"].get("path_store", "data")
            },
            "runner": {},
            "notification": {}
        })

        self.options.update({
            "store": {
                "1": TextOption(key="path_store", value=plugin["args"]["store"].get("path_store", "data"), config=plugin["args"]["store"]),
                "2": BoolOption(key="no_store", value=plugin["args"]["store"].get("no_store", False), config=plugin["args"]["store"]),
                "3": TextOption(key="global_store", value=plugin["args"]["store"].get("global_store", None), config=plugin["args"]["store"])
            },
            "runner": {
                "4": BoolOption(key="dont_store_on_error", value=plugin["args"]["runner"].get("dont_store_on_error", False), config=plugin["args"]["runner"])
            },
            "plugin_args": {

            }
        })


class TransitionOptionsView(ListView):
    name: AnyStr = "Add {object}"

    def __init__(self, history: List[View], config: Dict[AnyStr, Union[AnyStr, bool]], options: Dict[AnyStr, Option], options_config: Dict[AnyStr, Union[AnyStr, bool]]):
        self.history, self.config, self.options, self.options_config = history + [self], config, options, options_config
        self.views: Dict[AnyStr, AnyStr] = {
            "0": Back
        }
        print(self.options, self.options_config)


class StartPluginView(ListView):
    name: AnyStr = "Start Plugin"

    def __init__(self, history: List[View], config: Dict[AnyStr, Union[AnyStr, bool]]):
        self.history, self.config = history + [self], config
        self.views: Dict[AnyStr, AnyStr] = {
            "1": ConfigurePluginView,
            "0": Back
        }

        super(StartPluginView, self).__init__(views=self.views)


class StartTridentView(ListView):
    name: AnyStr = "Start Trident"

    def __init__(self, history: List[View], config: Dict[AnyStr, Union[AnyStr, bool]]):
        self.history, self.config = history + [self], config
        self.views: Dict[AnyStr, View] = {
            "0": Back
        }

        super(StartTridentView, self).__init__(views=self.views)

        print(self.config)
        daemon = TridentAdapter.daemon(self.config)
        print(2222, self.config)
        print(daemon)


class StartPluginsView(ListView):
    name: AnyStr = "Start Plugins"

    def __init__(self, history: List[View], config: Dict[AnyStr, Union[AnyStr, bool]]):
        self.history, self.config = history + [self], config
        self.views: Dict[AnyStr, View] = {
            "1": GlobalConfigurePluginsView,
            "2": ConfigurePluginsView(history=self.history.copy(), config=self.config.copy()),  # Instantiate to load the default settings
            "3": StartTridentView,
            "0": Back
        }

        super(StartPluginsView, self).__init__(views=self.views)

