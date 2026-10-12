#!/usr/bin/env python3
"""Freeze the score-free Phase 4 environment and input manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from thesis_experiments.run_manifest import build_run_manifest, write_run_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/experiments/run-manifests/phase4-environment.json"),
    )
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()
    manifest = build_run_manifest(args.repo_root, require_clean=not args.allow_dirty)
    output = args.output if args.output.is_absolute() else args.repo_root / args.output
    write_run_manifest(manifest, output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
