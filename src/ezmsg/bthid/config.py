import os
import typing
import asyncio

from configparser import ConfigParser

from pathlib import Path

CONFIG_ENV = 'EZMSG_BTHID_CONFIG'
CONFIG_PATH = Path(os.environ.get(CONFIG_ENV, '/etc/ezmsg-bthid.conf'))


class BTHIDConfig:

    P_CTRL = 0x0011 # Control port
    P_INTR = 0x0013 # Interrupt port

    parser: ConfigParser

    def __init__(self, config_path: typing.Optional[Path] = None):
        if config_path is None:
            config_path = Path('/') / CONFIG_PATH

        config_files = []
        if config_path.exists() and config_path.is_file():
            config_files.append(config_path)
        config_dir = config_path.with_suffix('.d')
        if config_dir.exists() and config_dir.is_dir():
            for fname in config_dir.glob('*'):
                config_files.append(fname)

        self.parser = ConfigParser()
        self.parser.read(config_files)

    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 6789

    @property
    def server_addr(self) -> typing.Tuple[str, int]:
        bt_host = self.parser.get('server', 'host', fallback = BTHIDConfig.DEFAULT_HOST)
        bt_port = int(self.parser.get('server', 'port', fallback = str(BTHIDConfig.DEFAULT_PORT)))
        return bt_host, bt_port
    
    DEFAULT_UUID = "00001124-0000-1000-8000-00805f9b34fb"

    @property
    def bluetooth_uuid(self) -> str:
        return self.parser.get('bluetooth', 'uuid', fallback = BTHIDConfig.DEFAULT_UUID)

    DEFAULT_PROFILE = "/bluez/ezmsg/bthid"
    
    @property
    def bluetooth_profile(self) -> str:
        return self.parser.get('bluetooth', 'profile', fallback = BTHIDConfig.DEFAULT_PROFILE)
    
    DEFAULT_AGENT = "/bluez/ezmsg/agent"

    @property
    def bluetooth_agent(self) -> str:
        return self.parser.get('bluetooth', 'agent', fallback = BTHIDConfig.DEFAULT_AGENT)
    