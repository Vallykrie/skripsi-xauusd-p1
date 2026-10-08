from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from thesis_experiments.features import (
    K1_COLUMNS,
    K2_COLUMNS,
    build_feature_frame,
    evaluation_mask,
    label_target_return,
)


def _ohlc_from_closes(
    closes: np.ndarray,
    *,
    start: str = "2026-01-01T00:00:00Z",
    times: pd.DatetimeIndex | None = None,
) -> pd.DataFrame:
    close = np.asarray(closes, dtype=float)
    if times is None:
        times = pd.date_range(start, periods=len(close), freq="h", tz="UTC")
    return pd.DataFrame(
        {
            "time": times,
            "open": close * np.exp(-0.002),
            "high": close * np.exp(0.003),
            "low": close * np.exp(-0.004),
            "close": close,
        }
    )


def _alternating_frame(size: int = 60) -> pd.DataFrame:
    step_returns = np.array(
        [0.01 if position % 2 else -0.01 for position in range(1, size)]
    )
    closes = 100.0 * np.exp(np.r_[0.0, np.cumsum(step_returns)])
    return _ohlc_from_closes(closes)


def test_k1_uses_current_and_five_prior_returns_with_sample_sigma():
    step_returns = np.full(59, 0.01)
    step_returns[0] = 0.02
    step_returns[43:49] = [-0.006, 0.005, -0.004, 0.003, -0.002, 0.001]
    closes = 100.0 * np.exp(np.r_[0.0, np.cumsum(step_returns)])
    result = build_feature_frame(
        _ohlc_from_closes(closes), np.zeros(60, dtype=int)
    )

    row = result.iloc[49]
    np.testing.assert_allclose(
        row[[f"return_lag_{lag}" for lag in range(6)]].to_numpy(dtype=float),
        [0.001, -0.002, 0.003, -0.004, 0.005, -0.006],
        atol=1e-14,
    )
    assert row["log_close_open"] == pytest.approx(0.002)
    assert row["log_high_low"] == pytest.approx(0.007)
    assert result.loc[24, "sigma_24"] == pytest.approx(0.01 / np.sqrt(24.0))
    assert result.loc[25, "sigma_24"] == pytest.approx(0.0, abs=1e-14)
    assert bool(row["feature_eligible"])
    assert list(result.columns[:5]) == ["time", "open", "high", "low", "close"]


def test_segment_boundary_resets_state_and_restarts_fifty_bar_warmup():
    first = _alternating_frame(55)
    second = _alternating_frame(51)
    second["time"] = pd.date_range(
        first["time"].iloc[-1] + pd.Timedelta(hours=1), periods=51, freq="h"
    )
    source = pd.concat([first, second], ignore_index=True)
    segments = np.r_[np.zeros(55, dtype=int), np.ones(51, dtype=int)]

    result = build_feature_frame(source, segments)

    assert np.isnan(result.loc[55, "return_lag_0"])
    assert not bool(result.loc[103, "feature_eligible"])
    assert bool(result.loc[104, "feature_eligible"])
    assert result.loc[104, "segment_bar_number"] == 50
    assert not bool(result.loc[54, "target_eligible"])


@pytest.mark.parametrize(
    ("closes", "expected"),
    [
        (np.full(50, 100.0), 50.0),
        (np.arange(1.0, 51.0), 100.0),
        (np.arange(50.0, 0.0, -1.0), 0.0),
    ],
)
def test_rsi_wilder_zero_cases(closes: np.ndarray, expected: float):
    result = build_feature_frame(_ohlc_from_closes(closes), np.zeros(50, dtype=int))

    assert result.loc[49, "rsi_14"] == pytest.approx(expected)


def test_rsi_uses_arithmetic_seed_then_wilder_recurrence():
    changes = np.array([1.0, -1.0] * 7 + [2.0])
    closes = 100.0 + np.r_[0.0, np.cumsum(changes)]

    result = build_feature_frame(
        _ohlc_from_closes(closes), np.zeros(len(closes), dtype=int)
    )

    assert result.loc[14, "rsi_14"] == pytest.approx(50.0)
    assert result.loc[15, "rsi_14"] == pytest.approx(56.666666666666664)


