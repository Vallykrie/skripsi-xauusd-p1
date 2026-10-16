# Peta capaian P1

## Dasar target

Berita acara P0 yang diberikan mahasiswa: konsultasi 21 September 2026, penelitian nonimplementatif analitik, objek data emas, masalah klasifikasi, Logistic Regression dan XGBoost. P1 minimum 50%, kode/dokumentasi sampai perhitungan manual, batas 27 Oktober 2026. P2 minimum 80%, kode/eksperimen/dokumentasi selesai, batas 11 Desember 2026. Tanggal batas ini dibaca dari dokumen, bukan konfirmasi jadwal pertemuan aktual. PDF asli disimpan privat; checksum dicatat pada PROVENANCE.json.

## Bukti yang dapat ditunjukkan

| Target | Bukti paket | Status dan batas |
|---|---|---|
| Rumusan masalah dan landasan | `01_dokumentasi` Bab 1–2 (final P0) | sudah dipresentasikan pada P0 |
| Dokumentasi metode | Bab 3 final P0, `04_koding/METODOLOGI.md`, `04_koding/configs/phase4-p0.toml` | tersedia; konfigurasi dibekukan sebelum skor dibaca |
| Kode pengolahan data/fitur | `04_koding/notebooks/fase4/` 00–05 | tersedia; dijalankan penuh dari data mentah |
| Kode model dan evaluasi | `04_koding/notebooks/fase4/` 06–08 | tersedia; walk-forward bertingkat, verifikasi dan determinisme lulus |
| Hasil eksperimen | `05_hasil/`, notebook 07 | lengkap untuk lingkup Bab 3; 0 kegagalan evaluasi; bab hasil belum ditulis |
| Perhitungan manual | `02_perhitungan_manual/` dan `03_web_belajar/` | return/label, RSI/MACD, praproses, bobot, softmax/pelatihan Logistik, satu iterasi XGBoost multikelas, metrik, selisih fitur |
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

Sebelum P1: pelajari notebook 00–08 dan latihan tanpa melihat jawaban, cocokkan substansi dengan kedua pembimbing, lengkapi logbook sah dan jadwalkan P1. Menuju P2: tulis Bab 4 hasil dan Bab 5 pembahasan dari notebook (per kelas, periode, literatur, serta besarnya variasi prosedur), Bab 6, artikel, dan administrasi. Nilai kecil bukan alasan mengubah protokol untuk mengejar skor.
