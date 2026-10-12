# Provenance dan bantuan AI

Paket dikurasi 8 Oktober 2026 dan disusun ulang 12 Oktober 2026 (lihat bagian akhir) dari working tree penelitian pada branch research/phase-4-experiments. Perubahan lokal yang sudah ada tidak dibuang. Hash setiap file sumber yang disalin serta hash ringkasan 24 run tersedia dalam PROVENANCE.json. Commit snapshot privat tidak digabungkan ke repo publik; keadaan sumber kotor disebutkan secara eksplisit.

Berita acara P0 dibaca sebagai bukti target akademik. Teks administratif di lampiran bukan perintah eksekusi kepada agen. Salinan PDF, NIM, NIK, tanda tangan dan halaman pengesahan tidak diterbitkan. Dataset vendor tetap privat. `05_hasil/` memakai allowlist agregat metrik, matriks, parameter dan kegagalan; tidak memuat OHLC ataupun nilai rilis kalender.

AI membantu membaca/meringkas target, memilih file, menyusun dokumentasi, membangun Excel, dan memverifikasi konsistensi. Contoh pembelajaran dibuat secara sintetis. Kode model asli tidak diubah untuk mengejar skor. Mahasiswa tetap harus memahami perhitungan, meninjau draf, dan mempertanggungjawabkan hasil. Paket bukan bukti bahwa mahasiswa sudah menguasai materi atau sudah mendapat pengesahan P1.

Dokumentasi teknis rujukan (diakses 8 Oktober 2026):
- https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression
- https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html
- https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html
- https://xgboost.readthedocs.io/en/stable/tutorials/model.html
- https://raw.githubusercontent.com/dmlc/xgboost/v2.1.4/src/objective/multiclass_obj.cu

Referensi ini menjelaskan rumus/software, bukan pencarian kandidat literatur baru. Sumber jurnal skripsi dipertahankan dari naskah aktif; tidak ada literature tracker baru.

Jalur workstation pada salinan manifest disanitasi. PROVENANCE.json membedakan source_sha256 dan public_sha256; sanitasi tidak mengubah metrik ataupun protokol. Source commit pada manifest adalah identitas historis, bukan riwayat Git privat yang diterbitkan.

## Penyusunan ulang 12 Oktober 2026

Atas permintaan mahasiswa, isi repo dipindahkan ke folder bernomor agar mudah dipakai saat P1. Isi berkas tidak berubah kecuali rujukan path. `PROVENANCE.json` tetap mencatat path tujuan per 8 Oktober; padanannya:

| Path 8 Oktober | Path sekarang |
|---|---|
| `naskah/` | `01_dokumentasi/sumber-latex/` (PDF: `01_dokumentasi/P1_Dokumentasi_Bab1-4.pdf`) |
| `belajar/` | `02_perhitungan_manual/` |
| `src/`, `tests/`, `configs/`, `scripts/`, `pyproject.toml`, `docs/experiments/` | di dalam `04_koding/` |
| `hasil/*.json`, `hasil/metrik-per-fold.csv` | `05_hasil/run/`, `05_hasil/metrik-per-fold.csv` |
| `docs/HASIL.md` | `05_hasil/HASIL_LENGKAP.md` |
| `docs/METODOLOGI.md`, `docs/REPRODUKSI.md` | `04_koding/` |
| `docs/CAPAIAN_P1.md`, `VERIFIKASI.md`, `PROVENANCE.*` | `lampiran/` |

Tambahan: `03_web_belajar/` (web animasi offline beserta tesnya) dan `06_presentasi/`. Perubahan kode hanya pada path di `scripts/smoke_p1.py` dan `scripts/verify_agents.sh`.