def test_macd_uses_arithmetic_seeds_before_recursive_ema():
    source = _ohlc_from_closes(np.arange(1.0, 61.0))

    result = build_feature_frame(source, np.zeros(60, dtype=int))

    assert result.loc[25, "macd_line_norm"] == pytest.approx(7.0 / 26.0)
    assert np.isnan(result.loc[25, "macd_signal_norm"])
    assert result.loc[33, "macd_line_norm"] == pytest.approx(7.0 / 34.0)
    assert result.loc[33, "macd_signal_norm"] == pytest.approx(7.0 / 34.0)
    assert result.loc[33, "macd_hist_norm"] == pytest.approx(0.0, abs=1e-15)


def test_macd_signal_uses_nonconstant_seed_and_recurrence():
    closes = np.r_[np.arange(1.0, 27.0), [28, 27, 31, 30, 34, 33, 37, 36, 40]]

    result = build_feature_frame(
        _ohlc_from_closes(closes), np.zeros(len(closes), dtype=int)
    )

    assert result.loc[33, "macd_line_norm"] == pytest.approx(
        0.21064337918498605
    )
    assert result.loc[33, "macd_signal_norm"] == pytest.approx(
        0.20096008969024234
    )
    assert result.loc[33, "macd_hist_norm"] == pytest.approx(
        0.00968328949474371
    )
    assert result.loc[34, "macd_signal_norm"] == pytest.approx(
        0.18384974289168685
    )
    assert result.loc[34, "macd_hist_norm"] == pytest.approx(
        0.011942648681874963
    )


def test_segment_reset_restarts_rsi_and_macd_from_same_initial_state():
    closes = np.r_[np.arange(1.0, 27.0), [28, 27, 31, 30, 34, 33, 37, 36, 40]]
    one_segment = _ohlc_from_closes(closes)
    repeated = pd.concat([one_segment, one_segment], ignore_index=True)
    repeated["time"] = pd.date_range(
        "2026-01-01T00:00:00Z", periods=len(repeated), freq="h", tz="UTC"
    )
    segments = np.r_[np.zeros(len(closes), dtype=int), np.ones(len(closes), dtype=int)]

    expected = build_feature_frame(
        one_segment, np.zeros(len(one_segment), dtype=int)
    )
    result = build_feature_frame(repeated, segments)

    technical = ["rsi_14", "macd_line_norm", "macd_signal_norm", "macd_hist_norm"]
    np.testing.assert_allclose(
        result.loc[len(closes) :, technical].to_numpy(dtype=float),
        expected.loc[:, technical].to_numpy(dtype=float),
        equal_nan=True,
    )


@pytest.mark.parametrize(
    ("target_return", "threshold", "expected"),
    [
        (-0.0200001, 0.02, "SELL"),
        (-0.02, 0.02, "HOLD"),
        (0.02, 0.02, "HOLD"),
        (0.0200001, 0.02, "BUY"),
    ],
)
def test_label_boundaries_match_chapter_three(
    target_return: float, threshold: float, expected: str
):
    assert label_target_return(target_return, threshold) == expected


def test_target_requires_exactly_one_hour_and_preserves_ineligible_values():
    hourly = _alternating_frame(52)
    exact = build_feature_frame(hourly, np.zeros(52, dtype=int))
    gap_times = hourly["time"].copy()
    gap_times.iloc[50:] += pd.Timedelta(hours=1)
    gap = build_feature_frame(
        hourly.assign(time=gap_times),
        np.zeros(52, dtype=int),
    )

    assert exact.loc[49, "decision_time"] == hourly.loc[49, "time"] + pd.Timedelta(
        hours=1
    )
    assert exact.loc[49, "target_end_time"] == hourly.loc[49, "time"] + pd.Timedelta(
        hours=2
    )
    assert bool(exact.loc[49, "target_eligible"])
    assert exact.loc[49, "target_return"] == pytest.approx(-0.01)
    assert not bool(gap.loc[49, "target_eligible"])
    assert gap.loc[49, "target_return"] == pytest.approx(-0.01)
    assert pd.isna(gap.loc[49, "target_label"])
    assert gap.loc[50, "return_lag_0"] == pytest.approx(-0.01)


