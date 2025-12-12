from dataclasses import dataclass, field
from typing import Any, Mapping, Literal

from archguard.ir.types import IRNode, IREdge

# Snapshot references

SnapshotRef = str
"""
A snapshot reference identifier.

Examples:
- "latest"
- "baseline"
- "main"
- "commit:abc123"
- "2025-01-15T12:30:00Z"
"""

# Snapshot metadata

@dataclass(frozen=True, slots=True)
class SnapshotMeta:
    """
    Metadata describing when and how the snapshot was produced.
    """
    repo_root: str
    commit: str | None = None
    branch: str | None = None
    created_at: str | None = None  # ISO-8601
    tool_version: str | None = None
    model_version: int | None = None

    extra: Mapping[str, Any] = field(default_factory=dict)

# Snapshot (core persisted object)

@dataclass(frozen=True, slots=True)
class Snapshot:
    """
    Immutable architecture snapshot.

    Snapshot contains:
      - enriched IR nodes
      - enriched IR edges
      - metadata

    Snapshot is:
      - deterministic
      - serializable
      - diffable
    """

    schema_version: int
    meta: SnapshotMeta

    nodes: tuple[IRNode, ...]
    edges: tuple[IREdge, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "meta": {
                "repo_root": self.meta.repo_root,
                "commit": self.meta.commit,
                "branch": self.meta.branch,
                "created_at": self.meta.created_at,
                "tool_version": self.meta.tool_version,
                "model_version": self.meta.model_version,
                "extra": dict(self.meta.extra),
            },
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }

    @staticmethod
    def empty(repo_root: str) -> "Snapshot":
        """
        Convenience constructor for empty snapshot.
        """
        return Snapshot(
            schema_version=1,
            meta=SnapshotMeta(repo_root=repo_root),
            nodes=(),
            edges=(),
        )

# Snapshot diff (structural)

@dataclass(frozen=True, slots=True)
class SnapshotDiff:
    """
    Structural difference between two snapshots.

    This is intentionally factual and rule-agnostic.
    """

    nodes_added: int
    nodes_removed: int
    edges_added: int
    edges_removed: int

    # Optional detailed breakdown (IDs, edges, etc.)
    details: Mapping[str, Any] = field(default_factory=dict)

    def is_empty(self) -> bool:
        return (
            self.nodes_added == 0
            and self.nodes_removed == 0
            and self.edges_added == 0
            and self.edges_removed == 0
        )

# Violation baseline status

ViolationStatus = Literal[
    "new",
    "existing",
    "fixed",
    "unknown",
]
"""
Status of a violation relative to a baseline snapshot.
"""

# Baseline comparison result

@dataclass(frozen=True, slots=True)
class BaselineResult:
    """
    Result of baseline comparison.
    """

    new: int
    existing: int
    fixed: int
    unknown: int

    def to_dict(self) -> dict[str, int]:
        return {
            "new": self.new,
            "existing": self.existing,
            "fixed": self.fixed,
            "unknown": self.unknown,
        }
