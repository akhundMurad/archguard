"""
ArchGuard Rules Engine
=====================

This package defines the Architecture Rules system for ArchGuard.

It provides:
- A rules AST and parsers (DSL/YAML)
- A compiler that turns rules into fast runtime predicates
- An evaluator that applies rules to Architecture IR
- Baseline comparison for "only fail on new violations"
- Human-readable explanations for CLI / IDE integrations

Typical flow:
    rules = load_rules("architecture.rules")
    ir = analyze_project(...)
    violations = evaluate(ir, rules)
"""

from pathlib import Path

from archguard.rules.ast import (
    RulesDocumentAst,
    RuleAst,
    WhenAst,
    DependencyWhenAst,
    NodeWhenAst,
    ExprAst,
    AndAst,
    OrAst,
    NotAst,
    CompareAst,
    FieldAst,
    LiteralAst,
)
from archguard.rules.baseline import BaselineComparer, BaselineResult, ViolationKeyStrategy
from archguard.rules.compiler import RulesCompiler
from archguard.rules.evaluator import DefaultRuleEvaluator, RuleEvaluatorProtocol
from archguard.rules.explain import explain_rule, explain_violation
from archguard.rules.errors import RulesError, RulesParseError, RulesCompileError, RulesEvalError
from archguard.rules.parser import DslRulesParserV0, RulesParser
from archguard.rules.types import Rule, RuleAction, RuleSet, RuleTarget

__all__ = [
    # AST
    "RulesDocumentAst",
    "RuleAst",
    "WhenAst",
    "DependencyWhenAst",
    "NodeWhenAst",
    "ExprAst",
    "AndAst",
    "OrAst",
    "NotAst",
    "CompareAst",
    "FieldAst",
    "LiteralAst",
    # Runtime types
    "Rule",
    "RuleAction",
    "RuleTarget",
    "RuleSet",
    # Parsing / compiling
    "RulesParser",
    "DslRulesParserV0",
    "RulesCompiler",
    # Evaluation
    "RuleEvaluatorProtocol",
    "DefaultRuleEvaluator",
    # Baseline
    "ViolationKeyStrategy",
    "BaselineComparer",
    "BaselineResult",
    # Explain
    "explain_rule",
    "explain_violation",
    # Errors
    "RulesError",
    "RulesParseError",
    "RulesCompileError",
    "RulesEvalError",
]

# Convenience helpers (public API)

def load_rules(path: str | Path):
    """
    Load and compile rules from a file.

    Currently uses the v0 DSL parser.
    """
    parser = DslRulesParserV0()
    compiler = RulesCompiler()

    doc = parser.parse_file(path)
    return compiler.compile(doc)


def evaluate(ir, rules: RuleSet):
    """
    Evaluate compiled rules against IR or IRIndex.
    """
    evaluator = DefaultRuleEvaluator()
    return evaluator.evaluate(ir, rules)
