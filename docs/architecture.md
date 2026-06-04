# Architecture

## 1. Core Engine
- Python-based Monte Carlo simulation engine
- Supports:
  - PERT distributions
  - Triangular distributions
- Reproducibility via `--seed`

---

## 2. Inputs
- YAML-defined scenarios ("Risk Shards")
- JSON Schema validation
- Scenario structure includes:
  - Frequency
  - Impact
- Organization profiles for evidence matching and calibration context
- Calibration profiles that map reviewed evidence into scenario ranges
- Control profiles as transformations, not embedded scenario properties

RiskShard does not currently apply heuristic contextual multipliers from organization profile fields. Org-specific analysis should flow through evidence-backed calibration and produce an explicit scenario YAML before simulation.

---

## 3. Outputs
- Per-shard statistics:
  - Mean
  - P95 / P99
- Portfolio aggregation
- Loss Exceedance Curve (LEC)
- JSON export
- Calibration reports with selected evidence, excluded evidence, warnings, and assumptions

---

## 4. Evidence Calibration Flow

```text
Source registry + gathered manifest
    ↓
Reviewed extractions
    ↓
Normalized evidence records
    ↓
Calibration profile + organization profile
    ↓
Calibrated scenario YAML
    ↓
Simulation engine
```

---

## 5. Control Simulation Layer

Transforms RiskShard from a calculator → decision engine.

### Concept
Controls are **transformations applied to scenarios**, not embedded properties.

### Components

#### 5.1 Control Objects
- Encapsulate risk reduction logic
- Examples:
  - Frequency reduction
  - Impact reduction

#### 5.2 Control Engine
- Applies one or multiple controls to a scenario
- Produces a modified scenario

#### 5.3 Orchestration Layer
- Runs:
  1. Baseline simulation
  2. Controlled simulation
- Ensures separation from core engine

#### 5.4 Comparator
- Computes:
  - Delta (mean, P95, P99)
  - % reduction

---

## 6. Execution Flow

```text
Scenario YAML
    ↓
Simulation Engine → Baseline Results
    ↓
Control Engine → Modified Scenario
    ↓
Simulation Engine → Controlled Results
    ↓
Comparator → Decision Output
