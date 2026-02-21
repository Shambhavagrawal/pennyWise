"""Learning capture, search, and curation with Jaccard similarity."""

import json
import time
from datetime import datetime, timezone

from .constants import (
    DEFAULT_JACCARD_THRESHOLD,
    LEARNINGS_PATH,
    VALID_CATEGORIES,
)


def _load() -> dict:
    return json.loads(LEARNINGS_PATH.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    data["metadata"]["total_learnings"] = len(data.get("learnings", []))
    LEARNINGS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def jaccard_similarity(text_a: str, text_b: str) -> float:
    """Word-level Jaccard similarity for duplicate detection."""
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def add(content: str, category: str, tags: list = None, session: int = None, context: str = "") -> str:
    """Add a learning entry."""
    if category not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category '{category}'. Valid: {sorted(VALID_CATEGORIES)}")

    data = _load()
    tags = tags or []

    # Use millisecond timestamp for unique ID
    learning_id = f"learning_{int(time.time() * 1000)}"
    now = datetime.now(timezone.utc).isoformat()

    entry = {
        "id": learning_id,
        "content": content,
        "category": category,
        "tags": tags,
        "session": session,
        "context": context,
        "created_at": now,
    }

    data["learnings"].append(entry)

    # Update category index
    if category in data.get("categories", {}):
        data["categories"][category].append(learning_id)

    _save(data)
    print(f"Added learning: {learning_id}")
    print(f"  Category: {category}")
    print(f"  Content: {content[:80]}{'...' if len(content) > 80 else ''}")
    return learning_id


def show(category: str = None, tag: str = None, session: int = None) -> None:
    """Show learnings with optional filters."""
    data = _load()
    learnings = data.get("learnings", [])

    if not learnings:
        print("No learnings captured yet.")
        return

    filtered = learnings
    if category:
        filtered = [l for l in filtered if l.get("category") == category]
    if tag:
        filtered = [l for l in filtered if tag in l.get("tags", [])]
    if session is not None:
        filtered = [l for l in filtered if l.get("session") == session]

    if not filtered:
        print("No matching learnings found.")
        return

    # Group by category
    by_category = {}
    for learning in filtered:
        cat = learning.get("category", "uncategorized")
        by_category.setdefault(cat, []).append(learning)

    for cat, items in sorted(by_category.items()):
        print(f"\n## {cat} ({len(items)})")
        for item in items:
            tags_str = f" [{', '.join(item.get('tags', []))}]" if item.get("tags") else ""
            session_str = f" (session #{item['session']})" if item.get("session") else ""
            print(f"  - {item['content']}{tags_str}{session_str}")
            print(f"    id: {item['id']} | {item['created_at']}")

    print(f"\nTotal: {len(filtered)} learnings")


def search(query: str) -> None:
    """Case-insensitive search across content, tags, and context."""
    data = _load()
    learnings = data.get("learnings", [])

    if not learnings:
        print("No learnings to search.")
        return

    query_lower = query.lower()
    results = []

    for learning in learnings:
        score = 0
        content = learning.get("content", "").lower()
        tags = [t.lower() for t in learning.get("tags", [])]
        context = learning.get("context", "").lower()

        # Score by match density
        if query_lower in content:
            score += content.count(query_lower) * 3
        for tag in tags:
            if query_lower in tag:
                score += 5
        if query_lower in context:
            score += context.count(query_lower) * 2

        if score > 0:
            results.append((score, learning))

    if not results:
        print(f"No learnings matching '{query}'.")
        return

    results.sort(key=lambda x: -x[0])
    print(f"Search results for '{query}' ({len(results)} matches):\n")
    for score, learning in results:
        tags_str = f" [{', '.join(learning.get('tags', []))}]" if learning.get("tags") else ""
        print(f"  [{learning.get('category', 'unknown')}] {learning['content']}{tags_str}")
        print(f"    id: {learning['id']} | relevance: {score}")


def curate(dry_run: bool = False, threshold: float = DEFAULT_JACCARD_THRESHOLD) -> None:
    """Find and merge duplicate learnings using Jaccard similarity."""
    data = _load()
    learnings = data.get("learnings", [])

    if len(learnings) < 2:
        print("Not enough learnings to curate (need at least 2).")
        return

    # Find similar pairs
    merge_groups = []
    merged_ids = set()

    for i in range(len(learnings)):
        if learnings[i]["id"] in merged_ids:
            continue
        group = [i]
        for j in range(i + 1, len(learnings)):
            if learnings[j]["id"] in merged_ids:
                continue
            sim = jaccard_similarity(learnings[i]["content"], learnings[j]["content"])
            if sim >= threshold:
                group.append(j)
                merged_ids.add(learnings[j]["id"])
        if len(group) > 1:
            merged_ids.add(learnings[i]["id"])
            merge_groups.append(group)

    if not merge_groups:
        print(f"No duplicates found (threshold: {threshold}).")
        return

    print(f"Found {len(merge_groups)} group(s) of similar learnings:\n")
    for group_idx, group in enumerate(merge_groups, 1):
        print(f"  Group {group_idx}:")
        for idx in group:
            print(f"    - {learnings[idx]['content'][:80]}...")
            print(f"      id: {learnings[idx]['id']}")

    if dry_run:
        print("\nDry run — no changes made.")
        return

    # Merge: keep longest content, combine tags
    new_learnings = []
    merged_indices = set()
    for group in merge_groups:
        for idx in group:
            merged_indices.add(idx)

        # Pick the longest content
        best = max(group, key=lambda idx: len(learnings[idx]["content"]))
        merged = dict(learnings[best])

        # Combine tags from all entries
        all_tags = set()
        for idx in group:
            all_tags.update(learnings[idx].get("tags", []))
        merged["tags"] = sorted(all_tags)

        new_learnings.append(merged)

    # Add non-merged learnings
    for i, learning in enumerate(learnings):
        if i not in merged_indices:
            new_learnings.append(learning)

    data["learnings"] = new_learnings
    data["metadata"]["last_curated"] = datetime.now(timezone.utc).isoformat()

    # Rebuild category index
    for cat in data.get("categories", {}):
        data["categories"][cat] = []
    for learning in new_learnings:
        cat = learning.get("category", "")
        if cat in data.get("categories", {}):
            data["categories"][cat].append(learning["id"])

    _save(data)
    removed = len(learnings) - len(new_learnings)
    print(f"\nMerged {removed} duplicate(s). {len(new_learnings)} learnings remaining.")
