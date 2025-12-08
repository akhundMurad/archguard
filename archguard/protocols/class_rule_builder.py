from typing import Protocol

from archguard import dto

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


class ClassRuleBuilderProtocol(Protocol):
    def that_reside_in(self, pattern: str) -> Self:
        raise NotImplementedError()

    def that_do_not_reside_in(self, pattern: str) -> Self:
        raise NotImplementedError()

    def should_have_name_matching(self, pattern: str) -> dto.Rule:
        raise NotImplementedError()

    def should_have_decorators(self, decorators: list[str]) -> dto.Rule:
        raise NotImplementedError()
