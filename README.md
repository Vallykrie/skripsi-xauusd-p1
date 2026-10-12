# P1 · Klasifikasi arah XAUUSD

**Analisis Kontribusi Fitur Teknikal dan Makroekonomi terhadap Kinerja Klasifikasi Arah XAUUSD Menggunakan Regresi Logistik Multinomial dan XGBoost**

Bahan Penilaian Kemajuan 1 (P1). Berita acara P0 menetapkan target minimum 50%: koding 50% dan dokumentasi sampai perhitungan manual, batas **Selasa, 27 Oktober 2026**. Persentase resmi ditentukan pembimbing, bukan oleh repo ini.

## Mulai dari sini

| Folder | Isi | Mulai dari |
|---|---|---|
| [`01_dokumentasi`](01_dokumentasi) | Draf Bab 1–4 (40 halaman) dan sumber LaTeX | [`P1_Dokumentasi_Bab1-4.pdf`](01_dokumentasi/P1_Dokumentasi_Bab1-4.pdf) |
| [`02_perhitungan_manual`](02_perhitungan_manual) | Excel 8 tab berumus aktif dan panduan dengan jawaban | [`Perhitungan_Manual_P1.xlsx`](02_perhitungan_manual/Perhitungan_Manual_P1.xlsx), tab `Mulai` |
| [`03_web_belajar`](03_web_belajar) | Web animasi offline: label sampai pohon XGBoost | [`Lab_P1_XAUUSD.html`](03_web_belajar/Lab_P1_XAUUSD.html) |
| [`04_koding`](04_koding) | **Notebook ringkas alur koding**, kode Fase 4, tes, konfigurasi beku, skrip | [`notebook/README.md`](04_koding/notebook/README.md), lalu [`README.md`](04_koding/README.md) (peta kode) |
| [`05_hasil`](05_hasil) | Ringkasan hasil, metrik per periode, agregat 24 run | [`README.md`](05_hasil/README.md) |
| [`06_presentasi`](06_presentasi) | Alur bicara 10–15 menit | [`README.md`](06_presentasi/README.md) |
| [`lampiran`](lampiran) | Peta capaian, verifikasi, provenance | [`CAPAIAN_P1.md`](lampiran/CAPAIAN_P1.md) |

## Target berita acara dan buktinya

| Butir | Bukti | Status |
|---|---|---|
| Koding 50% | `04_koding/` dan `05_hasil/` | Pipeline lengkap sudah berjalan: 24 run, 56 tes portabel |
| Dokumentasi | `01_dokumentasi/` | Draf Bab 1–4 |
| Perhitungan manual | `02_perhitungan_manual/`, `03_web_belajar/` | Label, RSI/MACD, praproses, Logistik, XGBoost, metrik |
| Pengesahan P1, logbook sah | Pembimbing | NOT TESTED |

## Jalankan tes

```bash
cd 04_koding
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
bash scripts/verify_agents.sh
python scripts/smoke_p1.py
node --test ../03_web_belajar/tests/lab-math.test.mjs
```

**Dua jenis angka:** `02_perhitungan_manual/` dan bab 00–06 web memakai angka SINTETIS untuk memahami rumus. `05_hasil/` dan bab 07 web memuat hasil penelitian aktual. BUY/HOLD/SELL adalah kelas arah, bukan instruksi transaksi. Hasil kecil atau negatif tetap dilaporkan; tidak ada klaim profit.

Repo ini **privat**. Satu-satunya data vendor yang disertakan ada di `04_koding/notebook/data/` (harga XAUUSD H1 MetaQuotes-Demo dan kalender MT5, byte-identik dengan input penelitian) beserta output notebook; keduanya harus dihapus sebelum repo dijadikan publik. Prediksi per bar pipeline resmi, model binari, formulir kampus, identitas administratif, dan kredensial tidak disertakan. Notebook menghasilkan ulang 42 skor run utama secara identik; reproduksi lewat skrip `04_koding/scripts/` tetap memerlukan artefak audit privat (NOT TESTED).

Bantuan AI dipakai untuk kurasi, dokumentasi, dan alat pembelajaran; mahasiswa bertanggung jawab memverifikasi dan menjelaskan seluruh metode. Rincian: [provenance dan penggunaan AI](lampiran/PROVENANCE.md).
