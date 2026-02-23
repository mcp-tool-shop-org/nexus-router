from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import jsonschema


def load_schema(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    return cast(dict[str, Any], json.loads(p.read_text(encoding="utf-8")))


def validate(instance: dict[str, Any], schema: dict[str, Any]) -> None:
    jsonschema.validate(instance=instance, schema=schema)
