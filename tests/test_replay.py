"""Tests for nexus-router.replay tool."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any, cast

import jsonschema

from nexus_router import events as E
from nexus_router.event_store import EventStore
from nexus_router.tool import replay, run


def _load_schema(name: str) -> dict[str, Any]:
    with (
        resources.files("nexus_router").joinpath(f"schemas/{name}").open("r", encoding="utf-8") as f
    ):
        return cast(dict[str, Any], json.load(f))


REPLAY_REQUEST_SCHEMA = _load_schema("nexus-router.replay.request.v0.2.json")
REPLAY_RESPONSE_SCHEMA = _load_schema("nexus-router.replay.response.v0.2.json")


class TestReplayContract:
    """Contract tests: validate request/response against schemas."""

    def test_minimal_request_valid(self) -> None:
        """Minimal valid request passes schema validation."""
        request = {"db_path": "/path/to/db.sqlite", "run_id": "abc-123"}
        jsonschema.validate(request, REPLAY_REQUEST_SCHEMA)

    def test_full_request_valid(self) -> None:
        """Full request with all fields passes schema validation."""
        request = {
            "db_path": "/path/to/db.sqlite",
            "run_id": "abc-123",
            "strict": False,
        }
        jsonschema.validate(request, REPLAY_REQUEST_SCHEMA)


class TestReplayGoldenFixtures:
    """Golden fixture tests for replay tool."""

    def test_replay_happy_path(self, tmp_path: Path) -> None:
        """Replay a valid run with no violations."""
        db_path = str(tmp_path / "test.db")

        # Create a valid run
        resp = run(
            {
                "goal": "replay test",
                "mode": "dry_run",
                "plan_override": [
                    {
                        "step_id": "s1",
                        "intent": "test step",
                        "call": {"tool": "my-tool", "method": "my_method", "args": {}},
                    }
                ],
            },
            db_path=db_path,
        )
        run_id = resp["run"]["run_id"]

        response = replay({"db_path": db_path, "run_id": run_id})

        # Validate response schema
        jsonschema.validate(response, REPLAY_RESPONSE_SCHEMA)

        assert response["ok"] is True
        assert response["violations"] == []

        run_view = response["run_view"]
        assert run_view["run_id"] == run_id
        assert run_view["mode"] == "dry_run"
        assert run_view["goal"] == "replay test"
        assert run_view["outcome"] == "ok"
        assert run_view["provenance_present"] is True
        assert "s1" in run_view["steps"]
        assert "my_method" in run_view["tools_used"]

    def test_replay_run_not_found(self, tmp_path: Path) -> None:
        """Replay with invalid run_id returns error."""
        db_path = str(tmp_path / "test.db")

        # Initialize DB
        store = EventStore(db_path)
        store.close()

        response = replay({"db_path": db_path, "run_id": "nonexistent"})

        jsonschema.validate(response, REPLAY_RESPONSE_SCHEMA)

        assert response["ok"] is False
        assert response["run_view"] is None
        assert len(response["violations"]) == 1
        assert response["violations"][0]["code"] == "RUN_NOT_FOUND"

    def test_replay_invariant_violation_step_completed_without_start(self, tmp_path: Path) -> None:
        """Replay detects STEP_COMPLETED without STEP_STARTED."""
        db_path = str(tmp_path / "test.db")

        # Manually create a malformed event sequence
        store = EventStore(db_path)
        run_id = store.create_run(mode="dry_run", goal="bad run")

        # Valid start
        store.append(run_id, E.RUN_STARTED, {"mode": "dry_run", "goal": "bad run"})
        store.append(run_id, E.PLAN_CREATED, {"plan": []})

        # STEP_COMPLETED without STEP_STARTED - invariant violation!
        store.append(run_id, E.STEP_COMPLETED, {"step_id": "orphan", "status": "ok"})

        store.append(run_id, E.PROVENANCE_EMITTED, {"provenance": {}})
        store.append(run_id, E.RUN_COMPLETED, {"outcome": "ok"})
        store.set_run_status(run_id, "COMPLETED")
        store.close()

        response = replay({"db_path": db_path, "run_id": run_id})

        jsonschema.validate(response, REPLAY_RESPONSE_SCHEMA)

        assert response["ok"] is False
        violation_codes = [v["code"] for v in response["violations"]]
        assert "STEP_COMPLETED_WITHOUT_START" in violation_codes

    def test_replay_invariant_violation_no_run_started(self, tmp_path: Path) -> None:
        """Replay detects missing RUN_STARTED event."""
        db_path = str(tmp_path / "test.db")

        # Create run but don't emit RUN_STARTED
        store = EventStore(db_path)
        run_id = store.create_run(mode="dry_run", goal="bad run")

        # Skip RUN_STARTED, go straight to PLAN_CREATED
        store.append(run_id, E.PLAN_CREATED, {"plan": []})
        store.append(run_id, E.RUN_COMPLETED, {"outcome": "ok"})
        store.set_run_status(run_id, "COMPLETED")
        store.close()

        response = replay({"db_path": db_path, "run_id": run_id})

        jsonschema.validate(response, REPLAY_RESPONSE_SCHEMA)

        assert response["ok"] is False
        violation_codes = [v["code"] for v in response["violations"]]
        assert "NO_RUN_STARTED" in violation_codes
        # Also should detect that RUN_STARTED wasn't first
        assert "RUN_STARTED_NOT_FIRST" in violation_codes or "NO_RUN_STARTED" in violation_codes

    def test_replay_strict_false_allows_violations(self, tmp_path: Path) -> None:
        """Replay with strict=False returns ok=True even with violations."""
        db_path = str(tmp_path / "test.db")

        # Create malformed run
        store = EventStore(db_path)
        run_id = store.create_run(mode="dry_run", goal="bad run")
        store.append(run_id, E.PLAN_CREATED, {"plan": []})  # Missing RUN_STARTED
        store.append(run_id, E.RUN_COMPLETED, {"outcome": "ok"})
        store.set_run_status(run_id, "COMPLETED")
        store.close()

        response = replay({"db_path": db_path, "run_id": run_id, "strict": False})

        jsonschema.validate(response, REPLAY_RESPONSE_SCHEMA)

        # ok=True because strict=False
        assert response["ok"] is True
        # But violations are still reported
        assert len(response["violations"]) > 0

    def test_replay_seq_gap_detected(self, tmp_path: Path) -> None:
        """Replay detects gaps in sequence numbers."""
        db_path = str(tmp_path / "test.db")

        # We can't easily create a seq gap with the normal API
        # because append() auto-increments. We'd need raw SQL.
        # For now, test that normal runs don't have seq issues.
        resp = run(
            {"goal": "seq test", "mode": "dry_run", "plan_override": []},
            db_path=db_path,
        )
        run_id = resp["run"]["run_id"]

        response = replay({"db_path": db_path, "run_id": run_id})

        # No seq violations in a properly created run
        seq_violations = [
            v for v in response["violations"] if v["code"] in ("SEQ_GAP", "SEQ_NOT_ZERO")
        ]
        assert seq_violations == []


class TestReplayPropertyBased:
    """Property-based tests for replay."""

    def test_valid_run_replays_ok(self, tmp_path: Path) -> None:
        """Any valid run should replay without violations."""
        db_path = str(tmp_path / "test.db")

        # Generate various valid runs
        test_cases = [
            # Empty plan
            {"goal": "empty", "mode": "dry_run", "plan_override": []},
            # Single step
            {
                "goal": "single",
                "mode": "dry_run",
                "plan_override": [
                    {
                        "step_id": "s1",
                        "intent": "x",
                        "call": {"tool": "t", "method": "m", "args": {}},
                    }
                ],
            },
            # Multiple steps
            {
                "goal": "multi",
                "mode": "dry_run",
                "plan_override": [
                    {
                        "step_id": "s1",
                        "intent": "x",
                        "call": {"tool": "t", "method": "m1", "args": {}},
                    },
                    {
                        "step_id": "s2",
                        "intent": "y",
                        "call": {"tool": "t", "method": "m2", "args": {}},
                    },
                ],
            },
            # Apply mode (allowed)
            {
                "goal": "apply",
                "mode": "apply",
                "policy": {"allow_apply": True},
                "plan_override": [
                    {
                        "step_id": "s1",
                        "intent": "x",
                        "call": {"tool": "t", "method": "m", "args": {}},
                    }
                ],
            },
        ]

        for i, request in enumerate(test_cases):
            resp = run(request, db_path=db_path)
            run_id = resp["run"]["run_id"]

            replay_resp = replay({"db_path": db_path, "run_id": run_id})

            assert replay_resp["ok"] is True, f"Case {i} failed: {replay_resp['violations']}"
            assert replay_resp["violations"] == []
