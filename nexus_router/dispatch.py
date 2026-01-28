"""Dispatch adapters for nexus-router tool calls."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple

from .exceptions import NexusBugError, NexusOperationalError


class DispatchAdapter(Protocol):
    """
    Protocol for dispatch adapters.

    Adapters implement the transport layer for tool calls.
    The router decides what to call; the adapter decides how to call it.
    """

    @property
    def adapter_id(self) -> str:
        """Unique identifier for this adapter instance."""
        ...

    def call(self, tool: str, method: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call.

        Args:
            tool: Tool identifier (e.g., "file-system")
            method: Method name (e.g., "read_file")
            args: Arguments dict for the method

        Returns:
            JSON-serializable dict with the result.

        Raises:
            NexusOperationalError: For expected failures (timeout, tool error, etc.)
            NexusBugError: For unexpected failures (bugs in adapter)
            Other exceptions: Treated as bugs by the router
        """
        ...


class NullAdapter:
    """
    Adapter that returns deterministic placeholder outputs.

    Used for:
    - dry_run mode (default)
    - Testing without external dependencies
    - Development/debugging
    """

    def __init__(self, adapter_id: str = "null") -> None:
        self._adapter_id = adapter_id

    @property
    def adapter_id(self) -> str:
        return self._adapter_id

    def call(self, tool: str, method: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Return a deterministic placeholder result."""
        return {
            "simulated": True,
            "tool": tool,
            "method": method,
            "args_echo": args,
            "result": None,
        }


class FakeAdapter:
    """
    Adapter with configurable responses for testing.

    Allows tests to specify exact outputs or errors for specific
    (tool, method) combinations.
    """

    def __init__(self, adapter_id: str = "fake") -> None:
        self._adapter_id = adapter_id
        self._responses: Dict[Tuple[str, str], Callable[..., Dict[str, Any]]] = {}
        self._default_response: Optional[Callable[..., Dict[str, Any]]] = None
        self._call_log: list[Dict[str, Any]] = []

    @property
    def adapter_id(self) -> str:
        return self._adapter_id

    @property
    def call_log(self) -> list[Dict[str, Any]]:
        """Log of all calls made to this adapter."""
        return self._call_log

    def set_response(
        self,
        tool: str,
        method: str,
        response: Dict[str, Any] | Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        """
        Set the response for a specific (tool, method) combination.

        Args:
            tool: Tool identifier
            method: Method name
            response: Either a dict to return, or a callable that takes args
                      and returns a dict (or raises an exception)
        """
        if callable(response):
            self._responses[(tool, method)] = response
        else:
            self._responses[(tool, method)] = lambda _args: response

    def set_default_response(
        self,
        response: Dict[str, Any] | Callable[[str, str, Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        """
        Set the default response for unregistered (tool, method) combinations.

        Args:
            response: Either a dict to return, or a callable that takes
                      (tool, method, args) and returns a dict
        """
        if callable(response):
            self._default_response = response
        else:
            self._default_response = lambda _t, _m, _a: response

    def set_operational_error(
        self,
        tool: str,
        method: str,
        message: str,
        error_code: str = "TOOL_ERROR",
    ) -> None:
        """Configure a specific call to raise NexusOperationalError."""

        def raise_error(_args: Dict[str, Any]) -> Dict[str, Any]:
            raise NexusOperationalError(message, error_code=error_code)

        self._responses[(tool, method)] = raise_error

    def set_bug_error(
        self,
        tool: str,
        method: str,
        message: str,
        error_code: str = "ADAPTER_BUG",
    ) -> None:
        """Configure a specific call to raise NexusBugError."""

        def raise_error(_args: Dict[str, Any]) -> Dict[str, Any]:
            raise NexusBugError(message, error_code=error_code)

        self._responses[(tool, method)] = raise_error

    def call(self, tool: str, method: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the configured response."""
        # Log the call
        self._call_log.append({"tool": tool, "method": method, "args": args})

        # Check for specific response
        key = (tool, method)
        if key in self._responses:
            return self._responses[key](args)

        # Check for default response
        if self._default_response is not None:
            return self._default_response(tool, method, args)

        # No response configured - return placeholder
        return {
            "fake": True,
            "tool": tool,
            "method": method,
            "args_echo": args,
            "result": None,
        }

    def reset(self) -> None:
        """Clear all configured responses and call log."""
        self._responses.clear()
        self._default_response = None
        self._call_log.clear()


class SubprocessAdapter:
    """
    Adapter that calls external commands via subprocess.

    Executes tool calls by invoking a base command with:
        <base_cmd> call <tool> <method> --json-args-file <path>

    The external command must:
    - Read JSON payload from the args file
    - Print JSON result to stdout on success
    - Exit with 0 on success, non-zero on failure

    All failures are mapped to NexusOperationalError (not bugs).
    """

    def __init__(
        self,
        base_cmd: List[str],
        *,
        adapter_id: Optional[str] = None,
        timeout_s: float = 30.0,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        max_capture_chars: int = 200_000,
    ) -> None:
        """
        Initialize SubprocessAdapter.

        Args:
            base_cmd: Base command as list (e.g., ["python", "-m", "mcpt.cli"])
            adapter_id: Optional custom adapter ID. If None, derived from base_cmd.
            timeout_s: Timeout for subprocess execution in seconds.
            cwd: Working directory for subprocess.
            env: Environment variables (merged with os.environ).
            max_capture_chars: Max chars to capture from stdout/stderr.
        """
        if not base_cmd:
            raise ValueError("base_cmd must not be empty")

        self._base_cmd = list(base_cmd)
        self._timeout_s = timeout_s
        self._cwd = cwd
        self._env = env
        self._max_capture_chars = max_capture_chars

        # Derive adapter_id if not provided
        if adapter_id is not None:
            self._adapter_id = adapter_id
        else:
            self._adapter_id = self._derive_adapter_id()

    def _derive_adapter_id(self) -> str:
        """Derive a stable adapter ID from base_cmd."""
        first_token = os.path.basename(self._base_cmd[0])
        # Add short hash of full command for uniqueness
        cmd_str = " ".join(self._base_cmd)
        cmd_hash = hashlib.sha256(cmd_str.encode()).hexdigest()[:6]
        return f"subprocess:{first_token}:{cmd_hash}"

    @property
    def adapter_id(self) -> str:
        return self._adapter_id

    def call(self, tool: str, method: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call via subprocess.

        Returns:
            Parsed JSON result from stdout.

        Raises:
            NexusOperationalError: For timeout, non-zero exit, or invalid JSON output.
        """
        # Build payload
        payload = {
            "tool": tool,
            "method": method,
            "args": args,
        }
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))

        # Write payload to temp file
        args_file_path: Optional[str] = None
        try:
            # Create temp file (delete=False for Windows compatibility)
            fd, args_file_path = tempfile.mkstemp(suffix=".json", prefix="nexus_args_")
            try:
                os.write(fd, payload_json.encode("utf-8"))
            finally:
                os.close(fd)

            # Build command
            cmd = self._base_cmd + ["call", tool, method, "--json-args-file", args_file_path]

            # Prepare environment
            run_env: Optional[Dict[str, str]] = None
            if self._env is not None:
                run_env = {**os.environ, **self._env}

            # Execute
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self._timeout_s,
                    cwd=self._cwd,
                    env=run_env,
                    shell=False,
                )
            except subprocess.TimeoutExpired as e:
                raise NexusOperationalError(
                    f"Command timed out after {self._timeout_s}s",
                    error_code="TIMEOUT",
                ) from e
            except FileNotFoundError as e:
                raise NexusOperationalError(
                    f"Command not found: {self._base_cmd[0]}",
                    error_code="COMMAND_NOT_FOUND",
                ) from e
            except OSError as e:
                raise NexusOperationalError(
                    f"OS error executing command: {e}",
                    error_code="OS_ERROR",
                ) from e

            # Check exit code
            if result.returncode != 0:
                raise NexusOperationalError(
                    f"Command exited with code {result.returncode}",
                    error_code="NONZERO_EXIT",
                )

            # Parse JSON output (use full stdout, not truncated)
            try:
                output = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise NexusOperationalError(
                    f"Invalid JSON output: {e}",
                    error_code="INVALID_JSON_OUTPUT",
                ) from e

            if not isinstance(output, dict):
                raise NexusOperationalError(
                    f"Output is not a JSON object: {type(output).__name__}",
                    error_code="INVALID_JSON_OUTPUT",
                )

            return output

        finally:
            # Clean up temp file
            if args_file_path is not None:
                try:
                    os.remove(args_file_path)
                except OSError:
                    pass  # Best effort cleanup

    def _truncate(self, text: str) -> str:
        """Truncate text to max_capture_chars."""
        if len(text) <= self._max_capture_chars:
            return text
        return text[: self._max_capture_chars] + f"... [truncated at {self._max_capture_chars}]"
