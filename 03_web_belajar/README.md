# 03 · Web belajar P1

Buka `Lab_P1_XAUUSD.html` langsung di browser (klik dua kali). Satu berkas, tanpa server, tetap jalan tanpa internet (font memakai bawaan sistem jika offline).

Sembilan bab langkah demi langkah: Peta P1, Label, Fitur K1–K3, Regresi Logistik, XGBoost, Walk-forward, Evaluasi, Hasil asli, Latihan. Tombol → / ← berpindah langkah, spasi memutar otomatis, `P` mode presentasi.

Bab XGBoost menumbuhkan pohon dari perhitungan langsung: g dan h per sampel, semua titik potong dicoba beserta gain, sampel turun ke cabang, bobot daun, jalur satu sampel uji, tiga pohon per kelas lalu softmax, dan iterasi 2–3 yang mengulang dengan p baru. Pilihan kelas, kedalaman (1/2), iterasi (1–3), dan x uji bisa diubah.

Angka bab 00–06 sintetis dan sama dengan `../02_perhitungan_manual/Perhitungan_Manual_P1.xlsx`. Bab 07 memuat Macro-F1 asli dari `../05_hasil/metrik-per-fold.csv` (run `metaquotes-demo-primary-0p5-k3`).

Batas contoh XGBoost: pencarian greedy semua titik tengah, λ = 1, γ = 0, min_child_weight = 0,5, η = 0,1, tanpa subsampling. Model penelitian memakai `tree_method="hist"`, min_child_weight 1, subsample/colsample 0,8, dan kisi Bab 3. Kedalaman 1 / iterasi 1 identik dengan tab XGBoost di Excel.

## Tes

```bash
node --test tests/lab-math.test.mjs
```

Tujuh tes membandingkan rumus web dengan angka acuan workbook (σ24, δ, label, RSI/MACD, langkah Logistik, gain stump 0,790588235, pohon HOLD dua tingkat, iterasi, Macro-F1).
