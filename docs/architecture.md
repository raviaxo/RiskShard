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

---

## 3. Outputs
- Per-shard statistics:
  - Mean
  - P95 / P99
- Portfolio aggregation
- Loss Exceedance Curve (LEC)
- JSON export

---

## 4. Control Simulation Layer (NEW)

Transforms RiskShard from a calculator → decision engine.

### Concept
Controls are **transformations applied to scenarios**, not embedded properties.

### Components

#### 4.1 Control Objects
- Encapsulate risk reduction logic
- Examples:
  - Frequency reduction
  - Impact reduction

#### 4.2 Control Engine
- Applies one or multiple controls to a scenario
- Produces a modified scenario

#### 4.3 Orchestration Layer
- Runs:
  1. Baseline simulation
  2. Controlled simulation
- Ensures separation from core engine

#### 4.4 Comparator
- Computes:
  - Delta (mean, P95, P99)
  - % reduction

---

## 5. Execution Flow

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