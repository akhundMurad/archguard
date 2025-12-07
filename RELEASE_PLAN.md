# ArchGuard Release Plan

This document outlines the planned version releases for **ArchGuard**, a Python architecture governance toolkit.  
Each release increment introduces a cohesive milestone, moving ArchGuard toward a full architecture rules engine, snapshot-based analysis system, CI-aware governance tool, and visual explorer.

ArchGuard follows **Semantic Versioning (SemVer)**:

- **0.x** — rapid development, API may change  
- **1.x** — stable, production-ready contracts  
- **≥2.x** — long-term continuity with backward compatibility  

---

# v0.1.0 — Core Architecture Rule Engine (MVP)

### Goal  
Deliver a minimal but functional rule engine integrated with pytest.

### Scope  
#### Import Rules  
- `modules().that_reside_in(pattern)`  
- `should_not_import(pattern)`  
- `should_only_import(patterns)`  

#### Naming Rules  
- Class selectors  
- Regex name matching  
- `and_name_ends_with()`  
- `should_reside_in(pattern)`  

#### AST-based Scanning (per rule invocation)  
- Extract imports  
- Extract classes  
- No shared project index yet  

#### PyTest Integration  
- Lightweight plugin  
- Rules defined in normal test files  
- Failures raised as `ArchitectureViolationError`  

#### Human-Readable Reporting  
- Grouped violations  
- File paths + line numbers  
- Pretty multi-line blocks  

### 📦 Deliverables  
- PyPI release  
- Example project  
- README Quickstart  

---

# v0.2.0 — Project Indexer + Layered Architecture Rules

### Goal  
Introduce a centralized static index and high-level layer-based rules.

### Scope  

## 1. Static Project Index (Snapshot v1)
- Full AST scan of the entire project  
- Stores:  
  - modules  
  - imports  
  - classes  
  - decorators  
  - file paths  
  - line numbers  
- Replaces per-rule scanning  
- Enables future snapshot-based features  

#### CLI:
```bash
archguard scan src/ -o snapshot.json
```

## 2. Layered Architecture Rules

* Define mapping between layers and module patterns
* Enforce access rules at module or layer level
* Powered by the index's import graph

API:

```python
layers(root="myapp")
  .define(...)
  .where("presentation").may_only_access("domain")
  ...
  .check()
```

### Deliverables

* Complete index system
* Layer rule engine
* Updated documentation
* Performance improvements

---

# v0.3.0 — Snapshots, Baseline Support, Changed-Only Checks

### Goal

Enable CI adoption and incremental enforcement for legacy systems.

### Scope

## 1. Snapshot v2

Enhancements:

* File checksums for each module
* Dependency graph (directed, weighted)
* Snapshot metadata
* Stable module identifiers

Snapshots become the foundation for:

* baseline comparison
* changed-only evaluation
* visual explorer

---

## 2. Baseline Mode (Only Fail on New Violations)

Baseline workflow:

```bash
archguard baseline --snapshot snapshot.json --out baseline.json
archguard check --baseline baseline.json
```

Baseline stores:

* accepted violations
* rule IDs
* violation signatures (deterministic)
* snapshot hash

CI fails only if:

* a new violation appears
* an existing violation changes signature
* rule definitions change (detected via hashing)

---

## 3. Changed-Only Checks

Enable fast evaluation by limiting rule checks to touched modules.

Mechanisms:

* Compare `snapshot_before.json` and current snapshot
* Identify changed modules via file checksums
* Expand to affected neighbors via import graph
* Evaluate rules only for impacted modules

CLI:

```bash
archguard check --changed-only
```

PyTest flag:

```
pytest --archguard-changed-only
```

---

### Deliverables

* Snapshot storage format v2
* Baseline comparison tool
* Changed-only evaluator
* GitHub Actions examples
* Documentation for CI workflows

---

# v0.4.0 — Visual Explorer (Dependency Graph + UI)

### 🎯 Goal

Enable visual understanding of architecture structure and evolution.

### 🔧 Scope

## 1. Graph Export

Generate graph models:

* Module → module dependency graph
* Layer → layer graph
* Weighted edges (# imports)

Export format:

```bash
archguard graph --snapshot snapshot.json --out graph.json
```

## 2. Web Explorer

CLI:

```bash
archguard serve --snapshot snapshot.json
```

UI capabilities:

* Interactive dependency graph
* Highlight:

  * import cycles
  * heavy edges
  * layer violations
* Module detail sidebar
* Search modules, toggle layers
* (Optional) snapshot diff preview: old vs new graph

Underlying tech:

* Static HTML + JS bundle (e.g., D3/Cytoscape)
* Bundled in Python package

---

### Deliverables

* Graph generator
* Web UI
* Documentation + screenshots

---

# v0.5.0 — Architecture Contracts (DSL + Config)

### Goal

Support explicit architecture definitions as either Python code or configuration.

### Scope

## 1. Python DSL

Example:

```python
contract = Contract(root="myapp")
contract.layer("domain", "myapp.domain..")
contract.rule("no_infra_imports").import_rule("myapp.domain..").should_not_import("myapp.infrastructure..")
contract.check()
```

## 2. YAML/JSON Config Support

Example (`archguard.yaml`):

```yaml
root_package: myapp

layers:
  domain: myapp.domain..
  infrastructure: myapp.infrastructure..

rules:
  - id: domain_to_infrastructure_only
    type: layer_access
    from: domain
    only_to: [infrastructure]
```

## 3. CLI Integration

```bash
archguard check --config archguard.yaml
```

### Deliverables

* Config schema
* DSL reference
* Examples for config-based governance

---

# v1.0.0 — Stable Release

### Goal

Deliver a polished, production-grade architecture governance toolkit.

### Requirements

* Stable API for:

  * rule engine
  * selectors
  * DSL
  * config
* Complete snapshot engine
* Mature visual explorer
* Strong documentation:

  * Quickstart
  * Rule reference
  * Layer architecture guide
  * CI usage
  * Visualization guide
* Full test suite
* Real-world examples (FastAPI, Django, services)

---

# Future Releases (Beyond v1.0)

Potential enhancements:

* Django & FastAPI presets
* Type-aware rules (via mypy AST or typed-ast)
* Rule plugins
* IDE integration (PyCharm, VSCode)
* Architecture drift heatmaps
* Full snapshot diff viewer
* Monorepo/multi-service governance
* Pattern mining & suggestion engine
* Refactoring hints based on rule violations

---

# Summary

This release plan guides ArchGuard from a minimal rule engine (0.1)
to a powerful architecture intelligence platform with:

* snapshots
* baselines
* visual exploration
* CI workflows
* architecture contracts

Each milestone builds on previous foundations, culminating in a stable 1.0 framework for Python architecture analysis and governance.
