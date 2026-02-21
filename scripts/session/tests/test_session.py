"""Tests for scripts/session/session.py."""

import json
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def setup_paths(tmp_path, monkeypatch):
    """Redirect all constants paths to temp directory."""
    import scripts.session.constants as constants
    import scripts.session.work_items as work_items_mod
    import scripts.session.learnings as learnings_mod
    import scripts.session.session as session_mod
    import scripts.session.quality as quality_mod

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

    # Patch session module (imports from constants)
    monkeypatch.setattr(session_mod, "WORK_ITEMS_PATH", tracking / "work_items.json")
    monkeypatch.setattr(session_mod, "LEARNINGS_PATH", tracking / "learnings.json")
    monkeypatch.setattr(session_mod, "STATUS_PATH", tracking / "status_update.json")
    monkeypatch.setattr(session_mod, "HISTORY_DIR", history)

    # Patch work_items module (used by create helper)
    monkeypatch.setattr(work_items_mod, "WORK_ITEMS_PATH", tracking / "work_items.json")
    monkeypatch.setattr(work_items_mod, "SPECS_DIR", specs)
    monkeypatch.setattr(work_items_mod, "TEMPLATES_DIR", templates)

    # Patch learnings module
    monkeypatch.setattr(learnings_mod, "LEARNINGS_PATH", tracking / "learnings.json")

    # Patch quality module
    monkeypatch.setattr(quality_mod, "CONFIG_PATH", tmp_path / "config.json")

    # Create initial files
    (tracking / "work_items.json").write_text(
        json.dumps(
            {
                "metadata": {
                    "total_items": 0,
                    "completed": 0,
                    "in_progress": 0,
                    "blocked": 0,
                    "last_updated": None,
                },
                "milestones": {},
                "work_items": {},
            }
        )
    )
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
    (tracking / "status_update.json").write_text(
        json.dumps(
            {
                "current_session": None,
                "current_work_item": None,
                "started_at": None,
                "status": "idle",
            }
        )
    )

    # Create spec templates
    (templates / "feature_spec.md").write_text(
        "# Feature Spec Template\n\n## Overview\n"
    )
    (templates / "bug_spec.md").write_text("# Bug Spec Template\n\n## Overview\n")

    return tmp_path


def _load_status(tmp_path):
    return json.loads(
        (tmp_path / "tracking" / "status_update.json").read_text(encoding="utf-8")
    )


def _load_work_items(tmp_path):
    return json.loads(
        (tmp_path / "tracking" / "work_items.json").read_text(encoding="utf-8")
    )


def _create_work_item(
    title="Test Feature", priority="high", work_type="feature", **kwargs
):
    """Helper to create a work item via the work_items module."""
    from scripts.session.work_items import create

    return create(work_type, title, priority, **kwargs)


# ---------- _next_session_number tests ----------


class TestNextSessionNumber:
    def test_returns_1_when_empty(self, setup_paths):
        from scripts.session.session import _next_session_number

        assert _next_session_number() == 1

    def test_increments_correctly(self, setup_paths):
        from scripts.session.session import _next_session_number

        history = setup_paths / "history"
        (history / "session_1.json").write_text("{}")
        (history / "session_2.json").write_text("{}")
        assert _next_session_number() == 3

    def test_handles_gaps(self, setup_paths):
        from scripts.session.session import _next_session_number

        history = setup_paths / "history"
        (history / "session_1.json").write_text("{}")
        (history / "session_5.json").write_text("{}")
        # Should return max + 1, not fill gaps
        assert _next_session_number() == 6

    def test_ignores_non_matching_files(self, setup_paths):
        from scripts.session.session import _next_session_number

        history = setup_paths / "history"
        (history / "session_3.json").write_text("{}")
        (history / "notes.json").write_text("{}")
        (history / "readme.md").write_text("notes")
        assert _next_session_number() == 4

    def test_creates_history_dir_if_missing(self, setup_paths):
        from scripts.session.session import _next_session_number
        import shutil

        history = setup_paths / "history"
        shutil.rmtree(history)
        assert not history.exists()
        result = _next_session_number()
        assert result == 1
        assert history.exists()


