# Verifikasi paket P1

Dilakukan 8 Oktober 2026 pada macOS dengan interpreter proyek yang sudah tersedia. Tes memuat kode dari src pada paket publik melalui pythonpath, bukan menyalin hasil tes sebagai pengganti eksekusi.

| Pemeriksaan | Hasil |
|---|---|
| `python -m pytest` paket publik | 56 lulus |
| `python -m ruff check .` paket publik | lulus |
| `bash scripts/verify_agents.sh` paket publik | lulus |
| `python scripts/smoke_p1.py` | 24 run,1320matriks/metrik dan ringkasan pasangan cocok; plumbing fitur/dua model sintetis berjalan |
| Repo penelitian privat `pytest` | 197 lulus,2 dilewati khusus Windows |
| Repo penelitian privat Ruff,verify_agents,smoke_test.sh | lulus; smoke dijalankan ulang setelah akses jaringan untuk install tersedia |
| Run utama privat metaquotes-primary-0p5-k3 | checksum prediksi, batas waktu, metrik dan kesamaan bar diverifikasi;198980baris prediksi lintas konfigurasi/analisis |
| Excel | 8sheet dirender dan diperiksa; return/sigma/RSI/MACD/label dibandingkan dengan features.py untuk61bar; uji perubahan harga/pengali,kelas absen,forecast kosong; softmax berjumlah1 dan daun XGBoost dibandingkan hitungan independen |
| PDF Bab1–4 | XeLaTeX/Biber berhasil,40halaman; seluruh halaman ditinjau sebagai contact sheet dan halaman tabel/daftar isi diperiksa lebih besar |

Excel desktop native **NOT TESTED**. Reproduksi training utama dari clone publik tanpa input privat **NOT TESTED**. Penguasaan mahasiswa dan pengesahan P1 **NOT TESTED**. Tes portabel tidak membuktikan ulang provenance vendor maupun vintage kalender.

PDF memakai Latin Modern Roman dan pembungkus report generik. Log menunjukkan satu overfull hbox0,571pt dan peringatan bahasa polyglossia; tinjauan visual tidak menunjukkan pemotongan isi. Ini draf kurasi publik, bukan keluaran format resmi kampus.
