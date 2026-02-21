"""Shared fixtures for the challenge test suite."""

import sys
from pathlib import Path

# Add backend/ to Python path so `from src.xxx` imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from src.main import app  # noqa: E402


@pytest.fixture()
def client():
    """FastAPI test client for integration tests."""
    return TestClient(app)
