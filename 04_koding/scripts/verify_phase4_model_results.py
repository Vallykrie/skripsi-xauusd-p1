"""Recompute saved model metrics and check paired prediction alignment."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from thesis_experiments.evaluation import score


def verify(output: Path) -> None:
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    prediction_path = output / "predictions.parquet"
    if hashlib.sha256(prediction_path.read_bytes()).hexdigest() != summary["predictions_sha256"]:
        raise ValueError("Prediction checksum mismatch")
    predictions = pd.read_parquet(prediction_path)
    for fold in summary["folds"]:
        name = fold["fold"]
        for model_name, configurations in fold["models"].items():
            groups = {}
            for config, record in configurations.items():
                if record["status"] != "TESTED":
                    continue
                for analysis, score_field in (("tuned", "scores"), ("fixed_k1_params", "fixed_scores")):
                    if analysis == "fixed_k1_params" and config == "K1":
                        continue
                    if record[score_field] is None:
                        continue
                    group = predictions.loc[
                        (predictions["fold"] == name) & (predictions["model"] == model_name)
                        & (predictions["configuration"] == config) & (predictions["analysis"] == analysis)
                    ].sort_values("decision_time")
                    if len(group) != fold["test_rows"]:
                        raise ValueError(f"Wrong prediction count: {name}/{model_name}/{config}/{analysis}")
                    if group["decision_time"].duplicated().any():
                        raise ValueError(f"Duplicate decisions: {name}/{model_name}/{config}/{analysis}")
                    if not group["target_end_time"].lt(pd.Timestamp(fold["test_end"])).all():
                        raise ValueError(f"Target crosses test boundary: {name}/{model_name}/{config}/{analysis}")
                    recomputed = score(
                        group["y_true"].to_numpy(), group["y_pred"].to_numpy(),
                        confusion_order=tuple(summary.get("confusion_order", ("SELL", "HOLD", "BUY"))),
                    )
                    for metric in ("macro_f1", "balanced_accuracy"):
                        saved = record[score_field][metric]
                        actual = recomputed[metric]
                        if (saved is None) != (actual is None) or (saved is not None and not np.isclose(saved, actual)):
                            raise ValueError(f"Metric mismatch: {name}/{model_name}/{config}/{analysis}/{metric}")
                    if recomputed["confusion_matrix"] != record[score_field]["confusion_matrix"]:
                        raise ValueError(f"Confusion matrix mismatch: {name}/{model_name}/{config}/{analysis}")
                    if analysis == "tuned":
                        groups[config] = group
            for left, right in (("K1", "K2"), ("K2", "K3")):
                if left in groups and right in groups:
                    for column in ("decision_time", "target_end_time", "y_true"):
                        if not groups[left][column].reset_index(drop=True).equals(groups[right][column].reset_index(drop=True)):
                            raise ValueError(f"Paired rows differ: {name}/{model_name}/{left}/{right}/{column}")
    print(f"verified {output}: {len(summary['folds'])} folds, {len(predictions)} prediction rows")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    verify(args.output)


if __name__ == "__main__":
    main()
