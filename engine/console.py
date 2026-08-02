import cmd
from pathlib import Path

from engine.calibration import (
    run_calibration,
    write_calibrated_scenario,
    write_calibration_markdown_report,
    write_calibration_report,
)
from engine.calibration_assistant import (
    format_module_calibration_proposal,
    propose_module_calibration,
)
from engine.country_priorities import (
    find_country_priority,
    format_country_priorities,
    format_country_priority_detail,
    top_country_priorities,
)
from engine.evidence_quality import has_errors, validate_evidence_quality
from engine.evidence_packs import (
    build_evidence_pack_registry,
    format_evidence_pack_detail,
    format_evidence_pack_registry,
)
from engine.executive_report import build_executive_report, format_executive_report_markdown
from engine.experience import analyze_gaps, format_gap_analysis, format_top_risks, rank_top_risks
from engine.experience import format_calibration_proposal, propose_calibration
from engine.fair_calc import IMPACT_UNCERTAINTY_NOTE, export_report, load_and_validate, plot_lec, run_portfolio
from engine.governance import (
    build_data_feed_inventory,
    format_data_feed_inventory,
    format_feed_detail,
)
from engine.data_packs import build_data_pack_manifest, format_data_pack_manifest
from engine.beta_readiness import build_beta_readiness_report, format_beta_readiness_report
from engine.contributor import build_contributor_preflight, format_contributor_preflight
from engine.doctor import build_doctor_report, format_doctor_report
from engine.provenance import build_module_provenance, format_provenance
from engine.readiness import build_readiness_dashboard, format_next_actions, format_readiness_dashboard
from engine.risk_modules import (
    find_risk_module,
    format_module_detail,
    format_module_list,
    module_for_scenario,
    search_risk_modules,
)
from engine.scenarios import scenario_paths, scenario_stage_label
from engine.shard_registry import build_shard_registry, format_shard_registry
from engine.coverage import build_coverage_report, format_coverage_report


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ANSI palette. Emitted only to a real interactive terminal; StringIO-backed
# stdout (tests and the browser console) is not a tty, so paint() returns plain
# text there. Matches the browser console: identity = indigo, data = cyan.
_ANSI = {
    "identity": "\033[38;5;105m",
    "data": "\033[38;5;80m",
    "muted": "\033[38;5;245m",
    "sys": "\033[38;5;42m",
    "caution": "\033[38;5;214m",
    "alert": "\033[38;5;203m",
    "bold": "\033[1m",
}
_ANSI_RESET = "\033[0m"


def paint(text, *codes, enabled=True):
    if not enabled or not codes:
        return text
    return "".join(_ANSI[code] for code in codes) + text + _ANSI_RESET


