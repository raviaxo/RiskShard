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
from engine.experience import analyze_gaps, format_gap_analysis, format_top_risks, rank_top_risks
from engine.experience import format_calibration_proposal, propose_calibration
from engine.fair_calc import export_report, load_and_validate, plot_lec, run_portfolio
from engine.governance import (
    build_data_feed_inventory,
    format_data_feed_inventory,
    format_feed_detail,
)
from engine.data_packs import build_data_pack_manifest, format_data_pack_manifest
from engine.contributor import build_contributor_preflight, format_contributor_preflight
from engine.doctor import build_doctor_report, format_doctor_report
from engine.readiness import build_readiness_dashboard, format_next_actions, format_readiness_dashboard
from engine.risk_modules import (
    find_risk_module,
    format_module_detail,
    format_module_list,
    module_for_scenario,
    search_risk_modules,
)
from engine.scenarios import scenario_paths, scenario_stage_label


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class RiskShardConsole(cmd.Cmd):
    intro = (
        "RiskShard console. Type 'help' for commands, "
        "'workflow' for the first-run path, or 'exit' to leave."
    )

    def __init__(self, root=PROJECT_ROOT, stdin=None, stdout=None):
        super().__init__(stdin=stdin, stdout=stdout)
        self.root = Path(root)
        self.scenario_path = None
        self.active_run_path = None
        self.module_id = None
        self.last_calibration_report = None
        self.last_run = None
        self.last_paths = {}
        self.options = {
            "trials": 10000,
            "dist": "pert",
            "seed": 42,
            "org_profile": None,
            "calibration": None,
            "threat": None,
            "report_output": self.root / "results" / "console_calibration.json",
            "markdown_output": self.root / "results" / "console_calibration.md",
            "scenario_output": self.root / "results" / "console_calibrated.yaml",
        }
        self.prompt = "riskshard> "

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
        self.write("1. toprisks\n")
        self.write("2. modules\n")
        self.write("3. countries\n")
        self.write("4. countries GB\n")
        self.write("5. modules info gb_finance_data_breach_midmarket\n")
        self.write("6. packs gb_finance_data_breach_midmarket\n")
        self.write("7. feeds\n")
        self.write("8. doctor\n")
        self.write("9. readiness\n")
        self.write("10. next\n")
        self.write("11. preflight\n")
        self.write("12. use gb_finance_data_breach_midmarket\n")
        self.write("13. show options\n")
        self.write("14. show gaps\n")
        self.write("15. propose\n")
        self.write("16. calibrate\n")
        self.write("17. show evidence\n")
        self.write("18. explain\n")
        self.write("19. run\n")
        self.write("20. report json\n")
        return None

    def help_workflow(self):
        self.do_workflow("")

    def do_use(self, arg):
        """use <module-id|scenario-id|path> - Select a module or scenario."""
        module = find_risk_module(arg.strip(), self.root)
        if module is not None:
            self.select_module(module)
            self.refresh_prompt()
            self.write(f"Using module {module['id']}: {module['title']}\n")
            self.write("Run 'packs', 'show options', then 'propose', 'calibrate', or 'run'.\n")
            return None

        path = resolve_scenario(self.root, arg.strip())
        if path is None:
            self.write("Module or scenario not found. Try 'modules' or 'search'.\n")
            return None

        self.scenario_path = path
        self.active_run_path = path
        module = module_for_scenario(path, self.root)
        self.module_id = module["id"] if module else None
        self.apply_recommendations(path)
        self.refresh_prompt()

        config = load_and_validate(path)
        self.write(f"Using {config['metadata']['name']} ({relative_to_root(path, self.root)})\n")
        self.write("Run 'show options', then 'calibrate' or 'run'.\n")
        return None

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
        """modules [search terms]|info <module-id> - Search or inspect risk modules."""
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
            self.write("No scenario selected. Try 'search' and 'use <id>'.\n")
            return None

        try:
            run = run_portfolio(
                self.active_run_path,
                trials=self.options["trials"],
                dist_type=self.options["dist"],
                seed=self.options["seed"],
            )
            lec_path = plot_lec(run["aggregate"], "Console")
        except Exception as exc:
            self.write(f"Run failed: {exc}\n")
            return None

        self.last_run = run
        self.last_paths["lec"] = lec_path
        self.write("Run complete.\n")
        print_stats(run["portfolio"], self.write)
        self.write(f"LEC: {relative_to_root(lec_path, self.root)}\n")
        return None

    def do_report(self, arg):
        """report json|markdown - Write or show latest report artifacts."""
        kind = arg.strip().lower() or "json"
        if kind == "json":
            if not self.last_run:
                self.write("No simulation run available. Run 'run' first.\n")
                return None
            path = export_report(
                self.last_run["shards"],
                self.last_run["portfolio"],
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
        else:
            self.write("Usage: report json|markdown\n")
        return None

    def do_toprisks(self, arg):
        """toprisks - Rank starter threats for the selected organization profile."""
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
            self.write("Latest simulation run:\n")
            print_stats(self.last_run["portfolio"], self.write)
            self.write("Run 'report json' to export the simulation report.\n")
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
        target = arg.strip() or self.module_id or self.options["threat"] or "au_finance_ransomware_midmarket"
        module = find_risk_module(target, self.root) if target else None
        if module is not None:
            proposal = propose_module_calibration(
                module["id"],
                root=self.root,
                org_profile_path=self.options["org_profile"] or self.root / module["artifacts"]["org_profile"],
            )
            self.write(format_module_calibration_proposal(proposal))
            return None

        threat = target or self.options["threat"] or infer_threat(self.scenario_path) or "ransomware"
        proposal = propose_calibration(self.ensure_org_profile(), threat)
        self.write(format_calibration_proposal(proposal))
        return None

    def do_preflight(self, arg):
        """preflight - Run contributor source/evidence/extraction/data-pack checks."""
        del arg
        self.write(format_contributor_preflight(build_contributor_preflight(self.root)))
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
        self.write(f"Module        : {self.module_id or 'unset'}\n")
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
        analysis = analyze_gaps(org_profile, threat)
        self.write(format_gap_analysis(analysis))

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

    def refresh_prompt(self):
        if self.scenario_path:
            self.prompt = f"riskshard({self.scenario_path.stem})> "
        else:
            self.prompt = "riskshard> "

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


def print_stats(stats, write):
    write(f"AVG : ${stats['mean']:,.2f}\n")
    write(f"P50 : ${stats['p50']:,.2f}\n")
    write(f"P95 : ${stats['p95']:,.2f}\n")
    write(f"P99 : ${stats['p99']:,.2f}\n")
