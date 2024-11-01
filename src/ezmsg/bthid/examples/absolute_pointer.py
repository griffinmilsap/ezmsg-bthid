import asyncio
import typing
import math
import time

from dataclasses import field

import numpy as np
import ezmsg.core as ez

from ezmsg.bthid.device import Touch
from ezmsg.util.rate import Rate

class TouchMessageGeneratorSettings(ez.Settings):
    pub_rate: float = 250 # Hz

class TouchMessageGeneratorState(ez.State):
    n_msgs: int = 0
    pub_times: typing.List[float] = field(default_factory = list)

class TouchMessageGenerator(ez.Unit):
    SETTINGS = TouchMessageGeneratorSettings
    STATE = TouchMessageGeneratorState

    OUTPUT_HID = ez.OutputStream(Touch.Message, num_buffers = 1)

    @ez.publisher(OUTPUT_HID)
    async def output_mouse(self) -> typing.AsyncGenerator:
        start = time.time()

        rate = Rate(self.SETTINGS.pub_rate)

        while True:

            if time.time() - start > 10.0:
                ez.logger.info(f'{self.STATE.n_msgs=}')
                ez.logger.info(f'{self.STATE.pub_times=}')
                raise ez.NormalTermination

            await rate.sleep()
            # await asyncio.sleep(1.0 / self.SETTINGS.pub_rate)

            w = 2.0 * math.pi * 0.1 * (time.time() - start)
            mag = 0.5 # (np.cos(0.5 * w) + 1.0) / 2.0
            cpx = np.exp(w * 1.0j) * mag
            yield self.OUTPUT_HID, Touch.Message(
                touch = 0x02,
                abs_x = (cpx.real + 1.0) / 2.0,
                abs_y = (cpx.imag + 1.0) / 2.0
            )
            self.STATE.pub_times.append(time.perf_counter())
            self.STATE.n_msgs += 1

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


