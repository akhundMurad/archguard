from archguard import dto, enums, protocols


class RuleValidator(protocols.RuleValidatorProtocol):
    def __init__(self, rule_set: list[dto.Rule]):
        self.rule_set = rule_set
        self._module_rules = [r for r in rule_set if r.rule_type == enums.RuleType.MODULES]
        self._class_rules = [r for r in rule_set if r.rule_type == enums.RuleType.CLASSES]

    def validate_imports(self, module: dto.ModuleInfo) -> list[dto.Violation]:
        violations: list[dto.Violation] = []

        for import_ in module.imports:
            fqname = _import_to_fqname(import_, module.name)

            for rule in self._module_rules:
                mr = rule.module_rule

                if not mr.applies_to_module(module.name):
                    continue

                if mr.violates_import(fqname):
                    violations.append(
                        dto.Violation(
                            violated_rule=rule,
                            offender_import=import_,
                        )
                    )

        return violations

    def validate_classes(self, module: dto.ModuleInfo) -> list[dto.Violation]:
        violations: list[dto.Violation] = []

        for class_ in module.classes:
            for rule in self._class_rules:
                cr = rule.class_rule

                if not cr.applies_to_module(module.name):
                    continue

                if cr.violates_class(class_):
                    violations.append(
                        dto.Violation(
                            violated_rule=rule,
                            offender_class=class_,
                        )
                    )

        return violations


def _import_to_fqname(imp: dto.ImportInfo, current_module: str) -> str:
    # Case: absolute "from x.y import z"
    if imp.from_module is not None and imp.level == 0:
        return f"{imp.from_module}.{imp.import_module}"

    # Case: absolute "import x.y"
    if imp.level == 0 and "." in imp.import_module:
        return imp.import_module

    # Case: relative import
    if imp.level > 0:
        return _resolve_relative_import(current_module, imp.level, imp.import_module)

    # Fallback: simple import
    return imp.import_module


def _resolve_relative_import(current_module: str, level: int, imported: str) -> str:
    """
    Convert a relative import to a fully-qualified path.

    Example:
    current_module = "myapp.infrastructure.repositories.order"
    level = 1 --> parent = "myapp.infrastructure.repositories"
    level = 2 --> parent = "myapp.infrastructure"
    """
    parts = current_module.split(".")

    # Remove `level` parts: current module name + (level - 1) parents
    parent = ".".join(parts[:-level])

    if parent:
        return f"{parent}.{imported}"
    return imported
