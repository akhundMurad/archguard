# ArchGuard — Architecture Testing & Architecture-as-Code

**Open-source static architecture analysis with drift detection and high-level architectural contracts**

ArchGuard is a tool for **architecture governance** that connects **static code analysis**,
**Architecture-as-Code**, **C4 modeling**, and **“Git for Architecture”** into a single workflow.

It is designed to make architecture **explicit, testable, reviewable, and versioned**, just like code.

---

## 🔷 Project Overview

ArchGuard consists of two complementary parts:

### **ArchGuard CLI (Open Source, MIT)**

A developer-first CLI tool that analyzes real codebases and builds a **low-level architecture model**:

* modules, packages, classes
* dependencies between files, layers, and services
* architectural layers (ui / application / domain / infra)
* detection of architectural rule violations
* architecture snapshots and diffs
* architecture drift detection
* CI / PR checks

### **ArchGuard Pro / SaaS (Commercial)**

A **high-level Architecture-as-Code platform** that defines and governs architecture at the system level:

* bounded contexts
* domains
* containers / services (C4 C1–C3)
* communication protocols (HTTP, gRPC, events)
* use cases / flows
* architectural rules and contracts
* mapping high-level architecture → code

The Pro platform stores architecture history, visualizes changes, and enforces architectural consistency across time.

---

## ✨ Key Features

### Static Architecture Analysis

* AST-based analysis (Python first; Java/TS/Go planned)
* import and dependency graph generation
* layer and container inference
* forbidden dependency detection
* DDD and Clean Architecture validation

### Architecture-as-Code

Define architecture directly in your repository:

```
architecture.yaml
archguard.rules
```

Supports:

* contexts, domains, containers
* layer mapping via glob patterns
* high-level service relations
* declarative architectural rules

### Architecture Rule DSL

Readable, expressive DSL for architecture testing:

```txt
rule "DDD: Domain must not depend on Infra" {
  id = "ddd_layering"
  severity = error

  when dependency {
    from.layer == "domain"
    to.layer   == "infra"
  }

  forbid "Domain layer must not depend on Infra layer"
}
```

### Architecture Drift Detection

ArchGuard compares:

* **actual architecture** (from code)
* **declared architecture** (high-level model)

and detects:

* newly introduced forbidden dependencies
* missing or unexpected services
* layer violations
* architectural erosion over time

### Snapshots & Diffs

Architecture is versioned just like code:

* snapshot generation per commit
* diffs between snapshots
* “fail only on new violations” mode
* PR-level architecture checks

### C4 Visualization (Pro)

* C1: System Context
* C2: Containers / Services
* C3: Components
* visual diff between architecture versions

---

## 🚀 Getting Started

### Installation

```bash
pip install archguard
```

(Planned: pipx, Homebrew, Docker, standalone binary)

---

## 🧭 CLI Usage

### Run architecture analysis

```bash
archguard scan .
```

### Check architectural rules

```bash
archguard rules check
```

### Create an architecture snapshot

```bash
archguard snapshot save
```

### Compare architecture versions

```bash
archguard diff HEAD~1
```

### Initialize architecture model

```bash
archguard init
```

This generates:

* `architecture.yaml` — high-level architecture model
* `archguard.rules` — architecture rule definitions

---

## 🏗️ High-Level Architecture Model

Example `architecture.yaml`:

```yaml
version: 1

system:
  id: healthcare-scheduling
  name: "Healthcare Scheduling"

containers:
  scheduling-api:
    context: scheduling
    code:
      roots:
        - path: "services/scheduling-api"
      layers:
        ui:
          - "services/scheduling-api/api/**"
        application:
          - "services/scheduling-api/app/**"
        domain:
          - "services/scheduling-api/domain/**"
        infra:
          - "services/scheduling-api/infra/**"
```

---

## 🧪 Architecture Rule DSL

Example `archguard.rules` file:

```txt
rule "No cross-context domain dependencies" {
  id = "domain_cross_context"
  severity = error

  when dependency {
    from.layer == "domain"
    to.layer   == "domain"
    from.context != to.context
  }

  forbid "Domain must not depend on domain of another bounded context"
}
```

---

## 📦 JSON Report Format (CI / IDE / PR)

ArchGuard produces a structured JSON report:

```bash
archguard scan --format json > archguard-report.json
```

Example:

```json
{
  "summary": {
    "total_violations": 5
  },
  "violations": [
    {
      "rule": {
        "id": "ddd_layering",
        "severity": "error"
      },
      "message": "Domain must not depend on Infra",
      "location": {
        "file": "services/domain/foo.py",
        "line": 12
      },
      "status": "new"
    }
  ]
}
```

This format is designed for:

* CI pipelines
* GitHub / GitLab PR comments
* IDE integrations
* SaaS ingestion and visualization

---

## 🌐 ArchGuard Pro (SaaS)

The commercial Pro platform provides:

* architecture history and snapshots
* visual architecture diffs
* C4 diagram rendering
* drift detection dashboards
* PR checks and comments
* multi-language analysis
* enterprise-grade architecture rules

The CLI remains **fully open-source (MIT)**.

---

## 🧱 Roadmap

See https://github.com/akhundMurad/archguard/issues/35 for details.

---

## 🤝 Contributing

Contributions, discussions, and feedback are welcome.
See `CONTRIBUTING.md`.

---

## 📜 License

* **ArchGuard CLI** — MIT License
* **ArchGuard Pro** — Commercial SaaS

---

## ⭐ Why ArchGuard?

* Architecture becomes **code**, not diagrams
* Architecture rules are **testable and enforceable**
* Architectural drift is detected early
* Architecture evolves **safely and transparently**
* Architecture review becomes part of the Git workflow
