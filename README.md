# Penilaian Kemajuan 1 (P1) — Skripsi XAUUSD

**Judul:** Analisis Kontribusi Fitur Teknikal dan Makroekonomi terhadap Kinerja Klasifikasi Arah XAUUSD Menggunakan Regresi Logistik Multinomial dan XGBoost

Repositori ini disusun khusus untuk Penilaian Kemajuan 1 (P1) agar pembimbing dapat meninjau naskah skripsi, notebook penelitian beserta hasilnya, dan perhitungan manual secara langsung dan ringkas.

## Struktur Repositori

| Folder | Isi Utama | Tautan |
|---|---|---|
| `01_Naskah_Skripsi/` | Draf naskah skripsi Bab 1–5 format resmi FILKOM UB (62 halaman; termasuk Bab 4 Implementasi dan Bab 5 Hasil) | [`Skripsi_Bab1-5_draf_2026-11-19.pdf`](01_Naskah_Skripsi/Skripsi_Bab1-5_draf_2026-11-19.pdf) |
| `02_Koding/` | Tujuh notebook penelitian (`01`–`07`), konfigurasi protokol, data input, dan 5 tabel hasil penelitian | [`02_Koding/README.md`](02_Koding/README.md) · [`02_Koding/hasil/README.md`](02_Koding/hasil/README.md) |
| `03_Perhitungan_Manual/` | Workbook Excel berumus aktif (8 tab), panduan langkah demi langkah + latihan, dan data sintetis | [`Panduan_Perhitungan_Manual.md`](03_Perhitungan_Manual/Panduan_Perhitungan_Manual.md) · [`Perhitungan_Manual_P1.xlsx`](03_Perhitungan_Manual/Perhitungan_Manual_P1.xlsx) |

## Ringkasan Hasil Utama (Ambang $0{,}5\sigma_{t,24}$, Rerata 7 Periode Uji)

Evaluasi dilakukan secara kronologis pada 7 periode uji (`2023-H1` s.d. `2026-Jan-Jul`, total 19.893 bar uji) dari 36.649 sampel bersama XAUUSD H1 *server* MetaQuotes-Demo:

| Model | K1 (Harga) | K2 (+ Teknikal) | K3 (+ Makro) | $\Delta$ K2−K1 (Positif) | $\Delta$ K3−K2 (Positif) |
|---|---:|---:|---:|---:|---:|
| Regresi Logistik Multinomial | 0,392154 | 0,392243 | 0,391609 | +0,000089 (4/7) | −0,000634 (3/7) |
| XGBoost | 0,393499 | 0,392416 | 0,392895 | −0,001083 (4/7) | +0,000479 (3/7) |
| Pembanding kelas mayoritas | 0,216652 | — | — | — | — |

Selisih dihitung berpasangan pada bar uji yang sama tanpa pembobotan jumlah bar. Kedua model konsisten melampaui pembanding kelas mayoritas (*macro-F1* sekitar 0,39 vs 0,22), sedangkan penambahan fitur teknikal maupun makroekonomi hanya menggeser rerata *macro-F1* kurang dari 0,002 dengan arah yang tidak konsisten antarperiode, antarmodel, dan antarambang. Rincian lengkap tersedia pada [`02_Koding/hasil/README.md`](02_Koding/hasil/README.md).

## Cara Menjalankan Notebook

Seluruh keluaran sel pada [`02_Koding/notebooks/`](02_Koding/notebooks/01_audit_harga_dan_gap.ipynb) sudah tersimpan sehingga kode, tabel, dan angka hasil dapat dibaca langsung di GitHub tanpa perlu dijalankan ulang. Apabila ingin menjalankan ulang secara lokal:

```bash
cd 02_Koding
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Jalankan notebook secara berurutan dari `01_audit_harga_dan_gap.ipynb` hingga `07_evaluasi_hasil.ipynb` (Notebook `06` memerlukan sekitar 16–20 menit untuk seluruh periode dan ambang; di macOS, `xgboost` memerlukan `libomp`).

## Catatan Data

Folder `02_Koding/data/` memuat data harga XAUUSD H1 dan kalender ekonomi yang diekspor dari MetaTrader 5 (*server* MetaQuotes-Demo) untuk keperluan keterulangan lokal. Repositori ini dibagikan secara privat hanya untuk keperluan bimbingan dan P1.
