.PHONY: verify test lint typecheck build

verify: lint typecheck test build
	@echo "✓ All checks passed"

test:
	pytest --cov=nexus_router --cov-report=term-missing

lint:
	ruff check nexus_router tests
	ruff format --check .

typecheck:
	mypy nexus_router --ignore-missing-imports

build:
	python -m build --sdist --wheel
