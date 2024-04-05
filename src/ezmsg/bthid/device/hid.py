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
    def write(self, writer: asyncio.StreamWriter) -> None:
        writer.write(self.report.hex().encode() + b'\n')


# Stream decoding: Hex + newline
async def read_report(reader: asyncio.StreamReader) -> bytes:
    report = await reader.readline()
    return bytes.fromhex(report.decode()[:-1]) if report else report


class HID(ABC):
    REPORT_DESCRIPTION: bytes

    class Message(HIDMessage):
        ...