class RiskShardConsole(cmd.Cmd):
    intro = (
        "\n"
        "  RiskShard\n"
        "  ─────────\n"
        "  Evidence-governed cyber risk shards. Every number traces to a\n"
        "  reviewed public source, with honest confidence and visible limits.\n"
        "\n"
        "  Start here\n"
        "    demo       run the whole first-run path automatically\n"
        "    workflow   see that path as steps you can type\n"
        "    help       guided command list\n"
        "    exit       leave\n"
    )

    def __init__(self, root=PROJECT_ROOT, stdin=None, stdout=None, results_dir=None):
        super().__init__(stdin=stdin, stdout=stdout)
        self.root = Path(root)
        # Where run/report/calibrate artifacts land. Defaults to the repo's results/ so
        # behaviour is unchanged; tests pass a temp directory so the suite stops writing
        # into the working tree (same class of problem as the strength-ledger mutation
        # fixed in 8085bc9).
        self.results_dir = Path(results_dir) if results_dir else self.root / "results"
        self.scenario_path = None
        self.active_run_path = None
        self.module_id = None
        self.last_calibration_report = None
        self.last_run = None
        self.last_paths = {}
        self.options = self.default_options()
        self.color = bool(getattr(self.stdout, "isatty", lambda: False)())
        self.prompt = self.c("riskshard> ", "identity") if self.color else "riskshard> "

    def c(self, text, *codes):
        return paint(text, *codes, enabled=self.color)

    def _strength_line(self):
        """One-line current strength, read from the progress ledger. '' if unavailable."""
        try:
            from engine.strength_ledger import LEDGER_RELPATH, latest_delta

            latest, _ = latest_delta(self.root / LEDGER_RELPATH)
            if latest is None:
                return ""
            m = latest["metrics"]
            version = latest.get("data_pack_version", "")
            split = (
                f" · {m['params_cell_matched']} cell-matched"
                if "params_cell_matched" in m
                else ""
            )
            return (
                f"  Strength: {m['params_source_backed']}/{m['params_total']} params source-backed"
                f"{split}"
                f" · {m['shards_fully_sourced']}/{m['shards']} shards at 6/6"
                f"{f' ({version})' if version else ''}\n"
            )
        except Exception:
            return ""

    def preloop(self):
        strength = self._strength_line()
        if self.color:
            self.intro = (
                "\n"
                "  " + self.c("RiskShard", "identity", "bold") + "\n"
                "  " + self.c("─────────", "identity") + "\n"
                "  Evidence-governed cyber risk shards. Every number traces to a\n"
                "  reviewed public source, with honest confidence and visible limits.\n"
                "\n"
                + (self.c(strength, "muted") if strength else "")
                + ("\n" if strength else "")
                + "  " + self.c("Start here", "muted") + "\n"
                "    " + self.c("demo", "identity") + "       run the whole first-run path automatically\n"
                "    " + self.c("workflow", "identity") + "   see that path as steps you can type\n"
                "    " + self.c("help", "identity") + "       guided command list\n"
                "    " + self.c("exit", "identity") + "       leave\n"
            )
        elif strength:
            self.intro = self.intro.replace(
                "\n\n  Start here\n", "\n\n" + strength + "\n  Start here\n"
            )

    def default_options(self):
        return {
            "trials": 10000,
            "dist": "pert",
            "seed": 42,
            "org_profile": None,
            "calibration": None,
            "threat": None,
            "report_output": self.results_dir / "console_calibration.json",
            "markdown_output": self.results_dir / "console_calibration.md",
            "scenario_output": self.results_dir / "console_calibrated.yaml",
        }

    def emptyline(self):
        return None

    def do_search(self, arg):
        """search [terms] - Find scenarios by filename, name, or YAML content."""
        terms = [term.lower() for term in arg.split() if term.strip()]
        rows = []

        for path in scenario_paths(self.root):
            text = path.read_text(errors="ignore")
            config = load_and_validate(path)
            name = config["metadata"]["name"]
            haystack = " ".join([path.stem, str(path), name, text]).lower()
            if terms and not all(term in haystack for term in terms):
                continue
            rows.append((path.stem, name, scenario_stage_label(config), relative_to_root(path, self.root)))

        if not rows:
            self.write("No matching scenarios.\n")
            return None

        self.write("Scenarios\n")
        self.write("ID                                      Stage              Name\n")
        self.write("--                                      -----              ----\n")
        for scenario_id, name, stage, rel_path in rows:
            self.write(f"{scenario_id:<39} {stage:<18} {name} ({rel_path})\n")
        return None

    def do_workflow(self, arg):
        """workflow - Show the shortest credible first-run path."""
        del arg
        self.write("First-run workflow\n")
        self.write("Goal: choose a real Risk Shard, understand its trust boundary, run it, then decide whether to consume or improve it.\n")
        self.write("Fastest path: run 'demo' to execute this entire path automatically with narration.\n")
        self.write("\n")
        self.write("[Start]\n")
        self.write("  where                 Show current location, selected shard, inputs, and next commands.\n")
        self.write("  start over            Clear selected shard, calibration, run state, and return to the root prompt.\n")
        self.write("\n")
        self.write("[Find Risk Shard]\n")
        self.write("  toprisks              Rank starter threats for the current company profile.\n")
        self.write("  modules               Browse available Risk Shards.\n")
        self.write("  countries             See country coverage priorities.\n")
        self.write("  countries GB          Explain the UK priority and current gap.\n")
        self.write("  registry              Show the machine-readable shard registry summary.\n")
        self.write("\n")
        self.write("[Scenario]\n")
        self.write("  use gb_finance_data_breach_midmarket\n")
        self.write("  scenario              Show the selected scenario and input context.\n")
        self.write("  packs                 Inspect evidence and assumptions behind the selected shard.\n")
        self.write("  challenge frequency.max  See the value, source, quote, and caveat behind one number.\n")
        self.write("  show gaps             Show what blocks stronger trust.\n")
        self.write("\n")
        self.write("[Run Risk]\n")
        self.write("  show options          Confirm scenario, org profile, calibration, threat, trials, dist, and seed.\n")
        self.write("  calibrate             Create an evidence-calibrated scenario draft when calibration inputs are set.\n")
        self.write("  run                   Simulate the active scenario and print a run receipt before the numbers.\n")
        self.write("\n")
        self.write("[Finding]\n")
        self.write("  explain               Explain the latest calibration or run.\n")
        self.write("  report json           Export the latest simulation report.\n")
        self.write("  report exec           Export a one-page board-ready executive summary.\n")
        self.write("\n")
        self.write("[Improve Model]\n")
        self.write("  enhance               Show the contribution path for improving evidence and calibration.\n")
        self.write("  propose               Propose stronger evidence selectors for the selected shard.\n")
        self.write("  feeds                 Inspect source freshness, ingestion, confidence, and renewal.\n")
        self.write("  beta                  Check stricter beta readiness before public operations.\n")
        self.write("  preflight             Check whether a contribution pack is structurally ready.\n")
        self.write("  registry              Confirm the shard-pack contract and current coverage.\n")
        self.write("  scaffold CLI          python scripts/contributor_preflight.py scaffold path/to/pack --module-id <id> --country <code> --industry <id> --company-size <id> --threat <id>\n")
        return None

    def help_workflow(self):
        self.do_workflow("")

    def do_help(self, arg):
        """help [command|all] - Guided command overview, or details for one command."""
        topic = arg.strip()
        if topic == "all":
            self.write("All commands (type 'help <command>' for detail):\n")
            return super().do_help("")
        if topic:
            return super().do_help(topic)
        self.write(
            "RiskShard commands (type 'help <command>' for detail, 'help all' for every command)\n"
            "\n"
            "Start here\n"
            "  demo            Run the whole first-run path automatically, with narration.\n"
            "  workflow        See that path as numbered steps you can type yourself.\n"
            "  modules         List the Risk Shards (country / industry / threat).\n"
            "  search <term>   Find a shard by keyword.\n"
            "  use <shard>     Select a shard to work with.\n"
            "\n"
            "Run a shard (use its numbers)\n"
            "  where           Confirm the selected inputs.\n"
            "  run             Simulate financial loss (Monte Carlo).\n"
            "  explain         Plain-language read of the last result.\n"
            "  report exec     Write a board-ready one-page summary.\n"
            "  report json     Export the full simulation report.\n"
            "\n"
            "Improve the evidence (see how much to trust it)\n"
            "  packs           Show the trust boundary: which numbers are source-backed.\n"
            "  coverage        Grade each shard's data strength: can I use this number?\n"
            "  show gaps       Show the next evidence gap to close.\n"
            "  propose         Suggest better source-backed evidence.\n"
            "\n"
            "Inspect and govern\n"
            "  doctor          Check the local environment and data health.\n"
            "  validate        Check evidence quality.\n"
            "  readiness       Show overall readiness ('beta' shows the beta gate).\n"
            "\n"
            "Contribute\n"
            "  contribute      Start a country / evidence contribution pack.\n"
            "\n"
            "  quit / exit     Leave the console.\n"
        )
        return None

    def do_demo(self, arg):
        """demo [risk-shard-id] - Run the canonical first-run path end to end with narration."""
        module_id = arg.strip() or "gb_finance_data_breach_midmarket"
        if find_risk_module(module_id, self.root) is None:
            self.write(
                f"Unknown Risk Shard: {module_id}. "
                "Run 'modules' to list available shards, then 'demo <risk-shard-id>'.\n"
            )
            return None

        self.reset_state()
        self.write("RiskShard guided demo\n")
        self.write(
            "This runs the canonical first-run path end to end: select a real Risk "
            "Shard, inspect its trust boundary, simulate financial loss, explain the "
            "result, export a report, and see the next evidence gap. Every step below "
            "is a real command you can type yourself.\n"
        )

        def step(number, title, command_hint):
            self.write(f"\n== Step {number} of 6 : {title} ==\n")
            self.write(f"(command: {command_hint})\n")

        step(1, "Select a Risk Shard", f"use {module_id}")
        self.do_use(module_id)

        step(2, "Inspect the trust boundary", "packs")
        self.do_packs("")

        step(3, "Simulate financial loss", "run")
        self.do_run("")

        step(4, "Explain the result", "explain")
        self.do_explain("")

        step(5, "Export a shareable report", "report json")
        self.do_report("json")

        step(6, "See the next improvement gap", "show gaps")
        self.do_show("gaps")

        self.write("\n== Demo complete ==\n")
        self.write(
            f"You selected {module_id}, saw which parameters are source-backed versus "
            "assumptions, ran a Monte Carlo loss simulation, exported a JSON report to "
            "results/, and identified the next evidence gap.\n"
        )
        self.write("Consume this shard : explain; report json; report exec (board summary)\n")
        self.write("Improve this shard : show gaps; propose; enhance\n")
        self.write("Start over         : start over\n")
        return None

    def do_use(self, arg):
        """use <module-id|scenario-id|path> - Select a module or scenario."""
        module = find_risk_module(arg.strip(), self.root)
        if module is not None:
            self.select_module(module)
            self.refresh_prompt()
            self.write(f"Using Risk Shard {module['id']}: {module['title']}\n")
            self.write(f"Location: {self.breadcrumb(include_run=False)}\n")
            self.write("Next: run 'where' or 'scenario' to confirm inputs, then choose 'consume' (use this shard's numbers now: run, explain, report) or 'enhance' (improve its evidence: packs, show gaps, propose).\n")
            return None

        path = resolve_scenario(self.root, arg.strip())
        if path is None:
            self.write("Risk Shard or scenario not found. Try 'modules' or 'search'.\n")
            return None

        self.scenario_path = path
        self.active_run_path = path
        module = module_for_scenario(path, self.root)
        self.module_id = module["id"] if module else None
        self.apply_recommendations(path)
        self.refresh_prompt()

        config = load_and_validate(path)
        self.write(f"Using {config['metadata']['name']} ({relative_to_root(path, self.root)})\n")
        self.write(f"Location: {self.breadcrumb(include_run=False)}\n")
        self.write("Next: run 'where' or 'scenario' to confirm inputs, then choose 'consume' or 'enhance'.\n")
        return None

    def do_where(self, arg):
        """where - Show current console location, selected context, and next actions."""
        del arg
        self.write_context_summary()
        return None

    def do_scenario(self, arg):
        """scenario [scenario-id|path] - Show scenario detail or the current scenario context."""
        if arg.strip():
            return self.do_info(arg)
        self.write_context_summary()
        return None

    def do_consume(self, arg):
        """consume - Show the path for using the selected model output."""
        del arg
        self.write("Consume model path\n")
        self.write(f"Location: {self.breadcrumb()}\n")
        self.write("Purpose : use a selected Risk Shard to produce an explainable risk narrative.\n")
        self.write("1. where          Confirm selected shard, company context, and simulation settings.\n")
        self.write("2. packs          Inspect confidence and assumptions before presenting numbers.\n")
        self.write("3. run            Simulate the active scenario and receive a run receipt.\n")
        self.write("4. explain        Explain what the latest result means and where trust is limited.\n")
        self.write("5. report json    Export the machine-readable report for review or downstream use.\n")
        return None

    def do_enhance(self, arg):
        """enhance - Show the path for improving evidence, calibration, and trust."""
        del arg
        self.write("Enhance model path\n")
        self.write(f"Location: {self.breadcrumb()}\n")
        self.write("Purpose : improve the shard so future runs depend less on assumptions.\n")
        self.write("1. packs          See which parameters are source-backed vs assumption-backed.\n")
        self.write("2. show gaps      Identify the most important missing evidence.\n")
        self.write("3. propose        Review stronger evidence selectors for calibration.\n")
        self.write("4. feeds          Check source freshness, ingestion date, confidence, and renewal.\n")
        self.write("5. preflight      Check a contribution pack before merging it into RiskShard.\n")
        self.write("6. validate       Run evidence quality gates after changes.\n")
        self.write("7. registry       Confirm the shard registry and machine-readable contract.\n")
        self.write("Scaffold CLI: python scripts/contributor_preflight.py scaffold path/to/pack --module-id <id> --country <code> --industry <id> --company-size <id> --threat <id>\n")
        return None

    def do_start(self, arg):
        """start over - Reset selected shard, calibration, run, and prompt state."""
        if arg.strip().lower() != "over":
            self.write("Usage: start over\n")
            return None
        self.reset_state()
        self.write("Started over.\n")
        self.write("Location: [Start]\n")
        self.write("Next: run 'workflow', 'modules', or 'toprisks'.\n")
        return None

    def do_reset(self, arg):
        """reset - Alias for start over."""
        del arg
        return self.do_start("over")

    def do_clear(self, arg):
        """clear - Alias for start over."""
        del arg
        return self.do_start("over")

    def do_info(self, arg):
        """info [scenario-id|path] - Show scenario ranges and metadata."""
        path = resolve_scenario(self.root, arg.strip()) if arg.strip() else self.scenario_path
        if path is None:
            self.write("No scenario selected. Try 'search' and 'use <id>'.\n")
            return None

        config = load_and_validate(path)
        metadata = config.get("metadata", {})
        self.write(f"Name      : {metadata.get('name')}\n")
        self.write(f"Version   : {metadata.get('version', 'n/a')}\n")
        self.write(f"Stage     : {scenario_stage_label(config)}\n")
        self.write(f"Benchmark : {metadata.get('benchmark_status', 'unspecified')}\n")
        self.write(f"Path      : {relative_to_root(path, self.root)}\n")
        self.write(f"Frequency : {config['frequency']}\n")
        self.write(f"Impact    : {config['impact']}\n")
        if metadata.get("description"):
            self.write(f"Notes     : {metadata['description'].strip()}\n")
        return None

    def do_modules(self, arg):
        """modules [search terms]|info <module-id> - Search or inspect Risk Shards."""
        parts = arg.split(maxsplit=1)
        if parts and parts[0] == "info":
            module = find_risk_module(parts[1] if len(parts) > 1 else self.module_id, self.root)
            if module is None:
                self.write("Module not found. Try 'modules'.\n")
                return None
            self.write(format_module_detail(module))
            return None

        query = arg.strip()
        self.write(format_module_list(search_risk_modules(query, self.root)))
        return None

    def do_module(self, arg):
        """module - Alias for modules."""
        return self.do_modules(arg)

    def do_riskshards(self, arg):
        """riskshards - Alias for modules."""
        return self.do_modules(arg)

    def do_registry(self, arg):
        """registry - Show the shard registry summary and contribution contract."""
        del arg
        self.write(format_shard_registry(build_shard_registry(self.root)))
        return None

    def do_coverage(self, arg):
        """coverage [module-id] - Grade shard data strength and self-qualification."""
        module_id = arg.strip() or None
        report = build_coverage_report(self.root, module_id=module_id)
        if module_id and not report["shards"]:
            self.write(f"Unknown risk module: {module_id}\n")
            return None
        self.write(format_coverage_report(report))
        return None

    def do_countries(self, arg):
        """countries [country-id] - Show prioritized country expansion targets."""
        country_id = arg.strip()
        if country_id:
            item = find_country_priority(country_id)
            if item is None:
                self.write(f"Unknown country priority: {country_id}\n")
                return None
            self.write(format_country_priority_detail(item))
            return None
        self.write(format_country_priorities(top_country_priorities()))
        return None

    def do_show(self, arg):
        """show options|evidence|warnings|assumptions|gaps - Inspect current state."""
        topic = arg.strip().lower() or "options"
        if topic == "options":
            self.show_options()
        elif topic in {"evidence", "selected"}:
            self.show_selected_evidence()
        elif topic == "warnings":
            self.show_report_list("warnings")
        elif topic == "assumptions":
            self.show_report_list("assumptions")
        elif topic == "gaps":
            self.show_gaps()
        else:
            self.write("Usage: show options|evidence|warnings|assumptions|gaps\n")
        return None

    def do_set(self, arg):
        """set <option> <value> - Set trials, dist, seed, org, calibration, threat, outputs."""
        parts = arg.split(maxsplit=1)
        if len(parts) != 2:
            self.write("Usage: set <option> <value>\n")
            return None

        key, value = parts[0].lower(), parts[1].strip()
        aliases = {
            "org": "org_profile",
            "org-profile": "org_profile",
            "report": "report_output",
            "markdown": "markdown_output",
            "scenario": "scenario_output",
        }
        key = aliases.get(key, key)

        try:
            if key == "trials":
                self.options[key] = int(value)
            elif key == "seed":
                self.options[key] = None if value.lower() in {"none", "off"} else int(value)
            elif key == "dist":
                if value not in {"pert", "triangular"}:
                    raise ValueError("dist must be pert or triangular")
                self.options[key] = value
            elif key in {"org_profile", "calibration", "report_output", "markdown_output", "scenario_output"}:
                self.options[key] = resolve_path(self.root, value)
            elif key == "threat":
                self.options[key] = value
            else:
                self.write(f"Unknown option: {key}\n")
                return None
        except ValueError as exc:
            self.write(f"Could not set {key}: {exc}\n")
            return None

        self.write(f"{key} = {format_option(self.options[key], self.root)}\n")
        return None

    def do_calibrate(self, arg):
        """calibrate - Generate an org-specific scenario plus JSON/Markdown reports."""
        del arg
        missing = self.missing_calibration_options()
        if missing:
            self.write(f"Missing required options: {', '.join(missing)}\n")
            self.write("Use 'set org <path>', 'set calibration <path>', and 'set threat <id>'.\n")
            return None

        try:
            report = run_calibration(
                self.scenario_path,
                self.options["org_profile"],
                self.root / "evidence",
                self.options["calibration"],
                threat=self.options["threat"],
                manifest_path=self.root / "sources" / "manifest.json",
                fx_rates_path=self.root / "calibrations" / "fx_rates.yaml",
            )
            report_path = write_calibration_report(report, self.options["report_output"])
            markdown_path = write_calibration_markdown_report(report, self.options["markdown_output"])
            scenario_path = write_calibrated_scenario(report, self.options["scenario_output"])
        except Exception as exc:
            self.write(f"Calibration failed: {exc}\n")
            return None

        self.last_calibration_report = report
        self.active_run_path = scenario_path
        self.last_paths.update({
            "calibration_json": report_path,
            "calibration_markdown": markdown_path,
            "calibrated_scenario": scenario_path,
        })

        generated = report["generated_scenario"]
        self.write("Calibration complete.\n")
        self.write(f"Scenario : {generated['metadata']['name']}\n")
        self.write(f"Frequency: {generated['frequency']}\n")
        self.write(f"Impact   : {generated['impact']}\n")
        self.write(f"Warnings : {len(report['warnings'])}\n")
        self.write(f"Quality issues: {len(report['quality_issues'])}\n")
        self.write(f"JSON     : {relative_to_root(report_path, self.root)}\n")
        self.write(f"Markdown : {relative_to_root(markdown_path, self.root)}\n")
        self.write(f"Scenario : {relative_to_root(scenario_path, self.root)}\n")
        return None

    def do_run(self, arg):
        """run - Simulate the selected or calibrated scenario."""
        del arg
        if self.active_run_path is None:
            self.write("No scenario selected. Try 'modules' and 'use <risk-shard-id>', or run 'workflow'.\n")
            return None

        try:
            run = run_portfolio(
                self.active_run_path,
                trials=self.options["trials"],
                dist_type=self.options["dist"],
                seed=self.options["seed"],
            )
            lec_path = plot_lec(run["aggregate"], "Console", output_dir=self.results_dir)
        except Exception as exc:
            self.write(f"Run failed: {exc}\n")
            return None

        self.last_run = run
        self.last_paths["lec"] = lec_path
        self.write_run_receipt(run)
        self.write("Results\n")
        print_stats(
            run["portfolio"],
            self.write,
            run["metadata"].get("currencies", {}).get("portfolio_currency"),
            paint_fn=self.c,
        )
        self.write(f"LEC: {relative_to_root(lec_path, self.root)}\n")
        self.write("Next consume: explain; report json\n")
        self.write("Next enhance: packs; show gaps; propose; enhance\n")
        self.write("Start over  : start over\n")
        return None

    def do_report(self, arg):
        """report json|markdown|exec - Write or show latest report artifacts."""
        kind = arg.strip().lower() or "json"
        if kind == "json":
            if not self.last_run:
                self.write("No simulation run available. Run 'run' first.\n")
                return None
            path = export_report(
                self.last_run["shards"],
                self.last_run["portfolio"],
                output_dir=self.results_dir,
                metadata=self.last_run["metadata"],
            )
            self.last_paths["simulation_json"] = path
            self.write(f"Simulation JSON: {relative_to_root(path, self.root)}\n")
        elif kind == "markdown":
            path = self.last_paths.get("calibration_markdown")
            if not path:
                self.write("No Markdown calibration report available. Run 'calibrate' first.\n")
                return None
            self.write(f"Calibration Markdown: {relative_to_root(path, self.root)}\n")
        elif kind == "exec":
            self.write_executive_report()
        else:
            self.write("Usage: report json|markdown|exec\n")
        return None

    def write_executive_report(self):
        if not self.last_run:
            self.write("No simulation run available. Run 'run' first.\n")
            return None
        module = self.current_module()
        if module is None:
            self.write(
                "No Risk Shard selected. Select one with 'use <risk-shard-id>' and "
                "'run' before 'report exec'.\n"
            )
            return None
        registry = build_evidence_pack_registry(self.root, module_id=module["id"])
        pack = registry["packs"][0] if registry["packs"] else {}
        report = build_executive_report(self.last_run, module, pack, root=self.root)
        markdown = format_executive_report_markdown(report)
        output_path = self.results_dir / f"exec_report_{module['id']}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        self.last_paths["executive_markdown"] = output_path
        self.write(f"Executive report: {relative_to_root(output_path, self.root)}\n")
        self.write(f"Bottom line: average {report['currency'] or ''} "
                   f"{round(report['mean']):,}/yr, P95 {round(report['p95']):,}, "
                   f"P99 {round(report['p99']):,}.\n")
        return None

    def do_toprisks(self, arg):
        """toprisks - Rank starter threats by current evidence and calibration readiness."""
        del arg
        org_profile = self.ensure_org_profile()
        rows = rank_top_risks(org_profile)
        self.write(format_top_risks(rows))
        return None

    def do_risks(self, arg):
        """risks - Alias for toprisks."""
        return self.do_toprisks(arg)

    def do_explain(self, arg):
        """explain - Explain the latest calibration or run state."""
        del arg
        if self.last_calibration_report:
            report = self.last_calibration_report
            generated = report["generated_scenario"]
            warnings = len(report["warnings"])
            issues = len(report["quality_issues"])
            estimated = sum(
                1 for item in report["selected_evidence"]
                if item["evidence_type"] != "source_backed"
            )
            self.write(f"Latest calibration: {generated['metadata']['name']}\n")
            self.write(f"Frequency: {generated['frequency']}\n")
            self.write(f"Impact   : {generated['impact']}\n")
            self.write(f"Selected evidence: {len(report['selected_evidence'])}\n")
            self.write(f"Estimated/synthetic selected parameters: {estimated}\n")
            self.write(f"Warnings: {warnings}; quality issues: {issues}\n")
            self.write("Run 'show evidence', 'show warnings', or 'show gaps' for detail.\n")
        elif self.last_run:
            self.write("Latest simulation run\n")
            self.write(f"Location: {self.breadcrumb()}\n")
            self.write(f"Risk Shard: {self.module_id or 'unset'}\n")
            self.write(f"Run target: {format_option(self.active_run_path, self.root)}\n")
            print_stats(
                self.last_run["portfolio"],
                self.write,
                self.last_run["metadata"].get("currencies", {}).get("portfolio_currency"),
                paint_fn=self.c,
            )
            self.write("Run 'report json' to export the simulation report, or 'enhance' to improve the trust boundary.\n")
        else:
            self.write("No calibration or simulation yet. Try 'workflow'.\n")
        return None

    def do_feeds(self, arg):
        """feeds [source-id] - Inspect source gathering, ingestion, confidence, and renewal."""
        source_id = arg.strip()
        inventory = build_data_feed_inventory()
        if not source_id:
            self.write(format_data_feed_inventory(inventory))
            return None

        feed = next((item for item in inventory["feeds"] if item["id"] == source_id), None)
        if feed is None:
            self.write(f"Unknown source feed: {source_id}\n")
            return None
        self.write(format_feed_detail(feed))
        return None

    def do_packs(self, arg):
        """packs [module-id] - Inspect governed evidence packs for risk modules."""
        module_id = arg.strip() or self.module_id
        registry = build_evidence_pack_registry(self.root, module_id=module_id)
        if module_id:
            if not registry["packs"]:
                self.write(f"Unknown evidence pack module: {module_id}\n")
                return None
            self.write(format_evidence_pack_detail(registry["packs"][0]))
            return None
        self.write(format_evidence_pack_registry(registry))
        return None

    def do_challenge(self, arg):
        """challenge [module-id] [parameter] - Show the value, source, quote, and caveat
        behind a number so you can defend or dispute it. Defaults to the selected shard."""
        parts = arg.split()
        module_id = None
        parameter = None
        # Accept: "", "param", "module", or "module param". A dotted token is a parameter.
        for token in parts:
            if "." in token and parameter is None:
                parameter = token
            elif module_id is None:
                module_id = token
        module_id = module_id or self.module_id
        if not module_id:
            self.write("Select a shard first (use <module-id>) or pass one: challenge <module-id> [parameter]\n")
            return None
        if find_risk_module(module_id, self.root) is None:
            self.write(f"Unknown Risk Shard: {module_id}\n")
            return None
        provenance = build_module_provenance(module_id, self.root)
        self.write(format_provenance(provenance, parameter=parameter))
        self.write(
            "Disagree with a number? Open a pre-filled dispute issue:\n"
            f"  python scripts/riskshard_modules.py provenance {module_id} --dispute <parameter>\n"
        )
        return None

    def do_provenance(self, arg):
        """provenance [module-id] [parameter] - Alias for 'challenge'."""
        return self.do_challenge(arg)

    def do_evidencepacks(self, arg):
        """evidencepacks - Alias for packs."""
        return self.do_packs(arg)

    def do_sources(self, arg):
        """sources [source-id] - Alias for feeds."""
        return self.do_feeds(arg)

    def do_readiness(self, arg):
        """readiness - Show global readiness, coverage, feed, pack, and install status."""
        del arg
        dashboard = build_readiness_dashboard(self.root, self.ensure_org_profile())
        self.write(format_readiness_dashboard(dashboard))
        return None

    def do_beta(self, arg):
        """beta - Show stricter beta readiness before scaling public operations."""
        del arg
        self.write(format_beta_readiness_report(build_beta_readiness_report(self.root)))
        return None

    def do_next(self, arg):
        """next - Show prioritized next best actions and commands."""
        del arg
        dashboard = build_readiness_dashboard(self.root, self.ensure_org_profile())
        self.write(format_next_actions(dashboard))
        return None

    def do_actions(self, arg):
        """actions - Alias for next."""
        return self.do_next(arg)

    def do_pack(self, arg):
        """pack - Show data-pack fingerprint and included paths."""
        del arg
        manifest = build_data_pack_manifest(self.root)
        self.write(format_data_pack_manifest(manifest))
        return None

    def do_propose(self, arg):
        """propose [module-id|threat] - Propose evidence selectors for calibration."""
        explicit_target = arg.strip()
        target = explicit_target or self.module_id or self.options["threat"] or "au_finance_ransomware_midmarket"
        module = find_risk_module(target, self.root) if target else None
        if module is not None:
            org_profile_path = self.root / module["artifacts"]["org_profile"]
            if not explicit_target and module["id"] == self.module_id and self.options["org_profile"]:
                org_profile_path = self.options["org_profile"]
            proposal = propose_module_calibration(
                module["id"],
                root=self.root,
                org_profile_path=org_profile_path,
            )
            self.write(format_module_calibration_proposal(proposal))
            return None

        threat = target or self.options["threat"] or infer_threat(self.scenario_path) or "ransomware"
        proposal = propose_calibration(self.ensure_org_profile(), threat)
        self.write(format_calibration_proposal(proposal))
        return None

    def do_preflight(self, arg):
        """preflight [pack-path] - Run contributor source/evidence/extraction/data-pack checks."""
        pack_path = arg.strip() or None
        self.write(format_contributor_preflight(build_contributor_preflight(self.root, pack_path=pack_path)))
        return None

    def do_doctor(self, arg):
        """doctor - Run local setup, source, evidence, scenario, readiness, and package checks."""
        run_tests = "--run-tests" in arg.split()
        self.write(format_doctor_report(build_doctor_report(self.root, run_tests=run_tests)))
        return None

    def do_contribute(self, arg):
        """contribute - Alias for preflight."""
        return self.do_preflight(arg)

    def do_validate(self, arg):
        """validate - Run evidence quality gates."""
        del arg
        issues = validate_evidence_quality(self.root / "evidence", self.root / "sources" / "manifest.json")
        if not issues:
            self.write("Evidence quality gates passed with no issues.\n")
            return None
        for item in issues:
            self.write(
                f"{item['severity'].upper()} {item['code']} "
                f"{item['record_id']}: {item['message']}\n"
            )
        if has_errors(issues):
            self.write("Validation completed with errors.\n")
        else:
            self.write("Validation completed with warnings only.\n")
        return None

    def do_exit(self, arg):
        """exit - Leave the console."""
        del arg
        self.write("Leaving RiskShard console.\n")
        return True

    def do_quit(self, arg):
        """quit - Leave the console."""
        return self.do_exit(arg)

    def do_EOF(self, arg):
        """Ctrl-D - Leave the console."""
        self.write("\n")
        return self.do_exit(arg)

    def show_options(self):
        self.write(f"Location      : {self.breadcrumb()}\n")
        self.write(f"Risk Shard    : {self.module_id or 'unset'}\n")
        self.write_selected_shard_context()
        self.write(f"Scenario      : {format_option(self.scenario_path, self.root)}\n")
        self.write(f"Run target    : {format_option(self.active_run_path, self.root)}\n")
        for key in [
            "org_profile",
            "calibration",
            "threat",
            "trials",
            "dist",
            "seed",
            "report_output",
            "markdown_output",
            "scenario_output",
        ]:
            self.write(f"{key:<13}: {format_option(self.options[key], self.root)}\n")

    def show_selected_evidence(self):
        if not self.last_calibration_report:
            self.write("No calibration report available. Run 'calibrate' first.\n")
            return
        for item in self.last_calibration_report["selected_evidence"]:
            selection = item.get("selection", {})
            self.write(
                f"{item['parameter']}: {item['title']} "
                f"score={selection.get('match_score')} "
                f"best={selection.get('best_available_for_parameter')}\n"
            )
            alternatives = selection.get("higher_scored_alternatives", [])
            for alternative in alternatives:
                self.write(
                    f"  higher: {alternative['id']} "
                    f"score={alternative['score']} source={alternative['source_name']}\n"
                )

    def show_report_list(self, key):
        if not self.last_calibration_report:
            self.write("No calibration report available. Run 'calibrate' first.\n")
            return
        items = self.last_calibration_report.get(key, [])
        if not items:
            self.write(f"No {key}.\n")
            return
        for item in items:
            if key == "warnings":
                self.write(f"- {item['code']}: {item['message']}\n")
            else:
                self.write(f"- {item.get('name', 'assumption')}: {item.get('notes', '')}\n")

    def show_gaps(self):
        org_profile = self.ensure_org_profile()
        threat = self.options["threat"]
        if not threat:
            threat = infer_threat(self.scenario_path) or "ransomware"
            self.options["threat"] = threat
        analysis = analyze_gaps(
            org_profile,
            threat,
            calibration_path=self.options.get("calibration"),
        )
        self.write(format_gap_analysis(analysis))

    def write_context_summary(self):
        self.write(f"Location      : {self.breadcrumb()}\n")
        self.write(f"Risk Shard    : {self.module_id or 'unset'}\n")
        self.write_selected_shard_context()
        self.write(f"Scenario      : {format_option(self.scenario_path, self.root)}\n")
        self.write(f"Run target    : {format_option(self.active_run_path, self.root)}\n")
        self.write(f"Org profile   : {format_option(self.options['org_profile'], self.root)}\n")
        self.write(f"Calibration   : {format_option(self.options['calibration'], self.root)}\n")
        self.write(f"Threat        : {self.options['threat'] or 'unset'}\n")
        self.write(
            "Simulation    : "
            f"trials={self.options['trials']}, "
            f"dist={self.options['dist']}, "
            f"seed={format_option(self.options['seed'], self.root)}\n"
        )
        self.write(f"Last run      : {'available' if self.last_run else 'none'}\n")
        self.write(f"Last calibration: {'available' if self.last_calibration_report else 'none'}\n")
        self.write("Consume model : consume -> run -> explain -> report json\n")
        self.write("Enhance model : enhance -> packs -> show gaps -> propose -> validate\n")
        self.write("Start over    : start over\n")

    def write_selected_shard_context(self):
        module = self.current_module()
        if module:
            context = module.get("context", {})
            self.write(
                "Context       : "
                f"country={context.get('country', 'unknown')}; "
                f"industry={context.get('industry', 'unknown')}; "
                f"size={context.get('company_size', 'unknown')}; "
                f"threat={module.get('threat', self.options['threat'] or 'unknown')}\n"
            )
            notes = module.get("practitioner_notes", {})
            if notes.get("good_for"):
                self.write(f"Use for       : {notes['good_for']}\n")
            if notes.get("not_good_for"):
                self.write(f"Not for       : {notes['not_good_for']}\n")
        elif self.options["threat"] or self.scenario_path:
            self.write(
                "Context       : "
                f"country=unknown; industry=unknown; size=unknown; "
                f"threat={self.options['threat'] or infer_threat(self.scenario_path) or 'unknown'}\n"
            )

        if self.scenario_path:
            config = load_and_validate(self.scenario_path)
            metadata = config.get("metadata", {})
            self.write(f"Stage         : {scenario_stage_label(config)}\n")
            self.write(f"Benchmark     : {metadata.get('benchmark_status', 'unspecified')}\n")

        captured = [
            f"scenario={'yes' if self.scenario_path else 'no'}",
            f"org={'yes' if self.options['org_profile'] else 'no'}",
            f"calibration={'yes' if self.options['calibration'] else 'no'}",
            f"threat={'yes' if self.options['threat'] else 'no'}",
        ]
        self.write(f"Inputs        : {'; '.join(captured)}\n")

    def write_run_receipt(self, run):
        config = load_and_validate(self.active_run_path)
        metadata = config.get("metadata", {})
        scenario_items = run["metadata"]["reproducibility"]["scenarios"]
        scenario_meta = scenario_items[0] if scenario_items else {}
        self.write("Run complete.\n")
        self.write("Run receipt\n")
        self.write(f"Location      : {self.breadcrumb(include_run=True)}\n")
        self.write(f"Risk Shard    : {self.module_id or 'unset'}\n")
        self.write_selected_shard_context()
        self.write(f"Scenario      : {metadata.get('name', 'unknown')}\n")
        self.write(f"Scenario file : {format_option(self.active_run_path, self.root)}\n")
        self.write(f"Org profile   : {format_option(self.options['org_profile'], self.root)}\n")
        self.write(f"Threat        : {self.options['threat'] or infer_threat(self.active_run_path) or 'unset'}\n")
        self.write(
            "Simulation    : "
            f"trials={self.options['trials']}, "
            f"dist={self.options['dist']}, "
            f"seed={format_option(self.options['seed'], self.root)}\n"
        )
        self.write(f"Fingerprint   : {scenario_meta.get('fingerprint', 'unknown')}\n")
        self.write(f"Currency      : {metadata.get('currency', 'unspecified')}\n")
        if self.last_calibration_report:
            estimated = sum(
                1 for item in self.last_calibration_report["selected_evidence"]
                if item["evidence_type"] != "source_backed"
            )
            self.write(
                "Calibration   : latest calibration in this session; "
                f"selected_evidence={len(self.last_calibration_report['selected_evidence'])}, "
                f"estimated_or_synthetic={estimated}, "
                f"warnings={len(self.last_calibration_report['warnings'])}, "
                f"quality_issues={len(self.last_calibration_report['quality_issues'])}\n"
            )
        else:
            self.write("Calibration   : no calibration run in this session; scenario values were used as-is.\n")
        self.write("Trust note    : numbers are useful only with the evidence pack and gaps beside them.\n")

    def missing_calibration_options(self):
        missing = []
        if self.scenario_path is None:
            missing.append("scenario")
        for key in ["org_profile", "calibration", "threat"]:
            if not self.options[key]:
                missing.append(key)
        return missing

    def apply_recommendations(self, path):
        stem = path.stem
        if "ransomware" in stem and self.options["threat"] is None:
            self.options["threat"] = "ransomware"
        if "business_email_compromise" in stem and self.options["threat"] is None:
            self.options["threat"] = "business_email_compromise"
        if stem == "au_finance_ransomware_midmarket":
            self.options["org_profile"] = self.root / "org_profiles" / "au_finance_midmarket.yaml"
            self.options["calibration"] = self.root / "calibrations" / "au_finance_ransomware.yaml"
            self.options["threat"] = "ransomware"
        if stem == "business_email_compromise":
            self.options["org_profile"] = self.root / "org_profiles" / "au_finance_midmarket.yaml"
            self.options["calibration"] = self.root / "calibrations" / "au_finance_business_email_compromise.yaml"
            self.options["threat"] = "business_email_compromise"
        if stem == "data_breach":
            self.options["org_profile"] = self.root / "org_profiles" / "au_finance_midmarket.yaml"
            self.options["calibration"] = self.root / "calibrations" / "au_finance_data_breach.yaml"
            self.options["threat"] = "data_breach"

    def select_module(self, module):
        self.module_id = module["id"]
        artifacts = module["artifacts"]
        self.scenario_path = self.root / artifacts["scenario"]
        self.active_run_path = self.scenario_path
        self.options["org_profile"] = self.root / artifacts["org_profile"]
        self.options["calibration"] = self.root / artifacts["calibration"]
        self.options["threat"] = module["threat"]

    def current_module(self):
        if self.module_id:
            return find_risk_module(self.module_id, self.root)
        if self.scenario_path:
            return module_for_scenario(self.scenario_path, self.root)
        return None

    def refresh_prompt(self):
        if self.scenario_path:
            self.prompt = f"riskshard({self.scenario_path.stem})> "
        else:
            self.prompt = "riskshard> "

    def breadcrumb(self, include_run=None):
        parts = ["Start"]
        if self.scenario_path or self.module_id:
            parts.append("Scenario")
        if self.last_calibration_report:
            parts.append("Calibration")
        should_include_run = self.last_run if include_run is None else include_run
        if should_include_run:
            parts.append("Run Risk")
        return " > ".join(f"[{part}]" for part in parts)

    def reset_state(self):
        self.scenario_path = None
        self.active_run_path = None
        self.module_id = None
        self.last_calibration_report = None
        self.last_run = None
        self.last_paths = {}
        self.options = self.default_options()
        self.refresh_prompt()

    def ensure_org_profile(self):
        if self.options["org_profile"]:
            return self.options["org_profile"]
        default = self.root / "org_profiles" / "au_finance_midmarket.yaml"
        self.options["org_profile"] = default
        self.write(f"Using default org profile: {relative_to_root(default, self.root)}\n")
        return default

    def write(self, text):
        self.stdout.write(text)


