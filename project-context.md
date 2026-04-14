# 🛡️ RiskShard: Project Manifest & Global Utility Strategy
**Codename:** The "Metasploit" of Quantitative Risk.
**Positioning:** Moving GRC from subjective heatmaps to objective, defensible, actuarial-style risk modeling (FAIR methodology).

---

## 🎯 I. The Big Vision & Marketing

### The Problem
Most Risk/GRC data is trapped in expensive, proprietary PDF reports. Enterprises and SMBs have no reliable "benchmark" to perform defensible, quantitative financial estimation of potential losses.

### The Solution: RiskShard
An open-source, machine-readable repository of **"Risk Shards"** (YAML-first data points). Every shard represents a LEGO brick of crowdsourced loss data (Frequency + Magnitude). We provide the *data* and the *calculators* so organizations can run their own models without expensive consultants.

### Target Audience
1. **CISOs/CIOs:** To explain risk in dollars to the Board.
2. **GRC Analysts:** To replace "Medium/High" guesswork.
3. **AI Agents (e.g., NemoClaw/OpenClaw):** To automatically ingest real-world risk benchmarks into enterprise Risk Registers via simple queries (e.g., "What is the benchmark loss for a Deepfake attack in Finance?").

---

## ✅ II. Current State of Engineering (Phase 2: Done)

### 1. Repository Rebranding
Successfully executed the pivot from `OpenRiskData` to `RiskShard`. Repo renamed, README updated.

### 2. Environment Specifications
- **Python:** 3.14 (Homebrew Managed).
- **Venv:** Confirmed active and functional (`source venv/bin/activate`).
- **Dependencies:** `pyyaml` successfully installed within the venv.

### 3. Repository Architecture (Confirmed Functional)
```text
RiskShard/
├── project-context.md      # This file (The Manifest)
├── README.md               # How to install/use the tool
├── LICENSE                 # Apache 2.0 Open Source License
├── scenarios/              # The database of loss events
│   ├── saas_ransomware.yaml # Initial test shard
├── scripts/                # The logic engines
│   └── fair_calc.py        # Valid Monte Carlo simulation engine
└── venv/                   # Private toolbox (IGNORED BY GIT)