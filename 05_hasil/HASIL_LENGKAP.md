# Hasil penelitian dan interpretasi

Angka berikut adalah agregat eksperimen Fase 4 tersimpan, bukan data sintetis pembelajaran. Setiap JSON publik adalah ekstrak allowlist ringkasan privat; checksum sumber disimpan dalam JSON dan `../lampiran/PROVENANCE.json`. Berkas privat asli dan prediksi per bar tetap tidak diterbitkan.

## Hasil utama MetaQuotes-Demo

Policy primary, ambang 0,5×sigma24, tujuh fold. Rerata macro-F1 antar-fold tanpa pembobotan bar:

| Model | K1 | K2 | K3 | Delta K2-K1 | Delta K3-K2 |
|---|---:|---:|---:|---:|---:|
| Logistik | 0.392300 | 0.392374 | 0.390922 | +0.000074 | -0.001452 |
| XGBoost | 0.390178 | 0.393466 | 0.393791 | +0.003289 | +0.000324 |

Delta dihitung dari presisi penuh sebelum pembulatan. Penambahan fitur menghasilkan selisih kecil dengan arah bervariasi antarperiode/model. Logistik: teknikal positif 3/7 fold; XGBoost 4/7. Makro positif 3/7 pada kedua model. Ini tidak membuktikan peningkatan yang konsisten, signifikansi statistik, hubungan kausal, atau keuntungan transaksi.

## Cara menelusuri angka

- `metrik-per-fold.csv`: seluruh status, N test, metrik, parameter per run/model/konfigurasi/fold.
- `run/*.json` (24 run): confusion_order, confusion_matrix, class_counts, selected_params, kandidat internal, kegagalan, skor parameter tetap, ringkasan berpasangan.
- `../02_perhitungan_manual/Perhitungan_Manual_P1.xlsx`, tab Hasil_Asli: tujuh fold utama yang sama, selisih dihitung dengan rumus aktif.
- Bab 4 dalam `../01_dokumentasi/P1_Dokumentasi_Bab1-4.pdf`: tabel utama, sensitivitas, parameter, matriks gabungan dan grafik perperiode.

K1/K2 run awal berurutan matriks SELL,HOLD,BUY; run yang lebih baru berurutan BUY,HOLD,SELL. Semua JSON publik memuat `confusion_order` secara eksplisit. Jangan menyamakan agregasi semua bar dengan rerata macro-F1 per fold: F1 bersifat nonlinear.

## Sensitivitas dan kegagalan tetap dilaporkan

24 run terdiri dari 12 run K1/K2 dan 12 run K1/K2/K3: dua sumber×dua policy×tiga ambang. Ambang0,25/1,0, holiday-reset, sumber Ultima, dan hiperparameter tetap adalah sensitivitas terpisah. Tidak memilih run berskor paling tinggi sebagai protokol utama.

Ultima: fold2023-H1,2023-H2,2024-H1 **NOT TESTED** untuk model karena riwayat broker tidak memenuhi kebutuhan validasi internal18bulan. Empat dari7fold terjadwal layak. JSON mempertahankan kegagalan kandidat; tidak menghapus tiga fold dari penyebut pelaporan.

K3: hash dan10anchor timestamp lulus untuk snapshot spesifik. Vintage actual first-release dan forecast pra-rilis independen tidak tersedia. Hasil K3 berlaku pada **snapshot retrospektif**, bukan arsip point-in-time penuh.

## Pemeriksaan yang bisa dilakukan dari paket publik

`python scripts/smoke_p1.py` (dari folder `04_koding/`) menghitung ulang F1/recall dari 1320 matriks skor dan memeriksa seluruh ringkasan delta. Ini mengecek konsistensi matematis agregat; integritas harga dan kesamaan prediksi perbar memerlukan artefak privat. Pelatihan penuh dari clone publik tanpa input privat: **NOT TESTED**. Tidak ada skor feasibility yang dipakai sebagai pengganti hasil utama.
