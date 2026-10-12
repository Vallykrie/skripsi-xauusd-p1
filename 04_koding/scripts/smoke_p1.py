"""Verify public aggregates and run a bounded synthetic feature/model example."""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / 'src'))

from thesis_experiments.features import K1_COLUMNS, build_feature_frame
from thesis_experiments.models import fit_predict
from thesis_experiments.protocol import load_protocol


def close(actual, expected):
    if expected is None:
        assert actual is None
    else:
        assert np.isclose(actual, expected, rtol=0, atol=1e-12), (actual, expected)


def from_matrix(record):
    matrix = np.array(record['confusion_matrix'], dtype=float)
    tp = np.diag(matrix)
    row, col = matrix.sum(axis=1), matrix.sum(axis=0)
    f1 = np.divide(2 * tp, row + col, out=np.zeros(3), where=(row + col) > 0)
    recall = tp / row if (row > 0).all() else None
    close(f1.mean(), record['macro_f1'])
    close(float(recall.mean()) if recall is not None else None, record['balanced_accuracy'])
    assert int(matrix.sum()) == record['n']


def verify_aggregates():
    checked = 0
    files = sorted((REPO / '05_hasil/run').glob('*-0p*.json')) + sorted((REPO / '05_hasil/run').glob('*-1p0*.json'))
    assert len(files) == 24, len(files)
    for path in files:
        summary = json.loads(path.read_text())
        for fold in summary['folds']:
            for configs in fold['models'].values():
                for rec in configs.values():
                    for field in ('scores', 'fixed_scores'):
                        if rec.get(field) is not None:
                            from_matrix(rec[field])
                            counts = rec[field]['class_counts']
                            assert np.array(rec[field]['confusion_matrix']).sum(axis=1).tolist() == [counts[c] for c in summary['confusion_order']]
                            checked += 1
        for model, pairs in summary['paired'].items():
            for field, left, right, fixed in [('macro_f1', 'K1', 'K2', False), ('balanced_accuracy', 'K1', 'K2', False), ('fixed_macro_f1', 'K1', 'K2', True), ('fixed_balanced_accuracy', 'K1', 'K2', True)]:
                verify_pair(summary, model, pairs[field], field.replace('fixed_', ''), left, right, fixed)
            for key, fixed in [('k3_minus_k2', False), ('k3_minus_k2_fixed', True)]:
                if key in pairs:
                    for metric in ('macro_f1', 'balanced_accuracy'):
                        verify_pair(summary, model, pairs[key][metric], metric, 'K2', 'K3', fixed)
    print(f'24 run agregat: {checked} matriks/metrik cocok; ringkasan pasangan cocok.')


def verify_pair(summary, model, paired, metric, left, right, fixed):
    field = 'fixed_scores' if fixed else 'scores'
    deltas = []
    for fold in summary['folds']:
        cfg = fold['models'][model]
        a, b = cfg.get(left, {}).get(field), cfg.get(right, {}).get(field)
        if a and b and a[metric] is not None and b[metric] is not None:
            deltas.append(b[metric] - a[metric])
    assert paired['total_folds'] == 7
    assert paired['paired_folds'] == len(deltas)
    assert np.allclose(deltas, paired['deltas'], rtol=0, atol=1e-12)
    close(statistics.mean(deltas) if deltas else None, paired['mean'])
    close(statistics.median(deltas) if deltas else None, paired['median'])
    close(statistics.stdev(deltas) if len(deltas) > 1 else None, paired['sample_std'])
    assert paired['positive_folds'] == sum(x > 0 for x in deltas)


def synthetic_smoke():
    raw = pd.read_csv(REPO / '02_perhitungan_manual/harga-sintetis.csv')
    raw['time'] = pd.to_datetime(raw['time'], utc=True)
    features = build_feature_frame(raw, [0] * len(raw))
    row = features.iloc[49]
    assert row['target_label'] == 'HOLD'
    close(row['sigma_24'], 0.0010630483439471705)
    close(row['rsi_14'], 61.234879339527616)
    close(row['macd_hist_norm'], 0.000029190170120937428)
    eligible = features.loc[features.feature_eligible & features.target_eligible].copy()
    assert set(eligible.target_label) == {'BUY', 'HOLD', 'SELL'}
    # Only a plumbing check: small synthetic train/test, no reported research score.
    train, test = eligible.iloc[:8], eligible.iloc[8:]
    protocol = load_protocol(ROOT / 'configs/phase4-experiments.toml')
    for model, params in [('logistic_regression', {'C': 0.01}), ('xgboost', {'max_depth': 3, 'n_estimators': 100, 'learning_rate': 0.05})]:
        predicted, _ = fit_predict(protocol, model, params, train, test, tuple(K1_COLUMNS))
        assert len(predicted) == len(test)
        assert set(predicted) <= {'BUY', 'HOLD', 'SELL'}
    print('SINTETIS: fitur, label, Logistik dan XGBoost dapat berjalan. Bukan eksperimen utama.')


if __name__ == '__main__':
    verify_aggregates()
    synthetic_smoke()
