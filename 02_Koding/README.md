# 02 · Koding Penelitian

Folder ini memuat alur kode penelitian dari pemeriksaan data mentah hingga evaluasi hasil akhir sesuai rancangan Bab 3 dan Bab 4 pada [`Skripsi_Bab1-4_draf_2026-11-26.pdf`](../01_Naskah_Skripsi/Skripsi_Bab1-4_draf_2026-11-26.pdf). Seluruh keluaran sel pada notebook `01`–`07` telah tersimpan sehingga dapat ditinjau langsung maupun dijalankan ulang.

## Pemetaan Notebook ke Naskah Skripsi

| Notebook | Isi Langkah Penelitian | Subbab Skripsi |
|---|---|---|
| [`01_audit_harga_dan_gap.ipynb`](notebooks/01_audit_harga_dan_gap.ipynb) | Pemeriksaan data harga H1, pengelompokan 1.705 celah data, dan pembentukan 10 segmen indikator | 3.6.1, 4.2.1 |
| [`02_label_target.ipynb`](notebooks/02_label_target.ipynb) | Penentuan waktu keputusan $\tau_t$, volatilitas $\sigma_{24}$, dan pelabelan BUY/HOLD/SELL (ambang 0,5; 0,25; 1,0) | 4.2.2, 4.3.2 |
| [`03_fitur_harga_teknikal.ipynb`](notebooks/03_fitur_harga_teknikal.ipynb) | Pembentukan 9 fitur harga (K1) serta 4 fitur RSI(14) dan MACD (K2); kelayakan mulai bar ke-51 per segmen | 4.2.3, 4.3.2–4.3.3 |
| [`04_fitur_makro.ipynb`](notebooks/04_fitur_makro.ipynb) | Validasi waktu kalender MT5 (10 jangkar UTC lintas DST) dan pembentukan 46 fitur makro (K3 = 59 kolom) | 3.6.2, 4.2.3, 4.3.4 |
| [`05_skema_validasi.ipynb`](notebooks/05_skema_validasi.ipynb) | Pembentukan himpunan sampel bersama (36.649 bar), 7 periode uji, 3 blok validasi internal, dan aturan *purge* | 3.6.3, 4.2.4, 4.4 |
| [`06_pelatihan_model.ipynb`](notebooks/06_pelatihan_model.ipynb) | Standardisasi/imputasi data latih, *tuning* *hyperparameter*, pelatihan Regresi Logistik Multinomial dan XGBoost | 4.2.4, 4.3.5–4.3.6, 4.4 |
| [`07_evaluasi_hasil.ipynb`](notebooks/07_evaluasi_hasil.ipynb) | Perhitungan *macro-F1*, *balanced accuracy*, perubahan berpasangan K2−K1 dan K3−K2, *confusion matrix*, serta sensitivitas | 4.2.5, 4.3.7, 4.4 |

## Struktur Isi `02_Koding/`

| Folder / Berkas | Kegunaan |
|---|---|
| `notebooks/` | Tujuh notebook berurutan (`01`–`07`) sebagai pelaksana utama protokol Bab 3 |
| `configs/` | Parameter penelitian beku ([`phase4-p0.toml`](configs/phase4-p0.toml)) dan jadwal perdagangan untuk klasifikasi celah ([`phase4-market-gaps.toml`](configs/phase4-market-gaps.toml)) |
| `data/` | Data input mentah XAUUSD H1 MetaQuotes-Demo (`market.csv`) dan kalender ekonomi MT5 (`mt5-economic-calendar-2020-2026.csv`) |
| `hasil/` | Lima berkas CSV ringkasan keluaran Notebook `07` beserta [`README.md`](hasil/README.md) |
| `requirements.txt` | Daftar pustaka Python yang diperlukan untuk menjalankan notebook |

## Menjalankan Ulang Notebook

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Buka folder `notebooks/` dan jalankan berurutan dari `01` hingga `07`. Keluaran perantara akan ditulis ke `data/interim/phase4-p0/` (otomatis diabaikan Git). Untuk uji cepat Notebook `06`, isi `PERIODE_DIJALANKAN = ["2023-H1"]` dan `AMBANG_DIJALANKAN = [0.5]` pada sel ketiga (run penuh menggunakan `None` untuk keduanya dan memakan waktu sekitar 16–20 menit). Di macOS, pustaka `xgboost` membutuhkan `libomp` (`brew install libomp`) apabila belum terpasang.
