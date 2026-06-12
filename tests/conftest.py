"""Pytest setup for the MolGenix demo application."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB = Path("test_molgenix.db")
os.environ["DATABASE_URL"] = f"sqlite:///./{TEST_DB.as_posix()}"

if TEST_DB.exists():
    TEST_DB.unlink()

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Return a TestClient with FastAPI lifespan initialized."""

    with TestClient(app) as test_client:
        yield test_client
