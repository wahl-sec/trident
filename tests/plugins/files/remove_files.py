#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List
from plugins.lib.files.files import remove_entry


class RemoveFiles:
    def execute_plugin(self, path, patterns: List[str] = []):
        remove_entry(path, patterns=patterns)
