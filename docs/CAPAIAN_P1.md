# Peta capaian P1

## Dasar target

Berita acara P0 yang diberikan mahasiswa: konsultasi 21 September 2026, penelitian nonimplementatif analitik, objek data emas, masalah klasifikasi, Logistic Regression dan XGBoost. P1 minimum 50%, kode/dokumentasi sampai perhitungan manual, batas 27 Oktober 2026. P2 minimum 80%, kode/eksperimen/dokumentasi selesai, batas 11 Desember 2026. Tanggal batas ini dibaca dari dokumen, bukan konfirmasi jadwal pertemuan aktual. PDF asli disimpan privat; checksum dicatat pada PROVENANCE.json.

## Bukti yang dapat ditunjukkan

| Target | Bukti paket | Status dan batas |
|---|---|---|
| Rumusan masalah dan landasan | naskah Bab 1–2 | draf substantif; review pembimbing belum terverifikasi |
| Dokumentasi metode | Bab 3, METODOLOGI.md, configs | tersedia; protokol tidak ditentukan ulang oleh skor |
| Kode pengolahan data/fitur | src/thesis_experiments, tests | tersedia; tes publik memakai data sintetis |
| Kode model dan evaluasi | models.py, folds.py, evaluation.py | tersedia; nested chronological evaluation |
| Hasil awal | Bab 4, hasil/ | agregat 24 run tersedia; input/prediksi privat |
| Perhitungan manual | Excel dan PANDUAN_MANUAL.md | return/label, RSI/MACD, praproses, bobot, softmax/pelatihan Logistik, satu iterasi XGBoost multikelas, metrik, selisih fitur |
| Pemahaman mahasiswa | latihan dengan kunci jawaban | kemampuan menjelaskan mandiri: NOT TESTED |
| Penilaian minimum 50% | dinilai terhadap target P0 | pengesahan pembimbing: NOT TESTED |
| Bimbingan dan logbook | ditangani melalui pertemuan nyata | jumlah catatan sah: NOT TESTED |

Jangan menghitung 50% berdasarkan jumlah file, baris kode, atau jumlah bab. Berita acara menetapkan target pekerjaan, sedangkan pengesahan kemajuan dilakukan pembimbing. Paket ini menyediakan bukti yang dapat ditinjau.

## Agenda penjelasan P1 (10–15 menit)

1. Masalah dan perbandingan K2–K1/K3–K2 (2 menit).
2. Target, waktu keputusan, serta audit gap (2 menit).
3. Contoh Excel: label, RSI/MACD, Logistik/XGBoost (5 menit).
4. Walk-forward, purge, pemilihan parameter, dan hasil asli (3 menit).
5. Batasan K3, review naskah, logbook, dan rencana P2 (2 menit).

Sebelum P1: selesaikan latihan tanpa melihat jawaban, cocokkan substansi dengan kedua pembimbing, perbaiki draf Bab 4, lengkapi logbook sah dan jadwalkan P1. Menuju P2: perdalam pembahasan per kelas/periode/literatur, revisi Bab 5–6, serta lengkapi artikel dan administrasi. Nilai kecil bukan alasan mengubah protokol untuk mengejar skor.
