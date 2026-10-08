#!/usr/bin/env python3
"""Run the frozen Phase 4 source-specific XAUUSD H1 price-gap audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from thesis_experiments.market_audit import run_market_audits


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--experiment-config",
        type=Path,
        default=Path("configs/phase4-experiments.toml"),
    )
    parser.add_argument(
        "--policy-config",
        type=Path,
        default=Path("configs/phase4-market-gaps.toml"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/interim/phase4/price-audit"),
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    summaries = run_market_audits(
        args.experiment_config,
        args.policy_config,
        args.output_dir,
    )
    report = {
        source: {
            "rows": summary["rows"]["count"],
            "gap_count": summary["gap_count"],
            "reset_gap_count": summary["reset_gap_count"],
            "segment_count": summary["segment_count"],
            "summary": str(args.output_dir / source / "summary.json"),
        }
        for source, summary in summaries.items()
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
