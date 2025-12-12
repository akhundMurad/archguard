"""
archguard.ir

Language-agnostic Intermediate Representation (IR) of architecture facts.

This package defines:
- canonical data structures (nodes, edges, IR)
- deterministic merge & normalization
- fast indexing and selection utilities
- stable identity keys
- internal IR validation

IR is:
- produced by analyzers
- enriched by mapping
- consumed by rules, snapshots, and reporting
"""

# Core types (stable public API)

from .types import (
    ArchitectureIR,
    IRNode,
    IREdge,
    CanonicalId,
    SourceLoc,
    SourcePos,
    Language,
    SymbolKind,
    DepType,
    Severity,
)

# Identity / keys

from .keys import (
    node_key,
    edge_key,
    dedupe_nodes,
    dedupe_edges,
)

# IR processing

from .merge import DefaultIRMerger
from .normalize import DefaultIRNormalizer

# Indexing & querying

from .index import (
    IRIndex,
    build_index,
)

from .select import (
    NodeFilter,
    EdgeFilter,
    select_nodes,
    select_edges,
    match_glob,
    match_regex,
)

# Validation

from .validate import (
    validate_ir,
    IRValidationOptions,
)

# Public export control

__all__ = (
    # types
    "ArchitectureIR",
    "IRNode",
    "IREdge",
    "CanonicalId",
    "SourceLoc",
    "SourcePos",
    "Language",
    "SymbolKind",
    "DepType",
    "Severity",

    # keys
    "node_key",
    "edge_key",
    "dedupe_nodes",
    "dedupe_edges",

    # processing
    "DefaultIRMerger",
    "DefaultIRNormalizer",

    # indexing
    "IRIndex",
    "build_index",

    # selection
    "NodeFilter",
    "EdgeFilter",
    "select_nodes",
    "select_edges",
    "match_glob",
    "match_regex",

    # validation
    "validate_ir",
    "IRValidationOptions",
)
