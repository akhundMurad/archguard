from dataclasses import dataclass, field

from archguard import enums
from archguard.dto.class_rule import ClassRule
from archguard.dto.module_rule import ModuleRule


@dataclass()
class Rule:
    rule_type: enums.RuleType
    module_rule: ModuleRule | None = field(default=None)
    class_rule: ClassRule | None = field(default=None)
