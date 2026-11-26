# Hasil Penelitian (Protokol Bab 3–4)

Seluruh angka di bawah ini berasal langsung dari keluaran [`07_evaluasi_hasil.ipynb`](../notebooks/07_evaluasi_hasil.ipynb) menggunakan data XAUUSD H1 *server* MetaQuotes-Demo sesuai rancangan Bab 3 dan Bab 4.

| Berkas | Isi |
|---|---|
| [`metrik-per-periode.csv`](metrik-per-periode.csv) | *Macro-F1* dan *balanced accuracy* per pengali ambang, analisis, model, konfigurasi, dan periode (231 baris) |
| [`rerata-utama.csv`](rerata-utama.csv) | Rerata tujuh periode, ambang utama $0{,}5\sigma_{t,24}$, termasuk pembanding kelas mayoritas |
| [`delta-utama.csv`](delta-utama.csv) | Perubahan berpasangan K2−K1 dan K3−K2, ambang $0{,}5\sigma_{t,24}$ (*macro-F1* dan *balanced accuracy*) |
| [`sensitivitas-ambang.csv`](sensitivitas-ambang.csv) | K2−K1 dan K3−K2 pada pengali ambang 0,25 dan 1,0 |
| [`sensitivitas-parameter-tetap.csv`](sensitivitas-parameter-tetap.csv) | K2−K1 dan K3−K2 saat K2/K3 memakai *hyperparameter* terpilih K1 |

## Ringkasan Data, Pemeriksaan Celah, dan Kalender (Subbab 3.6)

- **Data harga:** 38.799 bar H1 (2 Januari 2020 06.00 UTC – 31 Juli 2026 22.00 UTC); 1.705 celah (1.627 penutupan terjadwal, 69 libur bursa CME, 9 celah tidak terjelaskan → 10 segmen indikator).
- **Kelayakan sampel bersama:** fitur layak 38.333 bar, target layak 36.872 bar, irisan keduanya (**himpunan sampel bersama**) **36.649 bar**.
- **Distribusi label ambang utama ($0{,}5\sigma_{t,24}$):** BUY 9.840 (26,8%), HOLD 17.633 (48,1%), SELL 9.176 (25,0%).
- **Kalender MT5:** 706 peristiwa ekonomi AS dalam 8 kelompok peristiwa → membentuk 46 fitur makroekonomi (total K3 = 59 kolom). Tidak ada fitur yang dibuang sepanjang tujuh periode uji.
- **Pelaksanaan pemodelan:** 0 baris latih terbuang *purge*, 0 dari 756 kandidat *hyperparameter* gagal, dan 0 periode dengan *balanced accuracy* tidak terdefinisi.

## Rerata Kinerja Tujuh Periode Uji (Ambang Utama $0{,}5\sigma_{t,24}$)

| Model | Konfigurasi | *Macro-F1* | *Balanced accuracy* |
|---|---|---:|---:|
| Regresi Logistik | K1 (harga) | 0,392154 | 0,395686 |
| Regresi Logistik | K2 (+ teknikal) | 0,392243 | 0,395948 |
| Regresi Logistik | K3 (+ makro) | 0,391609 | 0,396018 |
| XGBoost | K1 (harga) | 0,393499 | 0,397577 |
| XGBoost | K2 (+ teknikal) | 0,392416 | 0,397104 |
| XGBoost | K3 (+ makro) | 0,392895 | 0,397445 |
| Pembanding kelas mayoritas | — | 0,216652 | 0,333333 |

## Perubahan Berpasangan *Macro-F1* (Ambang Utama)

| Model | Perubahan | Rerata | Median | Simp. baku | Periode positif |
|---|---|---:|---:|---:|---:|
| Regresi Logistik | K2 − K1 | +0,000089 | +0,000347 | 0,001539 | 4/7 |
| Regresi Logistik | K3 − K2 | −0,000634 | −0,002167 | 0,004770 | 3/7 |
| XGBoost | K2 − K1 | −0,001083 | +0,000707 | 0,006187 | 4/7 |
| XGBoost | K3 − K2 | +0,000479 | −0,000808 | 0,004859 | 3/7 |

Selisih dihitung berpasangan per periode pada bar uji yang sama tanpa pembobotan jumlah bar dan bukan uji signifikansi.

## Periode Uji dan Sampel (Total Uji = 19.893 Bar)

| Periode | Rentang (UTC, akhir tidak termasuk) | Latih | Uji | BUY / HOLD / SELL |
|---|---|---:|---:|---|
| 2023-H1 | 1 Jan – 1 Jul 2023 | 16.752 | 2.807 | 699 / 1.410 / 698 |
| 2023-H2 | 1 Jul 2023 – 1 Jan 2024 | 19.560 | 2.829 | 669 / 1.470 / 690 |
| 2024-H1 | 1 Jan – 1 Jul 2024 | 22.389 | 2.808 | 740 / 1.385 / 683 |
| 2024-H2 | 1 Jul 2024 – 1 Jan 2025 | 25.197 | 2.870 | 830 / 1.380 / 660 |
| 2025-H1 | 1 Jan – 1 Jul 2025 | 28.068 | 2.734 | 816 / 1.228 / 690 |
| 2025-H2 | 1 Jul 2025 – 1 Jan 2026 | 30.803 | 2.744 | 837 / 1.218 / 689 |
| 2026 Jan–Jul | 1 Jan – 1 Agu 2026 | 33.548 | 3.101 | 809 / 1.501 / 791 |

## Ringkasan *Confusion Matrix* Gabungan & Sensitivitas

- ***Recall* gabungan (19.893 bar uji):** Regresi Logistik mencatat *recall* BUY 0,267–0,271, HOLD 0,575–0,602, dan SELL 0,312–0,338; XGBoost mencatat BUY 0,301–0,309, HOLD 0,524–0,529, dan SELL 0,357–0,364 (pembanding kelas mayoritas selalu menebak HOLD).
- **Sensitivitas *hyperparameter* tetap (ambang 0,5):** Regresi Logistik K2−K1 +0,000764 (5/7) dan K3−K2 −0,001368 (3/7); XGBoost K2−K1 −0,001877 (2/7) dan K3−K2 +0,001104 (3/7).
- **Sensitivitas ambang (*tuning* per konfigurasi):**
  - $0{,}25\sigma_{t,24}$: Regresi Logistik K2−K1 +0,003965 (7/7), K3−K2 −0,001034 (4/7); XGBoost K2−K1 −0,004523 (1/7), K3−K2 −0,000310 (4/7).
  - $1{,}00\sigma_{t,24}$: Regresi Logistik K2−K1 +0,001081 (3/7), K3−K2 −0,002286 (2/7); XGBoost K2−K1 +0,000116 (4/7), K3−K2 +0,009021 (7/7).

## Cara Membaca Hasil

- Seluruh kombinasi model jauh di atas pembanding kelas mayoritas (*macro-F1* sekitar 0,39 vs 0,22), tetapi penambahan fitur teknikal maupun makroekonomi hanya menggeser *macro-F1* rata-rata kurang dari 0,002 pada ambang utama dengan arah tidak konsisten antarperiode, antarmodel, dan antarambang.
- Hasil mencakup pengaruh penyesuaian ulang *hyperparameter* di samping penambahan fitur (diurai melalui tabel parameter tetap).
- Hasil K3 berlaku pada *snapshot* kalender MT5 statis tanpa riwayat revisi *point-in-time* independen, dan tidak ada klaim keuntungan transaksi maupun efek sebab-akibat ekonomi.
