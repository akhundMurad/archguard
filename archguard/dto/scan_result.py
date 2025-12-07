from dataclasses import dataclass, field

from archguard.dto.violation import Violation


@dataclass()
class ScanResult:
    success: bool
    violations: list[Violation] = field(default_factory=list)
