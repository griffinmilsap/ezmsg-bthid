import typing
from .hid import HID

from .keyboard import Keyboard
from .mouse import Mouse


DEVICE_CLASSES: typing.List[type[HID]] = [
    Keyboard,
    Mouse
]

REPORT_DESCRIPTION = b''.join([d.REPORT_DESCRIPTION for d in DEVICE_CLASSES])