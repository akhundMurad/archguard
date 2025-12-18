from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

from archguard.rules.ast import (
    RulesDocumentAst,
    RuleAst,
    DependencyWhenAst,
    NodeWhenAst,
    AndAst,
    OrAst,
    NotAst,
    CompareAst,
    FieldAst,
    LiteralAst,
    SourceSpan,
)
from archguard.rules.errors import RulesParseError

# Public protocol

class RulesParser(Protocol):
    """
    Parse a rules file (DSL/YAML/etc.) into a RulesDocumentAst.
    """
    def parse_text(self, text: str, *, filename: str | None = None) -> RulesDocumentAst:
        raise NotImplementedError()

    def parse_file(self, path: str | Path) -> RulesDocumentAst:
        raise NotImplementedError()

# Minimal DSL parser (v0)
#
# This is intentionally a very small parser that supports a compact YAML-like DSL
# without external dependencies. It is NOT meant to be a fully featured language yet.
#
# Supported format (v0):
#
# rule:
#   id: no-domain-to-infra
#   name: Domain must not depend on Infra
#   severity: error|warning|info
#   action: forbid|allow|require
#   target: dependency|node
#   when:
#     all:
#       - field: from.layer
#         op: ==
#         value: domain
#       - field: to.layer
#         op: ==
#         value: infra
#
# Multiple rules are separated by a blank line and repeated "rule:" blocks.
#

