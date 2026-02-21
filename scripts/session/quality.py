"""Quality gate runner — reads .session/config.json and runs commands via subprocess."""

import json
import subprocess

from .constants import CONFIG_PATH


def run_quality_gates(fix: bool = False, scope: str = None) -> dict:
    """Run all enabled quality gates. Returns dict of {gate: {passed, message}}.

    Args:
        fix: If True, run formatting commands (auto-fix).
        scope: Limit to 'backend' or 'frontend'. Default: both.
    """
    if not CONFIG_PATH.exists():
        return {
            "error": {"passed": False, "message": f"Config not found: {CONFIG_PATH}"}
        }

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    gates = config.get("quality_gates", {})
    results = {}

    gate_configs = [
        ("test_execution", "Test Execution"),
        ("linting", "Linting"),
        ("formatting", "Formatting"),
        ("type_checking", "Type Checking"),
    ]

    for gate_key, gate_name in gate_configs:
        gate = gates.get(gate_key, {})
        if not gate.get("enabled", False):
            results[gate_name] = {"passed": True, "message": "Disabled"}
            continue

        commands = gate.get("commands", {})
        gate_passed = True
        messages = []

        for lang, cmd in commands.items():
            # Filter by scope
            if scope == "backend" and lang == "javascript":
                continue
            if scope == "frontend" and lang == "python":
                continue

            try:
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=120
                )
                if result.returncode == 0:
                    messages.append(f"{lang}: passed")
                else:
                    gate_passed = False
                    # Get last few lines of output for context
                    stderr = (
                        result.stderr.strip().split("\n")[-3:]
                        if result.stderr.strip()
                        else []
                    )
                    stdout = (
                        result.stdout.strip().split("\n")[-3:]
                        if result.stdout.strip()
                        else []
                    )
                    error_lines = stderr or stdout
                    messages.append(f"{lang}: FAILED — {'; '.join(error_lines)}")
            except subprocess.TimeoutExpired:
                gate_passed = False
                messages.append(f"{lang}: TIMEOUT (>120s)")
            except FileNotFoundError:
                gate_passed = False
                messages.append(f"{lang}: command not found ({cmd})")

        results[gate_name] = {
            "passed": gate_passed,
            "message": "; ".join(messages) if messages else "No commands configured",
        }

    return results
