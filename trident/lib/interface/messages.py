#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Trident: Interface Message

Message formats used for communication between :class:`TridentInterface` instances.
@author: Jacob Wahlman
"""

from trident.lib.interface.proto.connect_pb2 import DaemonConnectReply
from trident.lib.interface.proto.connect_pb2_grpc import DaemonConnectServicer


class DaemonConnect(DaemonConnectServicer):
    def Connect(self, request, context):
        print(type(request), type(context))
        return DaemonConnectReply(name="Test")
