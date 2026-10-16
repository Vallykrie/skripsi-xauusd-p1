"""Verify the 05_hasil summaries and run a bounded synthetic feature/model example."""

from __future__ import annotations

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


def skor_konfig(m, konfig, analisis):
    """K1 always uses the tuned run; in the fixed-parameter analysis K2/K3 reuse K1 parameters."""
    pilih = 'disetel' if konfig == 'K1' else analisis
    return m[(m['konfigurasi'] == konfig) & (m['analisis'] == pilih)].set_index('periode')['macro_f1']


def verify_results():
    """Recompute the paired summaries in 05_hasil from the per-period metrics."""
    hasil = REPO / '05_hasil'
    metrik = pd.read_csv(hasil / 'metrik-per-periode.csv')
    assert len(metrik) == 3 * (7 + 2 * 3 * 7 + 2 * 2 * 7), len(metrik)
    assert metrik['macro_f1'].between(0, 1).all()
    nama = {'regresi_logistik': 'Regresi Logistik', 'xgboost': 'XGBoost'}
    checked = 0
    for berkas, ambang_list, analisis in [('delta-utama.csv', [0.5], 'disetel'),
                                          ('sensitivitas-ambang.csv', [0.25, 1.0], 'disetel'),
                                          ('sensitivitas-parameter-tetap.csv', [0.5, 0.25, 1.0], 'parameter_tetap_k1')]:
        ringkas = pd.read_csv(hasil / berkas)
        if 'metrik' in ringkas:
            ringkas = ringkas[ringkas['metrik'] == 'macro_f1']
        for ambang in ambang_list:
            for model, label in nama.items():
                m = metrik[(metrik['ambang'] == ambang) & (metrik['model'] == model)]
                for kiri, kanan in (('K1', 'K2'), ('K2', 'K3')):
                    d = (skor_konfig(m, kanan, analisis) - skor_konfig(m, kiri, analisis)).dropna()
                    baris = ringkas[(ringkas['model'] == label) & (ringkas['perubahan'] == f'{kanan} − {kiri}')]
                    if 'ambang' in ringkas:
                        baris = baris[baris['ambang'] == ambang]
                    assert len(baris) == 1, (berkas, ambang, model, kiri, kanan)
                    baris = baris.iloc[0]
                    close(d.mean(), baris['rerata'])
                    close(d.median(), baris['median'])
                    close(statistics.stdev(d), baris['simpangan_baku'])
                    assert baris['periode_positif'] == f'{int((d > 0).sum())}/{len(d)}'
                    assert baris['pasangan'] == f'{len(d)}/7'
                    checked += 1
    print(f'05_hasil: {len(metrik)} baris metrik, {checked} ringkasan pasangan dihitung ulang dan cocok.')


def synthetic_smoke():
    raw = pd.read_csv(REPO / '02_perhitungan_manual/harga-sintetis.csv')
    raw['time'] = pd.to_datetime(raw['time'], utc=True)
    features = build_feature_frame(raw, [0] * len(raw))
    row = features.iloc[50]  # bar ke-51, observasi layak pertama pada contoh manual
    assert row['target_label'] == 'BUY'
    close(row['sigma_24'], 0.0010629948989485491)
    close(row['rsi_14'], 58.735724750440404)
    close(row['macd_hist_norm'], 0.000006163530420619676)
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
    verify_results()
    synthetic_smoke()
