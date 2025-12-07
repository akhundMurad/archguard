from enum import auto
from archguard.enums._str_enum import StrEnum


class RuleType(StrEnum):
    IMPORT: str = auto()
    NAMING: str = auto()
    LAYER: str = auto()
