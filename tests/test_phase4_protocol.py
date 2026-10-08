from pathlib import Path

import pandas as pd
import pytest

from thesis_experiments.protocol import (
    EXPECTED_FEATURES,
    audit_market_input,
    load_protocol,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_repository_protocol_matches_frozen_chapter_three():
    protocol = load_protocol(REPO_ROOT / "configs/phase4-experiments.toml")

    assert protocol.experiment.branch == "research/phase-4-experiments"
    assert protocol.experiment.seed == 42
    assert protocol.labels.horizon_hours == 1
    assert protocol.labels.volatility_window == 24
    assert protocol.labels.threshold_multipliers == (0.5, 0.25, 1.0)
    assert protocol.features.warmup_bars == 50
    assert protocol.features.k1 == EXPECTED_FEATURES["K1"]
    assert protocol.features.k2 == EXPECTED_FEATURES["K2"]
    assert len(protocol.outer_folds) == 7
    assert protocol.outer_folds[0].test_start.isoformat() == "2023-01-01T00:00:00+00:00"
    assert protocol.outer_folds[-1].test_end.isoformat() == "2026-08-01T00:00:00+00:00"
    assert protocol.inner_validation_months == 18
    assert protocol.inner_block_months == 6


def test_market_audit_verifies_checksum_and_schema(tmp_path):
    market_path = tmp_path / "market.csv"
    market_path.write_text(
        "time,open,high,low,close,tick_volume,spread,real_volume\n"
        "2026-01-01 00:00:00+00:00,1,2,0.5,1.5,10,2,0\n"
        "2026-01-01 01:00:00+00:00,1.5,2,1,1.8,11,2,0\n",
        encoding="utf-8",
    )

    import hashlib

    checksum = hashlib.sha256(market_path.read_bytes()).hexdigest()
    audit = audit_market_input(market_path, checksum)

    assert audit.row_count == 2
    assert audit.first_timestamp == pd.Timestamp("2026-01-01T00:00:00Z")
    assert audit.last_timestamp == pd.Timestamp("2026-01-01T01:00:00Z")
    assert audit.duplicate_timestamps == 0
    assert audit.non_monotonic_timestamps == 0
    assert audit.missing_values == 0
    assert audit.invalid_ohlc_rows == 0


def test_market_audit_rejects_checksum_mismatch(tmp_path):
    market_path = tmp_path / "market.csv"
    market_path.write_text("time,open,high,low,close,tick_volume,spread,real_volume\n")

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        audit_market_input(market_path, "0" * 64)


def test_market_audit_rejects_missing_columns(tmp_path):
    market_path = tmp_path / "market.csv"
    market_path.write_text("time,open,close\n2026-01-01T00:00:00Z,1,1\n")

    import hashlib

    checksum = hashlib.sha256(market_path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="Missing market columns"):
        audit_market_input(market_path, checksum)
