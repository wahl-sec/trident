#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident: Interface Daemon

Trident interface used for communication between daemons, controls orchestration of plugin execution,
and data transportation between Trident daemons.
@author: Jacob Wahlman
"""

from dataclasses import dataclass
from typing import List, NoReturn, Optional, Generator, Tuple
import concurrent.futures

import grpc

from trident.lib.interface.proto import (
    MESSAGES,
    TridentMessageStub,
    TridentMessageRequest,
    TridentMessageReply,
)

import logging

logger = logging.getLogger("__main__")


@dataclass
class TridentInterfaceSenderConfig:
    """Sending configuration for :class:`TridentInterface` used for controlling how
    the interface should handle any outgoing communications.

    :param ip: The IP to which the receiver :class:`TridentInterface` is listening on.
    :type ip: str
    :param port: The port on which the remote :class:`TridentRemoteDaemon` is listening on.
    :type port: int
    """

    ip: str
    port: int


@dataclass
class TridentSender:
    """Sender for :class:`TridentInterface` used for executing any outgoing communication
    to another :class:`TridentInterface`.

    :param sender_config: The configuration for this sender.
    :type sender_config: :class:`TridentInterfaceSenderConfig`
    """

    sender_config: TridentInterfaceSenderConfig


@dataclass
class TridentInterfaceReceiverConfig:
    """Receiver configuration for :class:`TridentInterface` used for controlling how
    the interface should handle any incoming communications.

    :param port: The port on which the remote :class:`TridentRemoteDaemon` is listening on.
    :type port: int
    """

    port: int


@dataclass
class TridentReceiver:
    """Receiver for :class:`TridentInterface` used for executing any incoming communication
    from another :class:`TridentInterface`.

    :param receiver_config: The configuration for this receiver.
    :type receiver_config: :class:`TridentInterfaceReceiverConfig`
    """

    receiver_config: TridentInterfaceReceiverConfig


@dataclass
class TridentInterfaceConfig:
    """Config class for :class:`TridentInterface` interfacing against a remote interface,
    used by :class:`TridentDaemon` to communicate with another remote :class:`TridentDaemon`.

    :param senders: The senders to which any outgoing communications go to.
    :type senders: List[:class:`TridentSender`]
    :param receiver: The receiver interface to which any incoming communications go to.
    :type receiver: :class:`TridentReceiver`
    """

    senders: List[TridentSender]
    receiver: Optional[TridentReceiver]


class TridentInterface:
    """Trident interface for communication with another :class:`TridentInterface`."""

    def __init__(self, interface_config: TridentInterfaceConfig) -> None:
        self.interface_config = interface_config

    def listen(self) -> NoReturn:
        """Starts a thread and listens for any incoming communications.
        The incoming communication is handled as defined in the :class:`TridentInterfaceReceiverConfig`
        """
        logger.debug("Initializing listening interface ...")
        _server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
        for service, adder in MESSAGES.items():
            adder((service)(), _server)
        _server.add_insecure_port(
            "[::]:" + str(self.interface_config.receiver.receiver_config.port)
        )
        _server.start()
        logger.info(
            f"Interface listening on port {self.interface_config.receiver.receiver_config.port} for incoming messages ..."
        )
        _server.wait_for_termination()

    def send(
        self,
        stub: TridentMessageStub,
        sender: str,
        message: TridentMessageRequest,
    ) -> Generator[Tuple[TridentSender, TridentMessageReply], None, None]:
        """Sends out a message to the linked :class:`TridentSender` instances.
        The outgoing communication is handled as defined in the :class:`TridentInterfaceSenderConfig`

        :param stub: The gRPC stub class that contains the message to send
        :type stub: :class:`TridentMessageStub`
        :param sender: The sender method used to send the message
        :type sender: str
        :param message: The message to send
        :type message: :class:`TridentMessageRequest`
        :return: The message reply if a response was produced
        :rtype: Generator[Tuple[TridentSender, TridentMessageReply], None, None]
        """
        for _sender in self.interface_config.senders:
            with grpc.insecure_channel(
                f"{_sender.sender_config.ip}:{_sender.sender_config.port}"
            ) as channel:
                logger.debug(f"Sending message of type {type(message)}")
                stub = stub(channel)
                _response = getattr(stub, sender)(message)
                logger.debug(f"Received response {_response}")
                yield (_sender, _response)
