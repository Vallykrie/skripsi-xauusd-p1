# 04 · Koding: peta kode dari metode ke fungsi

Untuk memahami alurnya, mulai dari [`notebook/`](notebook/README.md): empat notebook ringkas yang hasilnya identik dengan kode di bawah.

Folder ini adalah proyek Python penelitian: `src/thesis_experiments/` (modul), `tests/` (tes portabel dengan data sintetis), `configs/` (protokol beku), `scripts/` (run dan pemeriksaan), `docs/experiments/run-manifests/` (manifes lingkungan tersanitasi). Urutan tabel mengikuti alur Bab 3. Data input privat tidak disertakan. Uraian metode: [METODOLOGI.md](METODOLOGI.md); batas reproduksi: [REPRODUKSI.md](REPRODUKSI.md).

Semua berkas di tabel berada di `src/thesis_experiments/`.

| Tahap Bab 3 | Berkas : fungsi | Yang dikerjakan |
|---|---|---|
| Protokol beku | `protocol.py : load_protocol` (baris 138) | Membaca `configs/phase4-experiments.toml`, memeriksa kontrak beku dan hash input |
| Audit harga | `gaps.py : audit_price_gaps` (134), `market_audit.py` | Membedakan jeda terjadwal dari gap tak terjelaskan; tidak ada interpolasi |
| Label | `features.py : label_target_return` (33) | q > δ → BUY, q < −δ → SELL, selainnya HOLD |
| Fitur K1/K2 | `features.py : build_feature_frame` (190), `_wilder_rsi` (106), `_seeded_ema` (138), `_macd` (149) | 9 kolom harga, + RSI dan MACD/sinyal/hist dibagi close (13 kolom); warm-up 50 bar per segmen |
| Masker evaluasi | `features.py : evaluation_mask` (266) | Bar uji yang sama untuk K1/K2/K3 dan kedua model |
| Fitur K3 | `macro_gate.py : audit_macro_snapshot` (26), `macro_features.py : add_macro_features` (21) | Join kalender hanya setelah rilis; surprise kedaluwarsa 168 jam |
| Walk-forward | `folds.py : outer_split` (31), `inner_splits` (37), `training_mask` (26) | 7 periode uji, 3 blok validasi internal 6 bulanan, purge |
| Praproses | `models.py : TrainOnlyPreprocessor` (21) | Median, indikator hilang, scaler, semuanya di-fit dari data latih saja |
| Model dan kisi | `models.py : candidates` (50), `fit_predict` (64) | Logistik lbfgs, C ∈ {0,01; 0,1; 1; 10}; XGBoost 8 kandidat |
| Pemilihan parameter | `evaluation.py : _select_candidate` (45) | Rata-rata Macro-F1 tiga blok internal; jika seri: C lebih kecil; XGBoost kedalaman, lalu iterasi, lalu learning rate lebih kecil |
| Metrik dan selisih | `evaluation.py : score` (25), `_paired` (69), `evaluate` (85) | Macro-F1, balanced accuracy, matriks BUY/HOLD/SELL, K2−K1 dan K3−K2 berpasangan |
| Jejak run | `run_manifest.py`, `full_data_features.py` | Hash input/keluaran, versi paket, ringkasan sampel |

## Hubungan dengan perhitungan manual

| Langkah di Excel / web | Padanan kode |
|---|---|
| Tab `Harga_Target`, web bab 01 | `label_target_return`, perhitungan σ24 di `build_feature_frame` |
| Tab `RSI_MACD`, web bab 02 | `_wilder_rsi`, `_seeded_ema`, `_macd` |
| Tab `Logistik`, web bab 03 | `TrainOnlyPreprocessor` + `LogisticRegression` di `fit_predict` |
| Tab `XGBoost`, web bab 04 | `XGBClassifier(objective="multi:softprob")` di `fit_predict` |
| Web bab 05 | `outer_split`, `inner_splits`, `training_mask` |
| Tab `Makro`, web bab 02 langkah 4 | `add_macro_features` |
| Tab `Evaluasi`, web bab 06 | `score` |
| Tab `Hasil_Asli`, web bab 07 | `evaluate`, `_paired` |

Perhitungan manual memakai contoh kecil (6 sampel, satu fitur, satu langkah). Produksi memakai lbfgs, kedalaman 3–5, 100–300 iterasi, subsample dan colsample 0,8, serta `tree_method="hist"` (kandidat potong dari histogram, bukan semua titik tengah seperti contoh). Contoh menjelaskan rumus; contoh tidak mereproduksi koefisien model penelitian.

## Menjalankan tes

Dari folder `04_koding/`:

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
bash scripts/verify_agents.sh
python scripts/smoke_p1.py
```

Di macOS, XGBoost memerlukan libomp (`brew install libomp`) bila belum tersedia. Windows: pakai `.venv\Scripts\python.exe`.
