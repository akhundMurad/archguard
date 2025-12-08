from dataclasses import dataclass
from typing import Sequence
import fnmatch


@dataclass
class ModuleRule:
    reside_in: str | None = None
    should_not_reside_in: str | None = None

    should_not_import_from: str | None = None
    should_import_from: Sequence[str] | None = None

    def applies_to_module(self, module_name: str) -> bool:
        if self.reside_in and self.reside_in != module_name:
            return False

        if self.should_not_reside_in and self.should_not_reside_in == module_name:
            return False

        return True

    def violates_import(self, fqname: str) -> bool:
        # "must not import from" check
        if self.should_not_import_from and self.should_not_import_from in fqname:
            return True

        # "must import only from" patterns
        if self.should_import_from:
            # require at least one pattern to match
            if not any(fnmatch.fnmatch(fqname, pattern) for pattern in self.should_import_from):
                return True

        return False
