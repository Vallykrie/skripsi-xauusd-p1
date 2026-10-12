# Reproduksi dan batas akses

Semua perintah dijalankan dari folder `04_koding/`.

## Tiga tingkat pemeriksaan

1. **Portabel:** pytest, Ruff, verify_agents, smoke_p1. Menguji kode dan formula pembelajaran tanpa MT5 atau data privat.
2. **Agregat:** smoke_p1 menghitung ulang macro-F1 dan balanced accuracy dari matriks kebingungan setiap fold; memeriksa pasangan dan ringkasan. Ini tidak membuktikan ulang harga, timestamp atau prediksi per bar.
3. **Penuh:** memerlukan raw price, kalender, bukti sesi, price audit, manifest, fitur dan prediksi privat dengan checksum asli. Pada clone publik tanpa input tersebut: NOT TESTED. Jangan mengganti input dengan angka sintetis sambil mempertahankan klaim penelitian.

## Jalur pipeline asli (jika input privat yang sah tersedia)

```bash
python scripts/run_phase4_price_audit.py
python scripts/write_phase4_run_manifest.py
python scripts/run_phase4_full_data_features.py
python scripts/run_phase4_models.py --source metaquotes-demo --policy primary --threshold 0.5
python scripts/audit_phase4_macro_gate.py
python scripts/run_phase4_models.py --include-k3 --source metaquotes-demo --policy primary --threshold 0.5
python scripts/verify_phase4_model_results.py data/interim/phase4/model-results/metaquotes-demo-primary-0p5-k3
```

Manifest publik adalah salinan historis yang disanitasi dengan menghapus awalan jalur workstation. Hash publik berbeda; hash asli tercatat pada `../lampiran/PROVENANCE.json`. Untuk pemeriksaan rantai hash penuh, gunakan manifest privat asli bersama artefak privat. Manifest publik bukan manifest baru clone publik. Jangan menimpa manifest historis atau membuat scores_read=false seolah-olah skor belum pernah dibaca. Untuk reproduksi baru, simpan output di checkout terpisah, catat bahwa ini replikasi setelah skor diketahui, dan preservasi checksum/protokol historis. run_manifest.py menolak working tree kotor.

Input tidak dapat direkonstruksi dari checksum saja. Kalender adalah snapshot vendor dengan batasan revisi, bukan arsip vintage independen. Ekstraksi data baru tidak termasuk paket P1; login MT5 dilakukan manusia melalui GUI tanpa menuliskan kredensial. Seluruh API transaksi dilarang.

## Excel

Workbook dibangun dengan artifact-tool, formula dihitung ulang dan diperiksa terhadap Python/kode fitur. Sel kuning adalah input; teks menunjukkan kondisi warm-up/tidak layak. Aplikasi Excel desktop belum diuji bila tidak dicatat secara eksplisit pada `../lampiran/VERIFIKASI.md`. Workbook meminta pengguna mengikuti contoh kontinu; simulator tidak menggantikan audit gap/fold produksi.
