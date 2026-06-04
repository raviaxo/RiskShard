from pathlib import Path

from engine.profiles import load_yaml_file


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODULE_DIR = PROJECT_ROOT / "risk_modules"
REQUIRED_PARAMETERS = (
    "frequency.min",
    "frequency.likely",
    "frequency.max",
    "impact.min",
    "impact.likely",
    "impact.max",
)
REQUIRED_FIELDS = ("id", "title", "version", "status", "threat", "context", "artifacts")
REQUIRED_ARTIFACTS = ("scenario", "org_profile", "calibration", "evidence", "extractions")


class RiskModuleError(ValueError):
    pass


def module_paths(module_dir=DEFAULT_MODULE_DIR):
    module_dir = Path(module_dir)
    if not module_dir.exists():
        return []
    return sorted(
        path
        for path in module_dir.glob("*.yaml")
        if path.name != "README.md"
    )


def load_risk_modules(root=PROJECT_ROOT, module_dir=None):
    root = Path(root)
    module_dir = Path(module_dir) if module_dir else root / "risk_modules"
    modules = []
    seen = set()

    for path in module_paths(module_dir):
        module = load_yaml_file(path)
        validate_module(module, root, path)
        if module["id"] in seen:
            raise RiskModuleError(f"Duplicate risk module id: {module['id']}")
        seen.add(module["id"])
        module = dict(module)
        module["_source_file"] = path.relative_to(root).as_posix()
        modules.append(module)

    return sorted(modules, key=lambda item: item["id"])


def validate_module(module, root, path):
    for field in REQUIRED_FIELDS:
        if field not in module:
            raise RiskModuleError(f"{path}: missing required field {field}")

    artifacts = module["artifacts"]
    for field in REQUIRED_ARTIFACTS:
        if field not in artifacts:
            raise RiskModuleError(f"{path}: missing artifacts.{field}")

    for field in ("industry", "country", "company_size"):
        if field not in module["context"]:
            raise RiskModuleError(f"{path}: missing context.{field}")

    for field in ("scenario", "org_profile", "calibration"):
        if not (root / artifacts[field]).exists():
            raise RiskModuleError(f"{path}: artifacts.{field} does not exist: {artifacts[field]}")

    for field in ("evidence", "extractions", "controls"):
        for artifact_path in artifacts.get(field, []):
            if not (root / artifact_path).exists():
                raise RiskModuleError(f"{path}: artifacts.{field} does not exist: {artifact_path}")

    required = tuple(module.get("required_parameters") or REQUIRED_PARAMETERS)
    missing = [parameter for parameter in REQUIRED_PARAMETERS if parameter not in required]
    if missing:
        raise RiskModuleError(f"{path}: required_parameters missing {', '.join(missing)}")


def find_risk_module(value, root=PROJECT_ROOT):
    value = (value or "").strip()
    if not value:
        return None

    modules = load_risk_modules(root)
    by_id = {module["id"]: module for module in modules}
    if value in by_id:
        return by_id[value]

    value_lower = value.lower()
    for module in modules:
        scenario_stem = Path(module["artifacts"]["scenario"]).stem
        if value_lower in {
            scenario_stem.lower(),
            module["title"].lower(),
            module["threat"].lower(),
        }:
            return module
    return None


def module_for_scenario(scenario_path, root=PROJECT_ROOT):
    if scenario_path is None:
        return None
    root = Path(root)
    try:
        rel_path = Path(scenario_path).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        rel_path = Path(scenario_path).as_posix()

    for module in load_risk_modules(root):
        if module["artifacts"]["scenario"] == rel_path:
            return module
    return None


def search_risk_modules(query="", root=PROJECT_ROOT):
    terms = [term.lower() for term in query.split() if term.strip()]
    rows = []
    for module in load_risk_modules(root):
        haystack = " ".join([
            module["id"],
            module["title"],
            module["threat"],
            module["status"],
            " ".join(module.get("tags", [])),
            module.get("description", ""),
        ]).lower()
        if terms and not all(term in haystack for term in terms):
            continue
        rows.append(module)
    return rows


def format_module_list(modules):
    lines = [
        "Risk modules",
        "ID                                      Status             Threat                     Context",
        "--                                      ------             ------                     -------",
    ]
    for module in modules:
        context = module["context"]
        lines.append(
            f"{module['id']:<39} {module['status']:<18} "
            f"{module['threat']:<26} "
            f"{context['country']}/{context['industry']}/{context['company_size']}"
        )
    if len(lines) == 3:
        lines.append("No matching risk modules.")
    return "\n".join(lines) + "\n"


def format_module_detail(module):
    artifacts = module["artifacts"]
    notes = module.get("practitioner_notes", {})
    lines = [
        f"Risk module: {module['id']}",
        f"Title      : {module['title']}",
        f"Version    : {module['version']}",
        f"Status     : {module['status']}",
        f"Threat     : {module['threat']}",
        (
            "Context    : "
            f"{module['context']['country']} / {module['context']['industry']} / "
            f"{module['context']['company_size']}"
        ),
        f"Scenario   : {artifacts['scenario']}",
        f"Org profile: {artifacts['org_profile']}",
        f"Calibration: {artifacts['calibration']}",
        "",
        "Evidence files:",
    ]
    lines.extend(f"- {path}" for path in artifacts.get("evidence", []))
    lines.extend(["", "Extraction files:"])
    lines.extend(f"- {path}" for path in artifacts.get("extractions", []))
    if artifacts.get("controls"):
        lines.extend(["", "Control profiles:"])
        lines.extend(f"- {path}" for path in artifacts.get("controls", []))
    lines.extend([
        "",
        f"Good for   : {notes.get('good_for', 'n/a')}",
        f"Not good for: {notes.get('not_good_for', 'n/a')}",
    ])
    return "\n".join(lines) + "\n"
