from dataclasses import dataclass

from .hid import HID, HIDMessage

# This report ID cannot conflict with any other devices
TOUCH_ID = 0x03
_MAX_TOUCH = 10000
_LOGICAL_MAX = _MAX_TOUCH.to_bytes(2, 'little', signed = True)

class Touch(HID):
    """ TODO: Absolute movement pointer (single-touch digitizer)"""
    REPORT_DESCRIPTION = bytes([
        0x05, 0x0d,                    # USAGE_PAGE (Digitizer)
        0x09, 0x02,                    # USAGE (Pen)
        0xa1, 0x01,                    # COLLECTION (Application)
        0x85, TOUCH_ID,                #   Report ID
        
        # Declare a finger collection
        0x09, 0x20,                    #   Usage (Stylus)
        0xA1, 0x00,                    #   Collection (Physical)

        # Declare a finger touch (finger up/down)
        0x09, 0x42,                    #     Usage (Tip Switch)
        0x09, 0x32,                    #     USAGE (In Range)
        0x15, 0x00,                    #     LOGICAL_MINIMUM (0)
        0x25, 0x01,                    #     LOGICAL_MAXIMUM (1)
        0x75, 0x01,                    #     REPORT_SIZE (1)
        0x95, 0x02,                    #     REPORT_COUNT (2)
        0x81, 0x02,                    #     INPUT (Data,Var,Abs)

        # Declare the remaining 6 bits of the first data byte as constant -> the driver will ignore them
        0x75, 0x01,                    #     REPORT_SIZE (1)
        0x95, 0x06,                    #     REPORT_COUNT (6)
        0x81, 0x01,                    #     INPUT (Cnst,Ary,Abs)

        # Define absolute X and Y coordinates of 16 bit each (percent values multiplied with 100)
        # http:#www.usb.org/developers/hidpage/Hut1_12v2.pdf
        # Chapter 16.2 says: "In the Stylus collection a Pointer physical collection will contain the axes reported by the stylus."
        0x05, 0x01,                    #     Usage Page (Generic Desktop)
        0x09, 0x01,                    #     Usage (Pointer)
        0xA1, 0x00,                    #     Collection (Physical)
        0x09, 0x30,                    #        Usage (X)
        0x09, 0x31,                    #        Usage (Y)
        0x16, 0x00, 0x00,              #        Logical Minimum (0)
        0x26, *_LOGICAL_MAX,           #        Logical Maximum (_MAX_TOUCH)
        0x36, 0x00, 0x00,              #        Physical Minimum (0)
        0x46, *_LOGICAL_MAX,           #        Physical Maximum (_MAX_TOUCH)
        0x66, 0x00, 0x00,              #        UNIT (None)
        0x75, 0x10,                    #        Report Size (16),
        0x95, 0x02,                    #        Report Count (2),
        0x81, 0x02,                    #        Input (Data,Var,Abs)
        0xc0,                          #     END_COLLECTION

        0xc0,                          #   END_COLLECTION
        0xc0                           # END_COLLECTION
    ])

    @dataclass
    class Message(HIDMessage):
        touch: int = 0x00 # Individual buttons (3x) [bit0 = up/down, bit1 = in range]
        abs_x: float = 0.0 # (-1.0, 1.0)
        abs_y: float = 0.0 # (-1.0, 1.0)

        @property
        def report_id(self) -> int:
            return TOUCH_ID

        @property
        def payload(self) -> bytes:
            x = int(self.abs_x * _MAX_TOUCH).to_bytes(2, 'little', signed = True)
            y = int(self.abs_y * _MAX_TOUCH).to_bytes(2, 'little', signed = True)
            return bytes([self.touch & 0xFF, *x, *y])
