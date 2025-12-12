
from dataclasses import dataclass
from pathlib import Path

from archguard.ir.types import ArchitectureIR
from archguard.model.types import ArchitectureModel
from archguard.plugins.interfaces import AnalyzeConfig
from archguard.plugins.registry import AnalyzerRegistry
from archguard.rules.types import RuleSet
from archguard.snapshot.types import Snapshot, SnapshotDiff
from archguard.reporting.types import Report, Violation, EngineError, RunInfo

# Engine config + result

@dataclass(frozen=True)
class EngineConfig:
    repo_root: Path
    model_file: Path | None
    rules_files: tuple[Path, ...]
    baseline: str | None = None
    changed_only: bool = False
    include_paths: tuple[Path, ...] = ()
    exclude_globs: tuple[str, ...] = ()
    output_format: str = "text"
    deterministic: bool = True


@dataclass(frozen=True)
class ScanResult:
    snapshot: Snapshot
    report: Report
    diff: SnapshotDiff | None

# Interfaces (imported in real code)

from archguard.plugins.interfaces import Analyzer
from archguard.plugins.registry import LoadedAnalyzer
from archguard.ir.merge import DefaultIRMerger
from archguard.ir.normalize import DefaultIRNormalizer
from archguard.model.loader import DefaultArchitectureModelLoader
from archguard.model.validator import DefaultArchitectureModelValidator
from archguard.model.resolver import DefaultModelResolver
from archguard.mapping.enricher import DefaultArchitectureEnricher
from archguard.rules.loader import DefaultRuleSourceLoader
from archguard.rules.dsl import DefaultDSLParser
from archguard.rules.compiler import DefaultRuleCompiler
from archguard.rules.evaluator import DefaultRuleEvaluator
from archguard.snapshot.builder import DefaultSnapshotBuilder
from archguard.snapshot.store import FsSnapshotStore
from archguard.snapshot.diff import DefaultSnapshotDiffEngine
from archguard.snapshot.baseline import DefaultBaselineService
from archguard.reporting.builder import DefaultReportBuilder
from archguard.reporting.renderers import DefaultRendererRegistry
from archguard.reporting.keys import DefaultViolationKeyFactory
from archguard.vcs.git import GitVCSProvider

# Default engine wiring

