"""Frozen chronological boundaries and label-end purge for Phase 4."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from thesis_experiments.features import evaluation_mask
from thesis_experiments.protocol import OuterFold, Phase4Protocol


@dataclass(frozen=True)
class Split:
    name: str
    train: pd.Series
    test: pd.Series
    test_start: pd.Timestamp
    test_end: pd.Timestamp


def _eligible(frame: pd.DataFrame) -> pd.Series:
    return frame["feature_eligible"].astype(bool) & frame["target_eligible"].astype(bool)


def training_mask(frame: pd.DataFrame, boundary: pd.Timestamp) -> pd.Series:
    """Exclude labels ending at or after the first decision in the next block."""
    return _eligible(frame) & frame["target_end_time"].lt(boundary)


def outer_split(frame: pd.DataFrame, fold: OuterFold) -> Split:
    start = pd.Timestamp(fold.test_start)
    end = pd.Timestamp(fold.test_end)
    return Split(fold.name, training_mask(frame, start), evaluation_mask(frame, start, end), start, end)


def inner_splits(frame: pd.DataFrame, fold: OuterFold, protocol: Phase4Protocol) -> tuple[Split, ...]:
    end = pd.Timestamp(fold.test_start)
    start = end - pd.DateOffset(months=protocol.inner_validation_months)
    blocks = []
    for index in range(protocol.inner_validation_months // protocol.inner_block_months):
        block_start = start + pd.DateOffset(months=index * protocol.inner_block_months)
        block_end = block_start + pd.DateOffset(months=protocol.inner_block_months)
        blocks.append(Split(
            f"inner-{index + 1}",
            training_mask(frame, block_start),
            evaluation_mask(frame, block_start, block_end),
            block_start,
            block_end,
        ))
    return tuple(blocks)
