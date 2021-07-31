#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Trident Plugin Library: ICMP
Create ICMP packets to be used by the ping plugin for Trident.
Based On: https://gist.githubusercontent.com/pklaus/856268/raw/a4e295d0dbd1140bddc90616e93ab3b19718a87b/ping.py
@author: Jacob Wahlman
"""

from typing import AnyStr, NewType, ByteString

AddressFamily = NewType("AddressFamily", str)
SocketType = NewType("SocketType", str)
IPv4Address = NewType("IPv4Address", str)
Proto = NewType("Proto", int)

import select
import socket
import struct
import time

from plugins.lib.network.lib.packet import ICMP
from plugins.lib.network.lib.socket import Socket


RECV_BUFFER_SIZE = 1024
ICMP_CODE = socket.getprotobyname("icmp")


class PingQuery:
    def __init__(self, host: AnyStr, timeout: float, count: int):
        self.count = count
        self.timeout = timeout
        self.host = socket.gethostbyname(host)

    def __iter__(self):
        return (self.__next__() for _ in range(self.count))

    def __next__(self):
        if not self.count:
            raise StopIteration

        self.count -= 1
        return Ping(
            host=self.host,
            packet_id=int((id(self.timeout) / (self.count + 1)) % 65535),
            timeout=self.timeout,
            count=self.count,
            family=socket.AF_INET,
            type_=socket.SOCK_RAW,
        ).ping()

    def ping(self):
        _result = {}
        for count in range(self.count):
            _result[count] = Ping(
                host=self.host,
                packet_id=int((id(self.timeout) / (count + 1)) % 65535),
                timeout=self.timeout,
                count=count,
                family=socket.AF_INET,
                type_=socket.SOCK_RAW,
            ).ping()

        return _result


class Ping(Socket):
    def __init__(
        self,
        host: IPv4Address,
        packet_id: int,
        timeout: int,
        count: int,
        family: AddressFamily,
        type_: SocketType,
    ):
        self.packet_id = packet_id
        self.timeout = timeout
        self.count = count
        self.host = host

        self.delay = None
        self.raw_socket = self._create_socket(
            socket.AF_INET, socket.SOCK_RAW, ICMP_CODE
        )

    def ping(self):
        self._send_ping(
            packet=ICMP(destination=(self.host, 1), packet_id=self.packet_id).data
        )
        self.delay = self._receive_ping(time_sent=time.time(), time_left=self.timeout)
        return self.host, self.delay

    def _send_ping(self, packet: ByteString):
        if not packet:
            return

        sent = self.raw_socket.sendto(packet, packet.destionation)
        return self._send_ping(packet[sent:])

    def _receive_ping(self, time_sent: float, time_left: float):
        if time_left <= 0:
            return

        read, _, _ = select.select([self.raw_socket], [], [], time_left)
        received_time = time.time()
        if not read:
            return

        response, addr = self.raw_socket.recvfrom(RECV_BUFFER_SIZE)
        icmp_header = response[20:28]
        type_, code, checksum, packet_id, sequence = struct.unpack("bbHHh", icmp_header)

        if packet_id == self.packet_id:
            return received_time - time_sent

        return self._receive_ping(
            time_sent=time_sent, time_left=time_sent - received_time
        )
