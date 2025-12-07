from enum import Enum

class StrEnum(Enum):
    def _generate_next_value_(name: str, *args, **kwargs) -> str:
        return name.lower()
