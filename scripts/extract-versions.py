#!/usr/bin/env python3
"""Extract package versions from source repos and update versions.json.

Usage:
    python scripts/extract-versions.py [source_dir]

source_dir defaults to the parent of this repo (assumes sibling repos).
Parses pyproject.toml for Python packages and package.json for JS packages.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Repo name -> (package key in versions.json, config file type)
PACKAGES: dict[str, tuple[str, str]] = {
    "wrdata": ("wrdata", "pyproject"),
    "fracTime": ("fractime", "pyproject"),
    "wrtrade": ("wrtrade", "pyproject"),
    "wrchart": ("wrchart", "pyproject"),
    "wrchart-js": ("wrchart-js", "package.json"),
    "wayyDB": ("wayy-db", "pyproject"),
}

VERSION_RE = re.compile(r'^version\s*=\s*"([^"]+)"', re.MULTILINE)


def extract_pyproject_version(path: Path) -> str | None:
    """Extract version from pyproject.toml, project.toml, or setup.py."""
    for name in ("pyproject.toml", "project.toml"):
        toml_path = path / name
        if toml_path.exists():
            text = toml_path.read_text()
            match = VERSION_RE.search(text)
            if match:
                return match.group(1)
    # Fallback: check __init__.py for __version__
    for init in path.rglob("__init__.py"):
        text = init.read_text()
        match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
        if match:
            return match.group(1)
    return None


def extract_package_json_version(path: Path) -> str | None:
    """Extract version from package.json."""
    json_path = path / "package.json"
    if not json_path.exists():
        return None
    data = json.loads(json_path.read_text())
    return data.get("version")


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    if len(sys.argv) > 1:
        source_dir = Path(sys.argv[1]).resolve()
    else:
        # Default: parent of this repo (assumes sibling repos)
        source_dir = repo_root.parent

    versions_path = repo_root / "versions.json"
    if versions_path.exists():
        versions = json.loads(versions_path.read_text())
    else:
        versions = {"updated": "", "packages": {}}

    old_packages = versions.get("packages", {})
    changes: list[str] = []

    for repo_name, (pkg_key, config_type) in PACKAGES.items():
        repo_path = source_dir / repo_name
        if not repo_path.exists():
            print(f"  SKIP: {repo_name} not found at {repo_path}")
            continue

        if config_type == "pyproject":
            version = extract_pyproject_version(repo_path)
        else:
            version = extract_package_json_version(repo_path)

        if version is None:
            print(f"  SKIP: {repo_name} - no version found")
            continue

        old_version = old_packages.get(pkg_key, {}).get("version", "unknown")

        if old_version != version:
            changes.append(f"  {pkg_key}: {old_version} -> {version}")

        # Update version, preserve other fields
        if pkg_key in versions["packages"]:
            versions["packages"][pkg_key]["version"] = version
        else:
            versions["packages"][pkg_key] = {"version": version}

    versions["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    versions_path.write_text(json.dumps(versions, indent=2) + "\n")

    print(f"Updated {versions_path}")
    if changes:
        print("Changes detected:")
        for change in changes:
            print(change)
    else:
        print("No version changes detected.")


if __name__ == "__main__":
    main()
