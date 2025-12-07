from dataclasses import dataclass

from archguard.dto.rule import Rule


@dataclass()
class ScanResult:
    success: bool
    violated_rules: list[Rule]
