import tempfile
from pathlib import Path
from importlib.resources import files

import pytest

from ezmsg.bthid.config import BTHIDConfig

def test_config() -> None:
    config_text = files('ezmsg.bthid').joinpath('ezmsg-bthid.conf').read_text()
    extra = 'extra'
    with tempfile.TemporaryDirectory() as tmpdir:
        with tempfile.NamedTemporaryFile('w+', dir = tmpdir, suffix = '.conf') as temp_config:
            temp_config.write(config_text)
            temp_config.flush()
            conf_dir = Path(temp_config.name).with_suffix('.d')
            conf_dir.mkdir()
            with tempfile.NamedTemporaryFile('w+', dir = conf_dir) as errata_f:
                errata_f.write(f'[{extra}]')
                errata_f.flush()
                config = BTHIDConfig(Path(temp_config.name))
        
    assert config.bluetooth_uuid == BTHIDConfig.DEFAULT_UUID
    assert config.server_addr == (BTHIDConfig.DEFAULT_HOST, BTHIDConfig.DEFAULT_PORT)

if __name__ == '__main__':
    test_config()