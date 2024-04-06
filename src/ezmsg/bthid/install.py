
import sys
import typing

from subprocess import Popen, PIPE
from pathlib import Path
from importlib.resources import files

def _confirm_prompt(question: str, yes: bool = False) -> bool:
    reply = None if not yes else ""
    while reply not in ("", "y", "n"):
        reply = input(f"{question} (Y/n): ").lower()
    response = (reply in ("", "y"))
    if response:
        print(f'ACTION: {question}')
    return response

def _run_command(cmd: str, test_result: typing.Optional[bytes] = None) -> bytes:
    if test_result is None:
        process = Popen(cmd, stdout = PIPE, stderr = PIPE, shell = True)
        stdout, stderr = process.communicate()
        if stderr: print(stderr.strip())
        return stdout.strip()
    else:
        print(f'TEST -- NOT Running "{cmd}", assuming result: {test_result}')
        return test_result

_CONFIG_DIR = lambda root: root / 'etc'
_SERVICE_DIR = lambda root: root / Path('lib/systemd/system')

CONFIG_FILE = 'ezmsg-bthid.conf'
BOOT_SERVICE_FILE = 'ezmsg-bthid.service'

def install(
        root: Path = Path('/'), 
        yes: bool = False,
        test: bool = False
    ) -> None:

    data_files = files('ezmsg.bthid')

    # ADD CONFIG FILE
    config_dir = _CONFIG_DIR(root)
    if _confirm_prompt(f'Add {CONFIG_FILE} to {config_dir}', yes):
        with open(config_dir / CONFIG_FILE, 'w') as config_f:
            config_f.write(data_files.joinpath(CONFIG_FILE).read_text())
    
    # ADD BOOT SERVICE
    service_dir = _SERVICE_DIR(root)

    print('Boot service: start ezmsg-bthid daemon on boot')
    print('Why? The ezmsg-bthid daemon requires root, so do it on boot automatically')
    if _confirm_prompt(f'Write {BOOT_SERVICE_FILE} to {service_dir}', yes):
        with open(service_dir / BOOT_SERVICE_FILE, 'w') as f:
            boot_service_text = data_files.joinpath(BOOT_SERVICE_FILE).read_text()
            boot_service_text = boot_service_text.replace('python', sys.executable)
            f.write(boot_service_text)
        if _confirm_prompt('Issue "systemctl daemon-reload"', yes):
            _run_command('systemctl daemon-reload', test_result = b'' if test else None)

    # ENABLE BOOT SERVICE
    print('Checking if boot service is enabled...')
    boot_service_result = _run_command(
        f'systemctl is-enabled {BOOT_SERVICE_FILE}', 
        test_result = b'enabled' if test else None
    )
    print(f'Boot service status: {boot_service_result}')

    # CHECK IF BOOT SERVICE ENABLED
    if boot_service_result == b'enabled':
        print('Boot service enabled')
    elif boot_service_result == b'disabled':
        if _confirm_prompt(f'Enable {BOOT_SERVICE_FILE}', yes):
            _run_command(
                f'systemctl enable {BOOT_SERVICE_FILE}', 
                test_result = b'' if test else None
            )
    else:
        print('Boot service not installed or enabled')

    print("Install completed.  Reboot encouraged.")

def uninstall(root: Path = Path('/'), yes: bool = False, test: bool = False) -> None:

    # STOP/DISABLE SERVICES
    service_dir = _SERVICE_DIR(root)

    services: typing.List[Path] = [
        service_dir / BOOT_SERVICE_FILE,
    ]

    daemon_reload = False
    for service in services:
        if service.exists():
            if _confirm_prompt(f'Stop {service.name}', yes):
                _run_command(
                    f'systemctl stop {service.name}', 
                    test_result = b'' if test else None
                )

            service_enabled_result = _run_command(
                f'systemctl is-enabled {service.name}', 
                test_result = b'enabled' if test else None
            )

            if service_enabled_result == b'enabled' and _confirm_prompt(f'Disable {service.name}', yes):
                _run_command(
                    f'systemctl disable {service.name}', 
                    test_result = b'' if test else None
                )

            if _confirm_prompt(f'Remove {service}', yes):
                service.unlink()
                daemon_reload = True

    if daemon_reload and _confirm_prompt('Issue "systemctl daemon-reload"', yes):
        _run_command('systemctl daemon-reload', test_result = b'' if test else None)

    config_dir: Path = _CONFIG_DIR(root)

    # REMOVE ALL OTHER INSTALLED FILES
    files = services + [
        config_dir / CONFIG_FILE,
    ]

    for f in files:
        if f.exists() and _confirm_prompt(f'Remove {f}', yes):
            f.unlink()

    print("Uninstall completed.  Reboot encouraged.")