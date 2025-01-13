import logging
import socket
import struct

from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError

from . import TimesliceError

class CameraServer(TCPServer):

    def __init__(self, controller, port, address, *args, **kwargs):

        self.controller = controller
        self.port = port
        self.address = address
        self.connection_id = 0

        self.header_format = "<L"
        self.header_size = struct.calcsize(self.header_format)

        super().__init__(*args, **kwargs)

    def listen(self):

        super().listen(self.port, self.address)
        logging.info(f"Camera server listening on {self.address}:{self.port}")

    async def handle_stream(self, stream, address):

        addr_str = f"{address[0]}:{address[1]}"

        id = self.connection_id
        self.connection_id += 1

        logging.debug(f"New connection {id} from {addr_str}")

        stream.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        stream.socket.setsockopt(socket.IPPROTO_TCP, socket.SO_KEEPALIVE, 1)

        while True:
            try:
                header = await stream.read_bytes(self.header_size)
                data_size = struct.unpack(self.header_format, header)[0]

                data = await stream.read_bytes(data_size)
                logging.debug(f"Connection {id} {addr_str} received: {data_size} bytes")

                self.controller.process_camera_response(data)

            except StreamClosedError:
                logging.debug(f"Connection {id} {addr_str} closed")
                break
            except Exception as e:
                raise TimesliceError(e)

