import asyncio
import typing
import math
import time

import numpy as np
import ezmsg.core as ez

from ezmsg.bthid.device import Touch

class TouchMessageGeneratorSettings(ez.Settings):
    pub_rate: float = 60 # Hz

class TouchMessageGenerator(ez.Unit):
    SETTINGS: TouchMessageGeneratorSettings

    OUTPUT_HID = ez.OutputStream(Touch.Message)

    @ez.publisher(OUTPUT_HID)
    async def output_mouse(self) -> typing.AsyncGenerator:
        start = time.time()
        while True:

            if time.time() - start > 2.0:
                raise ez.NormalTermination

            await asyncio.sleep(1.0 / self.SETTINGS.pub_rate)

            w = 2.0 * math.pi * 2.0 * time.time()
            mag = (np.cos(0.5 * w) + 1.0) / 2.0
            cpx = np.exp(w * 1.0j) * mag
            yield self.OUTPUT_HID, Touch.Message(
                touch = 0x02,
                absolute_x = (cpx.real + 1.0) / 2.0,
                absolute_y = (cpx.imag + 1.0) / 2.0
            )

if __name__ == '__main__':

    import argparse 

    from ezmsg.bthid.config import BTHIDConfig
    from ezmsg.bthid.hidoutput import HIDOutput, HIDOutputSettings

    parser = argparse.ArgumentParser(description = 'Keyboard typing demo')

    parser.add_argument(
        '--host', '-h',
        type = str,
        default = BTHIDConfig.DEFAULT_HOST,
        help = f'hostname for ezmsg-bthid daemon. default: {BTHIDConfig.DEFAULT_HOST}'
    )

    parser.add_argument(
        '--port', '-p',
        type = int,
        default = BTHIDConfig.DEFAULT_HOST,
        help = f'port for ezmsg-bthid daemon. default: {BTHIDConfig.DEFAULT_PORT}'
    )

    class Args:
        host: str
        port: int 

    args = parser.parse_args(namespace = Args)

    generator = TouchMessageGenerator()

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
            (generator.OUTPUT_HID, hid_output.INPUT_HID),
        )
    )


