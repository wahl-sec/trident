#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Trident Plugin: Ping Library
Ping host(s) using ICMP.
Implemented to allow for asynchronous plugins, pings one host per iteration.
@author: Jacob Wahlman
"""

from threading import Event
from typing import Sequence, AnyStr, Generator, NewType, Dict
IPv4Address = NewType("IPv4Address", str)

from plugins.lib.network.lib.icmp import PingQuery


def ping_host(hosts: Sequence[IPv4Address], timeout: float, count: int, thread_event: Event=None) -> Dict[IPv4Address, Dict[int, float]]:
    if not isinstance(hosts, (list, tuple, set)):
        raise ValueError(f"Host list must be of type: list, tuple or set not: '{type(hosts)}'")

    _results = {host: {} for host in hosts}
    for host in hosts:
        if thread_event is not None and thread_event.is_set():
            break

        _results[host] = PingQuery(host=host, timeout=timeout, count=count).ping()

    return _results

def ping_host_iter(hosts: Sequence[IPv4Address], timeout: float, count: int, thread_event: Event=None) -> PingQuery:
    if not isinstance(hosts, (list, tuple, set)):
        raise ValueError(f"Host list must be of type: list, tuple or set not: '{type(hosts)}'")

    for host in hosts:
        if thread_event is not None and thread_event.is_set():
            break

        yield PingQuery(host=host, timeout=timeout, count=count)
