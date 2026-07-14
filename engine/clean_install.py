import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from engine.project_paths import PROJECT_ROOT


DEFAULT_PROOF_PATH = PROJECT_ROOT / "release" / "clean_install_proof.json"
DEFAULT_VENV_PATH = Path("/tmp/riskshard-beta-venv")
REQUIRED_COMMANDS = (
    "pip_show_riskshard",
    "package_smoke",
    "benchmark_target",
    "modules_list",
    "toprisks_json",
    "portfolio_smoke",
)


def build_clean_install_proof(
    root=PROJECT_ROOT,
    *,
    venv_path=DEFAULT_VENV_PATH,
    recreate=False,
    runner=None,
):
    root = Path(root).resolve()
    venv_path = Path(venv_path).resolve()
    runner = runner or subprocess.run

    if recreate and venv_path.exists():
        shutil.rmtree(venv_path)
    if not venv_path.exists():
        run_command(
            [sys.executable, "-m", "venv", str(venv_path)],
            cwd=root,
            env=os.environ.copy(),
            runner=runner,
            timeout=120,
        )

    python_bin = venv_python(venv_path)
    scripts_dir = python_bin.parent
    env = os.environ.copy()
    env["RISKSHARD_ROOT"] = str(root)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PATH"] = f"{scripts_dir}{os.pathsep}{env.get('PATH', '')}"

    commands = [
        ("install_package", [str(python_bin), "-m", "pip", "install", str(root)]),
        ("pip_show_riskshard", [str(python_bin), "-m", "pip", "show", "riskshard"]),
        ("package_smoke", [str(scripts_dir / "riskshard-package-smoke")]),
        (
            "benchmark_target",
            [
                str(scripts_dir / "riskshard-benchmark"),
                "--target",
                "gb_finance_data_breach_midmarket",
            ],
        ),
        ("modules_list", [str(scripts_dir / "riskshard-modules"), "list"]),
        ("toprisks_json", [str(scripts_dir / "riskshard-toprisks"), "--limit", "2", "--json"]),
        (
            "portfolio_smoke",
            [
                str(scripts_dir / "riskshard"),
                str(root / "scenarios"),
                "--trials",
                "25",
                "--dist",
                "pert",
                "--seed",
                "42",
            ],
        ),
    ]
    results = [
        sanitize_result(
            run_named_command(name, command, cwd=root, env=env, runner=runner),
            root,
            venv_path,
        )
        for name, command in commands
    ]
    command_results = [result for result in results if result["name"] != "install_package"]
    status = "pass" if all(result["returncode"] == 0 for result in results) else "fail"

    return {
        "proof_type": "riskshard_clean_install_proof",
        "status": status,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "root": "$RISKSHARD_ROOT",
        "venv_path": "$RISKSHARD_VENV",
        "python": sanitize_text(str(python_bin), root, venv_path),
        "package_name": "riskshard",
        "required_commands": list(REQUIRED_COMMANDS),
        "commands": results,
        "summary": {
            "passed": sum(1 for result in command_results if result["returncode"] == 0),
            "total": len(command_results),
        },
    }


def run_named_command(name, command, *, cwd, env, runner):
    result = run_command(command, cwd=cwd, env=env, runner=runner, timeout=180)
    return {
        "name": name,
        "command": command,
        "returncode": result.returncode,
        "stdout": trim_output(result.stdout) if result.returncode else "",
        "stderr": trim_output(result.stderr) if result.returncode else "",
    }


def run_command(command, *, cwd, env, runner, timeout):
    return runner(
        command,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def venv_python(venv_path):
    venv_path = Path(venv_path)
    if os.name == "nt":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def trim_output(value, limit=4000):
    value = value or ""
    if len(value) <= limit:
        return value
    return value[:limit] + "\n... truncated ..."


def sanitize_result(result, root, venv_path):
    return {
        **result,
        "command": [sanitize_text(part, root, venv_path) for part in result["command"]],
        "stdout": sanitize_text(result["stdout"], root, venv_path),
        "stderr": sanitize_text(result["stderr"], root, venv_path),
    }


def sanitize_text(value, root, venv_path):
    value = str(value)
    replacements = [
        (str(Path(root)), "$RISKSHARD_ROOT"),
        (str(Path(root).resolve()), "$RISKSHARD_ROOT"),
        (str(Path(venv_path)), "$RISKSHARD_VENV"),
        (str(Path(venv_path).resolve()), "$RISKSHARD_VENV"),
    ]
    for original, replacement in sorted(set(replacements), key=lambda item: len(item[0]), reverse=True):
        value = value.replace(original, replacement)
    return value


def write_clean_install_proof(proof, output_path=DEFAULT_PROOF_PATH):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
    return output_path


def load_clean_install_proof(path=DEFAULT_PROOF_PATH):
    path = Path(path)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def summarize_clean_install_proof(proof):
    if not proof:
        return {
            "status": "fail",
            "detail": "not recorded",
            "path": str(DEFAULT_PROOF_PATH),
            "missing_commands": list(REQUIRED_COMMANDS),
        }
    commands = {
        item["name"]: item
        for item in proof.get("commands", [])
    }
    missing = [
        name
        for name in REQUIRED_COMMANDS
        if commands.get(name, {}).get("returncode") != 0
    ]
    status = "pass" if proof.get("status") == "pass" and not missing else "fail"
    detail = (
        f"{proof.get('summary', {}).get('passed', 0)}/"
        f"{proof.get('summary', {}).get('total', len(REQUIRED_COMMANDS))} commands"
    )
    if status == "pass":
        detail = f"{detail}; {proof.get('generated_at')}"
    return {
        "status": status,
        "detail": detail,
        "path": proof.get("path", str(DEFAULT_PROOF_PATH)),
        "generated_at": proof.get("generated_at"),
        "missing_commands": missing,
    }


def format_clean_install_proof(proof):
    summary = summarize_clean_install_proof(proof)
    lines = [
        "RiskShard clean-install proof",
        f"Status: {summary['status']}",
        f"Detail: {summary['detail']}",
    ]
    if proof:
        lines.extend([
            f"Root: {proof.get('root')}",
            f"Venv: {proof.get('venv_path')}",
            "",
            "Commands",
        ])
        for result in proof.get("commands", []):
            status = "PASS" if result["returncode"] == 0 else "FAIL"
            lines.append(f"- {status} {result['name']}: {' '.join(result['command'])}")
    return "\n".join(lines) + "\n"
