# Metodologi dan peta kode

## Pertanyaan penelitian

Apakah penambahan kelompok teknikal (K2−K1), kemudian makro (K3−K2), mengubah kinerja klasifikasi BUY/HOLD/SELL XAUUSD H1 pada observasi uji yang sama? Dua model memberi pembanding linear/nonlinear. Hasil mengukur perubahan bersyarat fitur plus penyetelan ulang, bukan efek kausal maupun keuntungan transaksi.

## Alur dan kontrak

| Tahap | Kontrak | Kode |
|---|---|---|
| Input | OHLC positif, UTC, urut, unik; hash cocok | protocol.py |
| Audit | sesi terjadwal versus gap tak terjelaskan; tidak interpolasi | market_audit.py, gaps.py |
| Target | q=ln(C[t+1]/C[t]); tepat satu jam; δ=0,5σ24 | features.py |
| Fitur | warm-up 50 bar per segmen; seluruh fitur diketahui saat keputusan | features.py |
| K1 | r[t]…r[t−5], ln(C/O), ln(H/L), σ24 | 9 kolom |
| K2 | K1 + RSI14 + MACD(12,26,9)/C | 13 kolom |
| K3 | K2 + snapshot kalender, join rilis < keputusan | macro_gate.py, macro_features.py |
| Split | 7 blok uji, inner 18 bulan = 3 blok 6 bulan, purge | folds.py |
| Praproses | fit median/kolom/scaler pada train saja | models.py |
| Penalaan | C empat kandidat; XGBoost delapan kandidat, inner macro-F1 | evaluation.py, models.py |
| Pelaporan | prediksi, parameter, kegagalan, metrik, selisih berpasangan | evaluation.py |

Waktu pembukaan bar o[t]; keputusan τ[t]=o[t]+1 jam; label baru diketahui o[t]+2 jam. Target tidak boleh melewati akhir blok uji setengah terbuka. Latih yang akhir labelnya ≥ keputusan pertama blok berikutnya dibuang (purge). Riwayat untuk warm-up boleh berasal dari sebelum awal blok karena sudah tersedia.

σ24 adalah simpangan baku **sampel** dari 24 log-return (pembagi 23). StandardScaler memakai varians **populasi** train (pembagi n). Keduanya berbeda tujuan. RSI Wilder di-seed dari 14 perubahan; EMA di-seed dari SMA p harga, sinyal MACD dari 9 MACD valid. Hist/line/signal dibagi close.

Rilis kalender tepat pada keputusan belum digunakan. Forecast/actual kosong bukan nol. Surprise hanya untuk enam keluarga numerik CPI/NFP/unemployment; rate/FOMC hanya penanda pascarilis. Kejutan kedaluwarsa setelah 168 jam. Timestamp lulus anchor khusus snapshot, tetapi vintage independen tidak tersedia.

Grid dan seluruh tanggal tersedia pada configs/phase4-experiments.toml. Sensitivitas 0,25/1,0, holiday-reset, broker Ultima, dan parameter tetap dilaporkan terpisah. Scaler train-only juga digunakan untuk konfigurasi bermakro pada XGBoost sesuai kode tersimpan. Tidak ada random split, early stopping, atau pemilihan kebijakan berdasarkan skor uji.

Kode class ID memakai SELL=0,HOLD=1,BUY=2. Matriks kebingungan dilaporkan BUY,HOLD,SELL. Saat membaca matriks, selalu lihat urutannya, jangan menganggap urutan kode numerik sama dengan urutan laporan.