# ---------- start tests ----------


class TestStart:
    def test_sets_status_to_in_progress(self, setup_paths):
        from scripts.session.session import start

        item_id = _create_work_item("Login Feature")
        start(item_id)
        status = _load_status(setup_paths)
        assert status["status"] == "in_progress"
        assert status["current_work_item"] == item_id
        assert status["current_session"] == 1
        assert status["started_at"] is not None

    def test_sets_work_item_in_progress(self, setup_paths):
        from scripts.session.session import start

        item_id = _create_work_item("Login Feature")
        start(item_id)
        data = _load_work_items(setup_paths)
        assert data["work_items"][item_id]["status"] == "in_progress"

    def test_blocks_if_session_active(self, setup_paths, capsys):
        from scripts.session.session import start

        item_a = _create_work_item("Feature A")
        item_b = _create_work_item("Feature B")
        start(item_a)
        capsys.readouterr()  # Clear output from first start

        start(item_b)
        captured = capsys.readouterr()
        assert "Session already in progress" in captured.out

    def test_blocks_if_unmet_deps(self, setup_paths, capsys):
        from scripts.session.session import start

        dep_id = _create_work_item("Dependency")
        item_id = _create_work_item("Dependent Feature", dependencies=[dep_id])
        start(item_id)
        captured = capsys.readouterr()
        assert "unmet dependencies" in captured.out

    def test_allows_start_when_deps_met(self, setup_paths):
        from scripts.session.session import start
        from scripts.session.work_items import update

        dep_id = _create_work_item("Dependency")
        item_id = _create_work_item("Dependent Feature", dependencies=[dep_id])
        update(dep_id, status="completed")
        start(item_id)
        status = _load_status(setup_paths)
        assert status["status"] == "in_progress"
        assert status["current_work_item"] == item_id

    def test_nonexistent_item(self, setup_paths, capsys):
        from scripts.session.session import start

        start("nonexistent_item_id")
        captured = capsys.readouterr()
        assert "not found" in captured.out


# ---------- end tests ----------


class TestEnd:
    def test_writes_history_file(self, setup_paths, monkeypatch):
        from scripts.session.session import start, end

        # Mock run_quality_gates and subprocess
        monkeypatch.setattr(
            "scripts.session.session.run_quality_gates",
            lambda **kwargs: {"Test": {"passed": True, "message": "ok"}},
        )
        monkeypatch.setattr(
            "scripts.session.session.subprocess.run",
            lambda *args, **kwargs: MagicMock(stdout="1 file changed", returncode=0),
        )

        item_id = _create_work_item("Ending Feature")
        start(item_id)
        end(completion_status="completed", summary="Done with it")

        history_file = setup_paths / "history" / "session_1.json"
        assert history_file.exists()
        record = json.loads(history_file.read_text(encoding="utf-8"))
        assert record["session_number"] == 1
        assert record["work_item_id"] == item_id
        assert record["status"] == "completed"
        assert record["summary"] == "Done with it"

    def test_resets_status(self, setup_paths, monkeypatch):
        from scripts.session.session import start, end

        monkeypatch.setattr(
            "scripts.session.session.run_quality_gates",
            lambda **kwargs: {"Test": {"passed": True, "message": "ok"}},
        )
        monkeypatch.setattr(
            "scripts.session.session.subprocess.run",
            lambda *args, **kwargs: MagicMock(stdout="", returncode=0),
        )

        item_id = _create_work_item("Reset Feature")
        start(item_id)
        end()

        status = _load_status(setup_paths)
        assert status["status"] == "idle"
        assert status["current_session"] is None
        assert status["current_work_item"] is None
        assert status["started_at"] is None

    def test_updates_work_item_completed(self, setup_paths, monkeypatch):
        from scripts.session.session import start, end

        monkeypatch.setattr(
            "scripts.session.session.run_quality_gates",
            lambda **kwargs: {"Test": {"passed": True, "message": "ok"}},
        )
        monkeypatch.setattr(
            "scripts.session.session.subprocess.run",
            lambda *args, **kwargs: MagicMock(stdout="", returncode=0),
        )

        item_id = _create_work_item("Complete Feature")
        start(item_id)
        end(completion_status="completed")

        data = _load_work_items(setup_paths)
        assert data["work_items"][item_id]["status"] == "completed"
        assert len(data["work_items"][item_id]["sessions"]) == 1
        assert data["work_items"][item_id]["sessions"][0]["status"] == "completed"

    def test_updates_work_item_incomplete(self, setup_paths, monkeypatch):
        from scripts.session.session import start, end

        monkeypatch.setattr(
            "scripts.session.session.run_quality_gates",
            lambda **kwargs: {"Test": {"passed": True, "message": "ok"}},
        )
        monkeypatch.setattr(
            "scripts.session.session.subprocess.run",
            lambda *args, **kwargs: MagicMock(stdout="", returncode=0),
        )

        item_id = _create_work_item("Incomplete Feature")
        start(item_id)
        end(completion_status="incomplete")

        data = _load_work_items(setup_paths)
        # incomplete resets to not_started
        assert data["work_items"][item_id]["status"] == "not_started"

    def test_no_active_session(self, setup_paths, capsys):
        from scripts.session.session import end

        end()
        captured = capsys.readouterr()
        assert "No active session" in captured.out


