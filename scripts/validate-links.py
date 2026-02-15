#!/usr/bin/env python3
"""Validate all internal markdown links in the repository.

Finds every markdown link [text](path) in .md files, resolves the path
relative to the file's directory, and checks that the target exists.
External URLs (http://, https://) are skipped.

Exit 0 if all links valid, exit 1 if any broken.
"""

import re
import sys
from pathlib import Path

# Matches markdown links: [text](path)
# Captures the path portion, ignoring optional anchor fragments
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

# Directories to skip
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", "examples"}

# Files to skip (synced from source repos, may have links relative to their own repo)
SKIP_PATTERNS = {"packages/*/README.md"}


def is_synced_file(path: Path, root: Path) -> bool:
    """Check if file is a synced README (from source repos)."""
    rel = path.relative_to(root)
    parts = rel.parts
    # packages/*/README.md are synced from source repos
    return (len(parts) == 3 and parts[0] == "packages" and parts[2] == "README.md")


def find_md_files(root: Path) -> list[Path]:
    """Recursively find all .md files, skipping hidden/vendor dirs and synced files."""
    files: list[Path] = []
    for path in root.rglob("*.md"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if is_synced_file(path, root):
            continue
        files.append(path)
    return sorted(files)


def validate_links(root: Path) -> list[tuple[Path, int, str, str]]:
    """Return list of (file, line_number, link_text, broken_path) tuples."""
    broken: list[tuple[Path, int, str, str]] = []

    for md_file in find_md_files(root):
        lines = md_file.read_text().splitlines()
        file_dir = md_file.parent

        for line_num, line in enumerate(lines, start=1):
            for match in LINK_RE.finditer(line):
                link_text = match.group(1)
                raw_path = match.group(2)

                # Skip external URLs
                if raw_path.startswith(("http://", "https://", "mailto:")):
                    continue

                # Skip anchor-only links
                if raw_path.startswith("#"):
                    continue

                # Strip anchor fragment from path
                target_path = raw_path.split("#")[0]

                if not target_path:
                    # Was a path with only an anchor after stripping
                    continue

                resolved = (file_dir / target_path).resolve()

                if not resolved.exists():
                    broken.append((md_file, line_num, link_text, raw_path))

    return broken


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent

    print(f"Validating internal links in {repo_root}")
    print()

    broken = validate_links(repo_root)

    if not broken:
        md_count = len(find_md_files(repo_root))
        print(f"All links valid across {md_count} markdown files.")
        sys.exit(0)

    print(f"Found {len(broken)} broken link(s):")
    print()

    for file_path, line_num, link_text, target in broken:
        relative = file_path.relative_to(repo_root)
        print(f"  {relative}:{line_num}  [{link_text}]({target})")

    print()
    print("Fix the broken links above and re-run.")
    sys.exit(1)


if __name__ == "__main__":
    main()
