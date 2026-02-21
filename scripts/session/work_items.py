"""Work item CRUD operations, dependency validation, and graph visualization."""

import json
import re
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .constants import (
    MAX_ID_LENGTH,
    PRIORITY_ORDER,
    SPECS_DIR,
    TEMPLATES_DIR,
    TEMPLATE_MAP,
    VALID_PRIORITIES,
    VALID_STATUSES,
    VALID_TYPES,
    WORK_ITEMS_PATH,
)


def _load() -> dict:
    """Load work_items.json."""
    return json.loads(WORK_ITEMS_PATH.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    """Save work_items.json and update metadata counts."""
    items = data.get("work_items", {})
    data["metadata"]["total_items"] = len(items)
    data["metadata"]["completed"] = sum(
        1 for i in items.values() if i["status"] == "completed"
    )
    data["metadata"]["in_progress"] = sum(
        1 for i in items.values() if i["status"] == "in_progress"
    )
    data["metadata"]["blocked"] = sum(
        1 for i in items.values() if i["status"] == "blocked"
    )
    data["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
    WORK_ITEMS_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def generate_id(work_type: str, title: str, existing_ids: set) -> str:
    """Generate unique work item ID: {type}_{snake_title}[:40], with collision suffix."""
    cleaned = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    base_id = f"{work_type}_{cleaned}"[:MAX_ID_LENGTH]
    candidate = base_id
    counter = 2
    while candidate in existing_ids:
        suffix = f"_{counter}"
        candidate = base_id[: MAX_ID_LENGTH - len(suffix)] + suffix
        counter += 1
    return candidate


def create(
    work_type: str, title: str, priority: str, dependencies=None, urgent=False
) -> str:
    """Add work item to work_items.json, copy spec template, update metadata."""
    if work_type not in VALID_TYPES:
        raise ValueError(f"Invalid type '{work_type}'. Valid: {sorted(VALID_TYPES)}")
    if priority not in VALID_PRIORITIES:
        raise ValueError(
            f"Invalid priority '{priority}'. Valid: {sorted(VALID_PRIORITIES)}"
        )

    data = _load()
    items = data["work_items"]
    dependencies = dependencies or []

    # Validate dependencies exist
    for dep in dependencies:
        if dep not in items:
            raise ValueError(f"Dependency '{dep}' does not exist.")

    # Check urgent constraint: only one urgent item at a time
    if urgent:
        for item in items.values():
            if item.get("urgent", False) and item["status"] != "completed":
                raise ValueError(
                    f"Already have an urgent item: {item['id']}. Complete it first."
                )

    item_id = generate_id(work_type, title, set(items.keys()))
    now = datetime.now(timezone.utc).isoformat()

    items[item_id] = {
        "id": item_id,
        "type": work_type,
        "title": title,
        "status": "not_started",
        "priority": priority,
        "urgent": urgent,
        "dependencies": dependencies,
        "milestone": "",
        "spec_file": str(SPECS_DIR / f"{item_id}.md"),
        "created_at": now,
        "sessions": [],
    }

    # Copy spec template
    template_file = TEMPLATES_DIR / TEMPLATE_MAP.get(work_type, "feature_spec.md")
    spec_file = SPECS_DIR / f"{item_id}.md"
    SPECS_DIR.mkdir(parents=True, exist_ok=True)
    if template_file.exists():
        shutil.copy2(template_file, spec_file)
    else:
        spec_file.write_text(
            f"# {title}\n\n## Overview\n\n## Acceptance Criteria\n\n## Technical Approach\n\n## Testing Requirements\n",
            encoding="utf-8",
        )

    _save(data)
    print(f"Created work item: {item_id}")
    print(f"  Type: {work_type} | Priority: {priority} | Urgent: {urgent}")
    print(f"  Spec: {spec_file}")
    return item_id


def list_items(status=None, work_type=None, milestone=None) -> None:
    """List work items with optional filters."""
    data = _load()
    items = data["work_items"]

    if not items:
        print("No work items found.")
        return

    filtered = items.values()
    if status:
        filtered = [i for i in filtered if i["status"] == status]
    if work_type:
        filtered = [i for i in filtered if i["type"] == work_type]
    if milestone:
        filtered = [i for i in filtered if i.get("milestone") == milestone]

    filtered = list(filtered)
    if not filtered:
        print("No matching work items found.")
        return

    # Sort by priority then by creation date
    filtered.sort(
        key=lambda i: (PRIORITY_ORDER.get(i["priority"], 99), i["created_at"])
    )

    print(f"{'ID':<40} {'Type':<12} {'Priority':<10} {'Status':<14} {'Title'}")
    print("-" * 110)
    for item in filtered:
        urgent_marker = " !" if item.get("urgent") else ""
        print(
            f"{item['id']:<40} {item['type']:<12} {item['priority']:<10} {item['status']:<14} {item['title']}{urgent_marker}"
        )

    print(f"\nTotal: {len(filtered)} items")


def show(item_id: str) -> None:
    """Show detailed info for a work item."""
    data = _load()
    items = data["work_items"]

    if item_id not in items:
        print(f"Work item '{item_id}' not found.")
        return

    item = items[item_id]
    print(f"ID:           {item['id']}")
    print(f"Title:        {item['title']}")
    print(f"Type:         {item['type']}")
    print(f"Status:       {item['status']}")
    print(f"Priority:     {item['priority']}")
    print(f"Urgent:       {item.get('urgent', False)}")
    print(f"Milestone:    {item.get('milestone', '')}")
    print(
        f"Dependencies: {', '.join(item['dependencies']) if item['dependencies'] else 'None'}"
    )
    print(f"Created:      {item['created_at']}")
    print(f"Spec:         {item['spec_file']}")

    # Show dependency status
    if item["dependencies"]:
        print("\nDependency Status:")
        for dep in item["dependencies"]:
            dep_item = items.get(dep)
            if dep_item:
                status_icon = "+" if dep_item["status"] == "completed" else "-"
                print(f"  [{status_icon}] {dep} ({dep_item['status']})")
            else:
                print(f"  [?] {dep} (missing)")

    # Show sessions
    if item["sessions"]:
        print(f"\nSessions ({len(item['sessions'])}):")
        for s in item["sessions"]:
            print(
                f"  #{s['session_number']}: {s['status']} ({s.get('started_at', 'N/A')})"
            )

    # Show spec preview
    spec_path = Path(item["spec_file"])
    if spec_path.exists():
        lines = spec_path.read_text(encoding="utf-8").splitlines()[:30]
        print(f"\nSpec Preview ({spec_path}):")
        for line in lines:
            print(f"  {line}")
        if len(spec_path.read_text(encoding="utf-8").splitlines()) > 30:
            print("  ... (truncated)")


def update(item_id: str, **fields) -> None:
    """Update work item fields with constraint validation."""
    data = _load()
    items = data["work_items"]

    if item_id not in items:
        print(f"Work item '{item_id}' not found.")
        return

    item = items[item_id]
    changes = []

    if "status" in fields and fields["status"] is not None:
        new_status = fields["status"]
        if new_status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{new_status}'. Valid: {sorted(VALID_STATUSES)}"
            )
        old = item["status"]
        item["status"] = new_status
        changes.append(f"status: {old} -> {new_status}")

    if "priority" in fields and fields["priority"] is not None:
        new_priority = fields["priority"]
        if new_priority not in VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{new_priority}'. Valid: {sorted(VALID_PRIORITIES)}"
            )
        old = item["priority"]
        item["priority"] = new_priority
        changes.append(f"priority: {old} -> {new_priority}")

    if "milestone" in fields and fields["milestone"] is not None:
        old = item.get("milestone", "")
        item["milestone"] = fields["milestone"]
        changes.append(f"milestone: '{old}' -> '{fields['milestone']}'")

    if "add_dependency" in fields and fields["add_dependency"] is not None:
        dep = fields["add_dependency"]
        if dep not in items:
            raise ValueError(f"Dependency '{dep}' does not exist.")
        if dep == item_id:
            raise ValueError("Cannot depend on itself.")
        if dep not in item["dependencies"]:
            item["dependencies"].append(dep)
            changes.append(f"added dependency: {dep}")

    if "remove_dependency" in fields and fields["remove_dependency"] is not None:
        dep = fields["remove_dependency"]
        if dep in item["dependencies"]:
            item["dependencies"].remove(dep)
            changes.append(f"removed dependency: {dep}")

    if "set_urgent" in fields and fields["set_urgent"]:
        # Check constraint: only one urgent at a time
        for other in items.values():
            if (
                other["id"] != item_id
                and other.get("urgent", False)
                and other["status"] != "completed"
            ):
                raise ValueError(
                    f"Already have an urgent item: {other['id']}. Complete it first."
                )
        item["urgent"] = True
        changes.append("set urgent: True")

    if "clear_urgent" in fields and fields["clear_urgent"]:
        item["urgent"] = False
        changes.append("cleared urgent")

    if changes:
        _save(data)
        print(f"Updated {item_id}:")
        for c in changes:
            print(f"  {c}")
    else:
        print("No changes specified.")


