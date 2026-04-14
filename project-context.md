# 🛡️ RiskShard: Project Manifest & Global Utility Strategy
**Mission:** To be the "Metasploit" of Quantitative Risk—converting abstract threats into executable, machine-readable data.

---

## 🎯 I. The Vision & Marketing Strategy
**The Problem:** GRC data is currently "Dead Data"—trapped in subjective "High/Medium/Low" heatmaps and static PDF reports that offer zero actuarial value to the Board.

**The Solution:** **RiskShard**. An open-source, machine-readable repository of FAIR-native risk scenarios. We provide the *data shards* and the *logic engines* so GRC teams can build defensible financial models.

### Target Audience:
1. **The CISO:** To justify security spend with hard dollars, not colors.
2. **The GRC Analyst:** To automate the "Risk Register" using crowdsourced benchmarks.
3. **AI Agents (NemoClaw/OpenClaw):** To act as the "API for Risk," allowing agents to query: *"What is the benchmark loss for a Deepfake attack in the Finance sector?"*

### Core Tenets:
- **YAML-First:** Everything is machine-readable and AI-ready.
- **Universal Benchmarking:** Crowdsourced loss data (Frequency/Magnitude) for global utility.
- **Low Maintenance:** Automation-heavy validation via GitHub Actions.

---

## ✅ II. Engineering State of Charge (Phase 2: Verified)

### ⚙️ Technical Specs:
- **Runtime:** Python 3.14 (Homebrew Managed).
- **Environment:** Dedicated `(venv)` toolbox with `pyyaml` installed.
- **Current Logic:** `fair_calc.py` executes 10,000 Monte Carlo trials based on YAML inputs.

### 📂 Repository Structure:
- `scenarios/`: The library of "Risk Shards" (e.g., `saas_ransomware.yaml`).
- `scripts/`: Python engines (e.g., `fair_calc.py`).
- `project-context.md`: This file (The Source of Truth).
- `README.md`: The public manifesto and setup guide.

---

## 🚀 III. The Roadmap

### Phase 2.5 (Next Up): The Annualization Update
- **Goal:** Move from "Single Impact" to "Annual Loss Expectancy" (ALE).
- **Action:** Update shards to include **Loss Event Frequency (LEF)** parameters.
- **Formula:** `ALE = Frequency (Trials) × Impact (Trials)`.

### Phase 3: Scaling & AI
- Integration with AI agents for natural language risk querying.
- Community-driven "Universal Benchmark" database.

---

## 💻 IV. Offline Task List (For Sergio)
- [ ] **Data Hunting:** Collect real-world breach data from Verizon DBIR or SEC filings to build new shards.
- [ ] **Schema Design:** Draft a "perfect" YAML structure that includes both Frequency and Magnitude.
- [ ] **Marketing:** Review the README for "Metasploit" tone consistency.