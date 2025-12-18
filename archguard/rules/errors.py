from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class RulesError(Exception):
    """
    Base class for all rules-related errors.

    These errors should be surfaced to users as configuration/DSL issues,
    not as internal engine crashes.
    """
    message: str
    file: str | None = None
    line: int | None = None
    column: int | None = None
    details: Mapping[str, Any] | None = None

    def __str__(self) -> str:
        loc = ""
        if self.file:
            loc = self.file
            if self.line is not None:
                loc += f":{self.line}"
                if self.column is not None:
                    loc += f":{self.column}"
            loc += ": "
        return f"{loc}{self.message}"


@dataclass(frozen=True, slots=True)
class RulesParseError(RulesError):
    """Raised when rules input cannot be parsed."""
    pass


@dataclass(frozen=True, slots=True)
class RulesCompileError(RulesError):
    """Raised when parsed rules cannot be compiled into runtime predicates."""
    pass


@dataclass(frozen=True, slots=True)
class RulesEvalError(RulesError):
    """Raised when evaluating compiled rules fails unexpectedly."""
    pass
