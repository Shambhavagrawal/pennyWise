"""Tests for scripts/session/work_items.py."""

import json
import pytest


@pytest.fixture
def setup_paths(tmp_path, monkeypatch):
    """Redirect all constants paths to temp directory."""
    import scripts.session.constants as constants
    import scripts.session.work_items as work_items_mod

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

    # Patch the importing module (work_items imports from constants at module load time)
    monkeypatch.setattr(work_items_mod, "WORK_ITEMS_PATH", tracking / "work_items.json")
    monkeypatch.setattr(work_items_mod, "SPECS_DIR", specs)
    monkeypatch.setattr(work_items_mod, "TEMPLATES_DIR", templates)

    # Create initial work_items.json
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

    # Create spec templates
    (templates / "feature_spec.md").write_text(
        "# Feature Spec Template\n\n## Overview\n"
    )
    (templates / "bug_spec.md").write_text("# Bug Spec Template\n\n## Overview\n")

    return tmp_path


def _load_work_items(tmp_path):
    """Helper to load work_items.json from the temp tracking dir."""
    return json.loads(
        (tmp_path / "tracking" / "work_items.json").read_text(encoding="utf-8")
    )


# ---------- generate_id tests ----------


class TestGenerateId:
    def test_basic_generation(self, setup_paths):
        from scripts.session.work_items import generate_id

        result = generate_id("feature", "User Login Page", set())
        assert result == "feature_user_login_page"

    def test_collision_handling_appends_suffix(self, setup_paths):
        from scripts.session.work_items import generate_id

        existing = {"feature_login"}
        result = generate_id("feature", "Login", existing)
        assert result == "feature_login_2"

    def test_collision_handling_increments(self, setup_paths):
        from scripts.session.work_items import generate_id

        existing = {"feature_login", "feature_login_2"}
        result = generate_id("feature", "Login", existing)
        assert result == "feature_login_3"

    def test_max_length_truncation(self, setup_paths):
        from scripts.session.work_items import generate_id

        long_title = "a" * 100
        result = generate_id("feature", long_title, set())
        assert len(result) <= 40

    def test_special_characters_cleaned(self, setup_paths):
        from scripts.session.work_items import generate_id

        result = generate_id("bug", "Fix @#$% issue (urgent!)", set())
        # Should only contain a-z, 0-9, and underscores
        assert result.replace("_", "").isalnum()
        assert "@" not in result
        assert "#" not in result
        assert "!" not in result

    def test_leading_trailing_underscores_stripped(self, setup_paths):
        from scripts.session.work_items import generate_id

        result = generate_id("feature", "  Hello World  ", set())
        # The cleaned part should not have leading/trailing underscores
        # (type prefix adds one underscore)
        assert not result.startswith("feature__")
        assert not result.endswith("_")


# ---------- create tests ----------


class TestCreate:
    def test_creates_item_in_json(self, setup_paths):
        from scripts.session.work_items import create

        item_id = create("feature", "Login Page", "high")
        data = _load_work_items(setup_paths)
        assert item_id in data["work_items"]
        assert data["work_items"][item_id]["title"] == "Login Page"
        assert data["work_items"][item_id]["type"] == "feature"
        assert data["work_items"][item_id]["status"] == "not_started"

    def test_copies_spec_template(self, setup_paths):
        from scripts.session.work_items import create

        item_id = create("feature", "Login Page", "high")
        spec_file = setup_paths / "specs" / f"{item_id}.md"
        assert spec_file.exists()
        content = spec_file.read_text(encoding="utf-8")
        assert "Feature Spec Template" in content

    def test_bug_template_used_for_bug_type(self, setup_paths):
        from scripts.session.work_items import create

        item_id = create("bug", "Fix crash", "critical")
        spec_file = setup_paths / "specs" / f"{item_id}.md"
        assert spec_file.exists()
        content = spec_file.read_text(encoding="utf-8")
        assert "Bug Spec Template" in content

    def test_updates_metadata_counts(self, setup_paths):
        from scripts.session.work_items import create

        create("feature", "First Item", "high")
        create("feature", "Second Item", "medium")
        data = _load_work_items(setup_paths)
        assert data["metadata"]["total_items"] == 2
        assert data["metadata"]["last_updated"] is not None

    def test_invalid_type_raises(self, setup_paths):
        from scripts.session.work_items import create

        with pytest.raises(ValueError, match="Invalid type"):
            create("invalid_type", "Bad Item", "high")

    def test_invalid_priority_raises(self, setup_paths):
        from scripts.session.work_items import create

        with pytest.raises(ValueError, match="Invalid priority"):
            create("feature", "Bad Priority", "super_high")

    def test_urgent_constraint(self, setup_paths):
        from scripts.session.work_items import create

        create("feature", "Urgent One", "critical", urgent=True)
        with pytest.raises(ValueError, match="Already have an urgent item"):
            create("feature", "Urgent Two", "high", urgent=True)


