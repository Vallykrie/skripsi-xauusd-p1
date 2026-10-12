# Notebook: alur koding skripsi dalam 4 langkah

Versi ringkas dari kode penelitian (`../src/thesis_experiments/`). Isinya hanya logika inti, tanpa validasi panjang dan pencatatan provenance. Hasilnya **identik** dengan pipeline resmi: fitur, label, dan kolom makro sudah dicocokkan baris per baris, dan 42 skor Macro-F1 (7 periode × 2 model × 3 konfigurasi) sama dengan run resmi `metaquotes-demo-primary-0p5-k3`, selisih terbesar 5,6×10⁻¹⁷.

| Notebook | Isi | Output |
|---|---|---|
| `01_data_dan_gap.ipynb` | Baca harga H1, pemeriksaan dasar, gap, 10 segmen | `output/01_harga.parquet` |
| `02_label_dan_fitur.ipynb` | σ24, label BUY/HOLD/SELL, K1, RSI/MACD (K2), fitur makro (K3) | `output/02_fitur.parquet` |
| `03_walkforward_dan_model.ipynb` | 7 periode uji, purge, praproses, pemilihan parameter, Logistik dan XGBoost | `output/03_prediksi.parquet`, `output/03_parameter.csv` |
| `04_evaluasi.ipynb` | Macro-F1, balanced accuracy, K2−K1, K3−K2, grafik, cocokkan dengan hasil resmi | — |

Jalankan berurutan 01 → 04. Setiap notebook membaca output notebook sebelumnya.

## Cara membuka

Paling mudah di VS Code (ekstensi Jupyter), pilih interpreter `04_koding/.venv` (lihat README `04_koding`). Atau dari terminal di folder ini:

```bash
python -m pip install jupyterlab numpy pandas pyarrow scikit-learn==1.9.0 xgboost==2.1.4 matplotlib
jupyter lab
```

Notebook 03 adalah yang paling lama: sekitar 6 menit di MacBook ini (504 model XGBoost dan 252 model Logistik untuk pemilihan parameter, ditambah 42 model akhir). Untuk mencoba cepat, isi `PERIODE_DIJALANKAN = ["2023-H1"]` di sel pertamanya. Notebook 04 tetap jalan dengan sebagian periode, tetapi pencocokan resmi hanya untuk periode yang dijalankan.

## Data

`data/` berisi salinan byte-identik input penelitian (SHA-256 sama dengan konfigurasi beku): harga XAUUSD H1 MetaQuotes-Demo dan kalender ekonomi MT5. Data vendor ini hanya boleh berada di repo **privat**. Jika repo dijadikan publik, hapus `data/` dan `output/` serta bersihkan output sel notebook terlebih dahulu: ketentuan redistribusi MetaQuotes/MT5 belum diperiksa.

## Yang sengaja tidak ada di notebook

Audit sesi MT5 lengkap (hasilnya, 9 gap tak terjelaskan, ditulis langsung di notebook 01), sensitivitas ambang 0,25/1,0, policy holiday-reset, sumber Ultima, analisis hiperparameter tetap, diagnostik kelas mayoritas, checksum dan manifest. Semua itu tetap ada di kode penelitian dan dilaporkan di Bab 4.
