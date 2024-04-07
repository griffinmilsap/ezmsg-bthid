import socket
import asyncio
import typing
import logging

from pathlib import Path
from importlib.resources import files

from dbus_next.aio.message_bus import MessageBus
from dbus_next.constants import BusType
from dbus_next.signature import Variant
from dbus_next.service import ServiceInterface, method

from .device import REPORT_DESCRIPTION
from .device.hid import read_report

from .config import BTHIDConfig

logger = logging.getLogger(__name__)

handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s.%(msecs)03d - pid: %(process)d - %(threadName)s "
    + "- %(levelname)s - %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class BTHIDAgent(ServiceInterface):
    """ This dbus Service Interface handles replying "yes" to incoming pairing requests """

    @method()
    async def Release(self):
        logger.info("Agent: Release -- Unregistered")

    @method()
    async def RequestPinCode(self, device: 'o') -> 's': # type: ignore
        # Return a PIN code here; '0000' is a placeholder
        pin = "0000"
        logger.info(f"Agent: Pin Code Requested. Providing {pin}")
        return pin

    @method()
    async def DisplayPinCode(self, device: 'o', pincode: 's'): # type: ignore
        logger.info(f"Agent: Pin Code for {device}: {pincode}")

    @method()
    async def RequestPasskey(self, device: 'o') -> 'u': # type: ignore
        passkey = 123456
        logger.info(f"Agent: Passkey Requested. Providing {passkey}")
        return passkey

    @method()
    async def DisplayPasskey(self, device: 'o', passkey: 'u', entered: 'q'): # type: ignore
        logger.info(f"Agent: Passkey for {device}: {passkey}, entered: {entered}")

    @method()
    async def RequestConfirmation(self, device: 'o', passkey: 'u'): # type: ignore
        logger.info(f"Agent: Auto-Confirm passkey for {device}: {passkey} -- YES")
        # Automatically confirm without additional action

    @method()
    async def RequestAuthorization(self, device: 'o'): # type: ignore
        # Automatically authorize without additional action
        logger.info(f"Agent: Authorization requested; Authorizing")

    @method()
    async def AuthorizeService(self, device: 'o', uuid: 's'): # type: ignore
        # Automatically authorize the service without additional action
        logger.info(f"Agent: Service authorization requested; Authorizing")

    @method()
    async def Cancel(self):
        logger.info(f"Agent: Cancelled")


