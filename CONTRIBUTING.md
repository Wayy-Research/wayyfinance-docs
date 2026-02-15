# Contributing to wayyfinance-docs

## What Lives Here

This repo contains documentation, not source code. The source code for each package lives in its own repo.

**Hand-maintained** (edit directly):
- `overview/` — Ecosystem docs
- `packages/*/reference.md` — API references
- `cookbooks/` — Cross-package examples
- `guides/` — How-to guides
- `llms.txt` — LLM navigation index

**Auto-synced** (do not edit here):
- `packages/*/README.md` — Copied from source repos weekly
- `packages/*/examples/` — Copied from source repos weekly
- `versions.json` — Extracted from pyproject.toml / package.json
- `llms-full.txt` — Concatenated from all reference docs

## How to Contribute

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Run `python scripts/validate-links.py` to check links
5. Submit a PR

## Style Guide

- Use ATX headings (`#`, `##`, `###`)
- Code blocks must specify a language (```python, ```bash, ```typescript)
- All code examples should be runnable (or clearly marked as pseudocode)
- Keep reference docs in the standard format (see any `reference.md` for the template)
- Internal links use relative paths (`../guides/api-keys.md`)

## Reference Doc Template

Every `reference.md` follows this structure:

```markdown
# {Package} — API Reference
> Version: X.Y.Z | Python: 3.10+ | Install: `pip install {pkg}`

## Quick Start
## Core API
## Common Patterns
## Gotchas
## Integration
```

## Running Scripts Locally

```bash
# Validate all internal links
python scripts/validate-links.py

# Build llms-full.txt
bash scripts/build-llms-full.sh

# Extract current versions from source repos
python scripts/extract-versions.py /path/to/wayy-research/wf

# Full sync from source repos
bash scripts/sync.sh /path/to/wayy-research/wf
```
