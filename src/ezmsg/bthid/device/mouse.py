import typing

from dataclasses import dataclass

from ..util import float_to_signed_bytes
from .hid import HID, HIDMessage

# This report ID cannot conflict with any other devices
MOUSE_ID = 0x02

class Mouse(HID):
    """ Relative movement pointer (aka. a mouse) with two buttons."""
    REPORT_DESCRIPTION = bytes([

        0x05, 0x01,        # Usage Page (Generic Desktop Ctrls)
        0x09, 0x02,        # Usage (Mouse)
        0xA1, 0x01,        # Collection (Application)
        0x85, MOUSE_ID,    #   Report ID
        0x09, 0x01,        #   Usage (Pointer)
        0xA1, 0x00,        #   Collection (Physical)
        0x05, 0x09,        #     Usage Page (Button)
        0x19, 0x01,        #     Usage Minimum (0x01)
        0x29, 0x03,        #     Usage Maximum (0x03)
        0x15, 0x00,        #     Logical Minimum (0)
        0x25, 0x01,        #     Logical Maximum (1)
        0x75, 0x01,        #     Report Size (1)
        0x95, 0x03,        #     Report Count (3)
        0x81, 0x02,        #     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
        0x75, 0x05,        #     Report Size (5)
        0x95, 0x01,        #     Report Count (1)
        0x81, 0x01,        #     Input (Const,Array,Abs,No Wrap,Linear,Preferred State,No Null Position)
        0x05, 0x01,        #     Usage Page (Generic Desktop Ctrls)
        0x09, 0x30,        #     Usage (X)
        0x09, 0x31,        #     Usage (Y)
        0x09, 0x38,        #     Usage (Wheel)
        0x15, 0x81,        #     Logical Minimum (-127)
        0x25, 0x7F,        #     Logical Maximum (127)
        0x75, 0x08,        #     Report Size (8)
        0x95, 0x03,        #     Report Count (3)
        0x81, 0x06,        #     Input (Data,Var,Rel,No Wrap,Linear,Preferred State,No Null Position)
        0xC0,              #   End Collection
        0xC0,              # End Collection

    ])

    @dataclass
    class Message(HIDMessage):
        left_button: bool = False
        right_button: bool = False
        rel_x: float = 0.0 # (-1.0, 1.0)
        rel_y: float = 0.0 # (-1.0, 1.0)
        wheel: float = 0.0 # (-1.0, 1.0)

        @property
        def buttons(self) -> bytes:
            return _buttons_lut[(self.left_button, self.right_button)]

        @property
        def report_id(self) -> int:
            return MOUSE_ID

        @property
        def payload(self) -> bytes:
            return ( 
                self.buttons +
                float_to_signed_bytes(self.rel_x) + 
                float_to_signed_bytes(self.rel_y) + 
                float_to_signed_bytes(self.wheel) + 
                b'\x00\x00'
            )

# This lookup table (lut) accelerates payload generation
# Key: (left_button, right_button)
_buttons_lut: typing.Dict[typing.Tuple[bool, bool], bytes] = {
    (False, False): b'\x00',
    (True, False): b'\x01',
    (False, True): b'\x02',
    (True, True): b'\x03'
}