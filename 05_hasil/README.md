# 05 · Ringkasan hasil untuk P1

Sumber: run `metaquotes-demo-primary-0p5-k3` (data utama MetaQuotes-Demo, policy gap primer, ambang 0,5·σ24). Angka per periode: baris `run = metaquotes-demo-primary-0p5-k3` di [`metrik-per-fold.csv`](metrik-per-fold.csv) (42 baris: 7 periode × 2 model × 3 konfigurasi, semuanya `TESTED`). Rincian 24 run termasuk sensitivitas: [HASIL_LENGKAP.md](HASIL_LENGKAP.md) dan `run/`.

## Rerata Macro-F1 tujuh periode uji

| Model | K1 | K2 | K3 | K2 − K1 | K3 − K2 |
|---|---:|---:|---:|---:|---:|
| Regresi Logistik | 0,392300 | 0,392374 | 0,390922 | +0,000074 | −0,001452 |
| XGBoost | 0,390178 | 0,393466 | 0,393791 | +0,003289 | +0,000324 |

Selisih dihitung dari angka penuh per periode. Rerata tidak dibobot jumlah bar dan bukan uji signifikansi. Acuan tebakan acak tiga kelas ≈ 0,333.

## Periode uji

| Periode | Rentang (UTC, akhir tidak termasuk) | Bar uji |
|---|---|---:|
| 2023-H1 | 1 Jan – 1 Jul 2023 | 2.807 |
| 2023-H2 | 1 Jul 2023 – 1 Jan 2024 | 2.829 |
| 2024-H1 | 1 Jan – 1 Jul 2024 | 2.808 |
| 2024-H2 | 1 Jul 2024 – 1 Jan 2025 | 2.870 |
| 2025-H1 | 1 Jan – 1 Jul 2025 | 2.735 |
| 2025-H2 | 1 Jul 2025 – 1 Jan 2026 | 2.746 |
| 2026 Jan–Jul | 1 Jan – 1 Agu 2026 | 3.103 |

## Cara membacanya

- Menambah RSI/MACD (K2) dan fitur makro (K3) hanya menggeser Macro-F1 sangat kecil, dan arahnya tidak konsisten antarperiode maupun antarmodel.
- Selisih mencakup efek penyetelan ulang hiperparameter, bukan pengaruh murni fitur. Analisis parameter tetap dilaporkan terpisah di Bab 4.
- K3 berlaku untuk snapshot kalender MT5 retrospektif. Sepuluh jangkar waktu rilis cocok, tetapi vintage forecast/actual independen tidak tersedia.
- Ultima Markets hanya punya empat periode layak; tiga periode awal NOT TESTED.
- Tidak ada klaim keuntungan transaksi, kausalitas, atau manfaat universal.

Rincian lengkap (audit data, matriks kebingungan, hiperparameter terpilih, sensitivitas 0,25/1,0 dan holiday-reset) ada di Bab 4 pada [`../01_dokumentasi/P1_Dokumentasi_Bab1-4.pdf`](../01_dokumentasi/P1_Dokumentasi_Bab1-4.pdf).
