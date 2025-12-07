from dataclasses import dataclass, field

from archguard.dto.class_info import ClassInfo
from archguard.dto.import_info import ImportInfo
from archguard.dto.rule import Rule


@dataclass()
class Violation:
    violated_rule: Rule
    offender_import: ImportInfo | None = field(default=None)
    offender_class: ClassInfo | None = field(default=None)
