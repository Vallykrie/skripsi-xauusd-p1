"""Build score-free Phase 4 target/K1/K2 artifacts from frozen row policies."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from thesis_experiments.features import build_feature_frame, evaluation_mask
from thesis_experiments.protocol import Phase4Protocol, load_protocol

_POLICIES = {
    "primary": "row_policy.parquet",
    "holiday_reset_sensitivity": "row_policy_holiday_reset_sensitivity.parquet",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_roles(protocol: Phase4Protocol) -> dict[str, str]:
    return {
        settings.name: role
        for role, settings in protocol.inputs.items()
        if role in {"primary", "sensitivity"}
    }


def _load_aligned_input(
    root: Path,
    protocol: Phase4Protocol,
    source: str,
    row_policy_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    roles = _source_roles(protocol)
    if source not in roles:
        raise ValueError(f"Unknown price source {source}")
    settings = protocol.inputs[roles[source]]
    market_path = root / settings.path
    if _sha256(market_path) != settings.sha256:
        raise ValueError(f"SHA-256 mismatch for {market_path}")
    raw = pd.read_csv(market_path)
    raw["time"] = pd.to_datetime(raw["time"], utc=True, errors="raise")
    rows = pd.read_parquet(row_policy_path)
    required = {"row_index", "time", "segment_id", "target_end_allowed"}
    if set(rows.columns) != required:
        raise ValueError(f"Malformed row policy {row_policy_path}")
    indices = rows["row_index"].to_numpy(dtype=int)
    if len(indices) and (indices.min() < 0 or indices.max() >= len(raw)):
        raise ValueError(f"Row policy indices are out of range for {market_path}")
    selected = raw.iloc[indices].reset_index(drop=True)
    rows = rows.reset_index(drop=True)
    selected_ns = selected["time"].astype("datetime64[ns, UTC]")
    policy_ns = pd.to_datetime(rows["time"], utc=True).astype("datetime64[ns, UTC]")
    if not selected_ns.equals(policy_ns):
        raise ValueError(f"Row policy timestamps do not align with {market_path}")
    return selected, rows


def _class_counts(frame: pd.DataFrame, mask: pd.Series) -> dict[str, int]:
    labels = frame.loc[mask, "target_label"].dropna().astype(str)
    return dict(sorted(Counter(labels).items()))


def _frame_summary(
    frame: pd.DataFrame,
    protocol: Phase4Protocol,
) -> dict[str, Any]:
    eligible = frame["feature_eligible"] & frame["target_eligible"]
    folds: list[dict[str, Any]] = []
    for fold in protocol.outer_folds:
        mask = evaluation_mask(frame, fold.test_start, fold.test_end)
        folds.append(
            {
                "name": fold.name,
                "eligible_rows": int(mask.sum()),
                "class_counts": _class_counts(frame, mask),
            }
        )
    return {
        "rows": len(frame),
        "feature_eligible_rows": int(frame["feature_eligible"].sum()),
        "target_eligible_rows": int(frame["target_eligible"].sum()),
        "joint_eligible_rows": int(eligible.sum()),
        "class_counts": _class_counts(frame, eligible),
        "unlabeled_joint_eligible_rows": int(
            frame.loc[eligible, "target_label"].isna().sum()
        ),
        "folds": folds,
    }


def build_full_data_feature_artifacts(
    repo_root: str | Path,
    *,
    manifest_path: str | Path = "docs/experiments/run-manifests/phase4-environment.json",
    experiment_config: str | Path = "configs/phase4-experiments.toml",
    audit_dir: str | Path = "data/interim/phase4/price-audit",
    output_dir: str | Path = "data/interim/phase4/full-data-features",
) -> dict[str, Any]:
    """Create feature/label artifacts without fitting or scoring any model."""
    root = Path(repo_root).resolve()
    manifest_file = root / manifest_path
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if manifest.get("scores_read") is not False:
        raise ValueError("Phase 4 manifest must state scores_read=false")
    protocol = load_protocol(root / experiment_config)
    audit_root = root / audit_dir
    output = (root / output_dir).resolve()
    allowed_root = (root / "data/interim/phase4").resolve()
    if output == allowed_root or allowed_root not in output.parents:
        raise ValueError("Feature output must be a child of data/interim/phase4")
    stage = Path(tempfile.mkdtemp(prefix=".full-data-features-", dir=allowed_root))
    report: dict[str, Any] = {
        "schema_version": 1,
        "scores_read": False,
        "manifest": {
            "path": Path(manifest_path).as_posix(),
            "sha256": _sha256(manifest_file),
        },
        "sources": {},
    }
    try:
        for source, audit in sorted(manifest["market_audits"].items()):
            source_report: dict[str, Any] = {}
            for policy_name, row_policy_name in _POLICIES.items():
                row_policy_path = audit_root / source / row_policy_name
                raw, rows = _load_aligned_input(
                    root, protocol, source, row_policy_path
                )
                policy_report: dict[str, Any] = {
                    "row_policy": {
                        "path": row_policy_path.relative_to(root).as_posix(),
                        "sha256": _sha256(row_policy_path),
                    },
                    "thresholds": {},
                }
                destination = stage / source / policy_name
                destination.mkdir(parents=True)
                for multiplier in protocol.labels.threshold_multipliers:
                    frame = build_feature_frame(
                        raw,
                        rows["segment_id"],
                        threshold_multiplier=multiplier,
                        target_end_allowed=rows["target_end_allowed"],
                    )
                    label = str(multiplier).replace(".", "p")
                    artifact = destination / f"features-threshold-{label}.parquet"
                    frame.to_parquet(artifact, index=False, engine="pyarrow")
                    details = _frame_summary(frame, protocol)
                    details["artifact"] = {
                        "path": artifact.relative_to(stage).as_posix(),
                        "sha256": _sha256(artifact),
                    }
                    policy_report["thresholds"][str(multiplier)] = details
                source_report[policy_name] = policy_report
            report["sources"][source] = source_report
        (stage / "summary.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        backup: Path | None = None
        if output.exists():
            backup = Path(tempfile.mkdtemp(prefix=".full-data-backup-", dir=allowed_root))
            backup.rmdir()
            os.replace(output, backup)
        try:
            os.replace(stage, output)
        except OSError:
            if backup is not None and backup.exists():
                os.replace(backup, output)
            raise
        if backup is not None:
            shutil.rmtree(backup)
        return report
    finally:
        if stage.exists():
            shutil.rmtree(stage)
