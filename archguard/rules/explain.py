from dataclasses import dataclass
from typing import Any, Mapping

from archguard.reporting.types import Violation
from archguard.rules.types import Rule, RuleTarget

# Human-readable explanations

def explain_violation(v: Violation) -> str:
    """
    Turn a Violation into a compact explanation suitable for CLI/IDE tooltips.
    """
    d = v.details or {}
    target = d.get("target")

    if target == "dependency":
        dep_type = d.get("dep_type", "?")
        src = d.get("src_fqname") or d.get("src_id") or "<?>"
        dst = d.get("dst_fqname") or d.get("dst_id") or "<?>"
        src_layer = d.get("src_layer")
        dst_layer = d.get("dst_layer")

        parts: list[str] = []
        parts.append(f"Dependency violation ({dep_type}).")
        parts.append(f"{src} -> {dst}")

        if src_layer or dst_layer:
            parts.append(f"layers: {src_layer or '?'} -> {dst_layer or '?'}")

        return " ".join(parts)

    if target == "node":
        node_id = d.get("fqname") or d.get("node_id") or "<?>"
        kind = d.get("kind", "?")
        layer = d.get("layer")
        context = d.get("context")
        container = d.get("container")

        parts = [f"Node violation ({kind}): {node_id}"]
        extras = []
        if layer:
            extras.append(f"layer={layer}")
        if context:
            extras.append(f"context={context}")
        if container:
            extras.append(f"container={container}")
        if extras:
            parts.append(f"({', '.join(extras)})")
        return " ".join(parts)

    # Fallback
    return v.message


def explain_rule(rule: Rule) -> str:
    """
    Explain a compiled Rule at a high level (for listing rules, debug output).
    """
    target = "dependencies" if rule.target == RuleTarget.DEPENDENCY else "nodes"
    action = rule.action.value.lower()

    base = f"[{rule.id}] {rule.name} — {action} {target} ({rule.severity.value.lower()})"
    if rule.description:
        return f"{base}\n{rule.description}"
    return base

# Optional: "why did it match?" debug helpers (v0)

@dataclass(frozen=True, slots=True)
class PredicateTrace:
    """
    Minimal trace record for debugging predicate evaluation.
    """
    rule_id: str
    matched: bool
    details: Mapping[str, Any]


def trace_violation(v: Violation) -> PredicateTrace:
    """
    v0 trace: just echo violation details.
    Future: include expression tree and extracted field values.
    """
    return PredicateTrace(
        rule_id=v.rule_id,
        matched=True,
        details=v.details or {},
    )
