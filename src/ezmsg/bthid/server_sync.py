import socket
import typing
import logging
import threading

from queue import Queue
from pathlib import Path
from importlib.resources import files

from dbus_next.aio import MessageBus
from dbus_next.constants import BusType
from dbus_next.signature import Variant
from dbus_next.service import ServiceInterface, method

from .device import REPORT_DESCRIPTION
from .device.hid import decode_report

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
    def Release(self):
        logger.info("Agent: Release -- Unregistered")

    @method()
    def RequestPinCode(self, device: 'o') -> 's':
        pin = "0000"
        logger.info(f"Agent: Pin Code Requested. Providing {pin}")
        return pin

    @method()
    def DisplayPinCode(self, device: 'o', pincode: 's'):
        logger.info(f"Agent: Pin Code for {device}: {pincode}")

    @method()
    def RequestPasskey(self, device: 'o') -> 'u':
        passkey = 123456
        logger.info(f"Agent: Passkey Requested. Providing {passkey}")
        return passkey

    @method()
    def DisplayPasskey(self, device: 'o', passkey: 'u', entered: 'q'):
        logger.info(f"Agent: Passkey for {device}: {passkey}, entered: {entered}")

    @method()
    def RequestConfirmation(self, device: 'o', passkey: 'u'):
        logger.info(f"Agent: Auto-Confirm passkey for {device}: {passkey} -- YES")

    @method()
    def RequestAuthorization(self, device: 'o'):
        logger.info(f"Agent: Authorization requested; Authorizing")

    @method()
    def AuthorizeService(self, device: 'o', uuid: 's'):
        logger.info(f"Agent: Service authorization requested; Authorizing")

    @method()
    def Cancel(self):
        logger.info(f"Agent: Cancelled")


class BTHIDServer:
    hid_clients_lock: threading.Lock
    hid_clients: typing.Dict[socket.socket, Queue[bytes]]
    config: BTHIDConfig
    
    def __init__(self, config_path: typing.Optional[Path] = None):
        self.hid_clients_lock = threading.Lock()
        self.hid_clients = {}
        self.config = BTHIDConfig(config_path)

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
        
        # Bind Bluetooth HID ports
        control_thread = threading.Thread(
            target=self.serve_l2cap_socket, 
            args=(self.handle_control_port, address.value, self.config.P_CTRL)
        )
        interrupt_thread = threading.Thread(
            target=self.serve_l2cap_socket, 
            args=(self.handle_interrupt_port, address.value, self.config.P_INTR)
        )

        control_thread.start()
        interrupt_thread.start()

        host, port = self.config.server_addr
        tcp_server_socket = socket.create_server((host, port))
        tcp_server_socket.listen()

        tcp_server_thread = threading.Thread(
            target = self.accept_tcp_clients,
            args = (tcp_server_socket,)
        )
        tcp_server_thread.start()
        logger.info(f'ezmsg-bthid daemon listening on {host}:{port}/tcp')

        await bus.wait_for_disconnect()

    def accept_tcp_clients(self, tcp_server_socket: socket.socket) -> None:
        # Listen for TCP connections
        tcp_clients = []
        while True:
            conn, addr = tcp_server_socket.accept()
            tcp_client_thread = threading.Thread(target = self.handle_tcp_client, args = (conn, addr))
            tcp_clients.append(tcp_client_thread)
            tcp_client_thread.start()

    def handle_tcp_client(self, conn: socket.socket, addr: typing.Tuple[str, int]) -> None:
        """ Handle TCP client connections """
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                data = decode_report(data)
                with self.hid_clients_lock:
                    for queue in self.hid_clients.values():
                        queue.put_nowait(data)
        finally:
            conn.close()

    def serve_l2cap_socket(self, callback, address, port):
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((address, port))
        sock.listen(1)

        threads = typing.List[threading.Thread]

        while True:
            conn, info = sock.accept()
            handler = threading.Thread(target = callback, args = (conn, info))
            threads.append(handler)
            handler.start()

    def handle_control_port(self, conn: socket.socket, info: typing.Tuple[str, int]) -> None:
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
        finally:
            conn.close()

    def handle_interrupt_port(self, conn: socket.socket, info: typing.Tuple[str, int]) -> None:
        incoming = Queue()
        with self.hid_clients_lock:
            self.hid_clients[conn] = incoming
        try:
            while True:
                packet = incoming.get()
                conn.sendall(packet)
        except ConnectionResetError:
            pass
        finally:
            with self.hid_clients_lock:
                del self.hid_clients[conn]
            conn.close()