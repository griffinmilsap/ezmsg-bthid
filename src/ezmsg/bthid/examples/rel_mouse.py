import math
import time
import asyncio

from ..device import Mouse
from ..config import BTHIDConfig

# This example shows how to send messages to the device without invoking ezmsg

class Args:
    host: str
    port: int
    gain: float
    rate: float

async def rel_mouse(args: type[Args]) -> None:

    _, writer = await asyncio.open_connection(args.host, args.port)

    try:
        while True:
            await asyncio.sleep(1.0 / args.rate)
            Mouse.Message(
                rel_y = math.sin(time.time()) * args.gain,
                rel_x = math.cos(time.time()) * args.gain,
            ).write(writer)
            await writer.drain()

    finally:
        writer.close()

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description = 'relative cursor movement example')

    parser.add_argument(
        '--host',
        type = str,
        default = BTHIDConfig.DEFAULT_HOST,
        help = f'hostname for ezmsg-bthid daemon. default: {BTHIDConfig.DEFAULT_HOST}'
    )

    parser.add_argument(
        '--port',
        type = int,
        default = BTHIDConfig.DEFAULT_PORT,
        help = f'port for ezmsg-bthid daemon. default: {BTHIDConfig.DEFAULT_PORT}'
    )

    parser.add_argument(
        '--gain',
        type = float,
        default = 5e-2,
        help = 'magnitude of mouse movements',
    )

    parser.add_argument(
        '--rate',
        type = float,
        default = 50.0,
        help = 'hid report rate',
    )

    args = parser.parse_args(namespace = Args)

    asyncio.run(rel_mouse(args))