def delete(item_id: str, with_spec: bool = False) -> None:
    """Delete a work item. Check for dependents first."""
    data = _load()
    items = data["work_items"]

    if item_id not in items:
        print(f"Work item '{item_id}' not found.")
        return

    # Check if any other items depend on this one
    dependents = [
        iid for iid, i in items.items() if item_id in i.get("dependencies", [])
    ]
    if dependents:
        print(
            f"Cannot delete '{item_id}' — other items depend on it: {', '.join(dependents)}"
        )
        print("Remove the dependency first, or delete the dependent items.")
        return

    item = items.pop(item_id)
    _save(data)
    print(f"Deleted work item: {item_id}")

    if with_spec:
        spec_path = Path(item["spec_file"])
        if spec_path.exists():
            spec_path.unlink()
            print(f"Deleted spec file: {spec_path}")


def next_items(limit: int = 5) -> None:
    """Show next recommended work items (not_started, dependencies met, sorted by priority)."""
    data = _load()
    items = data["work_items"]

    candidates = []
    for item in items.values():
        if item["status"] != "not_started":
            continue
        # Check all dependencies are completed
        deps_met = all(
            items.get(dep, {}).get("status") == "completed"
            for dep in item.get("dependencies", [])
        )
        if deps_met:
            candidates.append(item)

    if not candidates:
        print(
            "No available work items. All items are either in progress, blocked, completed, or have unmet dependencies."
        )
        return

    # Sort: urgent first, then by priority
    candidates.sort(
        key=lambda i: (
            0 if i.get("urgent") else 1,
            PRIORITY_ORDER.get(i["priority"], 99),
            i["created_at"],
        )
    )

    candidates = candidates[:limit]
    print(f"Next {len(candidates)} recommended work items:\n")
    for i, item in enumerate(candidates, 1):
        urgent = " [URGENT]" if item.get("urgent") else ""
        print(f"  {i}. {item['id']}{urgent}")
        print(f"     {item['title']} ({item['priority']})")
        if item["dependencies"]:
            print(f"     deps: {', '.join(item['dependencies'])}")
        print()


