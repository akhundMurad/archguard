from typing import Protocol

from archguard import dto


class ScannerProtocol(Protocol):
    def scan_project_root(self, project_root: dto.ProjectRoot, rules: list[dto.Rule]) -> dto.ScanResult:
        raise NotImplementedError()
