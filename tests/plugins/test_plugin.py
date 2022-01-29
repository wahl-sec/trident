#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from random import randint


class TestPlugin:
    def __init__(self):
        self._state = None

    @property
    def plugin_state(self):
        return self._state

    @plugin_state.setter
    def plugin_state(self, state):
        self._state = state

    def _add(self, x, y):
        return x + y

    def execute_plugin(self, thread_event):
        for _ in range(0, 10):
            yield self._add(randint(0, 10), randint(0, 10))
