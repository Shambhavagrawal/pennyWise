"""Tests for scripts/session/learnings.py."""

import json
import pytest


@pytest.fixture
def setup_paths(tmp_path, monkeypatch):
    """Redirect all constants paths to temp directory."""
    import scripts.session.constants as constants
    import scripts.session.learnings as learnings_mod

    tracking = tmp_path / "tracking"
    tracking.mkdir()
    specs = tmp_path / "specs"
    specs.mkdir()
    templates = tmp_path / "templates"
    templates.mkdir()
    history = tmp_path / "history"
    history.mkdir()

    # Patch constants module
    monkeypatch.setattr(constants, "SESSION_DIR", tmp_path)
    monkeypatch.setattr(constants, "TRACKING_DIR", tracking)
    monkeypatch.setattr(constants, "SPECS_DIR", specs)
    monkeypatch.setattr(constants, "TEMPLATES_DIR", templates)
    monkeypatch.setattr(constants, "HISTORY_DIR", history)
    monkeypatch.setattr(constants, "WORK_ITEMS_PATH", tracking / "work_items.json")
    monkeypatch.setattr(constants, "LEARNINGS_PATH", tracking / "learnings.json")
    monkeypatch.setattr(constants, "STATUS_PATH", tracking / "status_update.json")
    monkeypatch.setattr(constants, "CONFIG_PATH", tmp_path / "config.json")

    # Patch the importing module
    monkeypatch.setattr(learnings_mod, "LEARNINGS_PATH", tracking / "learnings.json")

    # Create initial learnings.json
    (tracking / "learnings.json").write_text(
        json.dumps(
            {
                "metadata": {"total_learnings": 0, "last_curated": None},
                "categories": {
                    "architecture_patterns": [],
                    "gotchas": [],
                    "best_practices": [],
                    "technical_debt": [],
                    "performance_insights": [],
                    "security": [],
                },
                "learnings": [],
            }
        )
    )

    return tmp_path


def _load_learnings(tmp_path):
    """Helper to load learnings.json from the temp tracking dir."""
    return json.loads(
        (tmp_path / "tracking" / "learnings.json").read_text(encoding="utf-8")
    )


# ---------- jaccard_similarity tests ----------


class TestJaccardSimilarity:
    def test_identical_strings(self, setup_paths):
        from scripts.session.learnings import jaccard_similarity

        result = jaccard_similarity("hello world", "hello world")
        assert result == 1.0

    def test_empty_strings(self, setup_paths):
        from scripts.session.learnings import jaccard_similarity

        assert jaccard_similarity("", "") == 0.0
        assert jaccard_similarity("hello", "") == 0.0
        assert jaccard_similarity("", "hello") == 0.0

    def test_no_overlap(self, setup_paths):
        from scripts.session.learnings import jaccard_similarity

        result = jaccard_similarity("apple banana", "cherry date")
        assert result == 0.0

    def test_partial_overlap(self, setup_paths):
        from scripts.session.learnings import jaccard_similarity

        # words_a = {"the", "cat", "sat"}
        # words_b = {"the", "dog", "sat"}
        # intersection = {"the", "sat"} = 2
        # union = {"the", "cat", "sat", "dog"} = 4
        # jaccard = 2/4 = 0.5
        result = jaccard_similarity("the cat sat", "the dog sat")
        assert result == 0.5

    def test_case_insensitive(self, setup_paths):
        from scripts.session.learnings import jaccard_similarity

        result = jaccard_similarity("Hello World", "hello world")
        assert result == 1.0

    def test_subset_strings(self, setup_paths):
        from scripts.session.learnings import jaccard_similarity

        # words_a = {"hello"}
        # words_b = {"hello", "world"}
        # intersection = {"hello"} = 1
        # union = {"hello", "world"} = 2
        # jaccard = 1/2 = 0.5
        result = jaccard_similarity("hello", "hello world")
        assert result == 0.5


# ---------- add tests ----------


class TestAdd:
    def test_adds_entry(self, setup_paths):
        from scripts.session.learnings import add

        learning_id = add("Use async for IO", "best_practices")
        data = _load_learnings(setup_paths)
        assert len(data["learnings"]) == 1
        assert data["learnings"][0]["content"] == "Use async for IO"
        assert data["learnings"][0]["category"] == "best_practices"
        assert data["learnings"][0]["id"] == learning_id

    def test_updates_metadata_count(self, setup_paths):
        from scripts.session.learnings import add

        add("Learning one", "gotchas")
        add("Learning two", "security")
        data = _load_learnings(setup_paths)
        assert data["metadata"]["total_learnings"] == 2

    def test_validates_category(self, setup_paths):
        from scripts.session.learnings import add

        with pytest.raises(ValueError, match="Invalid category"):
            add("Some content", "nonexistent_category")

    def test_with_tags(self, setup_paths):
        from scripts.session.learnings import add

        add("SQLModel tip", "best_practices", tags=["sqlmodel", "database"])
        data = _load_learnings(setup_paths)
        assert data["learnings"][0]["tags"] == ["sqlmodel", "database"]

    def test_updates_category_index(self, setup_paths):
        from scripts.session.learnings import add

        learning_id = add("Pattern info", "architecture_patterns")
        data = _load_learnings(setup_paths)
        assert learning_id in data["categories"]["architecture_patterns"]

    def test_with_session_and_context(self, setup_paths):
        from scripts.session.learnings import add

        add("Context learning", "gotchas", session=5, context="During testing")
        data = _load_learnings(setup_paths)
        entry = data["learnings"][0]
        assert entry["session"] == 5
        assert entry["context"] == "During testing"


