from dataclasses import dataclass

from .hid import HID, HIDMessage

# This report ID cannot conflict with any other devices
KEYBOARD_ID = 0x01 

class Keyboard(HID):
    """ Generic Keyboard with Numpad """

    REPORT_DESCRIPTION = bytes([

        0x05, 0x01,        # Usage Page (Generic Desktop Ctrls)
        0x09, 0x06,        # Usage (Keyboard)
        0xA1, 0x01,        # Collection (Application)
        0x85, KEYBOARD_ID, #   Report ID
        0xA1, 0x00,        #   Collection (Physical)
        0x05, 0x07,        #     Usage Page (Kbrd/Keypad)
        0x19, 0xE0,        #     Usage Minimum (0xE0)
        0x29, 0xE7,        #     Usage Maximum (0xE7)
        0x15, 0x00,        #     Logical Minimum (0)
        0x25, 0x01,        #     Logical Maximum (1)
        0x75, 0x01,        #     Report Size (1)
        0x95, 0x08,        #     Report Count (8)
        0x81, 0x02,        #     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
        0x95, 0x01,        #     Report Count (1)
        0x75, 0x08,        #     Report Size (8)
        0x81, 0x01,        #     Input (Const,Array,Abs,No Wrap,Linear,Preferred State,No Null Position)
        0x95, 0x08,        #     Report Count (8)
        0x75, 0x08,        #     Report Size (8)
        0x15, 0x00,        #     Logical Minimum (0)
        0x25, 0x65,        #     Logical Maximum (101)
        0x05, 0x07,        #     Usage Page (Kbrd/Keypad)
        0x19, 0x00,        #     Usage Minimum (0x00)
        0x29, 0x65,        #     Usage Maximum (0x65)
        0x81, 0x00,        #     Input (Data,Array,Abs,No Wrap,Linear,Preferred State,No Null Position)
        0xC0,              #   End Collection
        0xC0,              # End Collection
    ])

    # Source: HID Usage Tables for USB, v1.21, section "10 - Keyboard/Keypad Page"
    # https://usb.org/sites/default/files/hut1_21.pdf

    MODIFIER_LEFT_CTRL = 1 << 0
    MODIFIER_LEFT_SHIFT = 1 << 1
    MODIFIER_LEFT_ALT = 1 << 2
    MODIFIER_LEFT_META = 1 << 3
    MODIFIER_RIGHT_CTRL = 1 << 4
    MODIFIER_RIGHT_SHIFT = 1 << 5
    MODIFIER_RIGHT_ALT = 1 << 6
    MODIFIER_RIGHT_META = 1 << 7

    KEYCODE_NONE = 0
    KEYCODE_A = 0x04
    KEYCODE_B = 0x05
    KEYCODE_C = 0x06
    KEYCODE_D = 0x07
    KEYCODE_E = 0x08
    KEYCODE_F = 0x09
    KEYCODE_G = 0x0a
    KEYCODE_H = 0x0b
    KEYCODE_I = 0x0c
    KEYCODE_J = 0x0d
    KEYCODE_K = 0x0e
    KEYCODE_L = 0x0f
    KEYCODE_M = 0x10
    KEYCODE_N = 0x11
    KEYCODE_O = 0x12
    KEYCODE_P = 0x13
    KEYCODE_Q = 0x14
    KEYCODE_R = 0x15
    KEYCODE_S = 0x16
    KEYCODE_T = 0x17
    KEYCODE_U = 0x18
    KEYCODE_V = 0x19
    KEYCODE_W = 0x1a
    KEYCODE_X = 0x1b
    KEYCODE_Y = 0x1c
    KEYCODE_Z = 0x1d
    KEYCODE_NUMBER_1 = 0x1e
    KEYCODE_NUMBER_2 = 0x1f
    KEYCODE_NUMBER_3 = 0x20
    KEYCODE_NUMBER_4 = 0x21
    KEYCODE_NUMBER_5 = 0x22
    KEYCODE_NUMBER_6 = 0x23
    KEYCODE_NUMBER_7 = 0x24
    KEYCODE_NUMBER_8 = 0x25
    KEYCODE_NUMBER_9 = 0x26
    KEYCODE_NUMBER_0 = 0x27
    KEYCODE_ENTER = 0x28
    KEYCODE_ESCAPE = 0x29
    KEYCODE_BACKSPACE_DELETE = 0x2a
    KEYCODE_TAB = 0x2b
    KEYCODE_SPACEBAR = 0x2c
    KEYCODE_MINUS = 0x2d
    KEYCODE_EQUAL_SIGN = 0x2e
    KEYCODE_LEFT_BRACKET = 0x2f
    KEYCODE_RIGHT_BRACKET = 0x30
    KEYCODE_BACKSLASH = 0x31
    KEYCODE_HASH = 0x32
    KEYCODE_SEMICOLON = 0x33
    KEYCODE_SINGLE_QUOTE = 0x34
    KEYCODE_ACCENT_GRAVE = 0x35
    KEYCODE_COMMA = 0x36
    KEYCODE_PERIOD = 0x37
    KEYCODE_FORWARD_SLASH = 0x38
    KEYCODE_CAPS_LOCK = 0x39
    KEYCODE_F1 = 0x3a
    KEYCODE_F2 = 0x3b
    KEYCODE_F3 = 0x3c
    KEYCODE_F4 = 0x3d
    KEYCODE_F5 = 0x3e
    KEYCODE_F6 = 0x3f
    KEYCODE_F7 = 0x40
    KEYCODE_F8 = 0x41
    KEYCODE_F9 = 0x42
    KEYCODE_F10 = 0x43
    KEYCODE_F11 = 0x44
    KEYCODE_F12 = 0x45
    KEYCODE_PRINT_SCREEN = 0x46
    KEYCODE_SCROLL_LOCK = 0x47
    KEYCODE_PAUSE_BREAK = 0x48
    KEYCODE_INSERT = 0x49
    KEYCODE_HOME = 0x4a
    KEYCODE_PAGE_UP = 0x4b
    KEYCODE_DELETE = 0x4c
    KEYCODE_END = 0x4d
    KEYCODE_PAGE_DOWN = 0x4e
    KEYCODE_RIGHT_ARROW = 0x4f
    KEYCODE_LEFT_ARROW = 0x50
    KEYCODE_DOWN_ARROW = 0x51
    KEYCODE_UP_ARROW = 0x52
    KEYCODE_CLEAR = 0x53
    KEYCODE_NUM_LOCK = 0x53
    KEYCODE_NUMPAD_DIVIDE = 0x54
    KEYCODE_NUMPAD_MULTIPLY = 0x55
    KEYCODE_NUMPAD_MINUS = 0x56
    KEYCODE_NUMPAD_PLUS = 0x57
    KEYCODE_NUMPAD_ENTER = 0x58
    KEYCODE_NUMPAD_1 = 0x59
    KEYCODE_NUMPAD_2 = 0x5a
    KEYCODE_NUMPAD_3 = 0x5b
    KEYCODE_NUMPAD_4 = 0x5c
    KEYCODE_NUMPAD_5 = 0x5d
    KEYCODE_NUMPAD_6 = 0x5e
    KEYCODE_NUMPAD_7 = 0x5f
    KEYCODE_NUMPAD_8 = 0x60
    KEYCODE_NUMPAD_9 = 0x61
    KEYCODE_NUMPAD_0 = 0x62
    KEYCODE_NUMPAD_DOT = 0x63
    KEYCODE_102ND = 0x64  # Right of left Shift on non-US keyboards
    KEYCODE_CONTEXT_MENU = 0x65
    KEYCODE_F13 = 0x68
    KEYCODE_F14 = 0x69
    KEYCODE_F15 = 0x6a
    KEYCODE_F16 = 0x6b
    KEYCODE_F17 = 0x6c
    KEYCODE_F18 = 0x6d
    KEYCODE_F19 = 0x6e
    KEYCODE_F20 = 0x6f
    KEYCODE_F21 = 0x70
    KEYCODE_F22 = 0x71
    KEYCODE_F23 = 0x72
    KEYCODE_EXECUTE = 0x74
    KEYCODE_HELP = 0x75
    KEYCODE_SELECT = 0x77
    KEYCODE_INTL_RO = 0x87
    KEYCODE_INTL_YEN = 0x89
    KEYCODE_HANGEUL = 0x90
    KEYCODE_HANJA = 0x91
    KEYCODE_LEFT_CTRL = 0xe0
    KEYCODE_LEFT_SHIFT = 0xe1
    KEYCODE_LEFT_ALT = 0xe2
    KEYCODE_LEFT_META = 0xe3
    KEYCODE_RIGHT_CTRL = 0xe4
    KEYCODE_RIGHT_SHIFT = 0xe5
    KEYCODE_RIGHT_ALT = 0xe6
    KEYCODE_RIGHT_META = 0xe7
    KEYCODE_MEDIA_PLAY_PAUSE = 0xe8
    KEYCODE_REFRESH = 0xfa

    @dataclass
    class Message(HIDMessage):
        mod_keys: int = 0

        # Descriptor supports up to 6 simultaneous keycodes
        key1: int = 0
        key2: int = 0
        key3: int = 0
        key4: int = 0
        key5: int = 0
        key6: int = 0

        @property
        def report_id(self) -> int:
            return KEYBOARD_ID

        @property
        def payload(self) -> bytes:
            return bytes([
                0xFF & self.mod_keys, 
                0x00, 
                0xFF & self.key1,
                0xFF & self.key2,
                0xFF & self.key3,
                0xFF & self.key4,
                0xFF & self.key5,
                0xFF & self.key6,
            ])