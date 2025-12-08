from dataclasses import dataclass
from typing import Optional, Sequence
import fnmatch
from archguard import dto


@dataclass
class ClassRule:
    reside_in_module: Optional[str] = None
    do_not_reside_in_module: Optional[str] = None

    should_have_name_matching: Optional[str] = None  # fnmatch pattern
    should_have_decorators: Optional[Sequence[str]] = None  # required decorators; None/[] = no restriction

    def applies_to_module(self, module_name: str) -> bool:
        if self.reside_in_module and self.reside_in_module != module_name:
            return False

        if self.do_not_reside_in_module and self.do_not_reside_in_module == module_name:
            return False

        return True

    def violates_class(self, class_: dto.ClassInfo) -> bool:
        # Name pattern
        if self.should_have_name_matching and not fnmatch.fnmatch(
            class_.name,
            self.should_have_name_matching,
        ):
            return True

        # Decorators
        if self.should_have_decorators:
            if not all(d in class_.decorators for d in self.should_have_decorators):
                return True

        return False
