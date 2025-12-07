# ArchGuard

**A Python-native architecture rules engine for enforcing architectural boundaries, detecting drift, and visualizing project structure.**

ArchGuard helps Python teams keep their architecture clean, modular, and maintainable.  
It analyzes your entire codebase, enforces rules for imports, naming, and layered design,  
and provides developer-friendly reporting and CI integrations.

---

## Features (Planned & In Development)

### Architecture Rules

- **Import Rules** — enforce allowed or forbidden dependencies  
- **Naming Rules** — enforce naming conventions across modules  
- **Layered Architecture Rules** — define layers and ensure proper boundaries  

### Static Indexer

- AST-based **ProjectIndex** scanning your entire codebase  
- One-time project analysis reused by all rules  
- Foundation for visuals, drift detection, and fast rule evaluation  

### Testing Integration

- Native **pytest integration**
- Human-readable violation reports  
- Works with or without configuration files  

### CI-Focused Capabilities

- **Only fail on new violations** (baseline comparison)  
- **Check only changed files** using Git diff  
- Ideal for incremental adoption in large or legacy codebases  

### Visualization

- Generate dependency graphs (modules & layers)  
- Local HTML explorer with interactive visualizations  
- Quickly diagnose coupling, cycles, and hotspots  

### Architecture Contracts (Code + Config)

- Python DSL for defining architecture rules programmatically  
- YAML/JSON configuration support for declarative architecture contracts  

---

## Quick Example (Early API Sketch)

```python
from archguard import modules

def test_presentation_does_not_access_infrastructure():
    rule = (
        modules(root="myapp")
        .that_reside_in("myapp.presentation..")
        .should_not_import("myapp.infrastructure..")
    )
    rule.check()
```

Layer example:

```python
from archguard import layers

def test_layered_architecture():
    rule = (
        layers(root="myapp")
        .define(
            presentation="myapp.presentation..",
            domain="myapp.domain..",
            infrastructure="myapp.infrastructure..",
        )
        .where("presentation").may_only_access("domain")
        .where("domain").may_only_access("infrastructure")
        .where("infrastructure").may_not_be_accessed_by_any_layer()
    )
    rule.check()
```

---

## Installation

*(Not yet available — package will be published to PyPI once v0.1.0 is released.)*

```bash
pip install archguard
```

---

## Roadmap

ArchGuard follows a clear release plan from core features to full architecture governance.

### **v0.1.0 – Core Rule Engine**

* Import rules
* Naming rules
* Basic AST scanning
* PyTest integration
* Human-readable reporting

### **v0.2.0 – Indexer + Layer Rules**

* Central `ProjectIndex`
* Layered architecture rules
* CLI: `archguard scan`

### **v0.3.0 – CI Integration**

* Fail only on new violations
* Check only changed files
* Git diff support

### **v0.4.0 – Visual Explorer**

* Dependency graph output
* Interactive HTML explorer
* CLI: `archguard serve`

### **v0.5.0 – Architecture Contracts**

* YAML/JSON config support
* Python DSL
* Contract-driven rule evaluation

For the full detailed roadmap:
👉 **[ROADMAP.md](./ROADMAP.md)**

👉 **[RELEASE_PLAN.md](./RELEASE_PLAN.md)**

---

## Project Goals

ArchGuard aims to become:

* A **standard tool** for Python architecture testing
* A foundation for **visualizing and understanding large codebases**
* A **CI-friendly gatekeeper** preventing architecture drift
* A flexible platform for architecture contracts across teams and repositories

---

## 📂 Repository Structure (Early Sketch)

```
archguard/
  ├── rules/
  ├── indexer/
  ├── reporting/
  ├── cli/
  ├── pytest_plugin.py
  ├── __init__.py
examples/
tests/
ROADMAP.md
RELEASE_PLAN.md
```

---

## Contributing

Contributions, ideas, and feedback are welcome!

Please check:

* **[CONTRIBUTING.md](./CONTRIBUTING.md)** (coming soon)
* GitHub issues for tasks & discussions
* GitHub Project board for roadmap progress

---

## License

MIT License
(See `LICENSE` file for full text.)
