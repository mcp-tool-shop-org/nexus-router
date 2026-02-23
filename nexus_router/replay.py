"""nexus-router.replay: Reconstruct run view from events and check invariants."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any

from . import events as E


@dataclass
class Violation:
    """An invariant violation found during replay."""

    code: str
    message: str
    seq: int | None = None
    event_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.seq is not None:
            result["seq"] = self.seq
        if self.event_id is not None:
            result["event_id"] = self.event_id
        return result


@dataclass
class StepTimeline:
    """Timeline for a single step."""

    step_id: str
    started_seq: int | None = None
    completed_seq: int | None = None
    tool_call_requested_seq: int | None = None
    tool_call_result_seq: int | None = None
    status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "started_seq": self.started_seq,
            "completed_seq": self.completed_seq,
            "tool_call_requested_seq": self.tool_call_requested_seq,
            "tool_call_result_seq": self.tool_call_result_seq,
            "status": self.status,
        }


@dataclass
class RunView:
    """Reconstructed view of a run from events."""

    run_id: str
    status: str | None = None
    outcome: str | None = None
    mode: str | None = None
    goal: str | None = None
    steps: dict[str, StepTimeline] = field(default_factory=dict)
    tools_used: list[str] = field(default_factory=list)
    provenance_present: bool = False
    terminal_event_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "outcome": self.outcome,
            "mode": self.mode,
            "goal": self.goal,
            "steps": {sid: s.to_dict() for sid, s in self.steps.items()},
            "tools_used": self.tools_used,
            "provenance_present": self.provenance_present,
            "terminal_event_type": self.terminal_event_type,
        }


def replay(
    *,
    db_path: str,
    run_id: str,
    strict: bool = True,
) -> dict[str, Any]:
    """
    Replay a run from events and check invariants.

    Args:
        db_path: Path to SQLite database file.
        run_id: The run ID to replay.
        strict: If True, invariant violations cause ok=False.

    Returns:
        Dict with ok, run_view, and violations.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # Check run exists
        run_row = conn.execute(
            "SELECT run_id, mode, goal, status FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        if run_row is None:
            return {
                "ok": False,
                "run_view": None,
                "violations": [{"code": "RUN_NOT_FOUND", "message": f"Run {run_id} not found"}],
            }

        # Get all events ordered by seq
        event_rows = conn.execute(
            "SELECT event_id, seq, type, payload_json FROM events "
            "WHERE run_id = ? ORDER BY seq ASC",
            (run_id,),
        ).fetchall()

        run_view = RunView(
            run_id=run_id,
            status=run_row["status"],
            mode=run_row["mode"],
            goal=run_row["goal"],
        )
        violations: list[Violation] = []

        # Check invariants as we replay
        _replay_events(event_rows, run_view, violations)

        ok = len(violations) == 0 if strict else True

        return {
            "ok": ok,
            "run_view": run_view.to_dict(),
            "violations": [v.to_dict() for v in violations],
        }

    finally:
        conn.close()


def _replay_events(
    event_rows: list[sqlite3.Row],
    run_view: RunView,
    violations: list[Violation],
) -> None:
    """Replay events and check invariants."""

    if not event_rows:
        violations.append(Violation(code="NO_EVENTS", message="Run has no events"))
        return

    # Track state for invariant checking
    seen_run_started = False
    seen_plan_created = False
    seen_terminal = False
    prev_seq: int | None = None
    active_steps: dict[str, int] = {}  # step_id -> started_seq

    for row in event_rows:
        event_id = row["event_id"]
        seq = row["seq"]
        event_type = row["type"]
        payload = json.loads(row["payload_json"])

        # INV: seq starts at 0 and strictly increases by 1
        if prev_seq is None:
            if seq != 0:
                violations.append(
                    Violation(
                        code="SEQ_NOT_ZERO",
                        message=f"First event seq should be 0, got {seq}",
                        seq=seq,
                        event_id=event_id,
                    )
                )
        else:
            if seq != prev_seq + 1:
                violations.append(
                    Violation(
                        code="SEQ_GAP",
                        message=f"Expected seq {prev_seq + 1}, got {seq}",
                        seq=seq,
                        event_id=event_id,
                    )
                )
        prev_seq = seq

        # INV: RUN_STARTED exists and is first
        if event_type == E.RUN_STARTED:
            if seq != 0:
                violations.append(
                    Violation(
                        code="RUN_STARTED_NOT_FIRST",
                        message=f"RUN_STARTED should be seq 0, found at {seq}",
                        seq=seq,
                        event_id=event_id,
                    )
                )
            seen_run_started = True
            run_view.mode = payload.get("mode")
            run_view.goal = payload.get("goal")

        # INV: PLAN_CREATED exists and appears after RUN_STARTED
        elif event_type == E.PLAN_CREATED:
            if not seen_run_started:
                violations.append(
                    Violation(
                        code="PLAN_BEFORE_RUN_STARTED",
                        message="PLAN_CREATED appeared before RUN_STARTED",
                        seq=seq,
                        event_id=event_id,
                    )
                )
            seen_plan_created = True

        # Track STEP_STARTED
        elif event_type == E.STEP_STARTED:
            step_id = payload.get("step_id")
            if step_id:
                if step_id not in run_view.steps:
                    run_view.steps[step_id] = StepTimeline(step_id=step_id)
                run_view.steps[step_id].started_seq = seq
                active_steps[step_id] = seq

        # Track TOOL_CALL_REQUESTED
        elif event_type == E.TOOL_CALL_REQUESTED:
            step_id = payload.get("step_id")
            call = payload.get("call", {})
            method = call.get("method")

            if step_id:
                # INV: TOOL_CALL_* must appear between STEP_STARTED and STEP_COMPLETED
                if step_id not in active_steps:
                    violations.append(
                        Violation(
                            code="TOOL_CALL_WITHOUT_STEP",
                            message=f"TOOL_CALL_REQUESTED for {step_id} without STEP_STARTED",
                            seq=seq,
                            event_id=event_id,
                        )
                    )
                if step_id in run_view.steps:
                    run_view.steps[step_id].tool_call_requested_seq = seq

            if method and method not in run_view.tools_used:
                run_view.tools_used.append(method)

        # Track TOOL_CALL_SUCCEEDED / TOOL_CALL_FAILED
        elif event_type in (E.TOOL_CALL_SUCCEEDED, E.TOOL_CALL_FAILED):
            step_id = payload.get("step_id")
            if step_id:
                if step_id not in active_steps:
                    violations.append(
                        Violation(
                            code="TOOL_RESULT_WITHOUT_STEP",
                            message=f"Tool result for {step_id} without STEP_STARTED",
                            seq=seq,
                            event_id=event_id,
                        )
                    )
                if step_id in run_view.steps:
                    run_view.steps[step_id].tool_call_result_seq = seq

        # Track STEP_COMPLETED
        elif event_type == E.STEP_COMPLETED:
            step_id = payload.get("step_id")
            status = payload.get("status")
            if step_id:
                # INV: STEP_STARTED must precede STEP_COMPLETED per step_id
                if step_id not in active_steps:
                    violations.append(
                        Violation(
                            code="STEP_COMPLETED_WITHOUT_START",
                            message=f"STEP_COMPLETED for {step_id} without STEP_STARTED",
                            seq=seq,
                            event_id=event_id,
                        )
                    )
                if step_id in run_view.steps:
                    run_view.steps[step_id].completed_seq = seq
                    run_view.steps[step_id].status = status
                # Mark step as no longer active
                active_steps.pop(step_id, None)

        # Track PROVENANCE_EMITTED
        elif event_type == E.PROVENANCE_EMITTED:
            run_view.provenance_present = True

        # Track terminal events
        elif event_type == E.RUN_COMPLETED:
            seen_terminal = True
            run_view.terminal_event_type = E.RUN_COMPLETED
            run_view.outcome = "ok"

        elif event_type == E.RUN_FAILED:
            seen_terminal = True
            run_view.terminal_event_type = E.RUN_FAILED
            run_view.outcome = "error"

    # Final invariant checks
    if not seen_run_started:
        violations.append(Violation(code="NO_RUN_STARTED", message="RUN_STARTED event not found"))

    if not seen_plan_created:
        violations.append(Violation(code="NO_PLAN_CREATED", message="PLAN_CREATED event not found"))

    if not seen_terminal:
        violations.append(
            Violation(
                code="NO_TERMINAL_EVENT",
                message="No terminal event (RUN_COMPLETED or RUN_FAILED) found",
            )
        )
