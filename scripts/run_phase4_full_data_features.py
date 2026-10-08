#!/usr/bin/env python3
"""Build score-free full-data Phase 4 target/K1/K2 artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from thesis_experiments.full_data_features import build_full_data_feature_artifacts


def main() -> int:
    report = build_full_data_feature_artifacts(Path.cwd())
    compact = {
        source: {
            policy: {
                threshold: details["joint_eligible_rows"]
                for threshold, details in policy_details["thresholds"].items()
            }
            for policy, policy_details in source_details.items()
        }
        for source, source_details in report["sources"].items()
    }
    print(json.dumps(compact, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
