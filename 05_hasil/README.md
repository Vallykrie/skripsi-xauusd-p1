# 05 · Hasil eksperimen Fase 4

Sumber: run notebook `04_koding/notebooks/fase4/` (16 Oktober 2026), data XAUUSD H1 MetaQuotes-Demo, protokol Bab 3 final P0. Tabel CSV di folder ini adalah salinan keluaran notebook 07 dan dihitung ulang oleh `04_koding/scripts/smoke_p1.py`.

| Berkas | Isi |
|---|---|
| `metrik-per-periode.csv` | Macro-F1 dan balanced accuracy per ambang, analisis, model, konfigurasi, dan periode (231 baris) |
| `rerata-utama.csv` | Rerata tujuh periode, ambang 0,5, termasuk diagnostik kelas mayoritas |
| `delta-utama.csv` | K2−K1 dan K3−K2 berpasangan, ambang 0,5 (Macro-F1 dan balanced accuracy) |
| `sensitivitas-ambang.csv` | K2−K1 dan K3−K2 pada ambang 0,25 dan 1,0 |
| `sensitivitas-parameter-tetap.csv` | K2−K1 dan K3−K2 bila K2/K3 memakai hiperparameter terpilih K1 |

## Rerata Macro-F1 tujuh periode uji (ambang 0,5·σ24)

| Model | K1 | K2 | K3 | K2 − K1 (periode positif) | K3 − K2 (periode positif) |
|---|---:|---:|---:|---:|---:|
| Regresi Logistik | 0,392154 | 0,392243 | 0,391609 | +0,000089 (4/7) | −0,000634 (3/7) |
| XGBoost | 0,393499 | 0,392416 | 0,392895 | −0,001083 (4/7) | +0,000479 (3/7) |
| Kelas mayoritas (diagnostik) | 0,216652 | | | | |

Selisih dihitung berpasangan per periode pada bar uji yang sama. Rerata tidak dibobot jumlah bar dan bukan uji signifikansi. Kegagalan evaluasi: 0.

## Periode uji

| Periode | Rentang (UTC, akhir tidak termasuk) | Bar uji |
|---|---|---:|
| 2023-H1 | 1 Jan – 1 Jul 2023 | 2.807 |
| 2023-H2 | 1 Jul 2023 – 1 Jan 2024 | 2.829 |
| 2024-H1 | 1 Jan – 1 Jul 2024 | 2.808 |
| 2024-H2 | 1 Jul 2024 – 1 Jan 2025 | 2.870 |
| 2025-H1 | 1 Jan – 1 Jul 2025 | 2.734 |
| 2025-H2 | 1 Jul 2025 – 1 Jan 2026 | 2.744 |
| 2026 Jan–Jul | 1 Jan – 1 Agu 2026 | 3.101 |

## Sensitivitas (rerata Δ Macro-F1, periode positif)

| Ambang | Model | K2 − K1 | K3 − K2 |
|---:|---|---:|---:|
| 0,25 | Regresi Logistik | +0,003965 (7/7) | −0,001034 (4/7) |
| 0,25 | XGBoost | −0,004523 (1/7) | −0,000310 (4/7) |
| 1,00 | Regresi Logistik | +0,001081 (3/7) | −0,002286 (2/7) |
| 1,00 | XGBoost | +0,000116 (4/7) | +0,009021 (7/7) |

## Cara membacanya

- Semua model jauh di atas tebakan kelas mayoritas, tetapi menambah RSI/MACD (K2) dan fitur makro (K3) hanya menggeser Macro-F1 rata-rata kurang dari 0,002 pada ambang utama, dengan arah yang tidak konsisten antarperiode, antarmodel, dan antarambang.
- Selisih mencakup efek penyetelan ulang hiperparameter, bukan pengaruh murni fitur. Analisis parameter tetap ada di `sensitivitas-parameter-tetap.csv`.
- Dibandingkan run lama (21–22 September), dua perbedaan aturan kecil (pemanasan satu bar dan batas purge) cukup untuk membalik tanda rerata XGBoost K2−K1 (+0,003289 menjadi −0,001083). Selisih sebesar ini berada dalam rentang variasi prosedur.
- K3 berlaku untuk snapshot kalender MT5 retrospektif. Sepuluh jangkar waktu rilis cocok, tetapi vintage forecast/actual independen tidak tersedia.
- Tidak ada klaim keuntungan transaksi, kausalitas, atau manfaat universal.
