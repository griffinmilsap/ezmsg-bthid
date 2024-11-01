import socket
import time
import math

import numpy as np

from ezmsg.bthid.device import Touch
from ezmsg.util.rate import Rate

pub_rate = 250
pub_times = []

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect(('127.0.0.1', 6789))

    rate = Rate(pub_rate)

    start = time.time()

    while True:
        if time.time() - start > 10.0:
            break

        rate.sleep_sync()

        w = 2.0 * math.pi * 0.1 * (time.time() - start)
        mag = 0.5 # (np.cos(0.5 * w) + 1.0) / 2.0
        cpx = np.exp(w * 1.0j) * mag
        msg = Touch.Message(
            touch = 0x02,
            abs_x = (cpx.real + 1.0) / 2.0,
            abs_y = (cpx.imag + 1.0) / 2.0
        )

        sock.sendall(msg.report.hex().encode() + b'\n')
        pub_times.append(time.perf_counter())

print(f'{pub_times=}')