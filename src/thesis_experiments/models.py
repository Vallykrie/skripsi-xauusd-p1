"""Train-only preprocessing and frozen Phase 4 model grids."""

from __future__ import annotations

import warnings
from itertools import product

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from thesis_experiments.protocol import Phase4Protocol

CLASS_ORDER = ("SELL", "HOLD", "BUY")
CLASS_IDS = {label: index for index, label in enumerate(CLASS_ORDER)}


class TrainOnlyPreprocessor:
    def __init__(self, *, scale: bool):
        self.scale = scale

    def fit(self, frame: pd.DataFrame) -> TrainOnlyPreprocessor:
        self.kept = [column for column in frame if frame[column].notna().any()]
        self.dropped = [column for column in frame if column not in self.kept]
        if not self.kept:
            raise ValueError("All feature columns are missing in training")
        self.medians = frame[self.kept].median().astype(float)
        self.indicators = [column for column in self.kept if frame[column].isna().any()]
        matrix = self._matrix(frame)
        self.scaler = StandardScaler().fit(matrix) if self.scale else None
        return self

    def _matrix(self, frame: pd.DataFrame) -> np.ndarray:
        values = frame[self.kept].fillna(self.medians).to_numpy(dtype=float)
        indicators = frame[self.indicators].isna().to_numpy(dtype=float)
        return np.column_stack((values, indicators))

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        matrix = self._matrix(frame)
        if self.scaler is not None:
            matrix = self.scaler.transform(matrix)
        if not np.isfinite(matrix).all():
            raise ValueError("Nonfinite values remain after train-only preprocessing")
        return matrix


def candidates(protocol: Phase4Protocol, model_name: str) -> list[dict[str, float | int]]:
    settings = protocol.models[model_name]
    if model_name == "logistic_regression":
        return [{"C": value} for value in settings["c_values"]]
    if model_name == "xgboost":
        return [
            {"max_depth": depth, "n_estimators": count, "learning_rate": rate}
            for depth, count, rate in product(
                settings["max_depth"], settings["n_estimators"], settings["learning_rate"]
            )
        ]
    raise ValueError(f"Unknown model: {model_name}")


def fit_predict(
    protocol: Phase4Protocol,
    model_name: str,
    params: dict[str, float | int],
    train: pd.DataFrame,
    test: pd.DataFrame,
    columns: tuple[str, ...],
) -> tuple[np.ndarray, list[str]]:
    labels = train["target_label"].astype(str).to_numpy()
    if set(labels) != set(CLASS_ORDER):
        raise ValueError("Training fold does not contain all three classes")
    prep = TrainOnlyPreprocessor(
        scale=model_name == "logistic_regression" or any(column.startswith("macro_") for column in columns)
    ).fit(train[list(columns)])
    x_train = prep.transform(train[list(columns)])
    x_test = prep.transform(test[list(columns)])
    y_train = np.array([CLASS_IDS[label] for label in labels], dtype=int)
    counts = np.bincount(y_train, minlength=3)
    weights = len(y_train) / (3 * counts[y_train])
    if model_name == "logistic_regression":
        settings = protocol.models[model_name]
        model = LogisticRegression(
            C=float(params["C"]), solver="lbfgs",
            max_iter=int(settings["max_iter"]), class_weight="balanced",
        )
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            model.fit(x_train, y_train)
    else:
        settings = protocol.models[model_name]
        model = XGBClassifier(
            objective="multi:softprob", num_class=3, max_depth=int(params["max_depth"]),
            n_estimators=int(params["n_estimators"]), learning_rate=float(params["learning_rate"]),
            subsample=float(settings["subsample"]), colsample_bytree=float(settings["colsample_bytree"]),
            reg_lambda=float(settings["reg_lambda"]), random_state=protocol.experiment.seed,
            n_jobs=1, tree_method="hist", eval_metric="mlogloss",
        )
        model.fit(x_train, y_train, sample_weight=weights)
    predicted = np.asarray(model.predict(x_test), dtype=int)
    return np.asarray(CLASS_ORDER)[predicted], prep.dropped
