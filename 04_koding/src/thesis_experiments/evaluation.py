"""Nested walk-forward evaluation with per-candidate failure records."""

from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, recall_score

from thesis_experiments.features import K1_COLUMNS, K2_COLUMNS
from thesis_experiments.folds import inner_splits, outer_split
from thesis_experiments.macro_features import MACRO_COLUMNS, NUMERIC_CODES
from thesis_experiments.models import CLASS_ORDER, candidates, fit_predict
from thesis_experiments.protocol import Phase4Protocol

FEATURE_COLUMNS = {"K1": tuple(K1_COLUMNS), "K2": tuple(K2_COLUMNS),
                   "K3": (*K2_COLUMNS, *MACRO_COLUMNS)}
CONFUSION_ORDER = ("BUY", "HOLD", "SELL")


def score(y_true: np.ndarray, y_pred: np.ndarray, *, confusion_order: tuple[str, ...] = CONFUSION_ORDER) -> dict:
    counts = {label: int(np.sum(y_true == label)) for label in CLASS_ORDER}
    return {
        "n": len(y_true),
        "class_counts": counts,
        "macro_f1": float(f1_score(y_true, y_pred, labels=CLASS_ORDER, average="macro", zero_division=0)),
        "balanced_accuracy": (
            float(recall_score(y_true, y_pred, labels=CLASS_ORDER, average="macro", zero_division=0))
            if all(counts.values()) else None
        ),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=confusion_order).tolist(),
    }


def _candidate_key(model_name: str, params: dict) -> tuple:
    if model_name == "logistic_regression":
        return (float(params["C"]),)
    return (int(params["max_depth"]), int(params["n_estimators"]), float(params["learning_rate"]))


def _select_candidate(frame: pd.DataFrame, fold, protocol: Phase4Protocol, model_name: str, columns: tuple[str, ...]) -> tuple[dict | None, list[dict]]:
    blocks = inner_splits(frame, fold, protocol)
    trials = []
    for params in candidates(protocol, model_name):
        scores = []
        failures = []
        for block in blocks:
            train, valid = frame.loc[block.train], frame.loc[block.test]
            try:
                if train.empty or valid.empty:
                    raise ValueError("Empty inner training or validation block")
                predicted, _ = fit_predict(protocol, model_name, params, train, valid, columns)
                scores.append(score(valid["target_label"].astype(str).to_numpy(), predicted)["macro_f1"])
            except (ValueError, RuntimeError, FloatingPointError) as exc:
                failures.append({"block": block.name, "reason": str(exc)})
        trials.append({"params": params, "inner_macro_f1": scores, "failures": failures,
                       "mean_macro_f1": float(np.mean(scores)) if len(scores) == len(blocks) and not failures else None})
    valid_trials = [trial for trial in trials if trial["mean_macro_f1"] is not None]
    if not valid_trials:
        return None, trials
    winner = min(valid_trials, key=lambda trial: (-trial["mean_macro_f1"], _candidate_key(model_name, trial["params"])))
    return winner["params"], trials


def _paired(results: list[dict], model_name: str, metric: str, *, fixed: bool = False,
            left: str = "K1", right: str = "K2") -> dict:
    field = "fixed_scores" if fixed else "scores"
    pairs = []
    for row in results:
        left_scores = row["models"].get(model_name, {}).get(left, {}).get(field)
        right_scores = row["models"].get(model_name, {}).get(right, {}).get(field)
        if left_scores is not None and right_scores is not None and left_scores[metric] is not None and right_scores[metric] is not None:
            pairs.append(right_scores[metric] - left_scores[metric])
    return {"total_folds": len(results), "paired_folds": len(pairs), "deltas": pairs,
            "mean": statistics.mean(pairs) if pairs else None,
            "median": statistics.median(pairs) if pairs else None,
            "sample_std": statistics.stdev(pairs) if len(pairs) > 1 else None,
            "positive_folds": sum(value > 0 for value in pairs)}


