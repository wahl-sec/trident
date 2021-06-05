#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, AnyStr, List, Union

from cli.views import ListView, Exit, View
from cli.views.configure import ConfigureView
from cli.views.plugins import StartPluginsView


class StartView(ListView):
    views: Dict[AnyStr, AnyStr] = {
        "1": StartPluginsView,
        "2": ConfigureView,
        "0": Exit
    }
    name: AnyStr = "Start"

    def __init__(self, history: List[View], config: Dict[AnyStr, Union[AnyStr, bool]]):
        super(StartView, self).__init__(views=self.views)
        self.history, self.config = history + [self], config

