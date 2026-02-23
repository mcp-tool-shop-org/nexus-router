from typing import Any


def gate_apply(policy: dict[str, Any]) -> None:
    if not policy.get("allow_apply", False):
        raise PermissionError("Policy does not allow apply (allow_apply=false).")
