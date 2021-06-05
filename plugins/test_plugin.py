#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from random import randint, random
from time import sleep, time
import socket

from plugins.lib.files.files import *
from plugins.lib.network.http import *
from plugins.lib.network.port import *
from plugins.lib.network.ping import *
from plugins.lib.network.lib.packet import TCP, UDP

class TestPlugin:
    def execute_plugin(self, thread_event, value):
        for i in range(value, value + 10):
            yield i + i;