def test_target_end_permission_is_explicit_and_does_not_drop_rows():
    source = _alternating_frame(52)
    allowed = np.ones(52, dtype=bool)
    allowed[50] = False

    result = build_feature_frame(
        source,
        np.zeros(52, dtype=int),
        target_end_allowed=allowed,
    )

    assert len(result) == len(source)
    assert not bool(result.loc[49, "target_eligible"])
    assert result.loc[49, "target_return"] == pytest.approx(-0.01)
    assert pd.isna(result.loc[49, "target_label"])


def test_threshold_multiplier_scales_sigma_and_labels_target():
    result = build_feature_frame(
        _alternating_frame(52), np.zeros(52, dtype=int), threshold_multiplier=0.25
    )

    expected_threshold = 0.25 * np.sqrt(24.0 * 0.01**2 / 23.0)
    assert result.loc[49, "target_threshold"] == pytest.approx(expected_threshold)
    assert result.loc[49, "target_label"] == "SELL"


def test_fold_mask_excludes_decisions_outside_interval_and_target_at_fold_end():
    result = build_feature_frame(_alternating_frame(55), np.zeros(55, dtype=int))
    fold_start = result.loc[49, "decision_time"]
    fold_end = result.loc[51, "decision_time"]

    mask = evaluation_mask(result, fold_start, fold_end)

    assert not bool(mask.loc[48])
    assert bool(mask.loc[49])
    assert not bool(mask.loc[50])
    assert not bool(mask.loc[51])


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda frame: frame.iloc[::-1].reset_index(drop=True), "strictly increasing"),
        (lambda frame: frame.assign(time=frame["time"].astype(str)), "UTC"),
        (lambda frame: frame.assign(close=-frame["close"]), "positive"),
        (lambda frame: frame.assign(high=frame["low"]), "OHLC"),
    ],
)
def test_invalid_market_inputs_fail_clearly(mutator, message: str):
    source = mutator(_alternating_frame(52))

    with pytest.raises(ValueError, match=message):
        build_feature_frame(source, np.zeros(52, dtype=int))


def test_duplicate_times_segment_alignment_and_multiplier_are_rejected():
    source = _alternating_frame(52)
    duplicate = source.copy()
    duplicate.loc[1, "time"] = duplicate.loc[0, "time"]

    with pytest.raises(ValueError, match="unique"):
        build_feature_frame(duplicate, np.zeros(52, dtype=int))
    with pytest.raises(ValueError, match="segment identifiers"):
        build_feature_frame(source, np.zeros(51, dtype=int))
    with pytest.raises(ValueError, match="threshold multiplier"):
        build_feature_frame(source, np.zeros(52, dtype=int), threshold_multiplier=0.0)
    with pytest.raises(ValueError, match="supported"):
        build_feature_frame(source, np.zeros(52, dtype=int), threshold_multiplier=0.75)


def test_future_ohlc_changes_cannot_change_earlier_features():
    source = _alternating_frame(70)
    changed = source.copy()
    changed.loc[60:, ["open", "high", "low", "close"]] *= 1.5

    original_result = build_feature_frame(source, np.zeros(70, dtype=int))
    changed_result = build_feature_frame(changed, np.zeros(70, dtype=int))

    pd.testing.assert_frame_equal(
        original_result.loc[:59, K2_COLUMNS],
        changed_result.loc[:59, K2_COLUMNS],
        check_exact=True,
    )
    assert tuple(K1_COLUMNS) == tuple(K2_COLUMNS[:9])