# ---------- list_items tests ----------


class TestListItems:
    def test_lists_all_items(self, setup_paths, capsys):
        from scripts.session.work_items import create, list_items

        create("feature", "Item A", "high")
        create("bug", "Item B", "low")
        list_items()
        captured = capsys.readouterr()
        assert "Item A" in captured.out
        assert "Item B" in captured.out
        assert "Total: 2" in captured.out

    def test_filter_by_status(self, setup_paths, capsys):
        from scripts.session.work_items import create, list_items, update

        create("feature", "Todo Item", "high")
        item_id = create("feature", "Done Item", "low")
        update(item_id, status="completed")
        list_items(status="completed")
        captured = capsys.readouterr()
        assert "Done Item" in captured.out
        assert "Total: 1" in captured.out

    def test_filter_by_type(self, setup_paths, capsys):
        from scripts.session.work_items import create, list_items

        create("feature", "Feature Item", "high")
        create("bug", "Bug Item", "low")
        list_items(work_type="bug")
        captured = capsys.readouterr()
        assert "Bug Item" in captured.out
        assert "Total: 1" in captured.out

    def test_empty_list(self, setup_paths, capsys):
        from scripts.session.work_items import list_items

        list_items()
        captured = capsys.readouterr()
        assert "No work items found" in captured.out

    def test_no_matching_items(self, setup_paths, capsys):
        from scripts.session.work_items import create, list_items

        create("feature", "A Feature", "high")
        list_items(status="completed")
        captured = capsys.readouterr()
        assert "No matching work items found" in captured.out


# ---------- update tests ----------


class TestUpdate:
    def test_status_change(self, setup_paths):
        from scripts.session.work_items import create, update

        item_id = create("feature", "My Item", "high")
        update(item_id, status="in_progress")
        data = _load_work_items(setup_paths)
        assert data["work_items"][item_id]["status"] == "in_progress"

    def test_priority_change(self, setup_paths):
        from scripts.session.work_items import create, update

        item_id = create("feature", "My Item", "low")
        update(item_id, priority="critical")
        data = _load_work_items(setup_paths)
        assert data["work_items"][item_id]["priority"] == "critical"

    def test_add_dependency(self, setup_paths):
        from scripts.session.work_items import create, update

        dep_id = create("feature", "Dependency", "high")
        item_id = create("feature", "My Item", "medium")
        update(item_id, add_dependency=dep_id)
        data = _load_work_items(setup_paths)
        assert dep_id in data["work_items"][item_id]["dependencies"]

    def test_remove_dependency(self, setup_paths):
        from scripts.session.work_items import create, update

        dep_id = create("feature", "Dependency", "high")
        item_id = create("feature", "My Item", "medium", dependencies=[dep_id])
        update(item_id, remove_dependency=dep_id)
        data = _load_work_items(setup_paths)
        assert dep_id not in data["work_items"][item_id]["dependencies"]

    def test_set_urgent_constraint(self, setup_paths):
        from scripts.session.work_items import create, update

        create("feature", "Item A", "high", urgent=True)
        item_b = create("feature", "Item B", "high")
        with pytest.raises(ValueError, match="Already have an urgent item"):
            update(item_b, set_urgent=True)

    def test_invalid_status_raises(self, setup_paths):
        from scripts.session.work_items import create, update

        item_id = create("feature", "My Item", "high")
        with pytest.raises(ValueError, match="Invalid status"):
            update(item_id, status="bogus")

    def test_cannot_depend_on_self(self, setup_paths):
        from scripts.session.work_items import create, update

        item_id = create("feature", "Self Ref", "high")
        with pytest.raises(ValueError, match="Cannot depend on itself"):
            update(item_id, add_dependency=item_id)


