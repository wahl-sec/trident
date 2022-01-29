#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from plugins.lib.files.files import *
from plugins.lib.network.http import *
from plugins.lib.network.port import *
from plugins.lib.network.ping import *
from plugins.lib.network.lib.packet import TCP, UDP


class TestPlugin:
    def __init__(self):
        self._state = None

    @property
    def plugin_state(self):
        return self._state

    @plugin_state.setter
    def plugin_state(self, state):
        self._state = state

    def execute_plugin(self, thread_event, path, depth):
        for entry in entries(
            path,
            depth=depth,
            exceptions=False,
            exclude=[path for path in self._state.keys()]
            if self._state is not None
            else None,
        ):
            if thread_event.is_set():
                return

            self._state[entry.path] = 1
            yield str(entry.path)