# ---------- show_status tests ----------


class TestShowStatus:
    def test_shows_idle_when_no_session(self, setup_paths, capsys, monkeypatch):
        from scripts.session.session import show_status

        # Mock subprocess for git calls
        monkeypatch.setattr(
            "scripts.session.session.subprocess.run",
            lambda *args, **kwargs: MagicMock(stdout="", returncode=0),
        )

        show_status()
        captured = capsys.readouterr()
        assert "No active session" in captured.out

    def test_shows_details_when_active(self, setup_paths, capsys, monkeypatch):
        from scripts.session.session import start, show_status

        # Mock subprocess for git calls
        monkeypatch.setattr(
            "scripts.session.session.subprocess.run",
            lambda *args, **kwargs: MagicMock(stdout="", returncode=0),
        )

        item_id = _create_work_item("Active Feature")
        start(item_id)
        capsys.readouterr()  # Clear start output

        show_status()
        captured = capsys.readouterr()
        assert "IN PROGRESS" in captured.out
        assert item_id in captured.out
        assert "Session #1" in captured.out

    def test_shows_work_item_counts_when_idle(self, setup_paths, capsys, monkeypatch):
        from scripts.session.session import show_status

        monkeypatch.setattr(
            "scripts.session.session.subprocess.run",
            lambda *args, **kwargs: MagicMock(stdout="", returncode=0),
        )

        _create_work_item("Feature A")
        _create_work_item("Feature B")
        show_status()
        captured = capsys.readouterr()
        assert "2 total" in captured.out
        assert "0 completed" in captured.out

    def test_shows_elapsed_time(self, setup_paths, capsys, monkeypatch):
        from scripts.session.session import start, show_status

        monkeypatch.setattr(
            "scripts.session.session.subprocess.run",
            lambda *args, **kwargs: MagicMock(stdout="", returncode=0),
        )

        item_id = _create_work_item("Timed Feature")
        start(item_id)
        capsys.readouterr()

        show_status()
        captured = capsys.readouterr()
        assert "Elapsed:" in captured.out

    def test_shows_overall_progress(self, setup_paths, capsys, monkeypatch):
        from scripts.session.session import start, show_status

        monkeypatch.setattr(
            "scripts.session.session.subprocess.run",
            lambda *args, **kwargs: MagicMock(stdout="", returncode=0),
        )

        _create_work_item("Another Feature")
        item_id = _create_work_item("Active Feature")
        start(item_id)
        capsys.readouterr()

        show_status()
        captured = capsys.readouterr()
        assert "Overall:" in captured.out
