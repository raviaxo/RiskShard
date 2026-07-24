import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
from pathlib import Path
from urllib.parse import urlparse

from engine.console import PROJECT_ROOT, RiskShardConsole
from engine.readiness import build_readiness_dashboard


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RiskShard Console</title>
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cpath d='M16 2 L29 12 L16 30 L3 12 Z' fill='%237c8cff'/%3E%3C/svg%3E">

  <style>
    :root {
      color-scheme: dark;
      /* Cool-ink base */
      --bg: #0b0e14;
      --panel: #111621;
      --panel-2: #161d2a;
      --line: #222b3a;
      --text: #e6edf3;
      --muted: #8794a8;
      /* Dual-signal: identity (indigo) for nav/labels/CTAs; data (cyan) for every numeric value. */
      --accent: #7c8cff;
      --identity-bg: rgba(124, 140, 255, 0.10);
      --data: #38d3e6;
      /* RAG — severity only */
      --sys: #35c98b;
      --accent-2: #f2b23e;
      --caution: #f2b23e;
      --danger: #f26d75;
      --alert: #f26d75;
      --input: #080b11;
      --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 14px;
      line-height: 1.45;
    }

    .app {
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr);
      height: 100vh;
      overflow: hidden;
    }

    aside {
      border-right: 1px solid var(--line);
      background: var(--panel);
      padding: 16px;
      height: 100vh;
      overflow-y: auto;
    }

    main {
      display: flex;
      min-width: 0;
      height: 100vh;
      min-height: 0;
      flex-direction: column;
    }

    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      min-height: 64px;
      padding: 14px 18px;
      border-bottom: 1px solid var(--line);
      background: #0d121c;
    }

    h1, h2 {
      margin: 0;
      font-weight: 650;
      letter-spacing: 0;
    }

    h1 { font-size: 18px; }
    h2 { font-size: 13px; color: var(--muted); }

    .status {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }

    .dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--sys);
      box-shadow: 0 0 0 3px rgba(53, 201, 139, 0.16);
    }

    .workflow-lanes {
      display: grid;
      gap: 12px;
      margin-top: 16px;
    }

    .lane {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(31, 36, 39, 0.45);
      padding: 10px;
    }

    .lane-title {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      color: var(--muted);
      font-family: var(--mono);
      font-size: 10.5px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.14em;
    }

    .lane-actions {
      display: grid;
      gap: 7px;
    }

    button {
      min-height: 44px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel-2);
      color: var(--text);
      cursor: pointer;
      font: inherit;
      text-align: left;
      padding: 8px 10px;
      display: grid;
      gap: 2px;
    }

    button.compact {
      min-height: 30px;
      padding: 6px 8px;
      font-size: 12px;
    }

    button:hover {
      border-color: var(--accent);
    }

    button.primary {
      border-color: var(--accent);
      background: var(--identity-bg);
    }

    button.warning {
      border-color: rgba(242, 178, 62, 0.5);
      background: rgba(242, 178, 62, 0.08);
    }

    button:focus-visible {
      outline: 2px solid var(--accent);
      outline-offset: 1px;
    }

    .button-title {
      font-weight: 640;
      letter-spacing: 0.01em;
    }

    .button-help {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.3;
    }

    .hint {
      color: var(--muted);
      font-size: 12px;
      margin: 12px 0 0;
    }

    .intro {
      margin-top: 14px;
      border: 1px solid rgba(124, 140, 255, 0.28);
      border-radius: 8px;
      background: var(--identity-bg);
      padding: 10px;
    }

    .intro-title {
      margin-bottom: 4px;
      font-weight: 650;
    }

    .dashboard {
      display: grid;
      gap: 14px;
      padding: 16px 18px;
      border-bottom: 1px solid var(--line);
      background: #0d121c;
    }

    .console-scroll {
      flex: 1;
      min-height: 0;
      overflow-y: auto;
    }

    .metric-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }

    .metric,
    .section {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      padding: 10px;
    }

    .metric-label {
      color: var(--muted);
      font-family: var(--mono);
      font-size: 10.5px;
      text-transform: uppercase;
      letter-spacing: 0.13em;
    }

    .item-meta {
      color: var(--muted);
      font-size: 12px;
    }

    .metric-value {
      margin-top: 5px;
      font-family: var(--mono);
      font-size: 19px;
      font-weight: 600;
      letter-spacing: -0.01em;
      color: var(--data);
    }

    .section-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 8px;
      font-weight: 650;
    }

    .list {
      display: grid;
      gap: 8px;
    }

    .item {
      display: grid;
      gap: 3px;
      padding: 8px 0;
      border-top: 1px solid rgba(52, 58, 62, 0.55);
    }

    .item:first-child {
      border-top: 0;
      padding-top: 0;
    }

    .item-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .badge {
      border-radius: 999px;
      border: 1px solid var(--line);
      padding: 2px 8px;
      font-size: 12px;
      white-space: nowrap;
    }

    .badge.good {
      border-color: rgba(53, 201, 139, 0.45);
      background: rgba(53, 201, 139, 0.08);
      color: var(--sys);
    }

    .badge.warn {
      border-color: rgba(242, 178, 62, 0.45);
      background: rgba(242, 178, 62, 0.08);
      color: var(--caution);
    }

    .badge.bad {
      border-color: rgba(242, 109, 117, 0.45);
      background: rgba(242, 109, 117, 0.08);
      color: var(--alert);
    }

    .dashboard-columns {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 10px;
    }

    .shard-list {
      display: grid;
      gap: 8px;
    }

    .shard-card {
      border-top: 1px solid rgba(52, 58, 62, 0.75);
      padding-top: 8px;
    }

    .shard-card:first-child {
      border-top: 0;
      padding-top: 0;
    }

    .trust-row {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
    }

    .context-actions {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
      margin-top: 10px;
    }

    .coverage-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }

    .coverage-table th,
    .coverage-table td {
      border-top: 1px solid rgba(52, 58, 62, 0.75);
      padding: 7px 6px;
      text-align: left;
      vertical-align: top;
    }

    .coverage-table th {
      color: var(--muted);
      font-weight: 650;
    }

    .param-grid {
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 4px;
      min-width: 230px;
    }

    .param-cell {
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 4px;
      text-align: center;
      font-size: 11px;
      white-space: nowrap;
    }

    button.param-cell {
      width: 100%;
      min-height: 28px;
      font-size: 11px;
      text-align: center;
    }

    .param-cell.good {
      border-color: #3b6d50;
      color: #94d7ad;
      background: rgba(40, 78, 55, 0.35);
    }

    .param-cell.warn {
      border-color: #72552b;
      color: #e5b76d;
      background: rgba(83, 62, 31, 0.35);
    }

    .param-cell.bad {
      border-color: #7b3e3e;
      color: #e19898;
      background: rgba(92, 42, 42, 0.35);
    }

    .row-actions {
      display: grid;
      gap: 5px;
      min-width: 96px;
    }

    .transcript {
      overflow: visible;
      padding: 18px;
      min-height: 220px;
    }

    .entry {
      border-bottom: 1px solid rgba(52, 58, 62, 0.75);
      padding: 12px 0;
    }

    .entry:first-child {
      padding-top: 0;
    }

    .command {
      color: var(--accent-2);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 13px;
      overflow-wrap: anywhere;
    }

    pre {
      margin: 8px 0 0;
      color: var(--text);
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 13px;
    }

    .input-bar {
      display: grid;
      flex: 0 0 auto;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      padding: 14px 18px;
      border-top: 1px solid var(--line);
      background: #141719;
    }

    input {
      min-width: 0;
      height: 40px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--input);
      color: var(--text);
      font: inherit;
      padding: 0 12px;
    }

    input:focus {
      outline: 2px solid rgba(96, 184, 132, 0.35);
      border-color: var(--accent);
    }

    .run-button {
      text-align: center;
      min-width: 76px;
    }

    @media (max-width: 780px) {
      .app { grid-template-columns: 1fr; }
      aside {
        border-right: 0;
        border-bottom: 1px solid var(--line);
        max-height: 42vh;
      }
      .metric-grid,
      .dashboard-columns,
      .context-actions {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <h1>RiskShard</h1>
      <h2>Evidence-backed risk scenario console</h2>
      <div class="intro">
        <div class="intro-title">What is a Risk Shard?</div>
        <div class="item-meta">A reusable cyber risk scenario for a specific geography, industry, company size, and threat. Use it to run a quantified narrative, inspect confidence, and improve missing evidence.</div>
      </div>
      <div class="workflow-lanes">
        <section class="lane">
          <div class="lane-title"><span>Start with your company</span></div>
          <div class="lane-actions">
            <button class="primary" data-command="demo"><span class="button-title">Guided demo</span><span class="button-help">Runs the whole first-run path automatically, with narration.</span></button>
            <button data-command="workflow"><span class="button-title">Recommended workflow</span><span class="button-help">Shows the shortest console path from context to run.</span></button>
            <button data-command="where"><span class="button-title">Where am I?</span><span class="button-help">Shows selected shard, inputs, last run, and next commands.</span></button>
            <button data-command="toprisks"><span class="button-title">Top risk readiness</span><span class="button-help">Ranks starter threats by current evidence coverage.</span></button>
            <button data-command="start over"><span class="button-title">Start over</span><span class="button-help">Clears selected shard, calibration, run state, and prompt.</span></button>
          </div>
        </section>
        <section class="lane">
          <div class="lane-title"><span>Find applicable Risk Shards</span></div>
          <div class="lane-actions">
            <button data-command="modules"><span class="button-title">Risk Shard Catalog</span><span class="button-help">Lists available shards and their country/industry/threat context.</span></button>
            <button data-command="use gb_finance_data_breach_midmarket"><span class="button-title">Use UK data breach</span><span class="button-help">Best current benchmark-review candidate.</span></button>
            <button data-command="use au_finance_ransomware_midmarket"><span class="button-title">Use AU ransomware</span><span class="button-help">Runnable shard with visible assumption gaps.</span></button>
          </div>
        </section>
        <section class="lane">
          <div class="lane-title"><span>Run and explain</span></div>
          <div class="lane-actions">
            <button data-command="consume"><span class="button-title">Consume model path</span><span class="button-help">Use a shard to produce an explainable result.</span></button>
            <button data-command="show options"><span class="button-title">Selected shard options</span><span class="button-help">Shows scenario, org profile, calibration, trials, and outputs.</span></button>
            <button data-command="run" class="warning"><span class="button-title">Run scenario</span><span class="button-help">Runs the selected shard and returns AVG, P50, P95, P99.</span></button>
            <button data-command="explain"><span class="button-title">Explain latest result</span><span class="button-help">Summarizes the latest calibration or simulation.</span></button>
            <button data-command="report json"><span class="button-title">Export JSON report</span><span class="button-help">Writes a reviewable local output after a run.</span></button>
            <button data-command="report exec"><span class="button-title">Board summary</span><span class="button-help">Writes a one-page board-ready executive Markdown after a run.</span></button>
          </div>
        </section>
        <section class="lane">
          <div class="lane-title"><span>Inspect and improve evidence</span></div>
          <div class="lane-actions">
            <button data-command="enhance"><span class="button-title">Enhance model path</span><span class="button-help">Improve evidence, calibration, and trust before wider use.</span></button>
            <button data-command="packs"><span class="button-title">Evidence pack</span><span class="button-help">Shows source-backed vs assumption-backed parameters.</span></button>
            <button data-command="challenge frequency.max"><span class="button-title">Challenge a number</span><span class="button-help">Shows the value, source, exact quote, and caveat behind one parameter.</span></button>
            <button data-command="coverage"><span class="button-title">Coverage &amp; confidence</span><span class="button-help">Grades each shard's data strength: can I use this number?</span></button>
            <button data-command="propose"><span class="button-title">Calibration proposal</span><span class="button-help">Suggests stronger selectors without silently changing files.</span></button>
            <button data-command="show gaps"><span class="button-title">Evidence gaps</span><span class="button-help">Shows what is missing before trust can increase.</span></button>
          </div>
        </section>
        <section class="lane">
          <div class="lane-title"><span>Govern data quality</span></div>
          <div class="lane-actions">
            <button data-command="readiness"><span class="button-title">Readiness dashboard</span><span class="button-help">Shows current coverage, trust, release, and next actions.</span></button>
            <button data-command="beta"><span class="button-title">Beta readiness</span><span class="button-help">Shows stricter product/data blockers before public operations.</span></button>
            <button data-command="feeds"><span class="button-title">Data feed governance</span><span class="button-help">Shows source freshness, confidence, and renewal status.</span></button>
            <button data-command="doctor"><span class="button-title">Local health check</span><span class="button-help">Checks environment, sources, evidence, and package readiness.</span></button>
            <button data-command="validate"><span class="button-title">Validate evidence</span><span class="button-help">Runs evidence quality gates.</span></button>
          </div>
        </section>
        <section class="lane">
          <div class="lane-title"><span>Contribute coverage</span></div>
          <div class="lane-actions">
            <button data-command="countries"><span class="button-title">Country roadmap</span><span class="button-help">Shows priority geographies for local contributors.</span></button>
            <button data-command="registry"><span class="button-title">Shard registry</span><span class="button-help">Shows the machine-readable shard-pack contract and current coverage.</span></button>
            <button data-command="countries GB"><span class="button-title">United Kingdom contribution detail</span><span class="button-help">GB is the taxonomy code for the UK.</span></button>
            <button data-command="preflight"><span class="button-title">Contributor preflight</span><span class="button-help">Checks proposed source/evidence/calibration packs.</span></button>
            <button class="primary" data-command="next"><span class="button-title">Next best actions</span><span class="button-help">Shows the most useful work to improve trust today.</span></button>
          </div>
        </section>
      </div>
      <p class="hint">Every button runs a real console command. Expert users can type commands directly below.</p>
    </aside>
    <main>
      <header>
        <div>
          <h1>Practitioner Console</h1>
          <h2 id="prompt">riskshard&gt;</h2>
        </div>
        <div class="status"><span class="dot"></span><span>Local</span></div>
      </header>
      <div id="console-scroll" class="console-scroll">
        <section id="dashboard" class="dashboard"></section>
        <section id="transcript" class="transcript" aria-live="polite"></section>
      </div>
      <form id="command-form" class="input-bar">
        <input id="command-input" autocomplete="off" spellcheck="false" placeholder="Type a RiskShard command">
        <button class="run-button primary" type="submit">Run</button>
      </form>
    </main>
  </div>
  <script>
    const transcript = document.querySelector("#transcript");
    const dashboard = document.querySelector("#dashboard");
    const consoleScroll = document.querySelector("#console-scroll");
    const promptLabel = document.querySelector("#prompt");
    const form = document.querySelector("#command-form");
    const input = document.querySelector("#command-input");

    function appendEntry(command, output) {
      const entry = document.createElement("article");
      entry.className = "entry";
      const commandLine = document.createElement("div");
      commandLine.className = "command";
      commandLine.textContent = command ? `[${commandFolder(command)}] $ ${command}` : "[Start] $ system";
      const pre = document.createElement("pre");
      pre.textContent = output;
      entry.append(commandLine, pre);
      transcript.appendChild(entry);
      consoleScroll.scrollTop = consoleScroll.scrollHeight;
    }

    async function requestJson(url, options = {}) {
      const response = await fetch(url, options);
      let payload = {};
      try {
        payload = await response.json();
      } catch (error) {
        payload = { error: "The server returned a response the browser could not read." };
      }
      if (!response.ok) {
        throw new Error(payload.error || `Request failed with HTTP ${response.status}`);
      }
      return payload;
    }

    async function refreshState() {
      const state = await requestJson("/api/state");
      promptLabel.textContent = state.prompt;
    }

    async function refreshDashboard() {
      const data = await requestJson("/api/dashboard");
      renderDashboard(data);
    }

    function badgeClass(status) {
      if (["calibrated", "current", "true", "ready_for_local_calibrated_run"].includes(String(status))) return "good";
      if (["calibrated_with_assumptions", "partially_supported", "renew_soon", "false", "needs_source_review", "needs_assumption_review"].includes(String(status))) return "warn";
      return "bad";
    }

    function displayStatus(status) {
      return String(status || "unknown").replaceAll("_", " ");
    }

    function commandFolder(command) {
      const first = command.trim().split(/\\s+/)[0] || "start";
      if (["workflow", "where", "start", "reset", "clear"].includes(first)) return "Start";
      if (["modules", "module", "riskshards", "search", "toprisks", "risks", "countries", "use", "scenario", "info"].includes(first)) return "Scenario";
      if (["show", "consume", "calibrate", "run", "report", "explain"].includes(first)) return first === "show" && command.includes("gaps") ? "Improve Model" : "Run Risk";
      if (["packs", "evidencepacks", "propose", "feeds", "sources", "preflight", "contribute", "validate", "enhance"].includes(first)) return "Improve Model";
      if (["readiness", "beta", "next", "actions", "doctor", "pack", "registry"].includes(first)) return "Govern Data";
      return "Console";
    }

    const parameterLabels = {
      "frequency.min": "F min",
      "frequency.likely": "F likely",
      "frequency.max": "F max",
      "impact.min": "I min",
      "impact.likely": "I likely",
      "impact.max": "I max"
    };

    function statusClass(status) {
      if (status === "source_backed") return "good";
      if (status === "assumption_only") return "warn";
      return "bad";
    }

    function commandButton(command, label, extraClass = "") {
      return `<button class="compact ${extraClass}" data-command="${command}">${label}</button>`;
    }

    function activeModuleActions(activeModuleId) {
      if (!activeModuleId) {
        return `
          <div class="item-meta">Select a Risk Shard to unlock evidence, run, explain, and report actions.</div>
          <div class="context-actions">
            ${commandButton("modules", "Browse Risk Shards", "primary")}
            ${commandButton("where", "Where am I?")}
            ${commandButton("use gb_finance_data_breach_midmarket", "Use UK data breach")}
            ${commandButton("use au_finance_ransomware_midmarket", "Use AU ransomware")}
            ${commandButton("start over", "Start over")}
          </div>
        `;
      }
      return `
        <div class="item-meta">Selected Risk Shard: ${activeModuleId}</div>
        <div class="context-actions">
          ${commandButton("where", "Where am I?")}
          ${commandButton("scenario", "Scenario")}
          ${commandButton("consume", "Consume")}
          ${commandButton("enhance", "Enhance")}
          ${commandButton(`modules info ${activeModuleId}`, "Shard info")}
          ${commandButton(`packs ${activeModuleId}`, "Evidence pack")}
          ${commandButton("show options", "Options")}
          ${commandButton("show gaps", "Gaps")}
          ${commandButton(`propose ${activeModuleId}`, "Propose")}
          ${commandButton("calibrate", "Calibrate", "warning")}
          ${commandButton("run", "Run", "warning")}
          ${commandButton("report json", "Report JSON")}
          ${commandButton("start over", "Start over")}
        </div>
      `;
    }

    function parameterCell(row, parameter) {
      const value = row.parameters[parameter] || { status: "missing" };
      const label = parameterLabels[parameter] || parameter;
      const command = value.status === "source_backed" ? `packs ${row.module_id}` : `propose ${row.module_id}`;
      const evidence = value.best_evidence_id ? `; best: ${value.best_evidence_id}` : "; no evidence candidate";
      return `<button class="param-cell ${statusClass(value.status)}" data-command="${command}" title="${parameter}: ${displayStatus(value.status)}${evidence}">${label}</button>`;
    }

    function renderCoverageMatrix(rows) {
      if (!rows.length) {
        return '<div class="item-meta">No Risk Shards are available yet.</div>';
      }
      return `
        <div class="shard-list">
          ${rows.slice(0, 5).map((row) => `
            <div class="shard-card">
              <div class="item-row"><strong>${row.module_id}</strong><span class="badge ${row.source_backed_direct === row.direct_total ? "good" : "warn"}">${row.source_backed_direct}/${row.direct_total} source-backed</span></div>
              <div class="item-meta">${row.country}/${row.industry}/${row.company_size}; threat ${row.threat}; confidence ${row.pack_confidence}</div>
              <div class="item-meta">Next gap: ${row.next_gap}</div>
              <div class="context-actions">
                ${commandButton(`use ${row.module_id}`, "Use")}
                ${commandButton(`packs ${row.module_id}`, "Evidence")}
                ${commandButton(`propose ${row.module_id}`, row.next_gap === "ready for practitioner review" ? "Review" : "Improve", row.next_gap === "ready for practitioner review" ? "" : "warning")}
              </div>
            </div>
          `).join("")}
        </div>
      `;
    }

    function renderDashboard(data) {
      const coverage = data.coverage;
      const feeds = data.feed_governance;
      const pack = data.data_pack;
      const gate = data.readiness_gate;
      const packs = data.evidence_packs || {};
      const actions = data.next_actions.slice(0, 3);
      const problemFeeds = feeds.problem_feeds.slice(0, 3);
      const activeModuleId = data.active_module_id;
      const coverageMatrix = packs.coverage_matrix || [];
      const org = data.org_profile;
      // UI-only presentation ordering: surface the shards that best match the
      // selected org context first. This is display sort, not an engine metric.
      const recommendedRows = [...coverageMatrix].sort((a, b) => shardFitScore(b, org) - shardFitScore(a, org));
      dashboard.innerHTML = `
        <div class="metric-grid">
          <div class="metric"><div class="metric-label">Current company context</div><div class="metric-value">${org.country}/${org.industry}</div><div class="item-meta">${org.employees} employees; ${org.company_size || "mid-market"} profile</div></div>
          <div class="metric"><div class="metric-label">Available Risk Shards</div><div class="metric-value">${coverageMatrix.length}</div><div class="item-meta">${Object.keys(coverage.threats).length} covered threats</div></div>
          <div class="metric"><div class="metric-label">Trust gate</div><div class="metric-value">${displayStatus(gate.status)}</div><div class="item-meta">ready to run is not benchmark-grade</div></div>
        </div>
        <div class="section">
          <div class="section-title"><span>Console path</span><span class="badge ${activeModuleId ? "good" : "warn"}">${activeModuleId ? "scenario selected" : "start"}</span></div>
          <div class="item-meta">Move through [Scenario] -> [Run Risk] -> [Finding], or switch to [Improve Model] when evidence is weak.</div>
          <div class="context-actions">
            ${commandButton("where", "Where am I?", "primary")}
            ${commandButton("consume", "Consume model")}
            ${commandButton("enhance", "Enhance model")}
            ${commandButton("start over", "Start over")}
          </div>
        </div>
        <div class="section">
          <div class="section-title"><span>Risk Shards for this context</span><span class="badge warn">ranked by fit and evidence</span></div>
          <div class="item-meta">These are real local shards. Exact company-specific matching is still early; use gaps and evidence packs to decide trust.</div>
          ${renderCoverageMatrix(recommendedRows)}
        </div>
        <div class="section">
          <div class="section-title"><span>Selected Risk Shard</span><span class="badge ${activeModuleId ? "good" : "warn"}">${activeModuleId ? "active" : "none"}</span></div>
          ${activeModuleActions(activeModuleId)}
        </div>
        <div class="dashboard-columns">
          <div class="section">
            <div class="section-title"><span>Trust boundary</span><span class="badge ${badgeClass(gate.status)}">${displayStatus(gate.status)}</span></div>
            <div class="list">
              <div class="item">
                <div class="item-row"><strong>Evidence base</strong><span class="badge good">${coverage.source_backed_records} source-backed</span></div>
                <div class="item-meta">${coverage.evidence_records} total records; ${coverage.direct_parameter_records} direct parameter records.</div>
              </div>
              <div class="item">
                <div class="item-row"><strong>Evidence packs</strong><span class="badge ${packs.low_confidence_packs?.length ? "warn" : "good"}">${packs.pack_count || 0} packs</span></div>
                <div class="item-meta">${(packs.low_confidence_packs || []).length} low-confidence pack(s); freshness ${Object.keys(packs.freshness_counts || {}).join(", ") || "unknown"}.</div>
              </div>
              <div class="item">
                <div class="item-row"><strong>Data pack</strong><span class="badge good">${pack.pack_version}</span></div>
                <div class="item-meta">${pack.file_count} governed files; fingerprint ${pack.fingerprint.slice(0, 12)}.</div>
              </div>
              ${problemFeeds.map((feed) => `
                <div class="item">
                  <div class="item-row"><strong>${feed.id}</strong><span class="badge bad">${feed.renewal_status}</span></div>
                  <div class="item-meta">source gathered ${feed.source_gathered_at || "never"}; evidence ingested ${feed.riskshard_evidence_ingested_at || "none"}</div>
                </div>
              `).join("")}
            </div>
          </div>
          <div class="section">
            <div class="section-title"><span>Improve or contribute</span><span class="badge warn">next evidence work</span></div>
            <div class="list">
              ${actions.map((action) => `
                <div class="item">
                  <div class="item-row"><strong>${action.title}</strong><span class="badge ${action.priority === "P0" ? "bad" : action.priority === "P1" ? "warn" : "good"}">${action.priority}</span></div>
                  <div class="item-meta">${action.area}; ${action.detail}</div>
                  <div class="command">${action.command}</div>
                </div>
              `).join("")}
              <div class="context-actions">
                ${commandButton("next", "More next actions", "primary")}
                ${commandButton("countries", "Country roadmap")}
                ${commandButton("registry", "Shard registry")}
                ${commandButton("preflight", "Contributor preflight")}
              </div>
            </div>
          </div>
        </div>
      `;
    }

    function shardFitScore(row, org) {
      let score = 0;
      if (row.country === org.country) score += 40;
      if (row.industry === org.industry) score += 20;
      if (row.company_size === org.company_size) score += 10;
      score += row.source_backed_direct || 0;
      if (row.pack_confidence === "high") score += 4;
      if (row.pack_confidence === "medium") score += 2;
      return score;
    }

    async function runCommand(command) {
      const trimmed = command.trim();
      if (!trimmed) return;
      appendEntry(trimmed, "Running...");
      input.value = "";
      const latest = transcript.lastElementChild.querySelector("pre");
      try {
        const result = await requestJson("/api/command", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ command: trimmed })
        });
        latest.textContent = result.output || "(no output)";
        promptLabel.textContent = result.prompt;
        await refreshDashboard();
      } catch (error) {
        latest.textContent = `Command failed: ${error.message}\n\nRefresh the page after restarting the local RiskShard server.`;
      }
    }

    document.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-command]");
      if (!button) return;
      runCommand(button.dataset.command);
    });

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      runCommand(input.value);
    });

    Promise.all([refreshState(), refreshDashboard()])
      .then(() => {
        appendEntry("", "Browser console ready. Click Workflow, Where am I?, or type a command below.");
        input.focus();
      })
      .catch((error) => {
        appendEntry("", `Browser console could not reach the local RiskShard server: ${error.message}`);
      });
  </script>
