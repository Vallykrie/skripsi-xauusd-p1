# 04 · Koding

**Mulai dari [`notebooks/fase4/`](notebooks/fase4/README.md).** Sembilan notebook berurutan adalah pelaksanaan resmi eksperimen Fase 4, dari audit data sampai evaluasi. Setiap notebook menjelaskan langkahnya dalam bahasa Indonesia dan menyebut subbab Bab 3 yang dipenuhi. Keluaran sel dari run resmi 16 Oktober 2026 sudah tersimpan, jadi notebook bisa dibaca tanpa dijalankan.

| Folder | Isi |
|---|---|
| `notebooks/fase4/` | **Eksperimen resmi**: notebook 00–08 |
| `configs/phase4-p0.toml` | Konfigurasi beku run resmi (dibekukan sebelum skor dibaca) |
| `configs/phase4-market-gaps.toml` | Jadwal sesi MetaQuotes dan libur CME untuk audit gap |
| `data/` | Input vendor: harga XAUUSD H1 MetaQuotes-Demo dan kalender MT5 (repo privat) |
| `src/thesis_experiments/`, `tests/`, `scripts/` | Pipeline lama (run 21–22 September), dipakai notebook 08 sebagai pembanding dan oleh tes portabel |
| `configs/phase4-experiments.toml`, `docs/experiments/` | Konfigurasi dan manifes pipeline lama |

Uraian metode: [METODOLOGI.md](METODOLOGI.md). Batas reproduksi: [REPRODUKSI.md](REPRODUKSI.md).

## Notebook dan Bab 3

| Notebook | Isi | Bab 3 |
|---|---|---|
| 00 | Konfigurasi beku, checksum input, catatan lingkungan | 3.3, 3.4, 3.12 |
| 01 | Audit harga, klasifikasi 1.705 gap, 10 segmen | 3.6.1 |
| 02 | Waktu keputusan, σ24, label BUY/HOLD/SELL (ambang 0,5; 0,25; 1,0) | 3.5 |
| 03 | Fitur harga K1 dan RSI/MACD K2; pemanasan mulai bar ke-51 | 3.7.1, 3.7.2 |
| 04 | Gerbang kalender (hash, 10 jangkar UTC) dan fitur makro K3 | 3.6.2, 3.7.3 |
| 05 | Masker bersama, tujuh periode uji, tiga blok validasi, purge | 3.9.1, 3.9.2 |
| 06 | Praproses data latih, Regresi Logistik dan XGBoost, penyetelan, prediksi | 3.9.2–3.9.4 |
| 07 | Macro-F1, balanced accuracy, K2−K1, K3−K2, sensitivitas | 3.10 |
| 08 | Verifikasi terhadap pipeline lama dan determinisme | 3.12 |

## Hubungan dengan perhitungan manual

| Langkah di Excel / web | Notebook |
|---|---|
| Tab `Harga_Target`, web bab 01 | 02 (σ24, δ, label) |
| Tab `RSI_MACD`, web bab 02 | 03 (`rsi_wilder`, `ema`, `macd`) |
| Tab `Makro`, web bab 02 langkah 4 | 04 |
| Web bab 05 | 05 (periode uji, blok validasi, purge) |
| Tab `Logistik` dan `XGBoost`, web bab 03–04 | 06 (`Praproses`, `latih_prediksi`, `setel`) |
| Tab `Evaluasi`, web bab 06 | 07 |
| Tab `Hasil_Asli`, web bab 07 | 07 (tabel utama dan selisih berpasangan) |

Perhitungan manual memakai contoh kecil (6 sampel, satu fitur, satu langkah). Model penelitian memakai lbfgs, kedalaman 3–5, 100–300 iterasi, subsample dan colsample 0,8, serta `tree_method="hist"`. Contoh menjelaskan rumus; contoh tidak mereproduksi koefisien model penelitian.

## Menjalankan

Dari folder `04_koding/`:

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -e '.[dev]' matplotlib ipykernel nbformat
python -m pytest
python -m ruff check .
bash scripts/verify_agents.sh
python scripts/smoke_p1.py
```

Lalu buka `notebooks/fase4/` di VS Code dengan kernel `.venv` dan jalankan 00 sampai 08 berurutan. Notebook 06 memerlukan sekitar 16 menit. Di macOS, XGBoost memerlukan libomp (`brew install libomp`) bila belum tersedia. Windows: pakai `.venv\Scripts\python.exe`.
