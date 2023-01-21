import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from trident.lib.interface.messages import DaemonConnect
from trident.lib.interface.proto.connect_pb2 import (
    DaemonConnectRequest,
    DaemonConnectReply,
)
from trident.lib.interface.proto.connect_pb2_grpc import (
    add_DaemonConnectServicer_to_server,
    DaemonConnectStub,
)

from typing import NewType

TridentMessageStub = NewType("TridentMessageStub", DaemonConnectStub)
TridentMessageRequest = NewType("TridentMessageRequest", DaemonConnectRequest)
TridentMessageReply = NewType("TridentMessageReply", DaemonConnectReply)

MESSAGES = {DaemonConnect: add_DaemonConnectServicer_to_server}
