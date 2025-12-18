import pytest

from archguard.rules.ast import (
    AndAst,
    OrAst,
    NotAst,
    CompareAst,
    FieldAst,
    LiteralAst,
    DependencyWhenAst,
    NodeWhenAst,
    RulesDocumentAst,
)
from archguard.rules.errors import RulesParseError
from archguard.rules.parser import DslRulesParserV0

# Helpers

def parse(text: str):
    return DslRulesParserV0().parse_text(text, filename="rules.txt")

# Tests: block splitting

def test_parser_ignores_blocks_not_starting_with_rule():
    text = """
# comment block

something:
  not: a rule

rule:
  id: r1
  name: A
  target: node
  when:
    all:
      - field: layer
        op: ==
        value: domain
"""
    doc = parse(text)
    assert isinstance(doc, RulesDocumentAst)
    assert len(doc.rules) == 1
    assert doc.rules[0].id == "r1"


def test_parser_multiple_rule_blocks_separated_by_blank_lines():
    text = """
rule:
  id: r1
  name: First
  target: node
  when:
    all:
      - field: layer
        op: ==
        value: domain

rule:
  id: r2
  name: Second
  target: dependency
  when:
    all:
      - field: from.layer
        op: ==
        value: domain
"""
    doc = parse(text)
    assert len(doc.rules) == 2
    assert doc.rules[0].id == "r1"
    assert doc.rules[1].id == "r2"

# Tests: when predicate parsing

def test_when_all_builds_and_ast_with_compare_items():
    text = """
rule:
  id: r1
  name: No domain -> infra
  target: dependency
  when:
    all:
      - field: from.layer
        op: ==
        value: domain
      - field: to.layer
        op: ==
        value: infra
"""
    doc = parse(text)
    r = doc.rules[0]
    assert isinstance(r.when, DependencyWhenAst)
    assert isinstance(r.when.predicate, AndAst)
    assert len(r.when.predicate.items) == 2

    c0 = r.when.predicate.items[0]
    assert isinstance(c0, CompareAst)
    assert isinstance(c0.left, FieldAst)
    assert c0.left.path == "from.layer"
    assert c0.op == "=="
    assert isinstance(c0.right, LiteralAst)
    assert c0.right.kind == "string"
    assert c0.right.value == "domain"


def test_when_any_builds_or_ast():
    text = """
rule:
  id: r1
  name: Any layer
  target: node
  when:
    any:
      - field: layer
        op: ==
        value: domain
      - field: layer
        op: ==
        value: infra
"""
    doc = parse(text)
    r = doc.rules[0]
    assert isinstance(r.when, NodeWhenAst)
    assert isinstance(r.when.predicate, OrAst)
    assert len(r.when.predicate.items) == 2


def test_when_not_builds_not_ast():
    text = """
rule:
  id: r1
  name: Not infra
  target: node
  when:
    not:
      field: layer
      op: ==
      value: infra
"""
    doc = parse(text)
    r = doc.rules[0]
    assert isinstance(r.when, NodeWhenAst)
    assert isinstance(r.when.predicate, NotAst)
    assert isinstance(r.when.predicate.item, CompareAst)
    assert r.when.predicate.item.left.path == "layer"


def test_inline_predicate_string_is_supported():
    text = """
rule:
  id: r1
  name: Inline
  target: dependency
  when:
    all:
      - from.layer == domain
"""
    doc = parse(text)
    r = doc.rules[0]
    assert isinstance(r.when, DependencyWhenAst)
    assert isinstance(r.when.predicate, AndAst)
    assert len(r.when.predicate.items) == 1
    c = r.when.predicate.items[0]
    assert isinstance(c, CompareAst)
    assert c.left.path == "from.layer"
    assert c.op == "=="
    assert c.right.value == "domain"


def test_list_literal_shorthand_is_parsed_into_list_literal():
    text = """
rule:
  id: r1
  name: In list
  target: node
  when:
    all:
      - field: kind
        op: in
        value: [module, package]
"""
    doc = parse(text)
    r = doc.rules[0]
    c = r.when.predicate.items[0]
    assert isinstance(c, CompareAst)
    assert isinstance(c.right, LiteralAst)
    assert c.right.kind == "list"
    assert c.right.value == ["module", "package"]

# Tests: rule metadata fields

def test_parser_reads_severity_action_message_suggestion_description():
    text = """
rule:
  id: r1
  name: Foo
  description: Hello
  severity: warning
  action: forbid
  target: node
  message: Bad node
  suggestion: Rename it
  when:
    all:
      - field: layer
        op: ==
        value: domain
"""
    doc = parse(text)
    r = doc.rules[0]
    assert r.description == "Hello"
    assert r.severity == "warning"
    assert r.action == "forbid"
    assert r.message == "Bad node"
    assert r.suggestion == "Rename it"
    assert isinstance(r.metadata, dict)
    assert r.metadata.get("parser") == "dsl-v0"

# Tests: failures

def test_missing_when_is_parse_error():
    text = """
rule:
  id: r1
  name: Missing when
  target: node
"""
    with pytest.raises(RulesParseError) as ex:
        parse(text)

    msg = str(ex.value).lower()
    assert "missing" in msg
    assert "when" in msg


def test_when_missing_all_any_not_is_parse_error():
    text = """
rule:
  id: r1
  name: Bad when
  target: node
  when:
    x:
      - field: layer
        op: ==
        value: domain
"""
    with pytest.raises(RulesParseError) as ex:
        parse(text)
    assert "must contain" in str(ex.value).lower()


def test_invalid_indentation_raises_parse_error():
    text = """
rule:
  id: r1
  name: Bad indent
  target: node
  when:
    all:
      - field: layer
      op: ==
        value: domain
"""
    with pytest.raises(RulesParseError):
        parse(text)


def test_invalid_inline_predicate_is_parse_error():
    text = """
rule:
  id: r1
  name: Bad inline
  target: node
  when:
    all:
      - layer ==
"""
    with pytest.raises(RulesParseError):
        parse(text)
