from dataclasses import dataclass, field
from typing import Any, Mapping, Literal

from archguard.ir.types import Severity

# Common location structure

@dataclass(frozen=True, slots=True)
class ReportLocation:
    """
    Location in source code, stable for rendering and tooling.
    """
    file: str
    line: int
    column: int = 1

    end_line: int | None = None
    end_column: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
        }

# Engine errors (not violations)

EngineErrorType = Literal[
    "config_error",
    "parse_error",
    "rules_error",
    "analyzer_error",
    "runtime_error",
]


@dataclass(frozen=True, slots=True)
class EngineError:
    """
    Represents internal failures that may affect analysis completeness.
    These are NOT architectural violations. They are tool/engine errors.

    Examples:
    - invalid architecture.yaml
    - rules DSL parse error
    - analyzer crash on a file
    """
    type: EngineErrorType
    message: str
    location: ReportLocation | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "message": self.message,
            "location": None if self.location is None else self.location.to_dict(),
            "details": dict(self.details),
        }

# Violations (rule matches)

ViolationStatus = Literal["new", "existing", "fixed", "unknown"]


@dataclass(frozen=True, slots=True)
class RuleRef:
    """
    Minimal rule metadata embedded into a violation for reporting.
    """
    id: str
    name: str
    severity: Severity
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "severity": self.severity.value,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class Violation:
    """
    A concrete rule match against the architecture.

    `violation_key` MUST be stable across runs for baseline support.
    """
    rule: RuleRef
    message: str
    status: ViolationStatus = "unknown"

    location: ReportLocation | None = None

    # "from/to" style context is useful for dependency violations
    context: Mapping[str, Any] = field(default_factory=dict)

    # Stable identity used for baselines/diffs
    violation_key: str | None = None

    # Optional: how to fix
    suggestion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule.to_dict(),
            "message": self.message,
            "status": self.status,
            "location": None if self.location is None else self.location.to_dict(),
            "context": dict(self.context),
            "violation_key": self.violation_key,
            "suggestion": self.suggestion,
        }

# Run metadata

@dataclass(frozen=True, slots=True)
class RunInfo:
    """
    Provenance information for this scan run.
    """
    repo_root: str
    commit: str | None = None
    branch: str | None = None

    model_file: str | None = None
    rules_files: tuple[str, ...] = ()

    baseline_ref: str | None = None
    mode: Literal["full", "changed_only"] = "full"

    created_at: str | None = None  # ISO-8601
    tool_version: str | None = None

    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "commit": self.commit,
            "branch": self.branch,
            "model_file": self.model_file,
            "rules_files": list(self.rules_files),
            "baseline_ref": self.baseline_ref,
            "mode": self.mode,
            "created_at": self.created_at,
            "tool_version": self.tool_version,
            "metadata": dict(self.metadata),
        }

# Summary (counts + groupings)

@dataclass(frozen=True, slots=True)
class Summary:
    """
    Aggregated report statistics.
    """
    total_violations: int
    by_severity: Mapping[str, int]
    by_status: Mapping[str, int]
    by_rule: Mapping[str, int]

    engine_errors: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_violations": self.total_violations,
            "by_severity": dict(self.by_severity),
            "by_status": dict(self.by_status),
            "by_rule": dict(self.by_rule),
            "engine_errors": self.engine_errors,
        }

# Diff summary (optional)

@dataclass(frozen=True, slots=True)
class DiffSummary:
    """
    Optional high-level diff summary suitable for CLI/PR comment.
    """
    nodes_added: int
    nodes_removed: int
    edges_added: int
    edges_removed: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes_added": self.nodes_added,
            "nodes_removed": self.nodes_removed,
            "edges_added": self.edges_added,
            "edges_removed": self.edges_removed,
        }

# Final report object

@dataclass(frozen=True, slots=True)
class Report:
    """
    Final output of the engine (in-memory).
    Can be rendered to text/json/sarif.
    """
    tool: str
    version: str
    run: RunInfo

    summary: Summary
    violations: tuple[Violation, ...] = ()
    engine_errors: tuple[EngineError, ...] = ()

    diff: DiffSummary | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "version": self.version,
            "run": self.run.to_dict(),
            "summary": self.summary.to_dict(),
            "violations": [v.to_dict() for v in self.violations],
            "engine_errors": [e.to_dict() for e in self.engine_errors],
            "diff": None if self.diff is None else self.diff.to_dict(),
        }
