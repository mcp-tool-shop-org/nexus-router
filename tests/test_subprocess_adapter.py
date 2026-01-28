"""Tests for SubprocessAdapter."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from nexus_router.dispatch import SubprocessAdapter
from nexus_router.exceptions import NexusOperationalError
from nexus_router.tool import run

# Path to the echo_tool fixture
ECHO_TOOL = Path(__file__).parent / "fixtures" / "echo_tool.py"


class TestSubprocessAdapterInit:
    """Tests for SubprocessAdapter initialization."""

    def test_empty_base_cmd_raises(self) -> None:
        """Empty base_cmd raises ValueError."""
        with pytest.raises(ValueError, match="must not be empty"):
            SubprocessAdapter([])

    def test_default_adapter_id_derived(self) -> None:
        """Default adapter_id is derived from base_cmd."""
        adapter = SubprocessAdapter([sys.executable, "-m", "some_module"])
        assert adapter.adapter_id.startswith("subprocess:")
        assert "python" in adapter.adapter_id.lower() or "exe" in adapter.adapter_id.lower()

    def test_custom_adapter_id(self) -> None:
        """Custom adapter_id is used when provided."""
        adapter = SubprocessAdapter(
            [sys.executable, str(ECHO_TOOL)],
            adapter_id="my-custom-adapter",
        )
        assert adapter.adapter_id == "my-custom-adapter"

    def test_adapter_id_stable(self) -> None:
        """Same base_cmd produces same derived adapter_id."""
        cmd = [sys.executable, str(ECHO_TOOL)]
        adapter1 = SubprocessAdapter(cmd)
        adapter2 = SubprocessAdapter(cmd)
        assert adapter1.adapter_id == adapter2.adapter_id

    def test_different_cmds_different_ids(self) -> None:
        """Different base_cmds produce different adapter_ids."""
        adapter1 = SubprocessAdapter([sys.executable, "script1.py"])
        adapter2 = SubprocessAdapter([sys.executable, "script2.py"])
        assert adapter1.adapter_id != adapter2.adapter_id


class TestSubprocessAdapterSuccess:
    """Tests for successful subprocess calls."""

    def test_success_returns_json(self) -> None:
        """Successful call returns parsed JSON."""
        adapter = SubprocessAdapter(
            [sys.executable, str(ECHO_TOOL)],
            adapter_id="echo-test",
        )

        result = adapter.call("my-tool", "my-method", {"key": "value"})

        assert result["success"] is True
        assert result["tool"] == "my-tool"
        assert result["method"] == "my-method"
        assert result["received_args"] == {"key": "value"}
        assert result["echo"] is True

    def test_success_with_complex_args(self) -> None:
        """Successful call with nested args."""
        adapter = SubprocessAdapter(
            [sys.executable, str(ECHO_TOOL)],
            adapter_id="echo-test",
        )

        complex_args = {
            "string": "hello",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {"a": {"b": {"c": 1}}},
        }

        result = adapter.call("tool", "method", complex_args)

        assert result["success"] is True
        assert result["received_args"] == complex_args

    def test_success_ignores_stderr(self) -> None:
        """Success returns JSON even when stderr has content."""
        adapter = SubprocessAdapter(
            [sys.executable, str(ECHO_TOOL)],
            adapter_id="echo-test",
        )

        result = adapter.call(
            "tool", "method", {"simulate_stderr": "Warning: something happened"}
        )

        assert result["success"] is True
        # stderr content is ignored in output


class TestSubprocessAdapterErrors:
    """Tests for subprocess error handling."""

    def test_timeout_raises_operational_error(self) -> None:
        """Timeout raises NexusOperationalError with TIMEOUT code."""
        adapter = SubprocessAdapter(
            [sys.executable, str(ECHO_TOOL)],
            adapter_id="echo-test",
            timeout_s=0.5,
        )

        with pytest.raises(NexusOperationalError) as exc_info:
            adapter.call("tool", "method", {"simulate_timeout": True})

        assert exc_info.value.error_code == "TIMEOUT"
        assert "timed out" in str(exc_info.value).lower()

    def test_nonzero_exit_raises_operational_error(self) -> None:
        """Non-zero exit code raises NexusOperationalError."""
        adapter = SubprocessAdapter(
            [sys.executable, str(ECHO_TOOL)],
            adapter_id="echo-test",
        )

        with pytest.raises(NexusOperationalError) as exc_info:
            adapter.call(
                "tool",
                "method",
                {"simulate_exit_code": 2, "stderr_message": "Something failed"},
            )

        assert exc_info.value.error_code == "NONZERO_EXIT"
        assert "code 2" in str(exc_info.value)

    def test_invalid_json_output_raises_operational_error(self) -> None:
        """Invalid JSON output raises NexusOperationalError."""
        adapter = SubprocessAdapter(
            [sys.executable, str(ECHO_TOOL)],
            adapter_id="echo-test",
        )

        with pytest.raises(NexusOperationalError) as exc_info:
            adapter.call("tool", "method", {"simulate_invalid_json": True})

        assert exc_info.value.error_code == "INVALID_JSON_OUTPUT"

    def test_command_not_found_raises_operational_error(self) -> None:
        """Missing command raises NexusOperationalError."""
        adapter = SubprocessAdapter(
            ["nonexistent_command_12345"],
            adapter_id="missing-cmd",
        )

        with pytest.raises(NexusOperationalError) as exc_info:
            adapter.call("tool", "method", {})

        assert exc_info.value.error_code == "COMMAND_NOT_FOUND"


class TestSubprocessAdapterIntegration:
    """Integration tests with full router."""

    def test_apply_mode_with_subprocess_adapter(self, tmp_path: Path) -> None:
        """Apply mode calls SubprocessAdapter correctly."""
        db_path = str(tmp_path / "test.db")
        adapter = SubprocessAdapter(
            [sys.executable, str(ECHO_TOOL)],
            adapter_id="echo-integration",
        )

        resp = run(
            {
                "goal": "subprocess integration test",
                "mode": "apply",
                "policy": {"allow_apply": True},
                "plan_override": [
                    {
                        "step_id": "s1",
                        "intent": "test subprocess call",
                        "call": {
                            "tool": "test-tool",
                            "method": "test-method",
                            "args": {"input": "hello"},
                        },
                    }
                ],
            },
            db_path=db_path,
            adapter=adapter,
        )

        assert resp["summary"]["mode"] == "apply"
        assert resp["summary"]["adapter_id"] == "echo-integration"
        assert resp["summary"]["outputs_applied"] == 1
        assert resp["results"][0]["status"] == "ok"
        assert resp["results"][0]["output"]["success"] is True
        assert resp["results"][0]["output"]["received_args"] == {"input": "hello"}

    def test_dry_run_never_calls_subprocess(self, tmp_path: Path) -> None:
        """dry_run mode never invokes subprocess."""
        db_path = str(tmp_path / "test.db")
        # Use a command that would fail if called
        adapter = SubprocessAdapter(
            ["nonexistent_command_that_would_fail"],
            adapter_id="should-not-call",
        )

        # This should succeed because dry_run never calls the adapter
        resp = run(
            {
                "goal": "dry_run subprocess test",
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
            adapter=adapter,
        )

        assert resp["summary"]["mode"] == "dry_run"
        assert resp["summary"]["adapter_id"] == "should-not-call"
        assert resp["results"][0]["simulated"] is True

    def test_subprocess_error_allows_subsequent_steps(self, tmp_path: Path) -> None:
        """Operational error from subprocess allows subsequent steps."""
        db_path = str(tmp_path / "test.db")
        adapter = SubprocessAdapter(
            [sys.executable, str(ECHO_TOOL)],
            adapter_id="echo-multi",
        )

        resp = run(
            {
                "goal": "multi-step subprocess test",
                "mode": "apply",
                "policy": {"allow_apply": True},
                "plan_override": [
                    {
                        "step_id": "s1",
                        "intent": "this will fail",
                        "call": {
                            "tool": "t",
                            "method": "m",
                            "args": {"simulate_exit_code": 1},
                        },
                    },
                    {
                        "step_id": "s2",
                        "intent": "this will succeed",
                        "call": {
                            "tool": "t",
                            "method": "m",
                            "args": {"input": "success"},
                        },
                    },
                ],
            },
            db_path=db_path,
            adapter=adapter,
        )

        assert resp["results"][0]["status"] == "error"
        assert resp["results"][1]["status"] == "ok"
        assert resp["summary"]["outputs_skipped"] == 1
        assert resp["summary"]["outputs_applied"] == 1


class TestSubprocessAdapterConfig:
    """Tests for SubprocessAdapter configuration options."""

    def test_custom_env(self) -> None:
        """Custom environment variables are passed to subprocess."""
        adapter = SubprocessAdapter(
            [sys.executable, str(ECHO_TOOL)],
            adapter_id="echo-env",
            env={"CUSTOM_VAR": "custom_value"},
        )

        # The echo tool doesn't use env vars, but we verify no crash
        result = adapter.call("tool", "method", {})
        assert result["success"] is True

    def test_custom_cwd(self, tmp_path: Path) -> None:
        """Custom cwd is used for subprocess."""
        adapter = SubprocessAdapter(
            [sys.executable, str(ECHO_TOOL)],
            adapter_id="echo-cwd",
            cwd=str(tmp_path),
        )

        result = adapter.call("tool", "method", {})
        assert result["success"] is True

    def test_max_capture_chars_does_not_break_parsing(self) -> None:
        """max_capture_chars only affects diagnostics, not JSON parsing."""
        adapter = SubprocessAdapter(
            [sys.executable, str(ECHO_TOOL)],
            adapter_id="echo-truncate",
            max_capture_chars=50,  # Very small, but parsing uses full output
        )

        # Should still work - truncation is for event storage, not parsing
        result = adapter.call("tool", "method", {"data": "x" * 100})
        assert result["success"] is True
        assert result["received_args"]["data"] == "x" * 100