</body>
</html>
"""


class WebConsoleApp:
    def __init__(self, root=PROJECT_ROOT):
        self.root = Path(root)
        self.console = RiskShardConsole(root=self.root, stdout=StringIO())
        self.lock = threading.Lock()

    def state(self):
        return {
            "prompt": self.console.prompt,
            "active_module_id": self.console.module_id,
        }

    def dashboard(self):
        dashboard = build_readiness_dashboard(self.root, self.console.ensure_org_profile())
        dashboard["active_module_id"] = self.console.module_id
        dashboard["active_scenario"] = (
            self.console.scenario_path.name
            if self.console.scenario_path
            else None
        )
        return dashboard

    def run_command(self, command):
        command = command.strip()
        if command in {"exit", "quit", "EOF"}:
            return {
                "prompt": self.console.prompt,
                "output": "The browser console stays open. Stop the local server when finished.",
            }

        with self.lock:
            buffer = StringIO()
            self.console.stdout = buffer
            self.console.onecmd(command)
            return {
                "prompt": self.console.prompt,
                "active_module_id": self.console.module_id,
                "output": buffer.getvalue(),
            }


class WebConsoleHandler(BaseHTTPRequestHandler):
    app = None

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self.send_html(INDEX_HTML)
        elif path == "/api/state":
            self.send_json(self.app.state())
        elif path == "/api/dashboard":
            self.send_json(self.app.dashboard())
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/command":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            command = payload.get("command", "")
            self.send_json(self.app.run_command(command))
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def log_message(self, format, *args):
        return

    def send_html(self, html):
        body = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def build_server(host="127.0.0.1", port=8765, root=PROJECT_ROOT):
    class Handler(WebConsoleHandler):
        app = WebConsoleApp(root=root)

    return ThreadingHTTPServer((host, port), Handler)
