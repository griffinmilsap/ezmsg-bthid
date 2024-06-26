import typing
from .hid import HID, HIDMessage

from .keyboard import Keyboard
from .mouse import Mouse
from .touch import Touch


DEVICE_CLASSES: typing.List[type[HID]] = [
    Keyboard,
    Mouse,
    Touch
]

REPORT_DESCRIPTION = b''.join([d.REPORT_DESCRIPTION for d in DEVICE_CLASSES])