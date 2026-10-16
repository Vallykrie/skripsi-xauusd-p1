# Alur presentasi P1 (10–15 menit)

Alat utama: `03_web_belajar/Lab_P1_XAUUSD.html`, mode **Presentasi** (tombol `P`). Pindah langkah dengan panah → dan ←. Spasi memutar otomatis.

| Menit | Bab web | Yang disampaikan |
|---|---|---|
| 0–2 | 00 Peta P1, langkah 1–3 | Target berita acara: koding 50% dan dokumentasi sampai perhitungan manual. Tunjukkan alur penelitian dalam satu layar. |
| 2–4 | 01 Label | Bar ke-51 (observasi layak pertama setelah 50 bar pemanasan) selesai, σ24 dari 24 log-return, δ = 0,5·σ24, label BUY pada contoh. Geser close berikutnya ke 2018 untuk HOLD dan ke 2015 untuk SELL. Langkah 6: waktu keputusan vs waktu label. |
| 4–5 | 02 Fitur K1–K3 | K1 9 kolom, K2 13 kolom. RSI: seed 14 lalu Wilder. Gerbang waktu makro. |
| 5–6 | 03 Logistik | Standardisasi, p = 1/3, gradien, β baru, softmax di x = 3 → BUY. |
| 6–10 | 04 XGBoost | Pohon HOLD kedalaman 2: g dan h, G/H akar, coba 5 titik potong, belah x < −0,5, belah lagi x < 1,5, bobot daun, telusuri x = 0. Langkah 14: pohon SELL dan BUY mengikuti alur yang sama. Langkah 15: iterasi berikutnya mengulang dengan p baru. |
| 10–11 | 05 Walk-forward | Tujuh periode uji, validasi internal 18 bulan, purge dari keputusan pertama blok. Tunjukkan gambar skema di notebook 05. |
| 11–12 | 06 Evaluasi | F1 per kelas, Macro-F1, contoh "selalu HOLD". |
| 12–14 | 07 Hasil asli | K1 → K2 → selisih → K3 → selisih. Langkah 6: kesimpulan, batasan, sisa menuju P2. Jika ditanya kode, buka notebook 07 (tabel dan grafik yang sama dari data asli). |
| 14–15 | — | Rencana P2: Bab 4 hasil dan Bab 5 pembahasan dari notebook, Bab 6, artikel. Tanya kebutuhan pembimbing. |

## Kalimat pembuka

"Sesuai berita acara P0, target P1 adalah koding 50% dan dokumentasi sampai perhitungan manual. Saya tunjukkan alurnya dulu, lalu perhitungan manual dari label sampai pohon XGBoost, kemudian eksperimen Fase 4 yang sudah berjalan penuh sesuai Bab 3 proposal."

## Kalau pembimbing bertanya XGBoost lebih dalam

1. Ganti **Pohon kelas** ke SELL atau BUY: pohonnya berhenti di kedalaman 1 karena sisi lain tidak punya gain positif atau H anak < 0,5. Ini menjawab mengapa bentuk pohon bisa berbeda per kelas.
2. Ganti **Iterasi** ke 2 atau 3: G akar berubah karena p dihitung ulang. Pohon baru belajar dari sisa kesalahan.
3. Ganti **Kedalaman** ke 1: hasil iterasi 1 sama persis dengan tab XGBoost di Excel (gain 0,790588 untuk SELL).

## Jawaban singkat yang perlu hafal

Semua ada di bab **08 Latihan** web (10 soal). Latih dengan suara sebelum membuka jawaban.

## Cadangan

- Jika browser bermasalah: buka Excel `02_perhitungan_manual/Perhitungan_Manual_P1.xlsx`, tab `Mulai`.
- Jika ditanya naskah: `01_dokumentasi/P1_Dokumentasi_Bab1-3.pdf` (Bab 1–3 final P0).
- Jika ditanya kode: `04_koding/notebooks/fase4/`, mulai notebook 00 (peta notebook ke subbab Bab 3).

## Kalau ditanya mengapa hasil berbeda dari draf sebelumnya

Run lama 21–22 September memuat analisis di luar proposal (sumber Ultima, policy holiday-reset) dan dua aturan kode yang tidak persis mengikuti teks Bab 3 (pemanasan bar ke-50, batas purge). Fase 4 dijalankan ulang sebagai notebook yang mengikuti Bab 3 persis, dengan konfigurasi dibekukan sebelum skor dibaca. Notebook 08 menunjukkan fitur dan label identik kecuali dua aturan itu. Bahwa perubahan sekecil itu bisa membalik tanda selisih XGBoost K2−K1 menunjukkan kontribusi fitur teknikal memang sangat kecil.
