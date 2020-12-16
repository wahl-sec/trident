#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Trident Plugin Library: Port
Implements logic to connect and communicate over ports on a given host.
@author: Jacob Wahlman
"""

from typing import AnyStr, NewType, Union, ByteString
PortConnect = NewType("PortConnect", None)
OpenPort = NewType("OpenPort", None)
IPv4Address = NewType("IPv4Address", str)
Proto = NewType("Proto", int)

import select
import socket
import time

from plugins.lib.network.lib.socket import Socket


class PortConnect(Socket):
    def __init__(self, host: IPv4Address, port: int, timeout: float):
        super(PortConnect, self).__init__(host=host, port=port, timeout=timeout, family=socket.AF_INET, type_=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)

    def __enter__(self) -> PortConnect:
        self.connect()
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback) -> None:
        for read in self.read:
            self.close(read)

        for write in self.write:
            self.close(write)

        self.close()

    def connect(self) -> Union[socket.error, None]:
        try:
            self.socket.connect((self.host, self.port))
            return self._wait_for_connect(time_sent=time.time(), time_left=self.timeout)
        except Exception as e:
            return e

        return error

    def _wait_for_connect(self, time_sent: float, time_left: float) -> Union[socket.error, None]:
        if time_left <= 0:
            return TimeoutError(f"Socket timed out connecting to port: '{self.port}'")

        self.read, self.write, error = select.select([self.socket], [self.socket], [self.socket], time_left)
        received_time = time.time()

        self.delay = received_time - time_sent
        if self.read or self.write:
            return error

        return self._wait_for_connect(time_sent=time_sent, time_left=time_sent - received_time)


class OpenPort(Socket):
    def __init__(self, host: IPv4Address, port: int, timeout: float, backlog: int=1):
        self.backlog = backlog
        super(OpenPort, self).__init__(host=host, port=port, timeout=timeout, family=socket.AF_INET, type_=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)

    def __enter__(self, backlog=1) -> OpenPort:
        self.bind(backlog)
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback) -> None:
        self.socket.close()

    def bind(self, backlog):
        self.socket.bind((self.host, self.port))
        self.socket.listen(backlog)

    def accept_connection(self):
        return self.socket.accept()