class DefaultArchGuardEngine:
    """
    The orchestrator. It wires components and runs the full pipeline.
    """

    def __init__(self) -> None:
        # Plugins/analyzers
        self.registry = AnalyzerRegistry()

        # IR pipeline
        self.ir_merger = DefaultIRMerger()
        self.ir_normalizer = DefaultIRNormalizer()

        # Model
        self.model_loader = DefaultArchitectureModelLoader()
        self.model_validator = DefaultArchitectureModelValidator()
        self.model_resolver = DefaultModelResolver()

        # Mapping/enrichment
        self.enricher = DefaultArchitectureEnricher()

        # Rules
        self.rule_source_loader = DefaultRuleSourceLoader()
        self.dsl_parser = DefaultDSLParser()
        self.rule_compiler = DefaultRuleCompiler()
        self.rule_evaluator = DefaultRuleEvaluator()

        # Snapshot/diff/baseline
        self.snapshot_builder = DefaultSnapshotBuilder()
        self.snapshot_store = FsSnapshotStore()
        self.diff_engine = DefaultSnapshotDiffEngine()
        self.key_factory = DefaultViolationKeyFactory()
        self.baseline_service = DefaultBaselineService()

        # Reporting
        self.report_builder = DefaultReportBuilder()
        self.renderers = DefaultRendererRegistry()

        # VCS (optional)
        self.vcs = GitVCSProvider()

    def scan(self, cfg: EngineConfig) -> ScanResult:
        engine_errors: list[EngineError] = []
        violations: list[Violation] = []
        diff: SnapshotDiff | None = None

        # ----------------------------
        # 0) VCS context (optional)
        # ----------------------------
        commit = self.vcs.current_commit(cfg.repo_root)

        # ----------------------------
        # 1) Load analyzers
        # ----------------------------
        self.registry.load_entrypoints()
        selected = self.registry.best_for_repo(cfg.repo_root)
        if not selected:
            engine_errors.append(EngineError(
                type="config_error",
                message="No analyzers found for this repository",
                location=None,
                details={"hint": "Install an analyzer plugin (e.g., archguard-python) or ensure source files exist."},
            ))
            # Continue: still produce a report with engine errors.

        # ----------------------------
        # 2) Analyze (produce raw IRs)
        # ----------------------------
        analyze_cfg = AnalyzeConfig(
            repo_root=cfg.repo_root,
            include_paths=cfg.include_paths,
            exclude_globs=cfg.exclude_globs,
            deterministic=cfg.deterministic,
            language_options={},
        )

        raw_irs: list[ArchitectureIR] = []
        for loaded in selected:
            try:
                raw_irs.append(loaded.analyzer.analyze(analyze_cfg))
            except Exception as e:
                engine_errors.append(EngineError(
                    type="runtime_error",
                    message=f"Analyzer '{loaded.analyzer.plugin_id}' failed",
                    location=None,
                    details={"error": repr(e), "analyzer": loaded.analyzer.plugin_id},
                ))

        # ----------------------------
        # 3) Merge + normalize IR
        # ----------------------------
        combined_ir = self.ir_merger.merge(raw_irs) if raw_irs else ArchitectureIR.empty(cfg.repo_root)
        normalized_ir = self.ir_normalizer.normalize(combined_ir)

        # ----------------------------
        # 4) Load + validate model (architecture.yaml)
        # ----------------------------
        model: ArchitectureModel | None = None
        if cfg.model_file and cfg.model_file.exists():
            try:
                model = self.model_loader.load(cfg.model_file)
                engine_errors.extend(self.model_validator.validate(model))
                model = self.model_resolver.resolve(model)
            except Exception as e:
                engine_errors.append(EngineError(
                    type="config_error",
                    message="Failed to load architecture model",
                    location={"file": str(cfg.model_file), "start": {"line": 1, "column": 1}},
                    details={"error": repr(e)},
                ))
                model = None

        # ----------------------------
        # 5) Enrich IR using model mapping
        # ----------------------------
        enriched_ir = normalized_ir
        if model is not None:
            try:
                enriched_ir = self.enricher.enrich(normalized_ir, model)
            except Exception as e:
                engine_errors.append(EngineError(
                    type="runtime_error",
                    message="Failed to enrich IR with architecture model mapping",
                    location=None,
                    details={"error": repr(e)},
                ))

        # ----------------------------
        # 6) Load + parse + compile rules
        # ----------------------------
        try:
            sources = self.rule_source_loader.load_sources(cfg.rules_files)
            ast_file = self.dsl_parser.parse_many(sources, source_names=[str(p) for p in cfg.rules_files])
            ruleset: RuleSet = self.rule_compiler.compile(ast_file)
        except Exception as e:
            engine_errors.append(EngineError(
                type="rules_error",
                message="Failed to load/parse/compile rules",
                location=None,
                details={"error": repr(e)},
            ))
            ruleset = RuleSet.empty()

        # ----------------------------
        # 7) Evaluate rules -> violations
        # ----------------------------
        try:
            violations = self.rule_evaluator.evaluate(enriched_ir, ruleset)
        except Exception as e:
            engine_errors.append(EngineError(
                type="runtime_error",
                message="Rule evaluation failed",
                location=None,
                details={"error": repr(e)},
            ))
            violations = []

        # ----------------------------
        # 8) Build snapshot and load baseline snapshot (optional)
        # ----------------------------
        snapshot = self.snapshot_builder.build(
            enriched_ir,
            meta={"commit": commit, "repo_root": str(cfg.repo_root)},
        )

        baseline_snapshot: Snapshot | None = None
        if cfg.baseline:
            if self.snapshot_store.exists(cfg.baseline):
                baseline_snapshot = self.snapshot_store.load(cfg.baseline)
                diff = self.diff_engine.diff(baseline_snapshot, snapshot)
                violations = self.baseline_service.mark_status(
                    violations=violations,
                    baseline_snapshot=baseline_snapshot,
                    key_factory=self.key_factory,
                )
            else:
                engine_errors.append(EngineError(
                    type="config_error",
                    message=f"Baseline snapshot not found: {cfg.baseline}",
                    location=None,
                    details={"hint": "Create a baseline with `archguard snapshot save --ref <name>`"},
                ))

        # Always save the current snapshot (ref decision is policy; here use 'latest')
        self.snapshot_store.save(snapshot, ref="latest")

        # ----------------------------
        # 9) Build report
        # ----------------------------
        report = self.report_builder.build(
            run=RunInfo(
                repo_root=str(cfg.repo_root),
                commit=commit,
                model_file=str(cfg.model_file) if cfg.model_file else None,
                rules_files=[str(p) for p in cfg.rules_files],
                baseline_ref=cfg.baseline,
                mode="changed_only" if cfg.changed_only else "full",
            ),
            violations=violations,
            engine_errors=engine_errors,
            diff=diff,
        )

        return ScanResult(snapshot=snapshot, report=report, diff=diff)
