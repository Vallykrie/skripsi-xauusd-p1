# Reproduksi dan batas akses

Semua perintah dijalankan dari folder `04_koding/`.

## Tiga tingkat pemeriksaan

1. **Portabel:** `pytest`, Ruff, `verify_agents.sh`, `smoke_p1.py`. Menguji kode pipeline lama dengan data sintetis, menghitung ulang ringkasan selisih berpasangan di `05_hasil/` dari metrik per periode, dan memeriksa contoh manual bar ke-51.
2. **Notebook:** `notebooks/fase4/` 00–08 dengan input di `data/`. Ini menjalankan ulang eksperimen penuh dari data mentah. Uji 16 Oktober 2026 pada salinan paket ini (di luar git): notebook 00–05 menghasilkan artefak antara yang identik byte demi byte dengan run resmi, dan notebook 08 lulus termasuk uji determinisme.
3. **Rantai bukti asli:** konfigurasi beku dan kode notebook di-commit pada repo penelitian sebelum skor dibaca (commit `0a671a3`); manifes run mencatat commit itu dengan `worktree_bersih = True`. Salinan di repo ini tidak membawa riwayat Git tersebut.

## Catatan

- Run ulang di salinan ini adalah replikasi setelah skor diketahui, bukan run beku baru. Jangan mengubah `configs/phase4-p0.toml` lalu menyajikannya sebagai protokol yang sama.
- Kalender MT5 adalah snapshot vendor dengan batasan revisi, bukan arsip vintage independen.
- Ekstraksi data baru tidak termasuk paket P1. Login MT5 dilakukan manusia melalui GUI tanpa menuliskan kredensial. Seluruh API transaksi dilarang.
- Skrip pipeline lama (`scripts/run_phase4_*.py`) memerlukan artefak audit privat run lama dan tidak dipakai untuk hasil yang dilaporkan.

## Excel

Workbook dihitung ulang dengan LibreOffice setelah perubahan 16 Oktober 2026 (contoh manual digeser ke bar ke-51, tab `Hasil_Asli` diganti hasil notebook). Nilai bar ke-51 dicocokkan dengan Python dan dengan `smoke_p1.py`. Aplikasi Excel desktop: NOT TESTED.
