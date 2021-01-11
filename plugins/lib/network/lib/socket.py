#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Trident Plugin Library: Socket
Implements the socket handler for Trident plugin.
@author: Jacob Wahlman
"""

from typing import NewType
IPv4Address = NewType("IPv4Address", str)
AddressFamily = NewType("AddressFamily", str)
SocketType = NewType("SocketType", str)
Protocol = NewType("Protocol", int)

import socket


class Socket:
    def __init__(self, host: IPv4Address, port: int, timeout: float, family: AddressFamily, type_: SocketType, proto: Protocol):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.read, self.write, self.delay = [], [], self.timeout
        self.socket = self._create_socket(family=family, type_=type_, proto=proto)

    def close(self, port_socket=None) -> None:
        if port_socket is None:
            port_socket = self.socket

        try:
            port_socket.close()
        except Exception as e:
            raise e

    def _create_socket(self, family: socket.AddressFamily, type_: socket.SocketType, proto: int) -> socket.socket:
        try:
            socket_ = socket.socket(family=family, type=type_, proto=proto)
        except socket.error as e:
            raise RuntimeError(f"Unexpected error creating socket: {e}")

        return socket_
