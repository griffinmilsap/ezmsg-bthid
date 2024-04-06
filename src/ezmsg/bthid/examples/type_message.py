import asyncio
import typing

import ezmsg.core as ez

from ezmsg.bthid.device import Keyboard

# This example uses an ezmsg unit to type messages

class GhostWriterSettings(ez.Settings):
    message: str
    pub_rate: float = 3 # Hz

class GhostWriter(ez.Unit):
    SETTINGS: GhostWriterSettings

    OUTPUT = ez.OutputStream(Keyboard.Message)

    @ez.publisher(OUTPUT)
    async def push_buttons(self) -> typing.AsyncGenerator:
        for character in self.SETTINGS.message:
            control_keys = 0x00
            keycode = 0x00

            if character.isdigit():
                keycode = ord(character) - ord('0') + Keyboard.KEYCODE_NUMBER_1
            elif character.isalpha():
                keycode = ord(character.lower()) - ord('a') + Keyboard.KEYCODE_A
                if character.isupper():
                    control_keys |= Keyboard.MODIFIER_LEFT_SHIFT
            elif character == ' ':
                keycode = Keyboard.KEYCODE_SPACEBAR
            elif character == ',':
                keycode = Keyboard.KEYCODE_COMMA
            elif character == '.':
                keycode = Keyboard.KEYCODE_PERIOD
            else: # ?
                keycode = Keyboard.KEYCODE_FORWARD_SLASH
                control_keys |= Keyboard.MODIFIER_LEFT_SHIFT
            
            yield self.OUTPUT, Keyboard.Message(
                mod_keys = control_keys, 
                key1 = keycode
            )

            yield self.OUTPUT, Keyboard.Message() # Release keys

            await asyncio.sleep(1.0 / self.SETTINGS.pub_rate)
        
        yield self.OUTPUT, Keyboard.Message(
            key1 = Keyboard.KEYCODE_ENTER
        )

        yield self.OUTPUT, Keyboard.Message() # Release key

        await asyncio.sleep(1.0 / self.SETTINGS.pub_rate)

        raise ez.Complete

if __name__ == '__main__':

    import argparse 

    from ezmsg.bthid.config import BTHIDConfig
    from ezmsg.bthid.hidoutput import HIDOutput, HIDOutputSettings

    parser = argparse.ArgumentParser(description = 'Keyboard typing demo')

    parser.add_argument(
        '--host',
        type = str,
        default = BTHIDConfig.DEFAULT_HOST,
        help = f'hostname for ezmsg-bthid daemon. default: {BTHIDConfig.DEFAULT_HOST}'
    )

    parser.add_argument(
        '--port',
        type = int,
        default = BTHIDConfig.DEFAULT_PORT,
        help = f'port for ezmsg-bthid daemon. default: {BTHIDConfig.DEFAULT_PORT}'
    )

    parser.add_argument(
        '--message', '-m',
        type = str,
        help = 'message to type (keep it alphanumeric)',
        default = 'Wake up, Neo...'
    )

    class Args:
        host: str
        port: int 
        message: str

    args = parser.parse_args(namespace = Args)

    generator = GhostWriter(
        GhostWriterSettings(
            message = args.message
        )
    )

    hid_output = HIDOutput(
        HIDOutputSettings(
            host = args.host,
            port = args.port
        )
    )

    ez.run(
        GENERATOR = generator,
        HID_OUTPUT = hid_output,
        connections = (
            (generator.OUTPUT, hid_output.INPUT_HID),
        )
    )



