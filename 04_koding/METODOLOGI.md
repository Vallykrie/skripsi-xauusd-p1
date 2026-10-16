# Metodologi dan peta kode

Protokol otoritatif: Bab 3 proposal final P0 (`../01_dokumentasi/P1_Dokumentasi_Bab1-3.pdf`). Eksperimen resmi: `notebooks/fase4/`, konfigurasi `configs/phase4-p0.toml`.

## Pertanyaan penelitian

Apakah penambahan kelompok teknikal (K2−K1), kemudian makro (K3−K2), mengubah kinerja klasifikasi BUY/HOLD/SELL XAUUSD H1 pada observasi uji yang sama? Dua model memberi pembanding linear dan nonlinear. Hasil mengukur perubahan bersyarat fitur plus penyetelan ulang, bukan efek kausal maupun keuntungan transaksi.

## Alur dan kontrak

| Tahap | Kontrak | Notebook |
|---|---|---|
| Input | OHLC positif, UTC, urut, unik; hash cocok dengan konfigurasi beku | 00, 01 |
| Audit | penutupan terjadwal dan libur bursa dibedakan dari gap tak terjelaskan; tidak ada interpolasi | 01 |
| Target | q=ln(C[t+1]/C[t]); tepat satu jam; δ=0,5·σ24 (sensitivitas 0,25 dan 1,0) | 02 |
| Fitur | pemanasan: observasi dipakai mulai bar ke-51 segmen; seluruh fitur diketahui saat keputusan | 03 |
| K1 | r[t]…r[t−5], ln(C/O), ln(H/L), σ24 | 9 kolom |
| K2 | K1 + RSI14 + MACD(12,26,9)/C | 13 kolom |
| K3 | K2 + 46 kolom snapshot kalender, join rilis < keputusan | 59 kolom |
| Split | 7 periode uji, validasi internal 18 bulan = 3 blok 6 bulan, purge | 05 |
| Praproses | median, indikator hilang, scaler di-fit pada data latih saja | 06 |
| Penalaan | Logistik C ∈ {0,01; 0,1; 1; 10}; XGBoost 8 kandidat; rata-rata Macro-F1 tiga blok | 06 |
| Pelaporan | prediksi per bar, parameter, kegagalan, metrik, selisih berpasangan, diagnostik kelas mayoritas | 06, 07 |

Waktu pembukaan bar o[t]; keputusan τ[t]=o[t]+1 jam; label baru diketahui o[t]+2 jam. Label uji harus berakhir di dalam periode uji setengah terbuka. Observasi latih yang akhir labelnya sama dengan atau setelah **waktu keputusan pertama observasi layak** pada blok berikutnya dibuang (purge). Riwayat untuk pemanasan boleh berasal dari sebelum awal blok karena sudah tersedia.

σ24 adalah simpangan baku **sampel** dari 24 log-return (pembagi 23). StandardScaler memakai varians **populasi** data latih (pembagi n). RSI Wilder di-seed dari 14 perubahan; EMA di-seed dari SMA p harga, sinyal MACD dari 9 MACD valid. Garis, sinyal, dan histogram dibagi close.

Rilis kalender tepat pada waktu keputusan belum digunakan. Forecast/actual kosong bukan nol. Surprise hanya untuk enam keluarga numerik CPI/NFP/pengangguran; rate/FOMC hanya penanda pascarilis. Surprise kedaluwarsa setelah 168 jam. Timestamp lulus 10 jangkar khusus snapshot, tetapi vintage independen tidak tersedia.

Sensitivitas ambang 0,25/1,0 dan sensitivitas parameter tetap (hiperparameter K1 dipakai ulang untuk K2/K3) dilaporkan terpisah. Untuk XGBoost, scaler data latih dipakai pada K3 karena kolom makro bersatuan berbeda. Tidak ada random split, early stopping, atau pemilihan aturan berdasarkan skor uji.

Kode kelas memakai SELL=0, HOLD=1, BUY=2. Matriks kebingungan dilaporkan dengan urutan BUY, HOLD, SELL.

## Perbedaan dengan pipeline lama

Notebook mengikuti teks Bab 3 pada dua aturan yang berbeda dari kode lama di `src/thesis_experiments`: pemanasan (kode lama memakai bar ke-50) dan batas purge (kode lama memakai awal kalender blok). Sumber Ultima dan policy holiday-reset dari run lama berada di luar protokol P0 dan tidak dijalankan. Notebook 08 menunjukkan bahwa selain dua aturan itu, fitur, label, dan fitur makro identik.