class BTHIDServer:
    """ This is the ezmsg-bthid daemon server.  It:
    * uses dbus to create a bluetooth profile advertising a HID SDP record
    * binds Bluetooth L2CAP HID ports 0x0011 (control) and 0x0013 (interrupt) (which requires root)
    * exposes the interrupt ports on a tcp port that local (or even remote) clients can connect to
    * handles incoming pairing requests with a bluez agent via dbus
    * TODO: makes the bluetooth adapter discoverable?
    """

    loop: asyncio.AbstractEventLoop
    hid_clients: typing.Dict[asyncio.Task, asyncio.Queue[bytes]]
    tcp_server: asyncio.Task
    config: BTHIDConfig

    def __init__(self, config: BTHIDConfig, loop: asyncio.AbstractEventLoop) -> None:
        """ Don't use this constructor to create a server; instead use BTHIDServer.start """
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
        logger.info(f'ezmsg-bthid daemon listening on {host}:{port}/tcp')
        return hid_server

    async def handle_tcp_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """ This is where tcp client reports are received and queued for forwarding to bluetooth interrupt """
        try:
            while True:
                data = await read_report(reader)
                if not data: break
                for queue in self.hid_clients.values():
                    queue.put_nowait(data)
        finally:
            writer.close()
    
    async def serve_forever(self) -> None:

        # Use dbus to create the HID bluetooth profile / SDP record
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
            {
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

        # Make sure adapter is discoverable and pairable forever
        # await adapter_property.call_set("org.bluez.Adapter1", "Powered", Variant('b', True)) # type: ignore
        await adapter_property.call_set("org.bluez.Adapter1", "DiscoverableTimeout", Variant('u', 0)) # type: ignore
        await adapter_property.call_set("org.bluez.Adapter1", "PairableTimeout", Variant('u', 0)) # type: ignore
        await adapter_property.call_set("org.bluez.Adapter1", "Pairable", Variant('b', True)) # type: ignore
        await adapter_property.call_set("org.bluez.Adapter1", "Discoverable", Variant('b', True)) # type: ignore

        # Register a dbus agent to handle automatic pairing
        agent = BTHIDAgent('org.bluez.Agent1')
        bus.export(self.config.bluetooth_agent, agent)

        introspection = await bus.introspect("org.bluez", "/org/bluez")
        bluez = bus.get_proxy_object("org.bluez", "/org/bluez", introspection)
        agent_manager = bluez.get_interface("org.bluez.AgentManager1")
        
        # We must tell dbus that we can confirm to pair
        await agent_manager.call_register_agent(self.config.bluetooth_agent, 'DisplayYesNo') # type: ignore
        await agent_manager.call_request_default_agent(self.config.bluetooth_agent) # type: ignore

        logger.info(f'Pairing Agent {self.config.bluetooth_agent}: Registered')

        # Bind and handle bluetooth HID ports
        async def handle_control_port(conn: socket.socket, _: typing.Tuple[str, int]) -> None:
            """ Not sure what the control port is for; we just keep it alive for now """
            try:
                while True:
                    data = await self.loop.sock_recv(conn, 1024)
                    if not data: break
            finally:
                conn.close()

        async def handle_interrupt_port(conn: socket.socket, info: typing.Tuple[str, int]) -> None:
            """ Interrupt port is where we send reports """
            queue: asyncio.Queue[bytes] = asyncio.Queue()
            client_task = self.loop.create_task(self.handle_hid_client(conn, queue, info))
            client_task.add_done_callback(self.hid_clients.pop)
            self.hid_clients[client_task] = queue

        control_task = self.loop.create_task(
            serve_l2cap_socket(
                handle_control_port, 
                address.value, 
                self.config.P_CTRL, 
                loop = self.loop
            )
        )

        interrupt_task = self.loop.create_task(
            serve_l2cap_socket(
                handle_interrupt_port, 
                address.value, 
                self.config.P_INTR, 
                loop = self.loop
            )
        )

        await bus.wait_for_disconnect()

    async def handle_hid_client(self, 
        interrupt: socket.socket, 
        queue: asyncio.Queue[bytes],
        info: typing.Tuple[str, int]
    ) -> None:
        """ This is where we handle connections with new devices that connect via bluetooth """
        logger.info(f'Bluetooth client connected: {info=}')
        try:
            while True:
                packet = await queue.get()
                await self.loop.sock_sendall(interrupt, packet)
        except ConnectionResetError:
            pass
        finally:
            interrupt.close()
    

ConnectionCallbackType = typing.Callable[[socket.socket,typing.Tuple[str, int]], typing.Coroutine[None, None, None]]

async def serve_l2cap_socket(
    callback: ConnectionCallbackType, 
    address: str, 
    port: int, 
    loop: typing.Optional[asyncio.AbstractEventLoop] = None
) -> None:
    """ Spiritual equivalent of asyncio.start_server for L2CAP HID sockets.
    asyncio.start_server isn't currently compatible with socket.SOCK_SEQPACKET sockets 
    """

    if loop is None:
        loop = asyncio.get_running_loop()

    sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP) # type: ignore
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((address, port))
    sock.listen(1)
    sock.setblocking(False)

    # If all references to a task are lost, the task may be cancelled at any time
    # so we hold onto all of the references until the task is done.
    all_connection_tasks = set()
    while True:
        conn, info = await loop.sock_accept(sock)
        task = loop.create_task(callback(conn, info))
        task.add_done_callback(all_connection_tasks.remove)
        all_connection_tasks.add(task)

