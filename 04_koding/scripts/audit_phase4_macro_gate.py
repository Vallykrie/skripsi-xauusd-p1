"""Check ten official calendar anchors and report K3 eligibility."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from thesis_experiments.macro_gate import audit_macro_snapshot
from thesis_experiments.protocol import load_protocol


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    protocol = load_protocol(root / "configs/phase4-experiments.toml")
    derived, report = audit_macro_snapshot(root, protocol)
    output = root / "data/interim/phase4/macro-gate"
    output.mkdir(parents=True, exist_ok=True)
    derived.to_parquet(output / "snapshot-with-utc.parquet", index=False)
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"timestamp_status": report["timestamp_status"], "vintage_status": report["vintage_status"],
                      "k3_status": report["k3_status"], "anchors_passed": sum(item["passed"] for item in report["anchors"]) }))


if __name__ == "__main__":
    main()
