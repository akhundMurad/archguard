# ArchGuard Roadmap

This document defines the long-term development plan for **ArchGuard**, a Python-native architecture rules engine designed to enforce structural boundaries, detect architecture drift, visualize dependencies, and empower teams to govern code evolution over time.

ArchGuard treats architecture as a **first-class testable artifact**.  
It creates a full snapshot of your software structure and applies rules against it — in CI, in development, or visually.

---

## Vision

ArchGuard's core philosophy:

- **Architecture should be explicit.**  
- **Architecture should be testable.**  
- **Architecture should evolve without drifting.**  
- **Architecture violations should be visible — immediately.**  
- **Architecture should be explainable through visuals and analysis.**

To achieve this, ArchGuard provides:

1. Rule engine (import, naming, layers)  
2. Project-wide static index (structural snapshot)  
3. CI-aware features (baseline, changed-only)  
4. Visual explorer for understanding modules, layers, and dependencies  
5. Architecture contracts (as code + config)

Together these form a comprehensive **architecture intelligence system for Python**.

---

## Core Concepts

ArchGuard is built on several internal pillars:

### **1. Project Index (Static Snapshot)**

A *complete frozen representation* of the project's modules, imports, classes, and file structure at a moment in time.

Snapshot includes:

- Module-to-file mapping  
- Import graph (directed, weighted)  
- Class metadata (names, decorators, bases, line numbers)  
- File checksums (for changed-only logic)

Snapshotted structure is stored as:

- In-memory `ProjectIndex`  
- Optional JSON snapshot on disk  
- Stable identifiers for modules + symbols  

### **2. Rule Engine**

Rules operate on a project snapshot:

- Import rules  
- Naming rules  
- Layered architecture rules  

Snapshots make rule evaluation:

- Fast  
- Deterministic  
- CI-friendly  
- Reproducible for baselines  

### **3. Baselines**

Baselines define which *existing* violations are currently tolerated.

Baselines store:

- Rule ID  
- Violation signature  
- Snapshot version/hash  

ArchGuard compares current violations against baseline snapshot and only fails on **new violations**.

### **4. Changed-Only Checks**

ArchGuard detects changes by comparing:

- Current snapshot’s file hashes  
- Previous snapshot (or baseline snapshot)  

This allows:

- Only checking rules affected by modified modules  
- Ultra-fast CI runs  
- PR impact isolation  

### **5. Visual Explorer**

A UI for visualizing:

- Module dependency graph  
- Layer interactions  
- Import hotspots  
- Violations  
- Snapshot differences (future)

---

## Milestones Overview

| Version | Focus |
|--------|--------|
| **v0.1.0** | Rule engine: imports, naming, pytest integration |
| **v0.2.0** | Project indexer + layered architecture rules |
| **v0.3.0** | Snapshots, baselines, changed-only |
| **v0.4.0** | Visual explorer (graphs + UI) |
| **v0.5.0** | Architecture contracts (config + DSL) |
| **v1.0.0** | Stable release, polished UX + docs |

---

## v0.1.0 — Core Rule Engine (MVP)

### Objective

Create the minimal, usable architecture testing toolkit.

### Features  

#### Import Rules

- Module selectors (`modules().that_reside_in(...)`)  
- Forbidden dependencies (`should_not_import`)  
- Allowed-only dependencies (`should_only_import`)  

#### Naming Rules

- Class-based selectors  
- Pattern matching for names  
- Validate location of selected classes  

#### AST Scanning (per rule)

- Lightweight scan of each module invoked by the rule  
- Extract imports and class definitions  
- Fast, no caching yet  

#### PyTest Integration

- Simple plugin  
- Rules written inside test files  
- Failures raised as `ArchitectureViolationError`  

#### Human-Readable Reporting

- Pretty, multi-line violation blocks  
- Display:
  - module  
  - offending import  
  - file path  
  - line number  

### Deliverables

- First PyPI release  
- Example project in `examples/basic/`  
- Initial documentation: Quickstart + simple rules  

---

## v0.2.0 — Project Indexer + Layered Architecture Rules

### Objective

Centralize analysis and enable powerful architecture rules.

### Features

---

## **1. Project Indexer (Static Snapshot v1)**

A single-pass static analyzer that builds a **complete snapshot** of the project:

#### Captures

- Modules  
- Imports  
- Classes  
- Decorators  
- Base classes  
- File paths  
- Line numbers  
- Checksums / content hashes  

#### Benefits

- Rules use the same data source  
- Major performance boost  
- Enables future features:
  - snapshots  
  - baseline  
  - changed-only  
  - visuals  

#### CLI

```bash
archguard scan myapp/ -o snapshot.json
```

---

## **2. Layered Architecture Rules**

The first high-level structural rule system.

API:

```python
layers(root="myapp")
  .define(
    presentation="myapp.presentation..",
    domain="myapp.domain..",
    infrastructure="myapp.infrastructure..",
  )
  .where("presentation").may_only_access("domain")
  .where("domain").may_only_access("infrastructure")
  .where("infrastructure").may_not_be_accessed_by_any_layer()
  .check()
```

#### Implemented using

* Import graph from snapshot
* Layer-to-modules mapping
* Layer violation examiner

---

## **3. Index Integration**

- Rule selectors (`modules()`, `classes()`, `layers()`) now use snapshot index
- Index loaded lazily or via CLI-generated `snapshot.json`

