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

## Setelah penyusunan ulang (12 Oktober 2026)

Dari folder `04_koding/` pada macOS: `pytest` 56 lulus; Ruff lulus; `verify_agents.sh` lulus; `smoke_p1.py` 24 run, 1320 matriks/metrik dan ringkasan pasangan cocok. `node --test ../03_web_belajar/tests/lab-math.test.mjs` 7 lulus. Web diperiksa di browser: seluruh langkah sembilan bab tanpa error JavaScript, lebar 1280 dan 390 px tanpa overflow halaman. Kompilasi ulang LaTeX setelah pemindahan folder: NOT TESTED (struktur relatif `sumber-latex/` tidak berubah).

## Pembaruan ke notebook Fase 4 (16 Oktober 2026)

Pada macOS dari folder `04_koding/`: `pytest` 56 lulus; Ruff lulus (termasuk notebook); `verify_agents.sh` lulus; `smoke_p1.py` menghitung ulang 24 ringkasan pasangan di `05_hasil/` dari 231 baris metrik dan memeriksa contoh manual bar ke-51. `node --test ../03_web_belajar/tests/lab-math.test.mjs` 7 lulus.

Notebook 00–05 dan 08 dijalankan pada salinan `04_koding/` di luar git: artefak antara (gap, fitur, fitur makro, dataset, blok validasi) identik byte demi byte dengan run resmi di repo penelitian, dan uji determinisme notebook 08 lulus. Notebook 06 (±16 menit) tidak dijalankan ulang pada salinan ini; keluaran tersimpan berasal dari run resmi.

Excel dihitung ulang dengan LibreOffice; nilai bar ke-51 (σ24 0,0010629949; δ 0,0005314974; q 0,0014862524; BUY; RSI 58,73572475) cocok dengan Python. PDF Bab 1–3 dikompilasi XeLaTeX/Biber, 29 halaman, satu overfull hbox 0,571 pt, contact sheet seluruh halaman ditinjau. Excel desktop native, penguasaan mahasiswa, dan pengesahan P1: NOT TESTED.