def render_graph(
    critical_path: bool = False, bottlenecks: bool = False, stats: bool = False
) -> None:
    """ASCII dependency graph with optional analysis."""
    data = _load()
    items = data["work_items"]

    if not items:
        print("No work items to graph.")
        return

    # 1. Build adjacency list: {id: [dependency_ids]}
    adj = {iid: item.get("dependencies", []) for iid, item in items.items()}

    # 2. Build reverse adjacency list (node -> list of dependents)
    reverse_adj = defaultdict(list)
    for node, deps in adj.items():
        for dep in deps:
            reverse_adj[dep].append(node)

    # 3. Topological sort (Kahn's algorithm — detects cycles)
    in_degree = {node: len(deps) for node, deps in adj.items()}
    queue = [n for n, d in in_degree.items() if d == 0]
    sorted_order = []
    while queue:
        queue.sort()  # deterministic order
        node = queue.pop(0)
        sorted_order.append(node)
        for dependent in reverse_adj[node]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(sorted_order) != len(adj):
        print("ERROR: Circular dependency detected")
        return

    # 4. ASCII rendering — print each node with indentation based on depth
    depth = {}
    for node in sorted_order:
        deps = adj[node]
        depth[node] = max((depth[d] for d in deps), default=-1) + 1

    status_icons = {
        "completed": "+",
        "in_progress": ">",
        "blocked": "x",
        "not_started": "o",
    }

    print("Work Item Dependency Graph:")
    print()
    for node in sorted_order:
        indent = "  " * depth[node]
        icon = status_icons.get(items[node]["status"], "o")
        urgent = " [URGENT]" if items[node].get("urgent") else ""
        print(f"{indent}[{icon}] {node}{urgent}")
        for dep in adj[node]:
            print(f"{indent}    <- {dep}")

    # 5. Critical path (longest path in DAG)
    if critical_path:
        dist = {n: 0 for n in sorted_order}
        parent = {n: None for n in sorted_order}
        for node in sorted_order:
            for dep in adj[node]:
                if dist[dep] + 1 > dist[node]:
                    dist[node] = dist[dep] + 1
                    parent[node] = dep
        # Backtrack from max
        end_node = max(dist, key=dist.get)
        path = []
        current = end_node
        while current is not None:
            path.append(current)
            current = parent[current]
        path.reverse()
        print(f"\nCritical path ({len(path)} items): {' -> '.join(path)}")

    # 6. Bottlenecks (nodes with most dependents)
    if bottlenecks:
        dependent_count = {n: 0 for n in adj}
        for node, deps in adj.items():
            for dep in deps:
                if dep in dependent_count:
                    dependent_count[dep] += 1
        top = sorted(dependent_count.items(), key=lambda x: -x[1])[:5]
        top_with_deps = [(n, c) for n, c in top if c > 0]
        if top_with_deps:
            print(
                f"\nBottlenecks: {', '.join(f'{n} ({c} dependents)' for n, c in top_with_deps)}"
            )
        else:
            print("\nNo bottlenecks (no dependencies between items).")

    # 7. Stats
    if stats:
        total = len(items)
        by_status = defaultdict(int)
        for item in items.values():
            by_status[item["status"]] += 1
        print(
            f"\nStats: {total} items — "
            + ", ".join(f"{s}: {c}" for s, c in sorted(by_status.items()))
        )
