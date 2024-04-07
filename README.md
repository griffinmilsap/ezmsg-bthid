# ezmsg-bthid
__Griffin Milsap 2024__  

Virtual Bluetooth HID device outputs for `ezmsg`!

* _Modernized Bluetooth dbus implementation from [msm](https://tailcall.net/posts/bluetooth-keyboard/#fnref:1)_
* _Digitizer HID descriptor from [Elmue at Codeproject](https://www.codeproject.com/Articles/1001891/A-USB-HID-Keyboard-Mouse-Touchscreen-emulator-with)_

# Purpose
Sometimes we want the capability to control other devices from an `ezmsg` system, and this module primarily exists to serve that purpose.  Installing this module onto a Linux machine (Raspberry Pi) enables us to control virtual pointer and keyboards attached to any device via Bluetooth with `ezmsg`.  It does this by using creating a Bluetooth HID profile/server and provides HID (Human Interface Device) compliant device descriptors.

The current implementation comes with the following HID device descriptors that you can use to inject events on client devices:
* 2-button + scroll wheel relative-movement pointer (aka. a mouse)
* Standard un-localized keyboard with numpad
* Absolute-positioning pointer (touch screen/digitizer)

The meat of this module is the server daemon that binds the Bluetooth HID ports (as root) and forwards the interrupt port to a configurable tcp port that unpriveliged users can connect to and send reports to.  This port can even be exposed to other clients on the network -- for example, if you wanted to run this on a Raspberry Pi ZeroW and forward Bluetooth HID traffic from other clients on the same network.

Once the server is up and running, `ezmsg-bthid` provides an `HIDOutput` unit that connects to the daemon and a set of HID message dataclasses that create properly formatted reports for the connected Bluetooth clients, based on the advertised descriptors.

``` python

import asyncio

import ezmsg.core as ez

from ezmsg.bthid.hidoutput import HIDOutput, HIDOutputSettings
from ezmsg.bthid.device import Keyboard

class KeypressGenerator(ez.Unit):

    OUTPUT_HID = ez.OutputStream(Keyboard.Message)

    @ez.publisher(OUTPUT_HID)
    async def pub_keypress(self):
        while True:
            await asyncio.sleep(1.0)
            yield (
                self.OUTPUT_HID, 
                Keyboard.Message(
                    key1 = Keyboard.KEYCODE_NUMBER_1 # Keydown
                )
            )

            yield (
                self.OUTPUT_HID, 
                Keyboard.Message(
                    key1 = Keyboard.KEYCODE_NONE # Keyup
                )
            )

generator = KeypressGenerator()

hid_output = HIDOutput(
    HIDOutputSettings(
        host = 'localhost',
        port = 6789
    )
)

ez.run(
    GENERATOR = generator,
    HID_OUTPUT = hid_output,
    connections = (
        (generator.OUTPUT_HID, hid_output.INPUT_HID),
    )
)

```

## Requirements
* A Linux system with BlueZ ^5.0 (Raspberry Pi works really well!)

## Dependencies
* Python 3.9+
* dbus-next

## Installation

1. Make sure you disable the Bluetooth input plugin.  To do that, edit `/lib/systemd/system/bluetooth.service` as superuser and change the ExecStart line to disable the `input` plugin:
    ```
    #ExecStart=/usr/libexec/bluetooth/bluetoothd
    ExecStart=/usr/libexec/bluetooth/bluetoothd -P input
    ```
    Then reload the systemctl daemon to apply the change to the service file and restart the bluetooth daemon
    ```
    sudo systemctl daemon-reload
    sudo systemctl restart bluetooth.service
    ```
2. Run the following commands:
    ```
    $ sudo su
    # python -m venv /opt/ezmsg-bthid
    # source /opt/ezmsg-bthid/bin/activate
    (ezmsg-bthid) # pip install --upgrade pip
    (ezmsg-bthid) # pip install git+https://github.com/griffinmilsap/ezmsg-bthid.git
    (ezmsg-bthid) # ezmsg-bthid install -y
    # reboot
    ```
    
    Note that in the script above, ezmsg-bthid is installed to a special virtual environment in `/opt`.  This is because `ezmsg-bthid serve` must be executed as `root`, and the `systemd` service files that the installer places involve running code from `ezmsg-bthid` _as root during boot_. Running services as root (especially ones that handle ports) comes with a host of caveats and cautions.  _The server could use a good review before deploying this module in production environments._

## Uninstall
Assuming the module was installed in the virtual environment in `/opt` as described above, this should do the trick:
```
sudo /opt/ezmsg-bthid/bin/ezmsg-bthid uninstall
```
Additionally: 
* Revert the changes to `/lib/systemd/system/bluetooth.service` and reload the systemctl daemon and restart `bluetooth.service`
* Delete the virtual environment: `rm -rf /opt/ezmsg-bthid`

# Pairing
You will need to pair your client device with the ezmsg-bthid server before you can successfully control the client with virtual HID instruments.  The ezmsg-bthid server comes with a pairing agent that should simplify this process, but on the off chance it doesn't work as advertised, the following instructions may help you troubleshoot

* Make sure the `ezmsg-bthid` daemon service is up and running.  You can check with`sudo systemctl status ezmsg-bthid.service`. It turns out most clients only check what the server's capabilities are once on pairing, if you make changes to the server, you'll need to forget the device and re-pair

### Manual Pairing
This shouldn't really be necessary, because the ezmsg-bthid daemon manages its own pairing agent and ensures the device is discoverable, but on the off-chance the bluez dbus API changes again, here's how you can manually pair a client device with the server.
1. Run `bluetoothctl` on the same machine that your service is running on and enter the following commands which will cause your Bluetooth adapter to be discoverable under the device's hostname for 3 minutes:  
    `default-agent`  
    `discoverable on`
2. On your client device, pair a new Bluetooth device during the discoverable period.  Again, the device should show up with the hostname of your server as the Bluetooth device name.
3. Accept pairing information on the client side __and__ on the server side at roughly the same time by typing `yes` in the `bluetoothctl` session once the pairing request comes up
4. `exit` out of `bluetoothctl`; as long as its up, it'll ask you to re-pair the client device every time it connects.

## Test HID capabilities
The `ezmsg-bthid` module comes with a few built-in examples that make it easy to test out the Bluetooth connection.  These examples should also be enlightening and demonstrate how to send properly formatted reports to the server.
* `python -m ezmsg.bthid.examples.rel_mouse` should move client cursor around in circles
* `python -m ezmsg.bthid.examples.type_message` should type messages on the client device
* `python -m ezmsg.bthid.examples.absolute_pointer` should send absolute mouse-move messages to fling the cursor around your screen in a preset spiral pattern

# Usage

```
$ ezmsg-bthid -h
usage: ezmsg-bthid [-h] [--config CONFIG] [--yes]
                   {serve,install,uninstall}

ezmsg-bthid command line

positional arguments:
  {serve,install,uninstall}

options:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        config file for ezmsg-bthid settings. default:
                        /etc/ezmsg-bthid.conf
  --yes, -y             yes to all questions for interactive
                        install/uninstall
```         

# Configuration
The configuration of this module can be done using `/etc/ezmsg-bthid.conf` which has the following format.  Most likely, the only settings you'll want to change in this file are the `[server]` `host` and `port` to meet your needs. 
``` ini
# configuration for ezmsg-bthid daemon

[server]
# Server binds Bluetooth HID ports as root and exposes the interrupt port on tcp
# host = localhost
# port = 6789 # tcp

[bluetooth]
# Probably shouldn't mess with this UUID
# https://www.bluetooth.com/specifications/assigned-numbers/service-discovery
# At the very least, the first 4 octets should remain 00001124
# uuid = 00001124-0000-1000-8000-00805f9b34fb

# Also probably never need to mess with these
# profile = /bluez/ezmsg/bthid
# agent = /bluez/ezmsg/agent

# any files in an associated *.d directory will also be loaded

```