def evaluate(frame: pd.DataFrame, protocol: Phase4Protocol, *, folds: tuple | None = None) -> tuple[dict, pd.DataFrame]:
    """Evaluate frozen feature configurations on identical eligible outer test rows."""
    chosen_folds = protocol.outer_folds if folds is None else folds
    configurations = {name: columns for name, columns in FEATURE_COLUMNS.items()
                      if name != "K3" or set(MACRO_COLUMNS).issubset(frame.columns)}
    results = []
    predictions = []
    for fold in chosen_folds:
        split = outer_split(frame, fold)
        train, test = frame.loc[split.train], frame.loc[split.test]
        row = {"fold": fold.name, "train_rows": len(train), "test_rows": len(test),
               "train_end_before": split.test_start.isoformat(), "test_end": split.test_end.isoformat(), "models": {}}
        if not train.empty and not test.empty:
            counts = train["target_label"].value_counts()
            majority = min(("BUY", "HOLD", "SELL"), key=lambda label: (-counts.get(label, 0), ("BUY", "HOLD", "SELL").index(label)))
            truth = test["target_label"].astype(str).to_numpy()
            row["majority_diagnostic"] = {"train_majority_class": majority,
                                          "scores": score(truth, np.full(len(truth), majority))}
        else:
            row["majority_diagnostic"] = {"status": "NOT TESTED", "reason": "Empty train or test block"}
        for model_name in ("logistic_regression", "xgboost"):
            row["models"][model_name] = {}
            k1_params = None
            for config, columns in configurations.items():
                record: dict = {"status": "NOT TESTED", "scores": None, "fixed_scores": None}
                row["models"][model_name][config] = record
                if test.empty:
                    record["reason"] = "Empty outer test fold"
                    continue
                if config == "K3":
                    numeric_families = [code for code in NUMERIC_CODES
                                        if train[f"macro_{code.lower()}_surprise"].notna().any()
                                        and test[f"macro_{code.lower()}_surprise"].notna().any()]
                    record["numeric_families_with_train_test_coverage"] = numeric_families
                    if not numeric_families:
                        record["reason"] = "No numeric macro family covers train and test"
                        continue
                params, trials = _select_candidate(frame, fold, protocol, model_name, columns)
                record["candidates"] = trials
                if params is None:
                    record["reason"] = "No candidate passed all inner blocks"
                    continue
                try:
                    predicted, dropped = fit_predict(protocol, model_name, params, train, test, columns)
                    truth = test["target_label"].astype(str).to_numpy()
                    record.update({"status": "TESTED", "selected_params": params, "dropped_columns": dropped,
                                   "scores": score(truth, predicted)})
                    output = pd.DataFrame({"fold": fold.name, "model": model_name, "configuration": config,
                                           "time": test["time"].to_numpy(), "decision_time": test["decision_time"].to_numpy(),
                                           "target_end_time": test["target_end_time"].to_numpy(),
                                           "y_true": truth, "y_pred": predicted, "analysis": "tuned"})
                    predictions.append(output)
                    if config == "K1":
                        k1_params = params
                        record["fixed_scores"] = record["scores"]
                    elif k1_params is not None:
                        fixed_predicted, _ = fit_predict(protocol, model_name, k1_params, train, test, columns)
                        record["fixed_scores"] = score(truth, fixed_predicted)
                        predictions.append(output.assign(y_pred=fixed_predicted, analysis="fixed_k1_params"))
                except (ValueError, RuntimeError, FloatingPointError) as exc:
                    record["reason"] = str(exc)
        results.append(row)
    summary = {"folds": results, "paired": {}, "confusion_order": CONFUSION_ORDER}
    for model_name in ("logistic_regression", "xgboost"):
        summary["paired"][model_name] = {
            metric: _paired(results, model_name, metric) for metric in ("macro_f1", "balanced_accuracy")
        }
        summary["paired"][model_name]["fixed_macro_f1"] = _paired(results, model_name, "macro_f1", fixed=True)
        summary["paired"][model_name]["fixed_balanced_accuracy"] = _paired(results, model_name, "balanced_accuracy", fixed=True)
        if "K3" in configurations:
            summary["paired"][model_name]["k3_minus_k2"] = {
                metric: _paired(results, model_name, metric, left="K2", right="K3")
                for metric in ("macro_f1", "balanced_accuracy")
            }
            summary["paired"][model_name]["k3_minus_k2_fixed"] = {
                metric: _paired(results, model_name, metric, fixed=True, left="K2", right="K3")
                for metric in ("macro_f1", "balanced_accuracy")
            }
    return summary, pd.concat(predictions, ignore_index=True) if predictions else pd.DataFrame()


def verified_feature_frame(root: Path, source: str, policy: str, threshold: float) -> tuple[pd.DataFrame, dict]:
    feature_root = root / "data/interim/phase4/full-data-features"
    report = json.loads((feature_root / "summary.json").read_text(encoding="utf-8"))
    manifest_path = root / "docs/experiments/run-manifests/phase4-environment.json"
    if report["manifest"]["sha256"] != hashlib.sha256(manifest_path.read_bytes()).hexdigest():
        raise ValueError("Feature artifact was built from a different frozen manifest")
    detail = report["sources"][source][policy]["thresholds"][str(threshold)]["artifact"]
    path = feature_root / detail["path"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != detail["sha256"]:
        raise ValueError(f"Feature artifact checksum mismatch: {path}")
    return pd.read_parquet(path), {"path": path.relative_to(root).as_posix(), "sha256": digest}