def resolve_scenario(root, value):
    if not value:
        return None
    root = Path(root)
    candidate = resolve_path(root, value)
    if candidate.exists():
        return candidate
    for path in scenario_paths(root):
        if path.stem == value:
            return path
    return None


def resolve_path(root, value):
    path = Path(value)
    if path.is_absolute():
        return path
    return Path(root) / path


def relative_to_root(path, root):
    if path is None:
        return "unset"
    path = Path(path)
    try:
        return str(path.resolve().relative_to(Path(root).resolve()))
    except ValueError:
        return str(path)


def format_option(value, root):
    if value is None:
        return "unset"
    if isinstance(value, Path):
        return relative_to_root(value, root)
    return str(value)


def infer_threat(path):
    if not path:
        return None
    stem = Path(path).stem
    if "ransomware" in stem:
        return "ransomware"
    if "breach" in stem:
        return "data_breach"
    if "business_email_compromise" in stem:
        return "business_email_compromise"
    return None


def format_money(value, currency=None):
    if currency and currency != "unspecified":
        return f"{currency} {value:,.2f}"
    return f"${value:,.2f}"


def print_stats(stats, write, currency=None, paint_fn=None):
    tint = paint_fn or (lambda text, *codes: text)
    write(f"AVG : {tint(format_money(stats['mean'], currency), 'data')}\n")
    write(f"P50 : {tint(format_money(stats['p50'], currency), 'data')}\n")
    write(f"P95 : {tint(format_money(stats['p95'], currency), 'data')}\n")
    write(f"P99 : {tint(format_money(stats['p99'], currency), 'data')}\n")
    write(f"Note: {tint(IMPACT_UNCERTAINTY_NOTE, 'muted')}\n")
