"""Create a score-free, reproducible Phase 4 execution manifest."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from thesis_experiments.protocol import Phase4Protocol, load_protocol

_PACKAGES = (
    "numpy",
    "pandas",
    "pyarrow",
    "scikit-learn",
    "xgboost",
    "pytest",
    "ruff",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(repo_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _input_metadata(repo_root: Path, protocol: Phase4Protocol) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for role, settings in sorted(protocol.inputs.items()):
        path = repo_root / settings.path
        actual = _sha256(path)
        if actual != settings.sha256:
            raise ValueError(
                f"SHA-256 mismatch for {path}: expected {settings.sha256}, got {actual}"
            )
        result[role] = {
            "name": settings.name,
            "path": settings.path.as_posix(),
            "sha256": actual,
            "cutoff": settings.cutoff.isoformat() if settings.cutoff else None,
            "gate_status": settings.gate_status,
        }
    return result


def _audit_metadata(audit_dir: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for source_dir in sorted(path for path in audit_dir.iterdir() if path.is_dir()):
        summary_path = source_dir / "summary.json"
        if not summary_path.is_file():
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        for name, expected in summary.get("artifacts", {}).items():
            artifact = source_dir / name
            actual = _sha256(artifact)
            if actual != expected:
                raise ValueError(
                    f"Audit artifact mismatch for {artifact}: expected {expected}, got {actual}"
                )
        result[source_dir.name] = {
            "summary_path": summary_path.as_posix(),
            "summary_sha256": _sha256(summary_path),
            "rows": summary["rows"]["count"],
            "gap_count": summary["gap_count"],
            "reset_gap_count": summary["reset_gap_count"],
            "segment_count": summary["segment_count"],
            "class_counts": summary["class_counts"],
            "sensitivities": summary["sensitivities"],
            "artifacts": summary["artifacts"],
        }
    if not result:
        raise ValueError(f"No verified market-audit summaries found in {audit_dir}")
    return result


def _package_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in _PACKAGES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "NOT INSTALLED"
    return versions


def build_run_manifest(
    repo_root: str | Path,
    *,
    experiment_config: str | Path = "configs/phase4-experiments.toml",
    policy_config: str | Path = "configs/phase4-market-gaps.toml",
    audit_dir: str | Path = "data/interim/phase4/price-audit",
    require_clean: bool = True,
) -> dict[str, Any]:
    """Build a deterministic manifest without reading or reporting model scores."""
    root = Path(repo_root).resolve()
    experiment_path = root / experiment_config
    policy_path = root / policy_config
    audits_path = root / audit_dir
    protocol = load_protocol(experiment_path)
    branch = _git(root, "branch", "--show-current")
    commit = _git(root, "rev-parse", "HEAD")
    status = tuple(line for line in _git(root, "status", "--porcelain").splitlines() if line)
    if branch != protocol.experiment.branch:
        raise ValueError(f"Manifest branch mismatch: expected {protocol.experiment.branch}, got {branch}")
    if require_clean and status:
        raise ValueError("Run manifest requires a clean worktree")
    packages = _package_versions()
    return {
        "schema_version": 1,
        "phase": 4,
        "scores_read": False,
        "git": {
            "branch": branch,
            "commit": commit,
            "clean": not status,
            "dirty_entry_count": len(status),
        },
        "environment": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "packages": packages,
        },
        "protocol": {
            "name": protocol.experiment.name,
            "timezone": protocol.experiment.timezone,
            "seed": protocol.experiment.seed,
            "experiment_config": {
                "path": Path(experiment_config).as_posix(),
                "sha256": _sha256(experiment_path),
            },
            "gap_policy": {
                "path": Path(policy_config).as_posix(),
                "sha256": _sha256(policy_path),
            },
            "labels": {
                "horizon_hours": protocol.labels.horizon_hours,
                "volatility_window": protocol.labels.volatility_window,
                "threshold_multipliers": list(protocol.labels.threshold_multipliers),
                "class_order": list(protocol.labels.class_order),
            },
            "features": {
                "warmup_bars": protocol.features.warmup_bars,
                "k1": list(protocol.features.k1),
                "k2": list(protocol.features.k2),
            },
            "evaluation": {
                "inner_validation_months": protocol.inner_validation_months,
                "inner_block_months": protocol.inner_block_months,
                "purge_bars": protocol.purge_bars,
                "outer_folds": [
                    {
                        "name": fold.name,
                        "test_start": fold.test_start.isoformat(),
                        "test_end": fold.test_end.isoformat(),
                    }
                    for fold in protocol.outer_folds
                ],
            },
            "models": protocol.models,
        },
        "inputs": _input_metadata(root, protocol),
        "market_audits": _audit_metadata(audits_path),
        "commands": {
            "market_audit": ".venv/bin/python scripts/run_phase4_price_audit.py",
            "tests": ".venv/bin/python -m pytest",
            "lint": ".venv/bin/python -m ruff check .",
        },
    }


def write_run_manifest(manifest: dict[str, Any], destination: str | Path) -> None:
    """Atomically publish a canonical JSON manifest."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
