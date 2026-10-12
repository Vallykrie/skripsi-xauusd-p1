# Alur presentasi P1 (10–15 menit)

Alat utama: `03_web_belajar/Lab_P1_XAUUSD.html`, mode **Presentasi** (tombol `P`). Pindah langkah dengan panah → dan ←. Spasi memutar otomatis.

| Menit | Bab web | Yang disampaikan |
|---|---|---|
| 0–2 | 00 Peta P1, langkah 1–3 | Target berita acara: koding 50% dan dokumentasi sampai perhitungan manual. Tunjukkan alur penelitian dalam satu layar. |
| 2–4 | 01 Label | Satu bar selesai, σ24 dari 24 log-return, δ = 0,5·σ24, label HOLD pada contoh. Geser close ke 2020 untuk menunjukkan BUY. Langkah 6: waktu keputusan vs waktu label. |
| 4–5 | 02 Fitur K1–K3 | K1 9 kolom, K2 13 kolom. RSI: seed 14 lalu Wilder. Gerbang waktu makro. |
| 5–6 | 03 Logistik | Standardisasi, p = 1/3, gradien, β baru, softmax di x = 3 → BUY. |
| 6–10 | 04 XGBoost | Pohon HOLD kedalaman 2: g dan h, G/H akar, coba 5 titik potong, belah x < −0,5, belah lagi x < 1,5, bobot daun, telusuri x = 0. Langkah 14: pohon SELL dan BUY mengikuti alur yang sama. Langkah 15: iterasi berikutnya mengulang dengan p baru. |
| 10–11 | 05 Walk-forward | Tujuh periode uji, validasi internal 18 bulan, purge. |
| 11–12 | 06 Evaluasi | F1 per kelas, Macro-F1, contoh "selalu HOLD". |
| 12–14 | 07 Hasil asli | K1 → K2 → selisih → K3 → selisih. Langkah 6: kesimpulan, batasan, sisa menuju P2. |
| 14–15 | — | Rencana P2: pembahasan per kelas/periode, Bab 5–6, artikel. Tanya kebutuhan pembimbing. |

## Kalimat pembuka

"Sesuai berita acara P0, target P1 adalah koding 50% dan dokumentasi sampai perhitungan manual. Saya tunjukkan alurnya dulu, lalu perhitungan manual dari label sampai pohon XGBoost, kemudian hasil awal yang sudah berjalan."

## Kalau pembimbing bertanya XGBoost lebih dalam

1. Ganti **Pohon kelas** ke SELL atau BUY: pohonnya berhenti di kedalaman 1 karena sisi lain tidak punya gain positif atau H anak < 0,5. Ini menjawab mengapa bentuk pohon bisa berbeda per kelas.
2. Ganti **Iterasi** ke 2 atau 3: G akar berubah karena p dihitung ulang. Pohon baru belajar dari sisa kesalahan.
3. Ganti **Kedalaman** ke 1: hasil iterasi 1 sama persis dengan tab XGBoost di Excel (gain 0,790588 untuk SELL).

## Jawaban singkat yang perlu hafal

Semua ada di bab **08 Latihan** web (10 soal). Latih dengan suara sebelum membuka jawaban.

## Cadangan

- Jika browser bermasalah: buka Excel `02_perhitungan_manual/Perhitungan_Manual_P1.xlsx`, tab `Mulai`.
- Jika ditanya naskah: `01_dokumentasi/P1_Dokumentasi_Bab1-4.pdf`.
- Jika ditanya kode: `04_koding/README.md`.
