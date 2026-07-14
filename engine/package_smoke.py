import importlib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_EXPECTED_ENTRY_POINTS = {
    "riskshard",
    "riskshard-calibrate",
    "riskshard-console",
    "riskshard-web-console",
    "riskshard-feeds",
    "riskshard-readiness",
    "riskshard-data-pack",
    "riskshard-preflight",
    "riskshard-doctor",
    "riskshard-modules",
    "riskshard-toprisks",
    "riskshard-package-smoke",
    "riskshard-benchmark",
    "riskshard-beta",
    "riskshard-clean-install",
}


def build_package_smoke_report(root=PROJECT_ROOT, *, expected_entry_points=None):
    root = Path(root)
    pyproject = root / "pyproject.toml"
    expected_entry_points = expected_entry_points or DEFAULT_EXPECTED_ENTRY_POINTS

    if not pyproject.exists():
        return {
            "status": "fail",
            "pyproject": str(pyproject),
            "configured_count": 0,
            "entry_points": [],
            "missing_entry_points": sorted(expected_entry_points),
        }

    targets = parse_project_script_targets(pyproject.read_text())
    entry_points = [
        validate_entry_point(name, target)
        for name, target in sorted(targets.items())
    ]
    configured_names = set(targets)
    missing = sorted(expected_entry_points - configured_names)
    for name in missing:
        entry_points.append({
            "name": name,
            "target": None,
            "status": "fail",
            "detail": "missing from pyproject.toml",
        })

    status = "pass" if all(item["status"] == "pass" for item in entry_points) else "fail"
    return {
        "status": status,
        "pyproject": str(pyproject),
        "configured_count": len(targets),
        "entry_points": entry_points,
        "missing_entry_points": missing,
    }


def parse_project_scripts(text):
    return list(parse_project_script_targets(text).keys())


def parse_project_script_targets(text):
    targets = {}
    in_scripts = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line == "[project.scripts]":
            in_scripts = True
            continue
        if in_scripts and line.startswith("["):
            break
        if in_scripts and "=" in line:
            name, target = line.split("=", 1)
            targets[name.strip()] = target.strip().strip('"').strip("'")

    return targets


def validate_entry_point(name, target):
    if not target or ":" not in target:
        return {
            "name": name,
            "target": target,
            "status": "fail",
            "detail": "target must be module:function",
        }

    module_name, function_name = target.split(":", 1)
    if not module_name or not function_name:
        return {
            "name": name,
            "target": target,
            "status": "fail",
            "detail": "target must include module and function",
        }

    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        return {
            "name": name,
            "target": target,
            "status": "fail",
            "detail": f"import failed: {exc}",
        }

    target_function = getattr(module, function_name, None)
    if not callable(target_function):
        return {
            "name": name,
            "target": target,
            "status": "fail",
            "detail": f"{function_name} is not callable",
        }

    return {
        "name": name,
        "target": target,
        "status": "pass",
        "detail": "importable callable",
    }


def format_package_smoke_report(report):
    lines = [
        "RiskShard package smoke",
        f"Status: {report['status']}",
        f"Configured entry points: {report['configured_count']}",
        "",
    ]

    for item in report["entry_points"]:
        target = f" -> {item['target']}" if item["target"] else ""
        lines.append(f"- {item['name']}{target}: {item['status']} ({item['detail']})")

    return "\n".join(lines) + "\n"
