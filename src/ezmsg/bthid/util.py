_scales = {
    1: 127,
    2: 32767,
}

def float_to_signed_bytes(value: float, length: int = 1) -> bytes:
    return int(value * _scales.get(length, (1 << ((length * 8) - 1)) - 1)) \
        .to_bytes(length = length, byteorder = 'big', signed = True)