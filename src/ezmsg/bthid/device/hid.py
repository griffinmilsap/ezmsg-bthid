import asyncio

from abc import ABC, abstractmethod

class HIDMessage(ABC):

    @property
    @abstractmethod
    def report_id(self) -> int:
        raise NotImplementedError

    @property
    def report(self) -> bytes:
        return bytes([0xA1, 0xFF & self.report_id]) + self.payload
    
    @property
    @abstractmethod
    def payload(self) -> bytes:
        raise NotImplementedError
    
    # Stream encoding: Hex + newline
    def encode(self) -> bytes:
        return self.report.hex().encode() + b'\n'


# Stream decoding: Hex + newline
def decode_report(report: bytes) -> bytes:
    return bytes.fromhex(report.decode()[:-1]) if report else report


class HID(ABC):
    REPORT_DESCRIPTION: bytes

    class Message(HIDMessage):
        ...
