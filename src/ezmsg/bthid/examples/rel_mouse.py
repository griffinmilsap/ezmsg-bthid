import math
import time
import typing
import asyncio

from pathlib import Path

from ..device import Mouse
from ..config import BTHIDConfig, CONFIG_PATH

# This example shows how to send messages to the device without invoking ezmsg

class Args:
    config: typing.Optional[Path]
    gain: float = 5e-2
    rate: float = 50.0

async def rel_mouse(args: type[Args]) -> None:

    writer = await BTHIDConfig(args.config).connect()

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
        '--config', '-c',
        type = lambda x: Path(x),
        default = None,
        help = f'config file for ezmsg-bthid settings. default: {CONFIG_PATH}'
    )

    parser.add_argument(
        '--gain', '-g',
        type = float,
        default = 5e-2,
        help = 'magnitude of mouse movements',
    )

    parser.add_argument(
        '--rate', '-r',
        type = float,
        default = 50.0,
        help = 'hid report rate',
    )

    args = parser.parse_args(namespace = Args)

    asyncio.run(rel_mouse(args))