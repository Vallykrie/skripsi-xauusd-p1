"""Run the frozen Phase 4 K1/K2/K3 model evaluation from audited features."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from thesis_experiments.evaluation import evaluate, verified_feature_frame
from thesis_experiments.macro_features import add_macro_features
from thesis_experiments.macro_gate import audit_macro_snapshot
from thesis_experiments.protocol import load_protocol


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="metaquotes-demo")
    parser.add_argument("--policy", default="primary")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--include-k3", action="store_true", help="Evaluate the frozen calendar snapshot under the Bab 3 operational assumption")
    parser.add_argument("--fold", help="Run one named fold for a bounded integration check")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    protocol = load_protocol(root / "configs/phase4-experiments.toml")
    manifest_path = root / "docs/experiments/run-manifests/phase4-environment.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("scores_read") is not False:
        raise ValueError("Frozen manifest must predate model scores")
    config_hash = hashlib.sha256((root / "configs/phase4-experiments.toml").read_bytes()).hexdigest()
    if config_hash != manifest["protocol"]["experiment_config"]["sha256"]:
        raise ValueError("Experiment configuration differs from frozen manifest")
    frame, source_artifact = verified_feature_frame(root, args.source, args.policy, args.threshold)
    macro_audit = None
    if args.include_k3:
        events, macro_audit = audit_macro_snapshot(root, protocol)
        if macro_audit["k3_status"] != "ELIGIBLE":
            raise ValueError("Macro timestamp anchor gate failed")
        frame = add_macro_features(frame, events)
    folds = tuple(fold for fold in protocol.outer_folds if fold.name == args.fold) if args.fold else None
    if args.fold and not folds:
        raise ValueError(f"Unknown fold: {args.fold}")
    summary, predictions = evaluate(frame, protocol, folds=folds)
    k3_tested = any(
        fold["models"][model].get("K3", {}).get("status") == "TESTED"
        for fold in summary["folds"] for model in ("logistic_regression", "xgboost")
    )
    summary.update({"source": args.source, "policy": args.policy, "threshold": args.threshold,
                    "feature_artifact": source_artifact, "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                    "k3_status": "TESTED" if k3_tested else "NOT TESTED",
                    "macro_audit": macro_audit})
    suffix = f"{args.source}-{args.policy}-{str(args.threshold).replace('.', 'p')}"
    if args.include_k3:
        suffix += "-k3"
    if args.fold:
        suffix += f"-{args.fold}"
    output = root / "data/interim/phase4/model-results" / suffix
    if output.exists():
        raise FileExistsError(f"Output already exists; preserve immutable run: {output}")
    output.mkdir(parents=True)
    if not predictions.empty:
        predictions.to_parquet(output / "predictions.parquet", index=False)
        summary["predictions_sha256"] = hashlib.sha256((output / "predictions.parquet").read_bytes()).hexdigest()
    (output / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
