import os
import typing
import asyncio

from pathlib import Path

from .server import BTHIDServer
from .server_sync import BTHIDServer as BTHIDServerSync
from .config import CONFIG_PATH
from .install import install, uninstall

class Args:
    command: str
    config: typing.Optional[Path]
    yes: bool

async def serve(args: type[Args]) -> None:
    assert os.geteuid() == 0, "This won't work without root"
    server = await BTHIDServer.start(args.config)
    await server.serve_forever()

async def serve_sync(args: type[Args]) -> None:
    assert os.geteuid() == 0, "This won't work without root"
    server = BTHIDServerSync(args.config)
    await server.serve_forever()

def cmdline() -> None:

    import argparse 

    parser = argparse.ArgumentParser(description = 'ezmsg-bthid command line')

    parser.add_argument(
        'command',
        choices = ['serve', 'install', 'uninstall', 'serve_sync']
    )

    parser.add_argument(
        '--config', '-c',
        type = lambda x: Path(x),
        default = None,
        help = f'config file for ezmsg-bthid settings. default: {CONFIG_PATH}',
    )

    parser.add_argument(
        '--yes', '-y',
        action = 'store_true',
        help = 'yes to all questions for interactive install/uninstall'
    )

    args = parser.parse_args(namespace = Args)
    
    if args.command == 'serve':
        asyncio.run(serve(args))
    elif args.command == 'serve_sync':
        asyncio.run(serve_sync(args))
    elif args.command == 'install':
        install(yes = args.yes)
    elif args.command == 'uninstall':
        uninstall(yes = args.yes)
    else:
        raise ValueError('Unknown Command')

if __name__ == "__main__":
    cmdline()