---

### Deliverables

* Full static index implementation
* Layer rule engine
* CLI for scanning
* Extended documentation + examples

---

## v0.3.0 — Snapshots, Baselines, Changed-Only Checks

### Objective

Enable CI-friendly workflows and incremental adoption.

---

## **1. Snapshot v2**

Snapshot now includes:

* Module graph
* Layer mapping (optional)
* File content hashes
* Rule execution metadata (optional)

Stored as `snapshot.json`.

---

## **2. Baseline Mode — Fail Only on New Violations**

CLI:

```bash
archguard baseline --snapshot snapshot.json --out baseline.json
```

Baseline contains:

* Project snapshot hash
* Violations grouped by rule ID
* Violation signatures
* Optional "accepted violation explanation" (future feature)

#### On rule run:

* Load baseline
* Compare with current violations
* Only fail if:

  * Violation is new
  * Violation signature changed
  * A rule gained new offenders

This enables safe onboarding in legacy codebases.

---

## **3. Changed-Only Evaluation**

Using two snapshots:

* `snapshot_before.json` (from main branch)
* `snapshot_after.json` (current working tree)

ArchGuard compares:

* File-level checksum changes
* Modules impacted
* Reverse dependencies that might be affected

Rule engine then evaluates only:

* Changed modules
* Modules importing changed modules
* Graph neighbors (configurable)

CLI:

```bash
archguard check --changed-only
```

PyTest flag:

```
pytest --archguard-changed-only
```

#### Performance goals

* Reduce rule evaluation to ~5–10% of full scan
* Ideal for large PRs, monorepos, microservices

---

## **4. Git Integration**

* `git diff` adapter
* Optional: use `git ls-files` for tracking uncommitted changes
* Fallback if git unavailable

---

### Deliverables

* Snapshot design documented
* Baseline workflow documented
* Changed-only mechanics documented
* GitHub Actions example integrating both

---

## v0.4.0 — Visual Explorer

### Objective

Provide deep architectural insights through interactive visualizations.

---

## **1. Dependency Graph Export**

Graph types:

* Module dependency graph
* Layer dependency graph
* Import weights
* Cycle detection

JSON format:

```json
{
  "nodes": [...],
  "edges": [...]
}
```

---

## **2. HTML Visual Explorer**

CLI:

```bash
archguard serve --snapshot snapshot.json
```

Features:

* Zoomable, searchable dependency graph
* Highlight:

  * violations
  * cycles
  * heavy import paths
* Layer visualization (layer-to-layer imports)
* Details panel for each node:

  * file
  * imports
  * outgoing and incoming edges
  * rule violations

---

## **3. Snapshot Comparisons (Optional Preview)**

UI comparison between two snapshots:

* "What changed" map
* New violations vs resolved violations
* Modules with altered dependencies

(Not required for 0.4 but feasible with snapshot architecture.)

---

### Deliverables

* Bundled static UI (React/Vite or lightweight JS)
* Graph backend generation
* Documentation + screenshots

---

## v0.5.0 — Architecture Contracts (DSL + Config)

### Objective

Define architecture using either Python code or configuration files.

---

## **1. Python DSL**

```python
from archguard import Contract

contract = Contract(root="myapp")
contract.layer("domain", "myapp.domain..")
contract.rule("only_domain_access") \
    .import_rule("myapp.presentation..") \
    .should_not_import("myapp.domain..")

contract.check()
```

---

## **2. YAML/JSON Contracts**

`archguard.yaml` example:

```yaml
root_package: myapp

layers:
  presentation: myapp.presentation..
  domain: myapp.domain..
  infrastructure: myapp.infrastructure..

rules:
  - id: presentation_only_calls_domain
    type: layer_access
    from: presentation
    only_to: [domain]

  - id: repository_naming
    type: naming
    target: classes
    where:
      name_ends_with: Repository
    must_reside_in: myapp.infrastructure.repositories..
```

---

## **3. CLI Support**

```bash
archguard check --config archguard.yaml
```

---

### Deliverables

* Config schema
* DSL reference
* Config <-> DSL translation documentation
* Example architecture contract repositories

---

## v1.0.0 — Stable Release

### Requirements

* Fully stable rule and selector APIs
* Complete snapshot engine
* Visual explorer polished
* Strong documentation:

  * Quickstart
  * Rule reference
  * Architecture contracts
  * CI integration
  * Visual exploration guide
* Real-world examples (FastAPI, Django, services)
* Strict test coverage

---

## Future Extensions (Post-1.0)

These ideas expand ArchGuard into a full architecture governance suite:

* Django/FastAPI presets
* Type-aware rules (via mypy AST)
* Plugin system for custom rules
* Architecture drift analytics
* Hotspot detection (fan-in/out metrics)
* Refactoring suggestions
* Multi-repo, multi-service governance
* Snapshot diff visualizations

---

## Summary

ArchGuard’s roadmap moves from:

* ✔ **Rule engine**
* ✔ **Project indexing**
* ✔ **Snapshots + CI tooling**
* ✔ **Visualization**
* ✔ **Architecture contracts**

...toward a sophisticated, extensible architecture intelligence system.

ArchGuard will enable teams to **understand, enforce, track, and evolve** their architecture with confidence — over time, across teams, and across entire codebases.
