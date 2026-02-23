"""Tests for nexus-router.inspect tool."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any, cast

import jsonschema
import pytest

from nexus_router.tool import inspect, run


def _load_schema(name: str) -> dict[str, Any]:
    with (
        resources.files("nexus_router").joinpath(f"schemas/{name}").open("r", encoding="utf-8") as f
    ):
        return cast(dict[str, Any], json.load(f))


INSPECT_REQUEST_SCHEMA = _load_schema("nexus-router.inspect.request.v0.2.json")
INSPECT_RESPONSE_SCHEMA = _load_schema("nexus-router.inspect.response.v0.2.json")


class TestInspectContract:
    """Contract tests: validate request/response against schemas."""

    def test_minimal_request_valid(self) -> None:
        """Minimal valid request passes schema validation."""
        request = {"db_path": "/path/to/db.sqlite"}
        jsonschema.validate(request, INSPECT_REQUEST_SCHEMA)

    def test_full_request_valid(self) -> None:
        """Full request with all fields passes schema validation."""
        request = {
            "db_path": "/path/to/db.sqlite",
            "run_id": "abc-123",
            "status": "COMPLETED",
            "limit": 100,
            "offset": 10,
            "since": "2025-01-01T00:00:00Z",
        }
        jsonschema.validate(request, INSPECT_REQUEST_SCHEMA)

    def test_invalid_status_rejected(self) -> None:
        """Invalid status value is rejected."""
        request = {"db_path": "/path/to/db.sqlite", "status": "INVALID"}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(request, INSPECT_REQUEST_SCHEMA)


class TestInspectGoldenFixtures:
    """Golden fixture tests for inspect tool."""

    def test_inspect_zero_runs(self, tmp_path: Path) -> None:
        """Inspect with 0 runs returns empty summary."""
        db_path = str(tmp_path / "test.db")

        # Create empty DB by running once and not keeping the result
        # Actually, we need to initialize the schema - use run with memory then copy
        # Simpler: just call inspect on a fresh DB path, it will fail or return empty
        # Let's create a proper DB first
        from nexus_router.event_store import EventStore

        store = EventStore(db_path)
        store.close()

        response = inspect({"db_path": db_path})

        # Validate response schema
        jsonschema.validate(response, INSPECT_RESPONSE_SCHEMA)

        assert response["summary"]["runs_total"] == 0
        assert response["summary"]["completed"] == 0
        assert response["summary"]["failed"] == 0
        assert response["summary"]["running"] == 0
        assert response["runs"] == []

    def test_inspect_two_runs_mixed_status(self, tmp_path: Path) -> None:
        """Inspect with 2 runs: 1 completed, 1 failed."""
        db_path = str(tmp_path / "test.db")

        # Create a completed run
        run(
            {
                "goal": "completed run",
                "mode": "dry_run",
                "plan_override": [
                    {
                        "step_id": "s1",
                        "intent": "test",
                        "call": {"tool": "t", "method": "m", "args": {}},
                    }
                ],
            },
            db_path=db_path,
        )

        # Create a failed run (policy denied)
        run(
            {
                "goal": "failed run",
                "mode": "apply",
                "policy": {"allow_apply": False},
                "plan_override": [
                    {
                        "step_id": "s1",
                        "intent": "test",
                        "call": {"tool": "t", "method": "n", "args": {}},
                    }
                ],
            },
            db_path=db_path,
        )

        response = inspect({"db_path": db_path})

        # Validate response schema
        jsonschema.validate(response, INSPECT_RESPONSE_SCHEMA)

        assert response["summary"]["runs_total"] == 2
        assert response["summary"]["completed"] == 1
        assert response["summary"]["failed"] == 1
        assert response["summary"]["running"] == 0
        assert len(response["runs"]) == 2

        # Check run details
        statuses = {r["status"] for r in response["runs"]}
        assert statuses == {"COMPLETED", "FAILED"}

    def test_inspect_filter_by_status(self, tmp_path: Path) -> None:
        """Inspect with status filter returns only matching runs."""
        db_path = str(tmp_path / "test.db")

        # Create mixed runs
        run({"goal": "run1", "mode": "dry_run", "plan_override": []}, db_path=db_path)
        run(
            {
                "goal": "run2",
                "mode": "apply",
                "policy": {"allow_apply": False},
                "plan_override": [
                    {
                        "step_id": "s1",
                        "intent": "x",
                        "call": {"tool": "t", "method": "m", "args": {}},
                    }
                ],
            },
            db_path=db_path,
        )

        # Filter by COMPLETED
        response = inspect({"db_path": db_path, "status": "COMPLETED"})

        assert response["summary"]["runs_total"] == 1
        assert all(r["status"] == "COMPLETED" for r in response["runs"])

    def test_inspect_filter_by_run_id(self, tmp_path: Path) -> None:
        """Inspect with run_id filter returns only that run."""
        db_path = str(tmp_path / "test.db")

        # Create two runs
        resp1 = run({"goal": "run1", "mode": "dry_run", "plan_override": []}, db_path=db_path)
        run({"goal": "run2", "mode": "dry_run", "plan_override": []}, db_path=db_path)

        run_id = resp1["run"]["run_id"]

        response = inspect({"db_path": db_path, "run_id": run_id})

        assert response["summary"]["runs_total"] == 1
        assert len(response["runs"]) == 1
        assert response["runs"][0]["run_id"] == run_id
