import jsonschema
import pytest

from nexus_router.tool import run


def test_missing_goal_rejected():
    with pytest.raises(jsonschema.ValidationError):
        run({"mode": "dry_run"})


def test_invalid_mode_rejected():
    with pytest.raises(jsonschema.ValidationError):
        run({"goal": "test", "mode": "invalid_mode"})
