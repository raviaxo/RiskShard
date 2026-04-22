# 🛡️ RiskShard
> **The Metasploit of Risk Quantification.**  
> Move beyond "High / Medium / Low" — simulate cyber risk in financial terms and make defensible decisions.

---

## 🚀 What is RiskShard?

RiskShard is an open-source engine for **quantifying cyber risk using Monte Carlo simulation**.

It transforms risk from:
- subjective → measurable  
- static → simulated  
- descriptive → decision-oriented  

---

## 🎯 Why RiskShard?

Traditional GRC fails because:
- Risk is expressed as **colors, not dollars**
- Data is **static and subjective**
- Decisions are **not defensible**

**RiskShard fixes this by:**
- Modeling risk as **probability distributions**
- Running **thousands of simulations**
- Producing **financial outputs (Mean, P95, P99)**

---

## 🧠 Core Capabilities

### 🔢 Simulation Engine
- Monte Carlo simulation
- PERT & triangular distributions
- Reproducibility via `--seed`

### 📦 Scenario System
- YAML-defined risk scenarios ("shards")
- JSON schema validation
- Fully machine-readable and extensible

### 📊 Outputs
- Mean loss
- P95 / P99 (tail risk)
- Loss Exceedance Curves (LEC)
- JSON export

### 🧩 Decision Engine (NEW)
- Simulate security controls
- Modify frequency and/or impact
- Compare **before vs after**
- Quantify risk reduction

---

## ⚙️ Quick Start

### 1. Clone
```bash
git clone https://github.com/raviaxo/RiskShard.git
cd RiskShard