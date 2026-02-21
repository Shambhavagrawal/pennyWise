from pathlib import Path

# Root paths (relative to project root — scripts are run from fullstack_python/)
SESSION_DIR = Path(".session")
TRACKING_DIR = SESSION_DIR / "tracking"
SPECS_DIR = SESSION_DIR / "specs"
TEMPLATES_DIR = SESSION_DIR / "templates"
HISTORY_DIR = SESSION_DIR / "history"
BRIEFINGS_DIR = SESSION_DIR / "briefings"
CONFIG_PATH = SESSION_DIR / "config.json"

# Tracking files
WORK_ITEMS_PATH = TRACKING_DIR / "work_items.json"
LEARNINGS_PATH = TRACKING_DIR / "learnings.json"
STATUS_PATH = TRACKING_DIR / "status_update.json"

# Valid enum values (must match solokit for compatibility)
VALID_TYPES = {
    "feature",
    "bug",
    "refactor",
    "security",
    "integration_test",
    "deployment",
}
VALID_PRIORITIES = {"critical", "high", "medium", "low"}
VALID_STATUSES = {"not_started", "in_progress", "blocked", "completed"}
VALID_CATEGORIES = {
    "architecture_patterns",
    "gotchas",
    "best_practices",
    "technical_debt",
    "performance_insights",
    "security",
}

# Priority sort order (for work-next ranking)
PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# Template filename mapping
TEMPLATE_MAP = {
    "feature": "feature_spec.md",
    "bug": "bug_spec.md",
    "refactor": "refactor_spec.md",
    "security": "security_spec.md",
    "integration_test": "integration_test_spec.md",
    "deployment": "deployment_spec.md",
}

# Defaults
MAX_ID_LENGTH = 40
DEFAULT_JACCARD_THRESHOLD = 0.6
