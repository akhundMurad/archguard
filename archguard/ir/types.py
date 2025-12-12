from dataclasses import dataclass, field
from enum import auto
from typing import Any, Mapping

from archguard.utils.enum import StrEnum

# Enums

class Language(StrEnum):
    PYTHON = auto()
    JAVA = auto()
    TYPESCRIPT = auto()
    JAVASCRIPT = auto()
    GO = auto()
    UNKNOWN = auto()


class SymbolKind(StrEnum):
    REPO = auto()
    CONTAINER = auto()
    FILE = auto()
    PACKAGE = auto()
    MODULE = auto()
    CLASS = auto()
    INTERFACE = auto()
    FUNCTION = auto()
    METHOD = auto()
    VARIABLE = auto()


class DepType(StrEnum):
    IMPORT = auto()
    REQUIRE = auto()
    INCLUDE = auto()
    TYPE_REF = auto()
    CALL = auto()

    # Higher-level (optional extractors)
    HTTP_CALL = auto()
    EVENT_PUBLISH = auto()
    EVENT_CONSUME = auto()
    DB_QUERY = auto()
    


class Severity(StrEnum):
    """
    Severity level of an architecture violation.

    Ordering (from strongest to weakest):
      ERROR   → build-breaking
      WARNING → visible but non-blocking
      INFO    → informational only

    Severity is intentionally:
      - language-agnostic
      - stable across versions
      - string-based for JSON/CLI/SaaS compatibility
    """

    ERROR = auto()
    WARNING = auto()
    INFO = auto()

    def is_blocking(self) -> bool:
        """
        Whether this severity should fail CI by default.
        """
        return self == Severity.ERROR

    @staticmethod
    def ordered() -> tuple["Severity", ...]:
        """
        Severity ordering from highest to lowest importance.
        """
        return (Severity.ERROR, Severity.WARNING, Severity.INFO)

    @staticmethod
    def from_str(value: str) -> "Severity":
        """
        Parse severity from string (case-insensitive).

        Raises:
            ValueError if invalid severity.
        """
        value = value.lower()
        for sev in Severity:
            if sev.value == value:
                return sev
        raise ValueError(f"Invalid severity: {value}")

# Source location

@dataclass(frozen=True, slots=True)
class SourcePos:
    line: int
    column: int = 1


@dataclass(frozen=True, slots=True)
class SourceLoc:
    file: str
    start: SourcePos
    end: SourcePos | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "start": {"line": self.start.line, "column": self.start.column},
            "end": None
            if self.end is None
            else {"line": self.end.line, "column": self.end.column},
        }


# Canonical identifier

@dataclass(frozen=True, slots=True)
class CanonicalId:
    """
    Stable, cross-language identifier.

    Format:
      {language}://{code_root}::{fqname}

    Example:
      python://billing-service::services.billing.domain.invoice
    """
    language: Language
    code_root: str
    fqname: str

    def __str__(self) -> str:
        return f"{self.language.value}://{self.code_root}::{self.fqname}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "language": self.language.value,
            "code_root": self.code_root,
            "fqname": self.fqname,
        }

# IR Node

@dataclass(frozen=True, slots=True)
class IRNode:
    """
    A node represents a code artifact (file/module/class/etc).
    """
    id: CanonicalId
    kind: SymbolKind

    # Best-effort metadata
    name: str | None = None
    path: str | None = None
    loc: SourceLoc | None = None

    # Enriched by mapping layer
    container: str | None = None
    layer: str | None = None
    context: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)

    attributes: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id.to_dict(),
            "kind": self.kind.value,
            "name": self.name,
            "path": self.path,
            "loc": None if self.loc is None else self.loc.to_dict(),
            "container": self.container,
            "layer": self.layer,
            "context": self.context,
            "tags": list(self.tags),
            "attributes": dict(self.attributes),
        }

# IR Edge

@dataclass(frozen=True, slots=True)
class IREdge:
    """
    Directed dependency edge between two IR nodes.
    """
    src: CanonicalId
    dst: CanonicalId
    dep_type: DepType

    loc: SourceLoc | None = None
    confidence: float = 1.0
    details: Mapping[str, Any] = field(default_factory=dict)

    # Enriched by mapping layer
    src_container: str | None = None
    src_layer: str | None = None
    src_context: str | None = None
    dst_container: str | None = None
    dst_layer: str | None = None
    dst_context: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "src": self.src.to_dict(),
            "dst": self.dst.to_dict(),
            "dep_type": self.dep_type.value,
            "loc": None if self.loc is None else self.loc.to_dict(),
            "confidence": self.confidence,
            "details": dict(self.details),
            "src_container": self.src_container,
            "src_layer": self.src_layer,
            "src_context": self.src_context,
            "dst_container": self.dst_container,
            "dst_layer": self.dst_layer,
            "dst_context": self.dst_context,
        }

# Architecture IR (the main object)

@dataclass(frozen=True, slots=True)
class ArchitectureIR:
    """
    Language-agnostic Intermediate Representation of architecture facts.

    This is the ONLY structure that:
      - analyzers produce
      - rules evaluate
      - snapshots store
      - diffs compare
    """
    schema_version: int
    produced_by: str  # e.g. "archguard-python@0.1.0"
    repo_root: str

    nodes: tuple[IRNode, ...]
    edges: tuple[IREdge, ...]

    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def empty(cls, repo_root: str) -> "ArchitectureIR":
        """
        Convenience constructor for an empty IR.
        """
        return cls(
            schema_version=1,
            produced_by="archguard-core",
            repo_root=str(repo_root),
            nodes=(),
            edges=(),
            metadata={},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "produced_by": self.produced_by,
            "repo_root": self.repo_root,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "metadata": dict(self.metadata),
        }
