#!/usr/bin/env python3
"""
Export the adapter template to a new directory with customized names.

Usage:
    python scripts/export_adapter_template.py my-adapter --kind redis
    python scripts/export_adapter_template.py my-adapter --kind redis --org my-github-org
    python scripts/export_adapter_template.py my-adapter --kind redis --output /path/to/output

This script:
1. Copies templates/adapter-template/ to the target directory
2. Renames files and directories (nexus_router_adapter_example -> nexus_router_adapter_{kind})
3. Rewrites placeholders in all files
4. Prints next steps
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path


# Files to skip during copy
SKIP_PATTERNS = [
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "*.egg-info",
]


def should_skip(path: Path) -> bool:
    """Check if path should be skipped."""
    name = path.name
    for pattern in SKIP_PATTERNS:
        if pattern.startswith("*"):
            if name.endswith(pattern[1:]):
                return True
        elif name == pattern:
            return True
    return False


def to_package_name(kind: str) -> str:
    """Convert kind to Python package name (underscores)."""
    return kind.replace("-", "_").lower()


def to_project_name(kind: str) -> str:
    """Convert kind to project name (hyphens)."""
    return kind.replace("_", "-").lower()


def replace_in_file(filepath: Path, replacements: dict[str, str]) -> None:
    """Replace all occurrences in a file."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Skip binary files
        return

    original = content
    for old, new in replacements.items():
        content = content.replace(old, new)

    if content != original:
        filepath.write_text(content, encoding="utf-8")


def export_template(
    kind: str,
    output_dir: Path,
    org: str = "YOUR-ORG",
    author_name: str = "Your Name",
    author_email: str = "your.email@example.com",
) -> None:
    """Export and customize the adapter template."""
    # Find template directory
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    template_dir = repo_root / "templates" / "adapter-template"

    if not template_dir.exists():
        print(f"Error: Template directory not found: {template_dir}", file=sys.stderr)
        sys.exit(1)

    # Derived names
    pkg_name = to_package_name(kind)  # e.g., "redis" or "my_adapter"
    proj_name = to_project_name(kind)  # e.g., "redis" or "my-adapter"
    class_name = "".join(word.title() for word in kind.replace("-", "_").split("_"))  # e.g., "Redis"

    # Check output doesn't exist
    if output_dir.exists():
        print(f"Error: Output directory already exists: {output_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Exporting adapter template...")
    print(f"  Kind: {kind}")
    print(f"  Package: nexus_router_adapter_{pkg_name}")
    print(f"  Project: nexus-router-adapter-{proj_name}")
    print(f"  Output: {output_dir}")
    print()

    # Copy template
    def ignore_fn(directory: str, files: list[str]) -> list[str]:
        return [f for f in files if should_skip(Path(directory) / f)]

    shutil.copytree(template_dir, output_dir, ignore=ignore_fn)

    # Rename src directory
    old_src = output_dir / "src" / "nexus_router_adapter_example"
    new_src = output_dir / "src" / f"nexus_router_adapter_{pkg_name}"
    if old_src.exists():
        old_src.rename(new_src)

    # Define replacements
    replacements = {
        # Package/module names
        "nexus_router_adapter_example": f"nexus_router_adapter_{pkg_name}",
        "nexus-router-adapter-example": f"nexus-router-adapter-{proj_name}",
        "nexus-router-adapter-{kind}": f"nexus-router-adapter-{proj_name}",
        "nexus_router_adapter_{kind}": f"nexus_router_adapter_{pkg_name}",
        # Class names
        "ExampleAdapter": f"{class_name}Adapter",
        # Kind placeholders
        'ADAPTER_KIND = "example"': f'ADAPTER_KIND = "{pkg_name}"',
        '"kind": "example"': f'"kind": "{pkg_name}"',
        "{kind}": proj_name,
        "{Kind}": class_name,
        # Org
        "YOUR-ORG": org,
        # Author (in pyproject.toml)
        "Your Name": author_name,
        "your.email@example.com": author_email,
    }

    # Apply replacements to all files
    for filepath in output_dir.rglob("*"):
        if filepath.is_file() and not should_skip(filepath):
            replace_in_file(filepath, replacements)

    print("Template exported successfully!")
    print()
    print("Next steps:")
    print(f"  1. cd {output_dir}")
    print("  2. Edit pyproject.toml:")
    print("     - Update description")
    print("     - Add your dependencies")
    print("     - Update author info")
    print("  3. Implement your adapter in src/nexus_router_adapter_{}/".format(pkg_name))
    print("  4. Run tests: pip install -e '.[dev]' && pytest -v")
    print("  5. Initialize git: git init && git add . && git commit -m 'initial'")
    print()
    print("Validation:")
    print("  from nexus_router.plugins import inspect_adapter")
    print(f'  result = inspect_adapter("nexus_router_adapter_{pkg_name}:create_adapter")')
    print("  print(result.render())")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export nexus-router adapter template with customized names.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s my-redis-adapter --kind redis
  %(prog)s kafka-adapter --kind kafka --org acme-corp
  %(prog)s grpc --kind grpc --output /tmp/my-adapter
        """,
    )
    parser.add_argument(
        "name",
        help="Adapter name (used for output directory if --output not specified)",
    )
    parser.add_argument(
        "--kind",
        required=True,
        help="Adapter kind (e.g., 'redis', 'kafka', 'grpc'). Used for class/module names.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output directory (default: ./nexus-router-adapter-{kind})",
    )
    parser.add_argument(
        "--org",
        default="YOUR-ORG",
        help="GitHub organization name for badge URLs (default: YOUR-ORG)",
    )
    parser.add_argument(
        "--author",
        default="Your Name",
        help="Author name for pyproject.toml",
    )
    parser.add_argument(
        "--email",
        default="your.email@example.com",
        help="Author email for pyproject.toml",
    )

    args = parser.parse_args()

    # Determine output directory
    kind = to_project_name(args.kind)
    if args.output:
        output_dir = args.output
    else:
        output_dir = Path.cwd() / f"nexus-router-adapter-{kind}"

    export_template(
        kind=args.kind,
        output_dir=output_dir,
        org=args.org,
        author_name=args.author,
        author_email=args.email,
    )


if __name__ == "__main__":
    main()
