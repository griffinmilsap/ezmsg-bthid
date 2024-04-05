import os
import socket
import asyncio
import typing

from pathlib import Path
from importlib.resources import files

from dbus_next.aio.message_bus import MessageBus
from dbus_next.constants import BusType
from dbus_next.signature import Variant

from .device import REPORT_DESCRIPTION
from .device.hid import read_report

from .config import BTHIDConfig, CONFIG_PATH


class BTHIDServer:

    loop: asyncio.AbstractEventLoop
    hid_clients: typing.Dict[asyncio.Task, asyncio.Queue[bytes]]
    tcp_server: asyncio.Task
    config: BTHIDConfig

    def __init__(self, config: BTHIDConfig, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        self.hid_clients = {}
        self.config = config

    @classmethod
    async def start(cls, config_path: typing.Optional[Path] = None, loop: typing.Optional[asyncio.AbstractEventLoop] = None) -> "BTHIDServer":

        config = BTHIDConfig(config_path)

        if loop is None:
            loop = asyncio.get_running_loop()

        hid_server = cls(config, loop = loop)
        host, port = config.server_addr
        server = await asyncio.start_server(hid_server.handle_tcp_client, host = host, port = port)
        hid_server.tcp_server = loop.create_task(server.serve_forever(), name = 'bthid_tcp_server')
        return hid_server

    async def handle_tcp_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            while True:
                data = await read_report(reader)
                if not data: break
                for queue in self.hid_clients.values():
                    queue.put_nowait(data)
        finally:
            writer.close()
    
    async def serve_forever(self) -> None:

        bus = await MessageBus(
            bus_type = BusType.SYSTEM,
            negotiate_unix_fd = True,
        ).connect()

        data_files = files('ezmsg.bthid')

        service_record = data_files.joinpath('sdp.xml').read_text()
        service_record = service_record.replace('$REPORT_DESC', REPORT_DESCRIPTION.hex().upper())

        introspection = await bus.introspect("org.bluez", "/org/bluez")
        bluez = bus.get_proxy_object("org.bluez", "/org/bluez", introspection)
        manager = bluez.get_interface("org.bluez.ProfileManager1")
        await manager.call_register_profile( # type: ignore
            self.config.bluetooth_profile, 
            self.config.bluetooth_uuid, 
            opts = {
                "Role": Variant('s', "server"),
                "RequireAuthentication": Variant('b', False),
                "RequireAuthorization": Variant('b', False),
                "AutoConnect": Variant('b', True),
                "ServiceRecord": Variant('s', service_record),
            }
        ) 

        introspection = await bus.introspect("org.bluez", "/org/bluez/hci0")
        hci0 = bus.get_proxy_object("org.bluez", "/org/bluez/hci0", introspection)
        adapter_property = hci0.get_interface("org.freedesktop.DBus.Properties")

        address = await adapter_property.call_get("org.bluez.Adapter1", "Address") # type: ignore

        async def handle_control_port(conn: socket.socket, _: typing.Tuple[str, int]) -> None:
            """ Not sure what the control port is for; we just keep it alive for now """
            try:
                while True:
                    data = await self.loop.sock_recv(conn, 1024)
                    if not data: break
            finally:
                conn.close()

        async def handle_interrupt_port(conn: socket.socket, info: typing.Tuple[str, int]) -> None:
            queue: asyncio.Queue[bytes] = asyncio.Queue()
            client_task = self.loop.create_task(self.handle_hid_client(conn, queue, info))
            client_task.add_done_callback(self.hid_clients.pop)
            self.hid_clients[client_task] = queue

        await asyncio.gather(
            serve_l2cap_socket(handle_control_port, address.value, self.config.P_CTRL, loop = self.loop),
            serve_l2cap_socket(handle_interrupt_port, address.value, self.config.P_INTR, loop = self.loop),
            return_exceptions = True
        )

    async def handle_hid_client(self, 
        interrupt: socket.socket, 
        queue: asyncio.Queue[bytes],
        info: typing.Tuple[str, int]
    ) -> None:
        print(f'Bluetooth client connected: {info=}')
        try:
            while True:
                packet = await queue.get()
                await self.loop.sock_sendall(interrupt, packet)
        except ConnectionResetError:
            pass
        finally:
            print(f'Bluetooth client disonnected: {info=}')
            interrupt.close()

ConnectionCallbackType = typing.Callable[[socket.socket,typing.Tuple[str, int]], typing.Coroutine[None, None, None],]

async def serve_l2cap_socket(
    callback: ConnectionCallbackType, 
    address: str, 
    port: int, 
    loop: typing.Optional[asyncio.AbstractEventLoop] = None
) -> None:

    if loop is None:
        loop = asyncio.get_running_loop()

    sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP) # type: ignore
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((address, port))
    sock.listen(1)
    sock.setblocking(False)

    all_connection_tasks = set()
    while True:
        conn, info = await loop.sock_accept(sock)
        task = loop.create_task(callback(conn, info))
        task.add_done_callback(all_connection_tasks.remove)
        all_connection_tasks.add(task)

