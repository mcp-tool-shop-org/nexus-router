#!/usr/bin/env python
"""
Test fixture: echo_tool.py

A minimal tool implementation for testing SubprocessAdapter.
Simulates various success and failure scenarios based on args.

Usage:
    python echo_tool.py call <tool> <method> --json-args-file <path>

Behavior controlled by args in the JSON payload:
    - "simulate_timeout": sleep longer than any reasonable timeout
    - "simulate_exit_code": exit with specified code
    - "simulate_invalid_json": print non-JSON output
    - "simulate_stderr": write to stderr (but still succeed)
    - Otherwise: echo back the payload as JSON
"""

from __future__ import annotations

import argparse
import json
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description="Echo tool for testing")
    subparsers = parser.add_subparsers(dest="command")

    call_parser = subparsers.add_parser("call")
    call_parser.add_argument("tool", help="Tool name")
    call_parser.add_argument("method", help="Method name")
    call_parser.add_argument("--json-args-file", required=True, help="Path to JSON args file")

    args = parser.parse_args()

    if args.command != "call":
        print(json.dumps({"error": "Unknown command", "command": args.command}))
        return 1

    # Read payload from file
    try:
        with open(args.json_args_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(json.dumps({"error": f"Failed to read args file: {e}"}))
        return 1

    tool_args = payload.get("args", {})

    # Simulate timeout
    if tool_args.get("simulate_timeout"):
        duration = tool_args.get("simulate_timeout_seconds", 3600)
        time.sleep(duration)
        return 0

    # Simulate specific exit code
    exit_code = tool_args.get("simulate_exit_code")
    if exit_code is not None:
        stderr_msg = tool_args.get("stderr_message", "Simulated error")
        print(stderr_msg, file=sys.stderr)
        return int(exit_code)

    # Simulate invalid JSON output
    if tool_args.get("simulate_invalid_json"):
        print("This is not valid JSON {{{")
        return 0

    # Simulate stderr output (but still succeed)
    if tool_args.get("simulate_stderr"):
        print(tool_args["simulate_stderr"], file=sys.stderr)

    # Success: echo back the payload with additional info
    result = {
        "success": True,
        "tool": args.tool,
        "method": args.method,
        "received_args": tool_args,
        "echo": True,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
