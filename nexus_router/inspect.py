"""nexus-router.inspect: Read-only summary over the event store."""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from . import events as E


def inspect(
    *,
    db_path: str,
    run_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    since: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Inspect the event store and return run summaries.

    Args:
        db_path: Path to SQLite database file.
        run_id: Filter to specific run (optional).
        status: Filter by status: RUNNING, COMPLETED, FAILED (optional).
        limit: Max runs to return (default 50).
        offset: Pagination offset (default 0).
        since: RFC3339 timestamp to filter runs created after (optional).

    Returns:
        Summary dict with counts and run details.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # Build WHERE clause
        conditions: List[str] = []
        params: List[Any] = []

        if run_id is not None:
            conditions.append("r.run_id = ?")
            params.append(run_id)

        if status is not None:
            conditions.append("r.status = ?")
            params.append(status)

        if since is not None:
            conditions.append("r.created_at >= ?")
            params.append(since)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Get counts
        count_sql = f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'RUNNING' THEN 1 ELSE 0 END) as running
            FROM runs r
            {where_clause}
        """
        count_row = conn.execute(count_sql, params).fetchone()

        summary = {
            "runs_total": count_row["total"] or 0,
            "completed": count_row["completed"] or 0,
            "failed": count_row["failed"] or 0,
            "running": count_row["running"] or 0,
        }

        # Get runs with pagination
        runs_sql = f"""
            SELECT run_id, mode, goal, status, created_at
            FROM runs r
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        runs_params = params + [limit, offset]
        run_rows = conn.execute(runs_sql, runs_params).fetchall()

        runs: List[Dict[str, Any]] = []
        for row in run_rows:
            run_summary = _build_run_summary(conn, dict(row))
            runs.append(run_summary)

        return {
            "summary": summary,
            "runs": runs,
        }

    finally:
        conn.close()


def _build_run_summary(conn: sqlite3.Connection, run_row: Dict[str, Any]) -> Dict[str, Any]:
    """Build a summary for a single run from its events."""
    run_id = run_row["run_id"]

    # Get all events for this run
    events = conn.execute(
        "SELECT type, payload_json FROM events WHERE run_id = ? ORDER BY seq ASC",
        (run_id,),
    ).fetchall()

    steps_planned = 0
    steps_executed = 0
    tools_used: List[str] = []
    outcome: Optional[str] = None
    last_failure_reason: Optional[str] = None

    import json

    for event in events:
        event_type = event["type"]
        payload = json.loads(event["payload_json"])

        if event_type == E.PLAN_CREATED:
            plan = payload.get("plan", [])
            steps_planned = len(plan)

        elif event_type == E.STEP_STARTED:
            steps_executed += 1

        elif event_type == E.TOOL_CALL_REQUESTED:
            call = payload.get("call", {})
            method = call.get("method")
            if method and method not in tools_used:
                tools_used.append(method)

        elif event_type == E.RUN_COMPLETED:
            outcome = "ok"

        elif event_type == E.RUN_FAILED:
            outcome = "error"
            reason = payload.get("reason")
            if reason:
                last_failure_reason = reason

    return {
        "run_id": run_row["run_id"],
        "mode": run_row["mode"],
        "goal": run_row["goal"],
        "status": run_row["status"],
        "created_at": run_row["created_at"],
        "steps_planned": steps_planned,
        "steps_executed": steps_executed,
        "tools_used": tools_used,
        "outcome": outcome,
        "last_failure_reason": last_failure_reason,
    }
