#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, AnyStr, List, Union, NoReturn

from cli.views import ListView, Back, View, TextOption, ChoiceOption, BoolOption, IntOption


class ConfigureView(ListView):
    options: Dict[AnyStr, AnyStr] = {}
    views: Dict[AnyStr, AnyStr] = {
        "0": Back
    }
    name: AnyStr = "Configure Trident"

    def __init__(self, history: List[View], config: Dict[AnyStr, Union[AnyStr, bool]]):
        super(ConfigureView, self).__init__(views=self.views)
        self.history, self.config = history + [self], config
        self.options.update({
            "logging_level": {
                "1": ChoiceOption(key="logging_level", value=self.config["logging_level"], options={
                    "INFO": "Output all log entries with level of INFO and above, default",
                    "WARNING": "Output only log entries with level of WARNING and above",
                    "DEBUG": "Output all log entries with level of DEBUG and above, verbose"
                }, config=self.config),
            },
            "trident": {
                "2": BoolOption(key="verbose", value=self.config["args"]["trident"]["verbose"], config=self.config["args"]["trident"]),
                "3": BoolOption(key="quiet", value=self.config["args"]["trident"]["quiet"], config=self.config["args"]["trident"]),
            },
            "daemon": {
                "4": IntOption(key="workers", value=self.config["args"]["daemon"]["workers"], config=self.config["args"]["daemon"])
            }
        })

