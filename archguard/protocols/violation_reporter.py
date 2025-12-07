from typing import Protocol

from archguard import dto


class ViolationReporterProtocol(Protocol):
    def format(self, scan_result: dto.ScanResult) -> str:
        raise NotImplementedError()
