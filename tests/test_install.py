import tempfile

from pathlib import Path

import pytest

from ezmsg.bthid.install import (
    install, 
    uninstall,
    _SERVICE_DIR,
    _CONFIG_DIR
)

def test_install():

    with tempfile.TemporaryDirectory() as fp:
        root = Path(fp)

        # Set up the relevant parts of this test filesystem
        _CONFIG_DIR(root).mkdir(parents = True, exist_ok = False)
        _SERVICE_DIR(root).mkdir(parents = True, exist_ok = False)

        install(root, yes = True, test = True)

        # TODO: Actually check the temp file system

        uninstall(root, yes = True, test = True)

        # TODO: Actually check the temp file system is EMPTY

if __name__ == '__main__':
    test_install()