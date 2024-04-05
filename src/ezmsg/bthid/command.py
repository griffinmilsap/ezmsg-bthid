import os
import typing
import asyncio

from pathlib import Path

from .server import BTHIDServer
from .config import CONFIG_PATH

class Args:
    command: str
    config: typing.Optional[Path]

async def serve(args: type[Args]) -> None:
    assert os.geteuid() == 0, "This won't work without root"
    server = await BTHIDServer.start(args.config)
    await server.serve_forever()

def cmdline() -> None:

    import argparse 

    parser = argparse.ArgumentParser(description = 'ezmsg-bthid command line')

    parser.add_argument(
        'command',
        choices = ['serve', 'install', 'uninstall']
    )

    parser.add_argument(
        '--config', '-c',
        type = lambda x: Path(x),
        default = None,
        help = f'config file for ezmsg-bthid settings. default: {CONFIG_PATH}',
    )

    args = parser.parse_args(namespace = Args)
    
    if args.command == 'serve':
        asyncio.run(serve(args))
    else:
        raise ValueError('Unknown Command')

if __name__ == "__main__":
    cmdline()