# ---------- delete tests ----------


class TestDelete:
    def test_basic_delete(self, setup_paths):
        from scripts.session.work_items import create, delete

        item_id = create("feature", "Doomed Item", "low")
        delete(item_id)
        data = _load_work_items(setup_paths)
        assert item_id not in data["work_items"]
        assert data["metadata"]["total_items"] == 0

    def test_blocks_when_has_dependents(self, setup_paths, capsys):
        from scripts.session.work_items import create, delete

        dep_id = create("feature", "Base Item", "high")
        create("feature", "Dependent Item", "medium", dependencies=[dep_id])
        delete(dep_id)
        captured = capsys.readouterr()
        assert "Cannot delete" in captured.out
        # Item should still exist
        data = _load_work_items(setup_paths)
        assert dep_id in data["work_items"]

    def test_with_spec_deletes_file(self, setup_paths):
        from scripts.session.work_items import create, delete

        item_id = create("feature", "With Spec", "high")
        spec_path = setup_paths / "specs" / f"{item_id}.md"
        assert spec_path.exists()
        delete(item_id, with_spec=True)
        assert not spec_path.exists()

    def test_without_spec_keeps_file(self, setup_paths):
        from scripts.session.work_items import create, delete

        item_id = create("feature", "Keep Spec", "high")
        spec_path = setup_paths / "specs" / f"{item_id}.md"
        assert spec_path.exists()
        delete(item_id, with_spec=False)
        assert spec_path.exists()

    def test_delete_nonexistent(self, setup_paths, capsys):
        from scripts.session.work_items import delete

        delete("nonexistent_id")
        captured = capsys.readouterr()
        assert "not found" in captured.out


# ---------- next_items tests ----------


class TestNextItems:
    def test_filters_not_started_only(self, setup_paths, capsys):
        from scripts.session.work_items import create, update, next_items

        item_a = create("feature", "Started Item", "high")
        update(item_a, status="in_progress")
        create("feature", "Ready Item", "high")
        next_items()
        captured = capsys.readouterr()
        assert "Ready Item" in captured.out
        assert "Started Item" not in captured.out

    def test_excludes_unmet_deps(self, setup_paths, capsys):
        from scripts.session.work_items import create, next_items

        dep_id = create("feature", "Dependency", "high")
        create("feature", "Blocked Item", "high", dependencies=[dep_id])
        next_items()
        captured = capsys.readouterr()
        # Only the dependency itself should show (it has no deps)
        assert "Dependency" in captured.out
        assert "Blocked Item" not in captured.out

    def test_sorts_urgent_first(self, setup_paths, capsys):
        from scripts.session.work_items import create, next_items

        create("feature", "Normal Item", "critical")
        create("feature", "Urgent Item", "low", urgent=True)
        next_items()
        captured = capsys.readouterr()
        # Urgent should appear before normal in output
        urgent_pos = captured.out.index("Urgent Item")
        normal_pos = captured.out.index("Normal Item")
        assert urgent_pos < normal_pos

    def test_sorts_by_priority(self, setup_paths, capsys):
        from scripts.session.work_items import create, next_items

        create("feature", "Low Item", "low")
        create("feature", "Critical Item", "critical")
        next_items()
        captured = capsys.readouterr()
        crit_pos = captured.out.index("Critical Item")
        low_pos = captured.out.index("Low Item")
        assert crit_pos < low_pos

    def test_no_candidates_message(self, setup_paths, capsys):
        from scripts.session.work_items import create, update, next_items

        item_id = create("feature", "Done Item", "high")
        update(item_id, status="completed")
        next_items()
        captured = capsys.readouterr()
        assert "No available work items" in captured.out

    def test_respects_limit(self, setup_paths, capsys):
        from scripts.session.work_items import create, next_items

        for i in range(10):
            create("feature", f"Item {i}", "medium")
        next_items(limit=3)
        captured = capsys.readouterr()
        assert "Next 3 recommended" in captured.out
