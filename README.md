# P1 · Klasifikasi arah XAUUSD

**Analisis Kontribusi Fitur Teknikal dan Makroekonomi terhadap Kinerja Klasifikasi Arah XAUUSD Menggunakan Regresi Logistik Multinomial dan XGBoost**

Paket publik untuk menjelaskan kode, metode, hasil awal, dan perhitungan manual pada Penilaian Kemajuan 1. Berita acara P0 menetapkan minimum 50%: “Koding 50 % dokumentasi sampai perhitungan manual”, batas **27 Oktober 2026**. Paket ini tidak menetapkan nilai/persentase resmi mahasiswa.

## Mulai dari sini

1. [Peta capaian dan kekurangan P1](docs/CAPAIAN_P1.md).
2. [Naskah Bab 1–4](naskah/P1_Dokumentasi.pdf) dan [sumbernya](naskah/README.md).
3. [Excel perhitungan manual](belajar/Perhitungan_Manual_P1.xlsx). Buka tab `Mulai`, ikuti urutan, ubah sel kuning.
4. [Panduan belajar beserta jawaban](belajar/PANDUAN_MANUAL.md).
5. [Metodologi dan peta kode](docs/METODOLOGI.md), [hasil penelitian](docs/HASIL.md), [reproduksi](docs/REPRODUKSI.md).

## Isi yang dipertahankan

| Direktori | Isi |
|---|---|
| `src/thesis_experiments/` | kode Fase 4: audit, fitur, fold, praproses, model, evaluasi |
| `configs/` | protokol dan kebijakan gap beku |
| `tests/` | pengujian portabel berbasis contoh sintetis |
| `naskah/` | draf Bab 1–4 dan referensi |
| `belajar/` | Excel aktif, panduan, data latihan sintetis |
| `hasil/` | agregat 24 run, metrik/parameter/kegagalan per fold, checksum |
| `docs/` | capaian P1, metodologi, reproduksi, provenance, batasan |

## Jalankan tanpa MT5

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
bash scripts/verify_agents.sh
python scripts/smoke_p1.py
```

Di macOS, XGBoost memerlukan libomp (`brew install libomp`) bila library itu belum tersedia. Windows: gunakan `.venv\Scripts\python.exe` sebagai interpreter.

**Dua jenis angka:** `belajar/` memuat angka SINTETIS untuk memahami rumus. `hasil/` memuat agregat penelitian aktual. Keduanya tidak boleh dicampur. BUY/HOLD/SELL adalah kelas arah, bukan instruksi transaksi. Peningkatan skor kecil/negatif tetap dilaporkan; tidak ada klaim profit.

Kode asli dan konfigurasi dikurasi dari snapshot branch `research/phase-4-experiments`, termasuk perubahan lokal yang sudah ada. Repo ini memakai riwayat Git baru. Data mentah, kalender privat, prediksi per bar, model binari, formulir kampus, identitas administratif dan kredensial tidak disertakan. Reproduksi pelatihan penuh dari clone publik saja: **NOT TESTED** karena input privat dikecualikan. Tes portabel dan perhitungan manual bisa dijalankan tanpa input tersebut.

Bantuan AI dipakai untuk kurasi, dokumentasi, dan alat pembelajaran; mahasiswa bertanggung jawab memverifikasi serta menjelaskan seluruh metode. Rincian [provenance dan penggunaan AI](docs/PROVENANCE.md).
