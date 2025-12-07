from dataclasses import dataclass, field

from archguard import enums


@dataclass()
class ModuleRule:
    reside_in: str | None = field(default=None)
    do_not_reside_in: str | None = field(default=None)
    should_not_import_from: list[str] = field(default_factory=list)
    should_import_from: list[str] = field(default_factory=lambda: ["*"])


@dataclass()
class ClassRule:
    reside_in_module: str | None = field(default=None)
    do_not_reside_in_module: str | None = field(default=None)
    should_have_name_matching: str | None = field(default=None)
    should_have_decorators: list[str] = field(default_factory=lambda: ["*"])


@dataclass()
class Rule:
    rule_type: enums.RuleType
    module_rule: ModuleRule | None = field(default=None)
    class_rule: ClassRule | None = field(default=None)
