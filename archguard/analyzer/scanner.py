from archguard import protocols, dto
from archguard.analyzer._rule_validator import RuleValidator


class Scanner(protocols.ScannerProtocol):
    def __init__(self, rule_set: list[dto.Rule]):
        self.rule_validator = RuleValidator(rule_set)

    def scan_project_root(self, project_root: dto.ProjectRoot) -> dto.ScanResult:
        violations: list[dto.Violation] = []

        for module in project_root.modules.values():
            violations.extend(self.rule_validator.validate_imports(module))
            violations.extend(self.rule_validator.validate_classes(module))

        return dto.ScanResult(
            success=len(violations) == 0,
            violations=violations,
        )
