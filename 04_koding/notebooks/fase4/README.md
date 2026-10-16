# Notebook Fase 4 — eksperimen sesuai Bab 3 final P0

Sembilan notebook ini adalah pelaksanaan resmi Fase 4, disalin dengan keluaran sel dari run resmi 16 Oktober 2026 di repo penelitian. Protokolnya mengikuti Bab 3 proposal final P0 (`../../../01_dokumentasi/P1_Dokumentasi_Bab1-3.pdf`), dan semua angka protokol dibaca dari `../../configs/phase4-p0.toml`.

| Notebook | Isi |
|---|---|
| `00_pembekuan_dan_input` | Konfigurasi beku, checksum input, catatan lingkungan dan commit |
| `01_audit_harga_dan_gap` | Pemeriksaan kualitas harga, klasifikasi 1.705 gap, 10 segmen |
| `02_label_target` | Waktu keputusan, σ24, label BUY/HOLD/SELL untuk ambang 0,5; 0,25; 1,0 |
| `03_fitur_harga_teknikal` | Fitur K1 dan RSI/MACD (K2), pemanasan mulai bar ke-51 |
| `04_fitur_makro` | Gerbang kalender (hash, 10 jangkar UTC) dan fitur makro K3 |
| `05_skema_validasi` | Masker bersama, tujuh periode uji, tiga blok validasi, purge |
| `06_pelatihan_model` | Praproses data latih, Regresi Logistik dan XGBoost, penyetelan, prediksi |
| `07_evaluasi_hasil` | Macro-F1, balanced accuracy, K2−K1, K3−K2, sensitivitas |
| `08_verifikasi` | Pencocokan dengan pipeline lama, determinisme, pembanding run lama |

## Cara menjalankan

Dari folder `04_koding/`, buat lingkungan dengan `python -m pip install -e '.[dev]' matplotlib ipykernel` (lihat `../../README.md`). Dari VS Code (ekstensi Jupyter): buka notebook, pilih kernel `.venv`, lalu *Run All*, berurutan dari 00 sampai 08. Untuk JupyterLab, pasang dulu `.venv/bin/python -m pip install jupyterlab`, lalu jalankan `.venv/bin/python -m jupyter lab notebooks/fase4`.

Notebook 06 memerlukan sekitar 20 menit untuk run penuh. Untuk mencoba cepat, isi `PERIODE_DIJALANKAN = ["2023-H1"]` dan `AMBANG_DIJALANKAN = [0.5]` di sel ketiganya. Run resmi memakai `None` untuk keduanya.

## Data dan hasil

- Input: harga MetaQuotes-Demo di `04_koding/data/research/…/market.csv` dan kalender MT5 di `04_koding/data/raw/macro_calendar/`. Repo ini privat; kedua berkas harus dihapus sebelum repo dijadikan publik. Checksum keduanya diperiksa di notebook 00.
- Semua keluaran ditulis ke `04_koding/data/interim/phase4-p0/`, yang diabaikan Git. Ringkasan hasilnya ada di `../../../05_hasil/`.
- Di luar repositori git (misalnya salinan ZIP), notebook 00 mencatat commit sebagai "tidak tersedia". Bagian notebook 08 yang membandingkan dengan run lama hanya berjalan di repo penelitian; keluaran tersimpan di notebook ini sudah memuatnya.

## Perbedaan dengan pipeline lama (`../../src/thesis_experiments`)

Atas keputusan mahasiswa (16 Oktober 2026), notebook mengikuti teks Bab 3 pada dua aturan, yaitu pemanasan mulai bar ke-51 dan purge berdasarkan waktu keputusan pertama blok. Sumber Ultima dan policy holiday-reset tidak dijalankan karena berada di luar protokol P0. Notebook 08 menunjukkan bahwa selain dua aturan itu, fitur, label, dan fitur makro identik dengan pipeline lama.
