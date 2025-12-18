from dataclasses import dataclass
from typing import Protocol, Sequence, Union

from archguard.ir.index import IRIndex, build_index
from archguard.ir.types import ArchitectureIR, IREdge, IRNode
from archguard.reporting.types import ReportLocation, Violation
from archguard.rules.types import Rule, RuleAction, RuleSet, RuleTarget

# Public protocol

IRInput = Union[ArchitectureIR, IRIndex]


class RuleEvaluatorProtocol(Protocol):
    def evaluate(self, ir: IRInput, rules: RuleSet) -> tuple[Violation, ...]:
        raise NotImplementedError()

# Helpers

def _node_location(n: IRNode) -> ReportLocation | None:
    if n.loc is None:
        return None
    return ReportLocation(
        file=n.loc.file,
        line=n.loc.start.line,
        column=n.loc.start.column,
        end_line=n.loc.end.line if n.loc.end else None,
        end_column=n.loc.end.column if n.loc.end else None,
    )


def _edge_location(e: IREdge) -> ReportLocation | None:
    if e.loc is None:
        return None
    return ReportLocation(
        file=e.loc.file,
        line=e.loc.start.line,
        column=e.loc.start.column,
        end_line=e.loc.end.line if e.loc.end else None,
        end_column=e.loc.end.column if e.loc.end else None,
    )


def _as_index(ir: IRInput) -> IRIndex:
    if isinstance(ir, IRIndex):
        return ir
    return build_index(ir)


def _passes_exceptions(obj: object, except_when: Sequence) -> bool:
    """
    Exceptions are predicates; if ANY exception predicate matches -> exclude (do not report).
    """
    for ex in except_when:
        try:
            if ex(obj):
                return False
        except Exception:
            # treat exception predicate failures as "not excluded"
            # (better UX than crashing evaluation)
            continue
    return True

# Evaluator

@dataclass(frozen=True, slots=True)
class DefaultRuleEvaluator(RuleEvaluatorProtocol):
    """
    Evaluates compiled RuleSet against IR (or IRIndex) and produces Violations.

    Semantics:
    - FORBID:
        Each matching object (node or edge) => a violation.
    - REQUIRE:
        If no matching object exists => a single violation for the rule.
    - ALLOW:
        v0 semantics = no-op (reserved for allowlist policies / future extensions).

    Notes:
    - This module expects rules to be compiled (Rule.when is a callable).
    - For performance, pass IRIndex (or this will build it).
    """

    def evaluate(self, ir: IRInput, rules: RuleSet) -> tuple[Violation, ...]:
        idx = _as_index(ir)
        out: list[Violation] = []

        for rule in rules.rules:
            if rule.target == RuleTarget.NODE:
                out.extend(self._eval_node_rule(idx, rule))
            elif rule.target == RuleTarget.DEPENDENCY:
                out.extend(self._eval_edge_rule(idx, rule))
            else:
                # Should never happen if compiler validates targets
                continue

        return tuple(out)

    def _eval_node_rule(self, idx: IRIndex, rule: Rule) -> list[Violation]:
        nodes = idx.nodes  # tuple[IRNode, ...] provided by index
        matches: list[IRNode] = []

        for n in nodes:
            try:
                if rule.when(n) and _passes_exceptions(n, rule.except_when):
                    matches.append(n)
            except Exception:
                # Fail-safe: do not crash full run due to one predicate
                continue

        if rule.action == RuleAction.REQUIRE:
            if not matches:
                return [self._require_missing_violation(rule, target="node")]
            return []

        if rule.action == RuleAction.ALLOW:
            # Reserved: allowlist policy will be implemented later (needs explicit scope semantics).
            return []

        # FORBID (default)
        violations: list[Violation] = []
        for n in matches:
            violations.append(
                Violation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    message=rule.message,
                    location=_node_location(n),
                    details={
                        "target": "node",
                        "node_id": str(n.id),
                        "fqname": n.id.fqname,
                        "kind": n.kind.value,
                        "path": n.path,
                        "container": n.container,
                        "layer": n.layer,
                        "context": n.context,
                    },
                    suggestion=rule.suggestion,
                    tags=rule.tags,
                )
            )
        return violations

    def _eval_edge_rule(self, idx: IRIndex, rule: Rule) -> list[Violation]:
        edges = idx.edges  # tuple[IREdge, ...] provided by index
        matches: list[IREdge] = []

        for e in edges:
            try:
                if rule.when(e) and _passes_exceptions(e, rule.except_when):
                    matches.append(e)
            except Exception:
                continue

        if rule.action == RuleAction.REQUIRE:
            if not matches:
                return [self._require_missing_violation(rule, target="dependency")]
            return []

        if rule.action == RuleAction.ALLOW:
            # Reserved: allowlist policy will be implemented later.
            return []

        # FORBID
        violations: list[Violation] = []
        for e in matches:
            violations.append(
                Violation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    message=rule.message,
                    location=_edge_location(e),
                    details={
                        "target": "dependency",
                        "dep_type": e.dep_type.value,
                        "src_id": str(e.src),
                        "dst_id": str(e.dst),
                        "src_fqname": e.src.fqname,
                        "dst_fqname": e.dst.fqname,
                        "src_container": e.src_container,
                        "src_layer": e.src_layer,
                        "src_context": e.src_context,
                        "dst_container": e.dst_container,
                        "dst_layer": e.dst_layer,
                        "dst_context": e.dst_context,
                    },
                    suggestion=rule.suggestion,
                    tags=rule.tags,
                )
            )
        return violations

    def _require_missing_violation(self, rule: Rule, *, target: str) -> Violation:
        msg = rule.message or f"Required {target} pattern not found."
        return Violation(
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            message=msg,
            location=None,
            details={"target": target, "action": "require"},
            suggestion=rule.suggestion,
            tags=rule.tags,
        )
