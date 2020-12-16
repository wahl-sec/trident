#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from random import randint, random
from time import sleep


@dataclass
class TestPlugin:
    def _add(self, x, y):
        return x + y

    def execute_plugin(self, thread_event):
        for i in range(0, 10):
            yield self._add(randint(0, 10), randint(0, 10))
