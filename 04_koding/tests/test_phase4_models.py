from __future__ import annotations

import numpy as np
import pandas as pd

from thesis_experiments.evaluation import _paired, score
from thesis_experiments.folds import inner_splits, outer_split
from thesis_experiments.models import TrainOnlyPreprocessor, candidates
from thesis_experiments.protocol import load_protocol


def _protocol():
    return load_protocol("configs/phase4-experiments.toml")


def test_frozen_inner_boundaries_and_label_end_purge():
    protocol = _protocol()
    times = pd.to_datetime(["2021-07-01T00:00:00Z", "2022-12-31T22:00:00Z", "2023-01-01T00:00:00Z"])
    frame = pd.DataFrame({"decision_time": times, "target_end_time": times + pd.Timedelta(hours=1),
                          "feature_eligible": True, "target_eligible": True})
    outer = outer_split(frame, protocol.outer_folds[0])
    assert outer.train.tolist() == [True, True, False]
    assert outer.test.tolist() == [False, False, True]
    inner = inner_splits(frame, protocol.outer_folds[0], protocol)
    assert [(block.test_start.isoformat(), block.test_end.isoformat()) for block in inner] == [
        ("2021-07-01T00:00:00+00:00", "2022-01-01T00:00:00+00:00"),
        ("2022-01-01T00:00:00+00:00", "2022-07-01T00:00:00+00:00"),
        ("2022-07-01T00:00:00+00:00", "2023-01-01T00:00:00+00:00"),
    ]


def test_preprocessor_learns_only_training_columns_and_medians():
    train = pd.DataFrame({"known": [1.0, np.nan, 3.0], "empty": [np.nan] * 3})
    test = pd.DataFrame({"known": [1000.0, np.nan], "empty": [20.0, 30.0]})
    prep = TrainOnlyPreprocessor(scale=False).fit(train)
    assert prep.dropped == ["empty"]
    assert prep.indicators == ["known"]
    assert prep.transform(test).tolist() == [[1000.0, 0.0], [2.0, 1.0]]


def test_frozen_grids_and_three_class_metric_semantics():
    protocol = _protocol()
    assert len(candidates(protocol, "logistic_regression")) == 4
    assert len(candidates(protocol, "xgboost")) == 8
    metrics = score(np.array(["BUY", "HOLD"]), np.array(["BUY", "BUY"]))
    assert metrics["balanced_accuracy"] is None
    assert metrics["confusion_matrix"] == [[1, 0, 0], [1, 0, 0], [0, 0, 0]]


def test_paired_summary_keeps_failed_fold_in_denominator():
    rows = [
        {"models": {"logistic_regression": {"K1": {"scores": {"macro_f1": 0.2}}, "K2": {"scores": {"macro_f1": 0.3}}}}},
        {"models": {"logistic_regression": {"K1": {"scores": None}, "K2": {"scores": None}}}},
    ]
    result = _paired(rows, "logistic_regression", "macro_f1")
    assert result["total_folds"] == 2
    assert result["paired_folds"] == 1
    assert result["positive_folds"] == 1