@dataclass(frozen=True, slots=True)
class DslRulesParserV0:
    """
    A minimal rules parser for a constrained YAML-ish DSL.

    Limitations:
    - indentation-sensitive
    - only supports: when/all, when/any, when/not
    - values are treated as strings unless list syntax [a,b,c] is used

    Intended only as a bootstrap parser.
    """

    def parse_file(self, path: str | Path) -> RulesDocumentAst:
        p = Path(path)
        return self.parse_text(p.read_text(encoding="utf-8"), filename=str(p))

    def parse_text(self, text: str, *, filename: str | None = None) -> RulesDocumentAst:
        filename = filename or "<rules>"

        blocks = self._split_rule_blocks(text)
        rules: list[RuleAst] = []

        for i, block in enumerate(blocks, start=1):
            try:
                rules.append(self._parse_rule_block(block, filename=filename))
            except RulesParseError:
                raise
            except Exception as e:  # convert unknown crashes to RulesParseError
                raise RulesParseError(
                    message=f"Failed to parse rule block #{i}: {e}",
                    file=filename,
                ) from e

        return RulesDocumentAst(rules=tuple(rules), span=SourceSpan(file=filename))

    def _split_rule_blocks(self, text: str) -> list[str]:
        lines = [ln.rstrip("\n") for ln in text.splitlines()]
        blocks: list[list[str]] = []
        current: list[str] = []

        def flush():
            nonlocal current
            if any(ln.strip() for ln in current):
                blocks.append(current)
            current = []

        for ln in lines:
            if not ln.strip():
                flush()
                continue
            current.append(ln)
        flush()

        # Keep only blocks starting with "rule:"
        filtered = []
        for b in blocks:
            first = next((ln for ln in b if ln.strip()), "")
            if first.strip() != "rule:":
                # allow comments-only blocks
                continue
            filtered.append("\n".join(b))
        return filtered

    def _parse_rule_block(self, block: str, *, filename: str) -> RuleAst:
        # Very small indentation parser.
        # Convert to dict-like structure where keys map to strings or nested dict/list.
        lines = [ln for ln in block.splitlines() if ln.strip() and not ln.strip().startswith("#")]
        if not lines or lines[0].strip() != "rule:":
            raise RulesParseError(message="Rule block must start with 'rule:'", file=filename)

        # Parse key/values with indentation
        root = self._parse_mapping(lines[1:], filename=filename, base_indent=self._indent_of(lines[1]) if len(lines) > 1 else 0)

        # Required fields
        rid = self._req_str(root, "id", filename)
        name = self._req_str(root, "name", filename)

        severity = self._opt_str(root, "severity", "error")
        action = self._opt_str(root, "action", "forbid")
        target = self._opt_str(root, "target", "dependency")

        message = self._opt_str(root, "message", None)
        suggestion = self._opt_str(root, "suggestion", None)
        description = self._opt_str(root, "description", None)

        when_obj = root.get("when")
        if when_obj is None:
            raise RulesParseError(message=f"Rule '{rid}' missing 'when:' block", file=filename)

        predicate = self._parse_when_predicate(when_obj, filename=filename)

        when_ast = DependencyWhenAst(predicate=predicate) if target == "dependency" else NodeWhenAst(predicate=predicate)

        return RuleAst(
            id=rid,
            name=name,
            description=description,
            severity=severity,   # compiler will validate enum
            action=action,       # compiler will validate enum
            when=when_ast,
            except_when=(),
            message=message,
            suggestion=suggestion,
            tags=(),
            span=SourceSpan(file=filename),
            metadata={"parser": "dsl-v0"},
        )

    # Parsing primitives

    def _indent_of(self, line: str) -> int:
        return len(line) - len(line.lstrip(" "))

    def _parse_mapping(self, lines: Sequence[str], *, filename: str, base_indent: int) -> dict:
        """
        Parse a mapping with possible nested mappings/lists.
        """
        out: dict = {}
        i = 0
        while i < len(lines):
            ln = lines[i]
            indent = self._indent_of(ln)
            if indent < base_indent:
                break
            if indent > base_indent:
                raise RulesParseError(message="Unexpected indentation", file=filename)

            stripped = ln.strip()
            if ":" not in stripped:
                raise RulesParseError(message=f"Expected key:value, got '{stripped}'", file=filename)

            key, rest = stripped.split(":", 1)
            key = key.strip()
            rest = rest.strip()

            if rest:
                out[key] = rest
                i += 1
                continue

            # nested structure
            # lookahead
            i += 1
            if i >= len(lines):
                out[key] = {}
                break

            next_ln = lines[i]
            next_indent = self._indent_of(next_ln)
            if next_indent <= base_indent:
                out[key] = {}
                continue

            # list item?
            if next_ln.strip().startswith("- "):
                items, consumed = self._parse_list(lines[i:], filename=filename, base_indent=next_indent)
                out[key] = items
                i += consumed
            else:
                nested, consumed = self._parse_mapping_with_consumed(lines[i:], filename=filename, base_indent=next_indent)
                out[key] = nested
                i += consumed

        return out

    def _parse_mapping_with_consumed(self, lines: Sequence[str], *, filename: str, base_indent: int) -> tuple[dict, int]:
        out: dict = {}
        i = 0
        while i < len(lines):
            ln = lines[i]
            indent = self._indent_of(ln)
            if indent < base_indent:
                break
            if indent > base_indent:
                raise RulesParseError(message="Unexpected indentation", file=filename)

            stripped = ln.strip()
            if ":" not in stripped:
                raise RulesParseError(message=f"Expected key:value, got '{stripped}'", file=filename)

            key, rest = stripped.split(":", 1)
            key = key.strip()
            rest = rest.strip()

            if rest:
                out[key] = rest
                i += 1
                continue

            # nested
            i += 1
            if i >= len(lines):
                out[key] = {}
                break

            next_ln = lines[i]
            next_indent = self._indent_of(next_ln)
            if next_indent <= base_indent:
                out[key] = {}
                continue

            if next_ln.strip().startswith("- "):
                items, consumed = self._parse_list(lines[i:], filename=filename, base_indent=next_indent)
                out[key] = items
                i += consumed
            else:
                nested, consumed = self._parse_mapping_with_consumed(lines[i:], filename=filename, base_indent=next_indent)
                out[key] = nested
                i += consumed

        return out, i

    def _parse_list(self, lines: Sequence[str], *, filename: str, base_indent: int) -> tuple[list, int]:
        items: list = []
        i = 0
        while i < len(lines):
            ln = lines[i]
            indent = self._indent_of(ln)
            if indent < base_indent:
                break
            if indent != base_indent:
                raise RulesParseError(message="Unexpected indentation in list", file=filename)

            stripped = ln.strip()
            if not stripped.startswith("- "):
                break

            payload = stripped[2:].strip()
            if payload:
                # scalar item
                items.append(payload)
                i += 1
                continue

            # nested mapping item
            i += 1
            if i >= len(lines):
                items.append({})
                break
            next_ln = lines[i]
            next_indent = self._indent_of(next_ln)
            if next_indent <= base_indent:
                items.append({})
                continue

            nested, consumed = self._parse_mapping_with_consumed(lines[i:], filename=filename, base_indent=next_indent)
            items.append(nested)
            i += consumed

        return items, i

    # AST conversion (when block)

    def _parse_when_predicate(self, when_obj: object, *, filename: str):
        """
        Convert a parsed structure into ExprAst.
        """
        if not isinstance(when_obj, dict):
            raise RulesParseError(message="'when' must be a mapping", file=filename)

        if "all" in when_obj:
            return AndAst(items=tuple(self._parse_pred_item(x, filename=filename) for x in when_obj["all"]))
        if "any" in when_obj:
            return OrAst(items=tuple(self._parse_pred_item(x, filename=filename) for x in when_obj["any"]))
        if "not" in when_obj:
            return NotAst(item=self._parse_pred_item(when_obj["not"], filename=filename))

        raise RulesParseError(message="when: must contain one of: all, any, not", file=filename)

    def _parse_pred_item(self, item: object, *, filename: str):
        if isinstance(item, dict):
            # expected: {field: ..., op: ..., value: ...}
            field = item.get("field")
            op = item.get("op", "==")
            value = item.get("value")

            if not isinstance(field, str) or not field.strip():
                raise RulesParseError(message="Predicate item missing non-empty 'field'", file=filename)

            if not isinstance(op, str) or not op.strip():
                raise RulesParseError(message="Predicate item missing non-empty 'op'", file=filename)

            lit = self._parse_literal(value)
            return CompareAst(left=FieldAst(path=field.strip()), op=op.strip(), right=lit)

        if isinstance(item, str):
            # extremely minimal fallback: "from.layer == domain"
            return self._parse_inline_compare(item, filename=filename)

        raise RulesParseError(message=f"Unsupported predicate item: {item!r}", file=filename)

    def _parse_inline_compare(self, text: str, *, filename: str):
        # naive split: <field> <op> <value>
        parts = text.strip().split()
        if len(parts) < 3:
            raise RulesParseError(message=f"Invalid inline predicate: {text!r}", file=filename)
        field = parts[0]
        op = parts[1]
        value = " ".join(parts[2:])
        return CompareAst(left=FieldAst(path=field), op=op, right=self._parse_literal(value))

    def _parse_literal(self, value: object) -> LiteralAst:
        if value is None:
            return LiteralAst(kind="null", value=None)

        if isinstance(value, bool):
            return LiteralAst(kind="bool", value=value)

        if isinstance(value, (int, float)):
            return LiteralAst(kind="number", value=value)

        if isinstance(value, list):
            return LiteralAst(kind="list", value=value)

        # string-ish: try to parse "[a,b,c]" list shorthand
        s = str(value).strip()
        if s.startswith("[") and s.endswith("]"):
            inner = s[1:-1].strip()
            if not inner:
                return LiteralAst(kind="list", value=[])
            parts = [p.strip() for p in inner.split(",")]
            return LiteralAst(kind="list", value=parts)

        return LiteralAst(kind="string", value=s)

    # Access helpers

    def _req_str(self, root: dict, key: str, filename: str) -> str:
        if key not in root:
            raise RulesParseError(message=f"Missing required key: {key}", file=filename)
        val = root[key]
        if not isinstance(val, str) or not val.strip():
            raise RulesParseError(message=f"Key '{key}' must be a non-empty string", file=filename)
        return val.strip()

    def _opt_str(self, root: dict, key: str, default):
        if key not in root:
            return default
        val = root[key]
        if val is None:
            return None
        return str(val).strip()
