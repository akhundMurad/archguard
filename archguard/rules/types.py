from dataclasses import dataclass, field
from enum import auto
from typing import Any, Callable, Mapping

from archguard.ir.types import Severity
from archguard.utils.enum import StrEnum

# Rule targets

class RuleTarget(StrEnum):
    """
    What kind of IR element this rule applies to.
    """
    DEPENDENCY = auto()
    NODE = auto()  # file/module/class/etc

# Rule predicates

@dataclass(frozen=True, slots=True)
class RulePredicate:
    """
    A compiled predicate function with metadata.

    Example:
      lambda edge: edge.src_layer == "domain" and edge.dst_layer == "infra"
    """
    name: str
    fn: Callable[[Any], bool]  # Any = IREdge or IRNode
    description: str | None = None

# Rule actions

class RuleAction(StrEnum):
    """
    What to do when predicate matches.
    """
    FORBID = auto()
    ALLOW = auto()
    REQUIRE = auto()

# Compiled Rule

@dataclass(frozen=True, slots=True)
class Rule:
    """
    One compiled architecture rule.
    """

    id: str
    name: str
    description: str | None
    severity: Severity

    target: RuleTarget
    predicate: RulePredicate
    action: RuleAction

    # Optional user-facing message
    message: str | None = None

    # Optional suggestion for fixing violation
    suggestion: str | None = None

    # Exceptions (compiled predicates that negate this rule)
    except_predicates: tuple[RulePredicate, ...] = ()

    # Arbitrary metadata (source file, line, tags, etc.)
    metadata: Mapping[str, Any] = field(default_factory=dict)

# RuleSet (main export)

@dataclass(frozen=True, slots=True)
class RuleSet:
    """
    Collection of compiled rules.

    RuleSet is:
      - immutable
      - deterministic
      - language-agnostic
    """

    rules: tuple[Rule, ...]

    @staticmethod
    def empty() -> "RuleSet":
        """
        Convenience constructor for empty ruleset.
        """
        return RuleSet(rules=())

    def rules_for_dependencies(self) -> tuple[Rule, ...]:
        return tuple(r for r in self.rules if r.target == RuleTarget.DEPENDENCY)

    def rules_for_nodes(self) -> tuple[Rule, ...]:
        return tuple(r for r in self.rules if r.target == RuleTarget.NODE)

    def __len__(self) -> int:
        return len(self.rules)

    def __iter__(self):
        return iter(self.rules)
