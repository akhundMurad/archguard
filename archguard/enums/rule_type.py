from enum import auto
from archguard.enums._str_enum import StrEnum


class RuleType(StrEnum):
    MODULES: str = auto()
    CLASSES: str = auto()
    LAYER_ACCESS: str = auto()
