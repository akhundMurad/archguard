from typing import Protocol
from archguard import dto


class RuleValidatorProtocol(Protocol):
    def validate_imports(self, module: dto.ModuleInfo) -> list[dto.Violation]:
        raise NotImplementedError()

    def validate_classes(self, module: dto.ModuleInfo) -> list[dto.Violation]:
        raise NotImplementedError()
