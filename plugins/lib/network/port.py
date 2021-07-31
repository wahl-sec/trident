#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Trident Plugin: Port Library
Common port operations, scanning, opening, etc.
Scanners are implemented using generators to allow for asynchronous plugins.
@author: Jacob Wahlman
"""

from typing import Union, NewType, Generator

IPv4Address = NewType("IPv4Address", str)

from plugins.lib.network.lib.port import PortConnect, OpenPort


def port_connect(
    host: IPv4Address, port: int, timeout: int = 5
) -> Union[PortConnect, None]:
    try:
        return PortConnect(host=host, port=port, timeout=timeout).connect()
    except Exception as e:
        raise RuntimeError(f"Failed to connect to port: '{port}' due to {e}")


def open_port(
    host: IPv4Address, port: int, timeout: int = 5, backlog: int = 1
) -> Generator:
    try:
        socket = OpenPort(host=host, port=port, timeout=timeout)
        socket.bind(backlog)
        yield socket.socket.accept()
    except Exception as e:
        raise RuntimeError(f"Failed to bind port: '{port}' due to {e}")
