"""Session lifecycle: start, end, status, validate."""

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .constants import (
    HISTORY_DIR,
    LEARNINGS_PATH,
    SPECS_DIR,
    STATUS_PATH,
    WORK_ITEMS_PATH,
)
from .quality import run_quality_gates


def _load_status() -> dict:
    return json.loads(STATUS_PATH.read_text(encoding="utf-8"))


def _save_status(data: dict) -> None:
    STATUS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_work_items() -> dict:
    return json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))


def _save_work_items(data: dict) -> None:
    data["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
    items = data.get("work_items", {})
    data["metadata"]["total_items"] = len(items)
    data["metadata"]["completed"] = sum(1 for i in items.values() if i["status"] == "completed")
    data["metadata"]["in_progress"] = sum(1 for i in items.values() if i["status"] == "in_progress")
    data["metadata"]["blocked"] = sum(1 for i in items.values() if i["status"] == "blocked")
    WORK_ITEMS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _next_session_number() -> int:
    """Determine next session number by scanning history files."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    existing = []
    for f in HISTORY_DIR.glob("session_*.json"):
        match = re.match(r"session_(\d+)\.json", f.name)
        if match:
            existing.append(int(match.group(1)))
    return max(existing, default=0) + 1


def _get_relevant_learnings(item: dict, limit: int = 10) -> list:
    """Score learnings by keyword overlap with the work item."""
    if not LEARNINGS_PATH.exists():
        return []

    learnings_data = json.loads(LEARNINGS_PATH.read_text(encoding="utf-8"))
    learnings = learnings_data.get("learnings", [])
    if not learnings:
        return []

    # Build keywords from the work item
    keywords = set()
    keywords.update(item.get("title", "").lower().split())
    keywords.update(item.get("type", "").lower().split("_"))

    spec_path = Path(item.get("spec_file", ""))
    if spec_path.exists():
        spec_text = spec_path.read_text(encoding="utf-8").lower()
        keywords.update(word for word in spec_text.split() if len(word) > 3)

    # Score each learning
    scored = []
    for learning in learnings:
        words = set(learning.get("content", "").lower().split())
        words.update(learning.get("tags", []))
        overlap = len(keywords & words)
        if overlap > 0:
            scored.append((overlap, learning))

    scored.sort(key=lambda x: -x[0])
    return [s[1] for s in scored[:limit]]


def start(item_id: str) -> None:
    """Start a session for a work item."""
    status = _load_status()
    if status["status"] == "in_progress":
        print(f"Session already in progress for: {status['current_work_item']}")
        print("Run '/end' to finish the current session first.")
        return

    wi_data = _load_work_items()
    items = wi_data["work_items"]

    if item_id not in items:
        print(f"Work item '{item_id}' not found.")
        return

    item = items[item_id]

    # Check dependencies are met
    unmet = [
        dep for dep in item.get("dependencies", [])
        if items.get(dep, {}).get("status") != "completed"
    ]
    if unmet:
        print(f"Cannot start '{item_id}' — unmet dependencies: {', '.join(unmet)}")
        return

    # Update status
    session_num = _next_session_number()
    now = datetime.now(timezone.utc).isoformat()

    status["current_session"] = session_num
    status["current_work_item"] = item_id
    status["started_at"] = now
    status["status"] = "in_progress"
    _save_status(status)

    # Update work item status
    item["status"] = "in_progress"
    _save_work_items(wi_data)

    # Print briefing
    print(f"Session #{session_num} started")
    print(f"Work Item: {item_id}")
    print(f"Title: {item['title']}")
    print(f"Type: {item['type']} | Priority: {item['priority']}")
    if item.get("urgent"):
        print("URGENT: Yes")
    print(f"Started: {now}")

    # Show spec
    spec_path = Path(item.get("spec_file", ""))
    if spec_path.exists():
        print(f"\n--- Spec ({spec_path}) ---")
        print(spec_path.read_text(encoding="utf-8"))
        print("--- End Spec ---")

    # Show relevant learnings
    relevant = _get_relevant_learnings(item)
    if relevant:
        print(f"\n--- Relevant Learnings ({len(relevant)}) ---")
        for learning in relevant:
            print(f"  [{learning.get('category', 'unknown')}] {learning['content']}")
        print("--- End Learnings ---")

    print(f"\nReady to implement. Run '/status' to check progress, '/validate' to run quality gates.")


def end(completion_status: str = "completed", summary: str = "") -> None:
    """End the current session."""
    status = _load_status()
    if status["status"] != "in_progress":
        print("No active session to end.")
        return

    item_id = status["current_work_item"]
    session_num = status["current_session"]
    started_at = status["started_at"]
    now = datetime.now(timezone.utc).isoformat()

    # Calculate duration
    start_dt = datetime.fromisoformat(started_at)
    end_dt = datetime.now(timezone.utc)
    duration_minutes = int((end_dt - start_dt).total_seconds() / 60)

    # Run quality gates
    print("Running quality gates...")
    gate_results = run_quality_gates()

    # Get git diff stat
    git_diff = ""
    try:
        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD"],
            capture_output=True, text=True, timeout=10
        )
        git_diff = result.stdout.strip().split("\n")[-1] if result.stdout.strip() else "No changes"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        git_diff = "Unable to get git diff"

    # Write session history
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    session_record = {
        "session_number": session_num,
        "work_item_id": item_id,
        "started_at": started_at,
        "ended_at": now,
        "duration_minutes": duration_minutes,
        "status": completion_status,
        "quality_gates": gate_results,
        "git_diff_stat": git_diff,
        "summary": summary,
        "learnings_captured": [],
    }
    history_file = HISTORY_DIR / f"session_{session_num}.json"
    history_file.write_text(json.dumps(session_record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Update work item
    wi_data = _load_work_items()
    items = wi_data["work_items"]
    if item_id in items:
        item = items[item_id]
        if completion_status == "completed":
            item["status"] = "completed"
        elif completion_status == "incomplete":
            item["status"] = "not_started"
        # cancelled keeps current status

        item["sessions"].append({
            "session_number": session_num,
            "started_at": started_at,
            "ended_at": now,
            "status": completion_status,
            "quality_gates_passed": all(
                g.get("passed", False) for g in gate_results.values()
            ),
            "summary": summary,
        })
        _save_work_items(wi_data)

    # Reset status
    status["current_session"] = None
    status["current_work_item"] = None
    status["started_at"] = None
    status["status"] = "idle"
    _save_status(status)

    # Print summary
    print(f"\nSession #{session_num} ended ({completion_status})")
    print(f"Work Item: {item_id}")
    print(f"Duration: {duration_minutes} minutes")
    print(f"Git: {git_diff}")
    print(f"\nQuality Gates:")
    for gate_name, result in gate_results.items():
        icon = "PASS" if result.get("passed") else "FAIL"
        print(f"  [{icon}] {gate_name}: {result.get('message', '')}")
    print(f"\nHistory saved: {history_file}")


def show_status() -> None:
    """Show current session status."""
    status = _load_status()

    if status["status"] != "in_progress":
        print("No active session.")
        wi_data = _load_work_items()
        items = wi_data["work_items"]
        total = len(items)
        completed = sum(1 for i in items.values() if i["status"] == "completed")
        in_progress = sum(1 for i in items.values() if i["status"] == "in_progress")
        print(f"\nWork items: {total} total, {completed} completed, {in_progress} in progress")
        return

    item_id = status["current_work_item"]
    session_num = status["current_session"]
    started_at = status["started_at"]

    # Calculate elapsed time
    start_dt = datetime.fromisoformat(started_at)
    elapsed = datetime.now(timezone.utc) - start_dt
    elapsed_minutes = int(elapsed.total_seconds() / 60)

    print(f"Session #{session_num} — IN PROGRESS")
    print(f"Work Item: {item_id}")
    print(f"Started: {started_at}")
    print(f"Elapsed: {elapsed_minutes} minutes")

    # Show work item details
    wi_data = _load_work_items()
    items = wi_data["work_items"]
    if item_id in items:
        item = items[item_id]
        print(f"Title: {item['title']}")
        print(f"Type: {item['type']} | Priority: {item['priority']}")

    # Git diff stat
    try:
        result = subprocess.run(
            ["git", "diff", "--stat"],
            capture_output=True, text=True, timeout=10
        )
        if result.stdout.strip():
            print(f"\nGit changes:\n{result.stdout.strip()}")
        else:
            print("\nNo uncommitted changes.")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Milestone progress
    total = len(items)
    completed = sum(1 for i in items.values() if i["status"] == "completed")
    print(f"\nOverall: {completed}/{total} work items completed")


def validate(fix: bool = False, scope: str = None) -> None:
    """Run quality gates and report results."""
    print("Running quality gate validation...\n")
    results = run_quality_gates(fix=fix, scope=scope)

    all_passed = True
    for gate_name, result in results.items():
        icon = "PASS" if result.get("passed") else "FAIL"
        if not result.get("passed"):
            all_passed = False
        print(f"  [{icon}] {gate_name}: {result.get('message', '')}")

    # Check spec completeness for current session
    status = _load_status()
    if status["status"] == "in_progress":
        item_id = status["current_work_item"]
        wi_data = _load_work_items()
        item = wi_data["work_items"].get(item_id, {})
        spec_path = Path(item.get("spec_file", ""))
        if spec_path.exists():
            content = spec_path.read_text(encoding="utf-8")
            # Check for unfilled placeholders
            placeholders = re.findall(r"\[.*?\]", content)
            if placeholders:
                print(f"\n  [WARN] Spec has {len(placeholders)} placeholder(s) — fill them in before completing")

    # Git status
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10
        )
        uncommitted = len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0
        if uncommitted:
            print(f"\n  [INFO] {uncommitted} uncommitted file(s)")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    print(f"\n{'All gates passed!' if all_passed else 'Some gates failed — fix before completing.'}")
