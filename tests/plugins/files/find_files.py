#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from json import dumps
from typing import List, Optional
from plugins.lib.files.files import entries


class FindFiles:
    def execute_plugin(self, path, patterns: Optional[List[str]] = None):
        for entry in entries(path, patterns=patterns):
            yield entry
