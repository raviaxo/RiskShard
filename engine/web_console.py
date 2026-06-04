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
  <style>
    :root {
      color-scheme: dark;
      --bg: #101214;
      --panel: #171a1d;
      --panel-2: #1f2427;
      --line: #343a3e;
      --text: #f4f1e8;
      --muted: #a8b0ad;
      --accent: #60b884;
      --accent-2: #d49a4a;
      --danger: #d87575;
      --input: #0c0e10;
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
      grid-template-columns: 280px minmax(0, 1fr);
      min-height: 100vh;
    }

    aside {
      border-right: 1px solid var(--line);
      background: var(--panel);
      padding: 16px;
    }

    main {
      display: flex;
      min-width: 0;
      min-height: 100vh;
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
      background: #141719;
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
      background: var(--accent);
    }

    .command-group {
      display: grid;
      gap: 8px;
      margin-top: 16px;
    }

    button {
      min-height: 36px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel-2);
      color: var(--text);
      cursor: pointer;
      font: inherit;
      text-align: left;
      padding: 8px 10px;
    }

    button:hover {
      border-color: var(--accent);
    }

    button.primary {
      border-color: #3b6d50;
      background: #1f3a2b;
    }

    button.warning {
      border-color: #72552b;
      background: #3a2e1d;
    }

    .hint {
      color: var(--muted);
      font-size: 12px;
      margin: 12px 0 0;
    }

    .dashboard {
      display: grid;
      gap: 14px;
      padding: 16px 18px;
      border-bottom: 1px solid var(--line);
      background: #111416;
    }

    .metric-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }

    .metric,
    .section {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      padding: 10px;
    }

    .metric-label,
    .item-meta {
      color: var(--muted);
      font-size: 12px;
    }

    .metric-value {
      margin-top: 4px;
      font-size: 18px;
      font-weight: 650;
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
      border-color: #3b6d50;
      color: #94d7ad;
    }

    .badge.warn {
      border-color: #72552b;
      color: #e5b76d;
    }

    .badge.bad {
      border-color: #7b3e3e;
      color: #e19898;
    }

    .dashboard-columns {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 10px;
    }

    .transcript {
      flex: 1;
      overflow: auto;
      padding: 18px;
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
      }
      .command-group {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .metric-grid,
      .dashboard-columns {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <h1>RiskShard</h1>
      <h2>Local browser console</h2>
      <div class="command-group">
        <button class="primary" data-command="workflow">Workflow</button>
        <button data-command="set org org_profiles/au_finance_midmarket.yaml">Load org</button>
        <button data-command="readiness">Readiness</button>
        <button data-command="doctor">Doctor</button>
        <button class="primary" data-command="next">Next actions</button>
        <button data-command="toprisks">Top risks</button>
        <button data-command="modules">Risk modules</button>
        <button data-command="modules info au_finance_ransomware_midmarket">Module info</button>
        <button data-command="packs au_finance_ransomware_midmarket">Evidence pack</button>
        <button data-command="feeds">Data feeds</button>
        <button data-command="pack">Data pack</button>
        <button data-command="preflight">Contributor check</button>
        <button data-command="propose">Propose calibration</button>
        <button data-command="search ransomware">Find scenarios</button>
        <button data-command="use au_finance_ransomware_midmarket">Use AU ransomware</button>
        <button data-command="use business_email_compromise">Use BEC</button>
        <button data-command="show options">Show options</button>
        <button data-command="show gaps">Show gaps</button>
        <button class="warning" data-command="calibrate">Calibrate</button>
        <button data-command="show evidence">Show evidence</button>
        <button data-command="explain">Explain latest</button>
        <button class="warning" data-command="run">Run simulation</button>
        <button data-command="report json">Report JSON</button>
        <button data-command="validate">Validate evidence</button>
      </div>
      <p class="hint">Commands run against your local RiskShard checkout. Outputs stay in ignored local files.</p>
    </aside>
    <main>
      <header>
        <div>
          <h1>Practitioner Console</h1>
          <h2 id="prompt">riskshard&gt;</h2>
        </div>
        <div class="status"><span class="dot"></span><span>Local</span></div>
      </header>
      <section id="dashboard" class="dashboard"></section>
      <section id="transcript" class="transcript" aria-live="polite"></section>
      <form id="command-form" class="input-bar">
        <input id="command-input" autocomplete="off" spellcheck="false" placeholder="Type a RiskShard command">
        <button class="run-button primary" type="submit">Run</button>
      </form>
    </main>
  </div>
  <script>
    const transcript = document.querySelector("#transcript");
    const dashboard = document.querySelector("#dashboard");
    const promptLabel = document.querySelector("#prompt");
    const form = document.querySelector("#command-form");
    const input = document.querySelector("#command-input");

    function appendEntry(command, output) {
      const entry = document.createElement("article");
      entry.className = "entry";
      const commandLine = document.createElement("div");
      commandLine.className = "command";
      commandLine.textContent = command ? "$ " + command : "$ system";
      const pre = document.createElement("pre");
      pre.textContent = output;
      entry.append(commandLine, pre);
      transcript.appendChild(entry);
      transcript.scrollTop = transcript.scrollHeight;
    }

    async function refreshState() {
      const response = await fetch("/api/state");
      const state = await response.json();
      promptLabel.textContent = state.prompt;
    }

    async function refreshDashboard() {
      const response = await fetch("/api/dashboard");
      const data = await response.json();
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

    function renderDashboard(data) {
      const coverage = data.coverage;
      const feeds = data.feed_governance;
      const pack = data.data_pack;
      const install = data.install_release;
      const localization = data.localization;
      const gate = data.readiness_gate;
      const scenarios = data.scenarios?.stage_counts || {};
      const modules = data.risk_modules || {};
      const packs = data.evidence_packs || {};
      const actions = data.next_actions.slice(0, 4);
      const problemFeeds = feeds.problem_feeds.slice(0, 3);
      const topRisks = data.top_risks.slice(0, 5);
      dashboard.innerHTML = `
        <div class="metric-grid">
          <div class="metric"><div class="metric-label">Readiness gate</div><div class="metric-value">${displayStatus(gate.status)}</div></div>
          <div class="metric"><div class="metric-label">Evidence records</div><div class="metric-value">${coverage.evidence_records}</div></div>
          <div class="metric"><div class="metric-label">Source-backed</div><div class="metric-value">${coverage.source_backed_records}</div></div>
          <div class="metric"><div class="metric-label">Risk modules</div><div class="metric-value">${modules.module_count || 0}</div></div>
        </div>
        <div class="section">
          <div class="section-title"><span>Next Actions</span><span class="badge ${badgeClass(gate.status)}">${displayStatus(gate.status)}</span></div>
          <div class="item-meta">${gate.summary}</div>
          <div class="list">
            ${actions.map((action) => `
              <div class="item">
                <div class="item-row"><strong>${action.title}</strong><span class="badge ${action.priority === "P0" ? "bad" : action.priority === "P1" ? "warn" : "good"}">${action.priority}</span></div>
                <div class="item-meta">${action.area}; ${action.detail}</div>
                <div class="command">${action.command}</div>
              </div>
            `).join("")}
          </div>
        </div>
        <div class="dashboard-columns">
          <div class="section">
            <div class="section-title"><span>Top Risk Readiness</span><span class="badge ${badgeClass(topRisks[0]?.status)}">${topRisks[0]?.status || "none"}</span></div>
            <div class="list">
              ${topRisks.map((risk) => `
                <div class="item">
                  <div class="item-row"><strong>${risk.label}</strong><span class="badge ${badgeClass(risk.status)}">${risk.status}</span></div>
                  <div class="item-meta">direct ${risk.direct_coverage}/${risk.direct_total}; assumptions ${risk.assumption_parameters}; next ${risk.next_steps[0]}</div>
                </div>
              `).join("")}
            </div>
          </div>
          <div class="section">
            <div class="section-title"><span>Governance</span><span class="badge ${problemFeeds.length ? "bad" : "good"}">${problemFeeds.length ? "needs review" : "current"}</span></div>
            <div class="list">
              <div class="item">
                <div class="item-row"><strong>${data.org_profile.name}</strong><span class="badge good">${data.org_profile.country}</span></div>
                <div class="item-meta">${data.org_profile.industry}; ${data.org_profile.employees} employees; regulatory ${data.org_profile.regulatory_intensity}</div>
              </div>
              <div class="item">
                <div class="item-row"><strong>Coverage</strong><span class="badge warn">${Object.keys(coverage.threats).length} threats</span></div>
                <div class="item-meta">${Object.keys(coverage.countries).join(", ") || "no country coverage"}; ${coverage.direct_parameter_records} direct parameter records</div>
              </div>
              <div class="item">
                <div class="item-row"><strong>Scenarios</strong><span class="badge good">${scenarios.governed_starter || 0} governed</span></div>
                <div class="item-meta">${scenarios.demo_fixture || 0} demo fixtures; labels are stored in scenario metadata</div>
              </div>
              <div class="item">
                <div class="item-row"><strong>Risk modules</strong><span class="badge good">${modules.module_count || 0} modules</span></div>
                <div class="item-meta">${Object.keys(modules.status_counts || {}).join(", ") || "no modules"}; threats ${(modules.threats || []).join(", ") || "none"}</div>
              </div>
              <div class="item">
                <div class="item-row"><strong>Evidence packs</strong><span class="badge ${packs.low_confidence_packs?.length ? "warn" : "good"}">${packs.pack_count || 0} packs</span></div>
                <div class="item-meta">${Object.keys(packs.freshness_counts || {}).join(", ") || "no pack freshness"}; low confidence ${(packs.low_confidence_packs || []).length}</div>
              </div>
              <div class="item">
                <div class="item-row"><strong>Localization</strong><span class="badge ${localization.covered_countries.length ? "warn" : "bad"}">${localization.covered_countries.length} countries</span></div>
                <div class="item-meta">currencies ${localization.currencies_in_evidence.join(", ") || "none"}; FX rates ${localization.fx_rate_count}</div>
              </div>
              <div class="item">
                <div class="item-row"><strong>Data pack</strong><span class="badge good">${pack.pack_version}</span></div>
                <div class="item-meta">${pack.file_count} governed files; ${pack.fingerprint.slice(0, 16)}</div>
              </div>
              <div class="item">
                <div class="item-row"><strong>Install/release</strong><span class="badge ${badgeClass(install.pyproject)}">${install.pyproject ? "installable" : "script-only"}</span></div>
                <div class="item-meta">${install.next_needed[0] || "console commands declared in pyproject"}</div>
              </div>
              ${problemFeeds.map((feed) => `
                <div class="item">
                  <div class="item-row"><strong>${feed.id}</strong><span class="badge bad">${feed.renewal_status}</span></div>
                  <div class="item-meta">source gathered ${feed.source_gathered_at || "never"}; evidence ingested ${feed.riskshard_evidence_ingested_at || "none"}</div>
                </div>
              `).join("")}
            </div>
          </div>
        </div>
      `;
    }

    async function runCommand(command) {
      const trimmed = command.trim();
      if (!trimmed) return;
      appendEntry(trimmed, "Running...");
      input.value = "";
      const response = await fetch("/api/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: trimmed })
      });
      const result = await response.json();
      const latest = transcript.lastElementChild.querySelector("pre");
      latest.textContent = result.output || "(no output)";
      promptLabel.textContent = result.prompt;
      if (!response.ok) {
        latest.textContent = result.error || latest.textContent;
      }
      await refreshDashboard();
    }

    document.querySelectorAll("[data-command]").forEach((button) => {
      button.addEventListener("click", () => runCommand(button.dataset.command));
    });

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      runCommand(input.value);
    });

    Promise.all([refreshState(), refreshDashboard()]).then(() => {
      appendEntry("", "Browser console ready. Click Workflow or type a command below.");
      input.focus();
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
        return {"prompt": self.console.prompt}

    def dashboard(self):
        return build_readiness_dashboard(self.root, self.console.ensure_org_profile())

    def run_command(self, command):
        command = command.strip()
        if command in {"exit", "quit", "EOF"}:
            return {
                "prompt": self.console.prompt,
                "output": "The browser console stays open. Stop the local server from Codex when finished.",
            }

        with self.lock:
            buffer = StringIO()
            self.console.stdout = buffer
            self.console.onecmd(command)
            return {
                "prompt": self.console.prompt,
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
