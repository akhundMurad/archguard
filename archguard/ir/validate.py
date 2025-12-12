from dataclasses import dataclass

from archguard.ir.types import ArchitectureIR, IREdge
from archguard.reporting.types import EngineError, ReportLocation


@dataclass(frozen=True, slots=True)
class IRValidationOptions:
    """
    Validation options for IR sanity checks.

    strict_references:
      - If True: every edge must reference existing nodes.
      - If False: allow edges pointing to external/unknown nodes (common for imports).
    """
    strict_references: bool = False
    max_nodes: int | None = None
    max_edges: int | None = None


def _edge_loc(e: IREdge) -> ReportLocation | None:
    if e.loc is None:
        return None
    return ReportLocation(
        file=e.loc.file,
        line=e.loc.start.line,
        column=e.loc.start.column,
        end_line=e.loc.end.line if e.loc.end else None,
        end_column=e.loc.end.column if e.loc.end else None,
    )


def validate_ir(ir: ArchitectureIR, *, opts: IRValidationOptions | None = None) -> list[EngineError]:
    """
    Validate internal consistency of ArchitectureIR.

    This validation is NOT about architecture correctness.
    It checks:
      - schema version supported (basic check)
      - node identity uniqueness
      - edge confidence range
      - edge references (optional strict mode)
      - basic size guards (optional)

    Returns:
      list[EngineError] (non-empty means IR is partially unreliable)
    """
    opts = opts or IRValidationOptions()
    errors: list[EngineError] = []

    # schema version
    if ir.schema_version <= 0:
        errors.append(EngineError(
            type="runtime_error",
            message=f"Invalid IR schema_version: {ir.schema_version}",
            location=None,
            details={"schema_version": ir.schema_version},
        ))

    # size guards (optional)
    if opts.max_nodes is not None and len(ir.nodes) > opts.max_nodes:
        errors.append(EngineError(
            type="runtime_error",
            message="IR contains too many nodes",
            location=None,
            details={"nodes": len(ir.nodes), "max_nodes": opts.max_nodes},
        ))

    if opts.max_edges is not None and len(ir.edges) > opts.max_edges:
        errors.append(EngineError(
            type="runtime_error",
            message="IR contains too many edges",
            location=None,
            details={"edges": len(ir.edges), "max_edges": opts.max_edges},
        ))

    # node identity uniqueness
    seen_nodes: set[str] = set()
    for n in ir.nodes:
        nid = str(n.id)
        if not nid.strip():
            errors.append(EngineError(
                type="runtime_error",
                message="IR node has empty canonical id",
                location=None,
                details={"node": n.to_dict()},
            ))
            continue

        if nid in seen_nodes:
            errors.append(EngineError(
                type="runtime_error",
                message="Duplicate IR node id detected",
                location=None,
                details={"node_id": nid},
            ))
        else:
            seen_nodes.add(nid)

    node_ids = seen_nodes

    # edge checks
    for e in ir.edges:
        # confidence must be [0,1]
        if not (0.0 <= float(e.confidence) <= 1.0):
            errors.append(EngineError(
                type="runtime_error",
                message="Edge confidence must be within [0,1]",
                location=_edge_loc(e),
                details={
                    "confidence": e.confidence,
                    "src": str(e.src),
                    "dst": str(e.dst),
                    "dep_type": e.dep_type.value,
                },
            ))

        # canonical ids must be non-empty
        if not str(e.src).strip() or not str(e.dst).strip():
            errors.append(EngineError(
                type="runtime_error",
                message="Edge has empty src or dst canonical id",
                location=_edge_loc(e),
                details={"edge": e.to_dict()},
            ))

        # optional strict references check
        if opts.strict_references:
            src_ok = str(e.src) in node_ids
            dst_ok = str(e.dst) in node_ids
            if not src_ok or not dst_ok:
                errors.append(EngineError(
                    type="runtime_error",
                    message="Edge references missing node(s) (strict mode)",
                    location=_edge_loc(e),
                    details={
                        "missing_src": not src_ok,
                        "missing_dst": not dst_ok,
                        "src": str(e.src),
                        "dst": str(e.dst),
                        "dep_type": e.dep_type.value,
                    },
                ))

    return errors
