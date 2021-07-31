#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Trident Plugin Library: Packets
Packets used by other network components.
Transport Layer: TCP, UDP
Internet Layer: ICMP
@author: Jacob Wahlman
"""

from typing import ByteString, Tuple, NewType, Optional

IPv4Address = NewType("IPv4Address", str)
Port = NewType("Port", int)

import struct
import socket
import array

ICMP_ECHO_REQUEST = 8


class ICMP:
    def __init__(self, destination: Tuple[IPv4Address, Port], packet_id: int):
        self.destination = destination
        self.data = self._create_packet(packet_id)

    def _checksum(self, packet: ByteString) -> int:
        checksum = 0
        for count in range(0, len(packet), 2):
            checksum += packet[count + 1] * 256 + packet[count]
            checksum &= 0xFFFFFFFF

        checksum = (checksum >> 16) + (checksum & 0xFFFF)
        checksum += checksum >> 16
        checksum = (~checksum) & 0xFFFF
        checksum = checksum >> 8 | (checksum << 8 & 0xFF00)
        return checksum

    def _create_packet(self, packet_id: int) -> ByteString:
        header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, 0, packet_id, 1)
        return struct.pack(
            "bbHHh",
            ICMP_ECHO_REQUEST,
            0,
            socket.htons(self._checksum(header)),
            packet_id,
            1,
        )


class TCP:
    def __init__(
        self,
        source: Tuple[IPv4Address, Port],
        destination: Tuple[IPv4Address, Port],
        flags: int = 0,
        payload: Optional[ByteString] = None,
        size: int = 512,
    ):
        self.source = source
        self.destination = destination
        self.payload = payload
        self.flags = flags
        self.size = size
        self.data = self._create_packet()

    def _checksum(self, packet: ByteString) -> int:
        if len(packet) % 2 != 0:
            packet += b"\0"

        res = sum(array.array("H", packet))
        res = (res >> 16) + (res & 0xFFFF)
        res += res >> 16
        return (~res) & 0xFFFF

    def _create_packet(self) -> ByteString:
        source_ip, source_port = self.source
        destination_ip, destination_port = self.destination

        packet = struct.pack(
            "!HHIIBBHHH",
            source_port,
            destination_port,
            0,
            0,
            5 << 4,
            self.flags,
            self.size,
            0,
            0,
        )

        data = struct.pack(
            "!4s4sHH",
            socket.inet_aton(source_ip),
            socket.inet_aton(destination_ip),
            socket.IPPROTO_TCP,
            len(packet),
        )

        if self.payload is None:
            self.payload = b""

        return (
            struct.pack(
                "!HHIIBBHHH",
                source_port,
                destination_port,
                0,
                0,
                5 << 4,
                self.flags,
                self.size,
                self._checksum(packet + data),
                0,
            )
            + self.payload
        )


class UDP:
    def __init__(
        self,
        source: Tuple[IPv4Address, Port],
        destination: Tuple[IPv4Address, Port],
        payload: Optional[ByteString] = None,
    ):
        self.source = source
        self.destination = destination
        self.payload = payload
        self.data = self._create_packet()

    def _checksum(self, packet: ByteString) -> int:
        if len(packet) % 2 != 0:
            packet += b"\0"

        res = sum(array.array("H", packet))
        res = (res >> 16) + (res & 0xFFFF)
        res += res >> 16
        return (~res) & 0xFFFF

    def _create_packet(self) -> ByteString:
        source_ip, source_port = self.source
        destination_ip, destination_port = self.destination

        packet = struct.pack("!HHHH", source_port, destination_port, 0, 0)

        data = struct.pack(
            "!4s4sHH",
            socket.inet_aton(source_ip),
            socket.inet_aton(destination_ip),
            socket.IPPROTO_UDP,
            len(packet),
        )

        if self.payload is None:
            self.payload = b""

        return (
            struct.pack(
                "!HHHH",
                source_port,
                destination_port,
                len(packet) + len(self.payload),
                self._checksum(packet + data),
            )
            + self.payload
        )
