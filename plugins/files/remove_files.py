#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, AnyStr

from plugins.lib.files.files import *


class RemoveFiles:
    def execute_plugin(
        self,
        path: AnyStr,
        pattern: AnyStr = None,
        depth: int = -1,
        exclude: List[AnyStr] = None,
    ):
        remove_entries(path=path, patterns=pattern)
