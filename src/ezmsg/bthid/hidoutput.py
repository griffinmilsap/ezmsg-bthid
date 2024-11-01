import asyncio

import ezmsg.core as ez

from .config import BTHIDConfig
from .device.hid import HIDMessage


class HIDOutputSettings(ez.Settings):
    host: str = BTHIDConfig.DEFAULT_HOST
    port: int = BTHIDConfig.DEFAULT_PORT
    reconnect_timeout: float = 0 # sec; if 0, don't attempt to reconnect


class HIDOutputState(ez.State):
    queue: asyncio.Queue[HIDMessage]
    dead: bool = False


class HIDOutput(ez.Unit):

    SETTINGS = HIDOutputSettings
    STATE = HIDOutputState

    INPUT_HID = ez.InputStream(HIDMessage)

    async def initialize(self) -> None:
        self.STATE.queue = asyncio.Queue()

    @ez.task
    async def handle_connection(self) -> None:

        while True:
            try:
                _, writer = await asyncio.open_connection(
                    host = self.SETTINGS.host, 
                    port = self.SETTINGS.port
                )

            except ConnectionRefusedError:
                if self.SETTINGS.reconnect_timeout:
                    ez.logger.info('Attempting reconnection to ezmsg-bthid daemon...')
                    await asyncio.sleep(self.SETTINGS.reconnect_timeout)
                    continue
                else:
                    ez.logger.info('ezmsg-bthid daemon not reachable')
                    break

            ez.logger.info('Connected to ezmsg-bthid daemon!')

            try:
                while True:
                    msg = await self.STATE.queue.get()
                    msg.write(writer)
                    writer.write(msg.encode())
                    await writer.drain()

            except ConnectionResetError:
                ez.logger.info('Disconnected from ezmsg-bthid daemon')

            finally:
                writer.close()

        self.STATE.dead = True

    @ez.subscriber(INPUT_HID)
    async def write(self, msg: HIDMessage) -> None:
        # Don't needlessly buffer messages that won't ever hit the daemon
        if not self.STATE.dead:
            self.STATE.queue.put_nowait(msg)
