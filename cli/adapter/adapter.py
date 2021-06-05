#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import NoReturn, AnyStr, Dict, Union

from trident import Trident, TridentConfig


class PluginsAdapter:
    pass


class TridentAdapter:
    @staticmethod
    def daemon(config: Dict[AnyStr, Union[AnyStr, int, bool]]) -> Trident:
        return Trident(TridentConfig(config))

