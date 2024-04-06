import asyncio

import ezmsg.core as ez

from .config import BTHIDConfig
from .device.hid import HIDMessage


class HIDOutputSettings(ez.Settings):
    host: str = BTHIDConfig.DEFAULT_HOST
    port: int = BTHIDConfig.DEFAULT_PORT


class HIDOutputState(ez.State):
    queue: asyncio.Queue[HIDMessage]


class HIDOutput(ez.Unit):

    SETTINGS: HIDOutputSettings
    STATE: HIDOutputState

    INPUT_HID = ez.InputStream(HIDMessage)

    async def initialize(self) -> None:
        self.STATE.queue = asyncio.Queue()

    @ez.task
    async def handle_connection(self) -> None:

        while True:
            try:
                ez.logger.info('(Re)Connecting to ezmsg-bthid daemon...')
                _, writer = await asyncio.open_connection(
                    host = self.SETTINGS.host, 
                    port = self.SETTINGS.port
                )

            except ConnectionRefusedError:
                ez.logger.info('ezmsg-bthid daemon not running?')
                await asyncio.sleep(5.0) # Wait a bit before trying to reconnect
                continue

            ez.logger.info('Connected to ezmsg-bthid daemon!')

            try:
                while True:
                    msg = await self.STATE.queue.get()
                    msg.write(writer)
                    await writer.drain()

            except ConnectionResetError:
                ez.logger.info('Disconnected from ezmsg-bthid daemon')

            finally:
                writer.close()

    @ez.subscriber(INPUT_HID)
    async def write(self, msg: HIDMessage) -> None:
        self.STATE.queue.put_nowait(msg)