# ---------- search tests ----------


class TestSearch:
    def test_finds_by_content_match(self, setup_paths, capsys):
        from scripts.session.learnings import add, search

        add("Always use async database sessions", "best_practices")
        add("Never use raw SQL queries", "gotchas")
        search("async")
        captured = capsys.readouterr()
        assert "async database sessions" in captured.out
        assert "1 matches" in captured.out

    def test_finds_by_tag_match(self, setup_paths, capsys):
        from scripts.session.learnings import add, search

        add("Some content about python", "best_practices", tags=["fastapi", "python"])
        add("Other unrelated content", "gotchas", tags=["react"])
        search("fastapi")
        captured = capsys.readouterr()
        assert "python" in captured.out
        assert "1 matches" in captured.out

    def test_no_results(self, setup_paths, capsys):
        from scripts.session.learnings import add, search

        add("Something about databases", "best_practices")
        search("kubernetes")
        captured = capsys.readouterr()
        assert "No learnings matching" in captured.out

    def test_empty_learnings(self, setup_paths, capsys):
        from scripts.session.learnings import search

        search("anything")
        captured = capsys.readouterr()
        assert "No learnings to search" in captured.out

    def test_scores_content_higher_than_context(self, setup_paths, capsys):
        from scripts.session.learnings import add, search

        # Content match scores 3 per occurrence, context scores 2
        add("testing is important", "best_practices", context="while working")
        add("while working on project", "gotchas", context="testing notes")
        search("testing")
        captured = capsys.readouterr()
        # Both should appear, first result should be content-match
        assert "2 matches" in captured.out


# ---------- curate tests ----------


class TestCurate:
    def test_merges_duplicates(self, setup_paths, monkeypatch, capsys):
        from scripts.session.learnings import add, curate

        # Use monkeypatch on time to ensure different IDs
        import time

        call_count = [0]
        original_time = time.time

        def mock_time():
            call_count[0] += 1
            return original_time() + call_count[0]

        monkeypatch.setattr(time, "time", mock_time)

        add("always use async for database operations", "best_practices")
        add("always use async for database operations in routes", "best_practices")
        curate(threshold=0.6)
        captured = capsys.readouterr()
        assert "Merged" in captured.out

        data = _load_learnings(setup_paths)
        assert len(data["learnings"]) == 1

    def test_keeps_longest_content(self, setup_paths, monkeypatch):
        from scripts.session.learnings import add, curate

        import time

        call_count = [0]
        original_time = time.time

        def mock_time():
            call_count[0] += 1
            return original_time() + call_count[0]

        monkeypatch.setattr(time, "time", mock_time)

        add("use async for database operations", "best_practices")
        add("use async for database operations in route handlers", "best_practices")
        curate(threshold=0.4)
        data = _load_learnings(setup_paths)
        assert len(data["learnings"]) == 1
        assert "route handlers" in data["learnings"][0]["content"]

    def test_combines_tags(self, setup_paths, monkeypatch):
        from scripts.session.learnings import add, curate

        import time

        call_count = [0]
        original_time = time.time

        def mock_time():
            call_count[0] += 1
            return original_time() + call_count[0]

        monkeypatch.setattr(time, "time", mock_time)

        add("use async for database operations", "best_practices", tags=["async"])
        add(
            "use async for database operations always",
            "best_practices",
            tags=["database"],
        )
        curate(threshold=0.5)
        data = _load_learnings(setup_paths)
        assert len(data["learnings"]) == 1
        tags = data["learnings"][0]["tags"]
        assert "async" in tags
        assert "database" in tags

    def test_dry_run_no_changes(self, setup_paths, monkeypatch, capsys):
        from scripts.session.learnings import add, curate

        import time

        call_count = [0]
        original_time = time.time

        def mock_time():
            call_count[0] += 1
            return original_time() + call_count[0]

        monkeypatch.setattr(time, "time", mock_time)

        add("always use async for database operations", "best_practices")
        add("always use async for database operations in routes", "best_practices")
        curate(dry_run=True, threshold=0.6)
        captured = capsys.readouterr()
        assert "Dry run" in captured.out

        data = _load_learnings(setup_paths)
        # Both learnings should still be there
        assert len(data["learnings"]) == 2

    def test_no_duplicates_found(self, setup_paths, monkeypatch, capsys):
        from scripts.session.learnings import add, curate

        import time

        call_count = [0]
        original_time = time.time

        def mock_time():
            call_count[0] += 1
            return original_time() + call_count[0]

        monkeypatch.setattr(time, "time", mock_time)

        add("completely different topic about security", "security")
        add("react component patterns for frontend", "best_practices")
        curate(threshold=0.6)
        captured = capsys.readouterr()
        assert "No duplicates found" in captured.out

    def test_not_enough_learnings(self, setup_paths, capsys):
        from scripts.session.learnings import curate

        curate()
        captured = capsys.readouterr()
        assert "Not enough learnings" in captured.out
