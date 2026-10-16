# Belajar perhitungan manual untuk P1

Tujuannya: Anda mampu menjelaskan satu observasi sejak harga sampai skor evaluasi, serta membedakan pelabelan, pelatihan, dan prediksi. Semua angka contoh di sini **SINTETIS**, kecuali bagian hasil penelitian yang diberi label tersendiri. Workbook `Perhitungan_Manual_P1.xlsx` memakai rumus aktif; sel kuning dapat diubah. Simulator harga hanya mencakup 61 bar kontinu, bukan pengganti audit gap produksi.

## 1. Pahami masalahnya sebelum rumus

Saat satu bar H1 selesai, kita mengetahui open/high/low/close bar tersebut. Kita mencoba mengklasifikasikan arah **penutupan bar berikutnya**. Data vendor tidak memberi label BUY/HOLD/SELL. Label dibuat dari harga berikutnya saat menyusun dataset historis. Dalam prediksi, harga berikutnya belum diketahui.

- Fitur: informasi yang sudah diketahui saat keputusan.
- Label benar: jawaban yang diketahui satu jam kemudian.
- Model: mempelajari hubungan fitur dan label dari masa lalu.
- Evaluasi: membandingkan prediksi dengan label pada periode yang lebih baru.

BUY berarti naik melampaui ambang, SELL turun melampaui ambang, HOLD perubahan di antara keduanya. Ketiganya kelas arah, bukan perintah trading.

## 2. Return, volatilitas dan label

Buka `Harga_Target`. Bar pertama dimulai pada 5 Januari 2026 00:00 UTC, bar selanjutnya satu jam kemudian. Bar ke-51 terdapat pada **baris Excel 57**; ini observasi pertama yang layak karena Bab 3 mensyaratkan sedikitnya 50 bar pemanasan (bar 1–50, baris 7–56, bertanda WARM-UP). Jika open time-nya 7 Januari 01:00, keputusan dibuat 02:00, dan label baru diketahui 03:00 setelah bar selanjutnya selesai.

### Log-return

$$r_t=\ln(C_t/C_{t-1}).$$

Contoh close 2018 ke 2017: `LN(2017/2018)` = **−0,0004956630**, sekitar −0,04957%. Excel `F57=LN(E57/E56)`. Nilai ini adalah return historis yang sudah diketahui, bukan target masa depan.

### Volatilitas historis

Ambil 24 return terakhir F34:F57. Ini membutuhkan 25 harga penutupan untuk membentuk 24 perubahan.

$$\bar r=\frac{\sum_{i=1}^{24}r_i}{24},\qquad \sigma_{24}=\sqrt{\frac{\sum_{i=1}^{24}(r_i-\bar r)^2}{23}}.$$

`G57=AVERAGE(F34:F57)` = 0,0001655905. `H57=STDEV.S(F34:F57)` = **0,0010629949**. Pembagi 23 berasal dari simpangan baku sampel. Jangan memakai STDEV.P untuk volatilitas target ini.

### Ambang dan label satu bar

$$\delta_t=0{,}5\sigma_{24};\qquad q_{t+1}=\ln(C_{t+1}/C_t).$$

Pada baris 57: δ = **0,0005314974**. Close berikutnya 2020, sehingga `J57=LN(2020/2017)` = **0,0014862524**.

| Kondisi | Label |
|---|---|
| q > δ | BUY |
| q < −δ | SELL |
| −δ ≤ q ≤ δ | HOLD |

Karena 0,0014862524 > 0,0005314974, labelnya **BUY**: kenaikan berikutnya melewati ambang atas.

**Coba:** ubah `E58` dari 2020 menjadi **2018**. q menjadi `LN(2018/2017)` ≈ 0,0004956630, berada di antara −δ dan δ sehingga `L57` menjadi **HOLD**. Dengan **2015**, q ≈ −0,0009920636 < −δ sehingga label **SELL**. Kembalikan 2020 setelah latihan. High/low/open tidak digunakan untuk langkah label ini; bila menjadikan tabel sebagai input kode produksi, relasi OHLC juga harus diperbaiki agar sah.

Sel `B4` mengubah pengali untuk melihat sensitivitas; dalam penelitian utama nilainya tetap 0,5, tidak dipilih dari skor terbaik. 0,25 dan 1,0 adalah run terpisah. Sigma nol membuat observasi tidak layak. Bar terakhir tidak memiliki target. Pemanasan: observasi baru dipakai setelah sedikitnya 50 bar, jadi bar ke-51 adalah yang pertama layak. Di data riil target juga harus tepat satu jam, satu segmen, dan berakhir sebelum batas akhir fold.

### Sembilan fitur K1

Enam lag r_t sampai r_(t−5), `LN(C/O)`, `LN(H/L)`, dan σ24. Contoh bentuk bar ada di kolom M; rentang bar = `LN(C57/D57)` karena C=High dan D=Low pada tabel ini. Target q bukan fitur. K2 menambahkan RSI dan tiga komponen MACD.

## 3. RSI memakai perubahan harga, bukan log-return

Buka `RSI_MACD`. `d=close sekarang−close sebelumnya`; gain=max(d,0); loss=max(−d,0).

Untuk 14 perubahan pertama, rata-rata gain dan loss berupa rata-rata aritmetika. Pada contoh, jumlah gain 15, jumlah loss 10, sehingga seed:

$$\overline g=15/14=1{,}071429,\quad\overline\ell=10/14=0{,}714286.$$

RS=15/10 dan RSI=100−100/(1+15/10)=**60,000000**. Ini baris Excel 21, bar ke-15, karena 14 perubahan membutuhkan 15 harga.

Bar berikutnya gain=3, loss=0. Wilder:

$$\overline g_{baru}=(13\overline g+3)/14=1{,}209184;\quad\overline\ell_{baru}=(13\overline\ell+0)/14=0{,}663265.$$

RSI baru ≈ **64,577657**. Lanjutkan rekursi hingga baris 57 (bar ke-51); hasilnya **58,73572475**. Tidak menghitung ulang SMA 14 pada setiap bar. Jika gain/loss rata-rata sama-sama nol, RSI=50; loss nol saja memberi 100; gain nol saja memberi 0.

## 4. EMA dan MACD

EMA(p) harus di-seed dengan rata-rata p harga awal:

$$EMA_p(t)=\alpha C_t+(1-\alpha)EMA_p(t-1),\quad\alpha=2/(p+1).$$

EMA12 pertama di `I18=AVERAGE(B7:B18)`. EMA26 pertama di `J32=AVERAGE(B7:B32)`. Setelah keduanya tersedia, MACD = EMA12−EMA26 (`K32`). Sinyal9 pertama di `L40=AVERAGE(K32:K40)`, kemudian α=2/10=0,2. Histogram=MACD−sinyal.

Pada baris 57: MACD/C = **0,0011625092**, sinyal/C = **0,0011563457**, hist/C = **0,00000616353**. Workbook memperlihatkan EMA dan selisih mentah agar mudah diikuti; kode model memakai ketiga komponen yang dibagi close. RSI tetap pada skala 0–100. Setelah gap tak terjelaskan, seluruh seed dimulai ulang dan pemanasan 50 bar diterapkan lagi (observasi mulai bar ke-51 segmen).

## 5. Praproses dan bobot kelas

Buka `Logistik`. Enam input x adalah −2,−1,0,1,2,3 dengan label SELL,SELL,HOLD,HOLD,BUY,BUY. Ini satu fitur ilustratif, bukan keenam bar pertama data penelitian.

Mean train=0,5. Varians populasi=(6,25+2,25+0,25+0,25+2,25+6,25)/6 = 17,5/6. Std=**1,707825128**. Untuk x=3:

$$x'=(3-0{,}5)/1{,}707825128=1{,}463850109.$$

Gunakan `STDEV.P`, sebab StandardScaler memakai ddof=0. Fit mean/std dari train saja; x uji 300 tidak boleh mengubah mean train. Kolom konstan memakai skala efektif 1 (x'=0 untuk nilai yang sama dengan mean).

Nilai hilang diisi median train, disertai indikator ketiadaan bila kolom pernah hilang pada train. Contoh train [1,kosong,3], median=2; uji [1000,kosong] berubah [1000,2], bukan memakai median dari uji. Kolom yang seluruhnya kosong pada train dibuang, walau ada angka pada uji. Tidak ada imputasi OHLC atau label.

Bobot kelas:

$$w_c=n/(3n_c).$$

Enam bar dengan dua per kelas memberi bobot 1. Jika distribusi train BUY=1,HOLD=4,SELL=1, bobot BUY/SELL=2, HOLD=0,5. Ini meningkatkan penalti kesalahan pada kelas minoritas; tidak menciptakan data baru.

## 6. Logistik: prediksi dan satu langkah pelatihan

### Prediksi

Setiap kelas mendapat logit:

$$z_c=b_c+\beta_c x',\quad p_c=\frac{e^{z_c-m}}{\sum_k e^{z_k-m}},\quad m=\max z.$$

Pengurangan m mencegah overflow dan tidak mengubah peluang. Saat b=β=0, ketiga logit=0 dan p=1/3. Prediksi memakai peluang terbesar; probabilitas tidak sama dengan harga/return.

### Pelatihan ilustratif

Pakai one-hot truth y_ic (1 pada kelas benar). Gradien berbobot per bar:

$$g_{ic}=w_i(p_{ic}-y_{ic}).$$

Untuk satu bar SELL dengan bobot1: g_SELL=−2/3, g_HOLD=1/3, g_BUY=1/3. Gradien negatif pada kelas benar mendorong logit kelas itu naik.

Workbook memakai objektif belajar **jumlah** cross-entropy berbobot + λ/2 Σβ², tanpa penalti bias. λ=0,1 dan eta=0,1. Ini pilihan latihan, bukan konversi numerik langsung C model riset.

$$b'_c=b_c-\eta\sum_i g_{ic},\quad \beta'_c=\beta_c-\eta(\sum_i g_{ic}x'_i+\lambda\beta_c).$$

Karena kelas seimbang, gradien bias total nol. Beta baru SELL ≈ **−0,234216018**, HOLD≈0, BUY≈**+0,234216018**. Pada x uji=3, logit sesudah ≈ [−0,342857143,0,+0,342857143]. Probabilitas [SELL,HOLD,BUY] = **[0,227574947;0,320645697;0,451779355]**. Prediksi **BUY**.

Cross-entropy awal=6×ln3 = **6,591673732**. Regularisasi awal nol karena beta nol. Sel lambda akan memengaruhi langkah ketika beta sudah tidak nol; semakin besar lambda, semakin kuat penahanan beta. Eta terlalu besar dapat merusak pembelajaran.

**Batas:** produksi menggunakan solver **lbfgs**, L2 dan grid C={0,01;0,1;1;10}, dipilih lewat validasi internal. Workbook memakai satu langkah gradient descent untuk menjelaskan proses belajar, bukan mengklaim menghasilkan koefisien lbfgs yang sama.

## 7. XGBoost: tiga kelas dan satu iterasi

Buka `XGBoost`. Data sama dengan contoh Logistik, namun model pohon membaca x mentah. Ketiga logit awal sama sehingga p=1/3. Untuk tiap kelas:

$$g_{ic}=w_i(p_{ic}-y_{ic}),\quad h_{ic}=\max(2p_{ic}(1-p_{ic})w_i,10^{-16}).$$

Faktor **2** adalah batas diagonal Hessian pada objektif multikelas XGBoost 2.1.4. Jangan menggantinya dengan p(1−p) biner. Hessian softmax penuh juga mempunyai elemen luar diagonal; workbook mengikuti aproksimasi diagonal implementasi, bukan menganggap Hessian penuh diagonal.

Bobot1 memberi h=4/9. Satu bar SELL memberi gradien [−2/3,1/3,1/3]. Jumlahkan G dan H per calon daun.

### Hitung split kelas SELL dengan cut −0,5

Daun kiri memiliki x=−2,−1 (keduanya SELL): G_L=−4/3, H_L=8/9. Daun kanan empat bar: G_R=4/3,H_R=16/9. Total G=0,H=24/9.

Dengan λ=1 dan γ=0:

$$w^*_j=-G_j/(H_j+\lambda).$$

w kiri = (4/3)/(17/9) = **12/17=0,705882353**. w kanan = −(4/3)/(25/9)= **−12/25=−0,48**.

$$Gain=\frac12\left[\frac{G_L^2}{H_L+\lambda}+\frac{G_R^2}{H_R+\lambda}-\frac{G^2}{H+\lambda}\right]-\gamma=\mathbf{0{,}790588235}.$$

Bandingkan kandidat cut −0,5 dan 1,5 pada tiap kelas. Bobot kiri/kanan bukan probabilitas; itu tambahan logit. Workbook memakai **min_child_weight=0,5** untuk contoh enam bar, sedangkan produksi memakai default1. Jika memakai 1, sisi dua bar memiliki H=8/9<1 sehingga split ini tidak sah. Perbedaan tersebut sengaja dicatat agar contoh tetap kecil.

Pada x uji=3, daun terpilih [SELL,HOLD,BUY] ≈ [−0,48;0,24;0,705882353]. Kalikan eta=0,1: logit baru [−0,048;0,024;0,070588235]. Softmax memberi sekitar [0,31244517;0,33577087;0,35178396], sehingga **BUY**. Lihat nilai presisi aktif di B36:B38. Tidak ada transaksi yang dieksekusi.

Model multikelas lazimnya membangun satu pohon per kelas per iterasi. `n_estimators=100` adalah 100 iterasi boosting; jangan menyebutnya 100 pohon total untuk tiga kelas. Contoh ini hanya satu iterasi dengan stump dan dua kandidat split; produksi memakai kedalaman3/5, eta0,05/0,1, iterasi100/300, subsample0,8, colsample0,8, lambda1, seed42, tree_method hist. Tidak mereplikasi keseluruhan training produksi dengan tangan.

## 8. Makro: kapan angka boleh dipakai?

Contoh sintetis actual CPI=3,2%,forecast=3,0%, surprise=**0,2 poin persentase**, bukan 0,2% perubahan relatif. Rilis 13:30 UTC:

| Waktu keputusan | Boleh dipakai? | Mengapa |
|---|---|---|
| 13:00 | tidak | belum rilis |
| 13:30 | tidak | aturan rilis harus lebih kecil secara ketat |
| 14:00 | ya | umur 0,5 jam |
| tujuh hari kemudian 13:30 | surprise hilang | umur 168 jam, kedaluwarsa |

Jika forecast kosong, surprise **MISSING**, bukan actual−0. Umur capped168; penanda within1/6/24 jam hanya sesudah rilis. Kalender nyata dibagi menurut keluarga; angka CPI dan NFP tidak dicampur satu kolom.

Validitas join waktu tidak sama dengan validitas vintage. K3 penelitian memiliki anchor timestamp yang cocok, tetapi snapshot historis bisa mencerminkan revisi actual/forecast. Hasil K3 berlaku pada snapshot retrospektif, bukan bukti simulasi real-time sepenuhnya point-in-time.

## 9. Walk-forward, purge dan penalaan

Latih awal [1 Jan2020,1 Jan2023). Uji pertama [1 Jan2023,1 Jul2023). Fold berikutnya menambah masa lalu ke latih. Tujuh fold terjadwal, terakhir [1 Jan2026,1 Agu2026). Interval setengah terbuka: awal termasuk, akhir tidak.

Untuk fold pertama, validasi internal terdiri dari Jul–Des2021, Jan–Jun2022, Jul–Des2022. Kandidat C/XGBoost dipilih berdasarkan **rata-rata tiga macro-F1 internal**. Kegagalan satu blok membuat kandidat tidak sah; tidak memakai rata-rata dua blok tersisa. Setelah dipilih, latih ulang seluruh train luar, baru prediksi test. Skor test tidak memilih parameter.

Contoh purge: keputusan latih 23:00, akhir target 00:00; keputusan pertama test 00:00. Observasi latih tersebut dibuang karena akhir label **sama dengan** keputusan pertama test. Keputusan latih 22:00 dengan akhir target23:00 masih sah. Target test yang berakhir tepat batas akhir interval juga dikeluarkan. Riwayat fitur yang sudah terjadi boleh digunakan untuk pemanasan. Pada data riil, "keputusan pertama test" adalah waktu keputusan observasi layak pertama di blok itu; misalnya periode 2023-H1 dimulai 1 Januari, tetapi keputusan pertamanya 3 Januari 2023 02:00 UTC karena pasar tutup saat libur tahun baru.

**Mengapa tidak random split?** Bar masa depan bisa masuk train untuk memprediksi masa lalu. Median/scaler dapat membawa informasi distribusi masa depan. Protokol kronologis menjaga urutan ketersediaan informasi; tidak menjamin skor tinggi.

## 10. Matriks kebingungan, F1 dan balanced accuracy

Buka `Evaluasi`. Baris truth, kolom prediksi; urutan BUY,HOLD,SELL:

| Truth / Pred | BUY | HOLD | SELL |
|---|---:|---:|---:|
| BUY | 4 | 1 | 1 |
| HOLD | 1 | 5 | 0 |
| SELL | 2 | 1 | 3 |

Untuk BUY: TP=4; FP=1+2=3 (kolom BUY di luar diagonal); FN=1+1=2 (baris BUY di luar diagonal).

$$Precision=TP/(TP+FP)=4/7;\quad Recall=TP/(TP+FN)=4/6.$$

$$F1=2TP/(2TP+FP+FN)=8/13=0{,}615384615.$$

HOLD: TP5,FP2,FN1 → F1=10/13=0,769230769. SELL: TP3,FP1,FN3 → F1=6/10=0,6.

$$MacroF1=(0{,}615384615+0{,}769230769+0{,}6)/3=\mathbf{0{,}661538462}.$$

Balanced accuracy adalah rata-rata recall: (4/6+5/6+3/6)/3=**0,666666667**. Accuracy=(4+5+3)/18 juga 0,666666667 pada contoh seimbang ini, namun tidak selalu sama pada data tak seimbang.

Jika sebuah kelas benar tidak muncul, recall tidak terdefinisi sehingga balanced accuracy tiga kelas tidak dilaporkan. F1 dengan penyebut nol ditetapkan0, dan macro tetap dibagi3. Coba nolkan satu baris truth. Jangan mengubahnya diam-diam menjadi evaluasi dua kelas.

## 11. Mengukur kontribusi kelompok fitur

Untuk satu model dan periode uji pada bar/label yang sama:

$$\Delta_{teknikal}=F1(K2)-F1(K1),\quad\Delta_{makro}=F1(K3)-F1(K2).$$

Tab `Hasil_Asli` berisi **hasil penelitian aktual** dari run notebook Fase 4 (16 Oktober 2026): MetaQuotes-Demo, ambang 0,5. Logistik periode 2023-H1: K1=0,4237922724; K2=0,4232301924; selisih=**−0,0005620800**. Tambahan teknikal menurunkan skor sedikit pada periode itu.

Rata-rata tujuh selisih tanpa bobot jumlah bar: Logistik K2−K1=+0,0000891404, XGBoost=−0,0010833324; periode positif 4/7 dan 4/7. K3−K2 Logistik=−0,0006335018, XGBoost=+0,0004788672; periode positif 3/7 dan 3/7. Angka ini tidak sama dengan contoh matriks sintetis di atas.

Rerata periode tidak sama dengan F1 dari matriks gabungan semua periode. Simpangan baku ringkasan memakai pembagi n−1; tidak dihitung untuk satu pasangan. Bila suatu periode gagal dievaluasi, periode itu tetap dihitung dalam penyebut tujuh dan tidak diberi skor nol.

Selisih kecil dan tidak konsisten tetap menjawab pertanyaan penelitian. Hiperparameter setiap konfigurasi disetel ulang, sehingga ini perubahan bersyarat fitur + retuning. Sensitivitas parameter tetap membantu memisahkan kedua unsur; tidak mengubahnya menjadi bukti sebab-akibat.

## 12. Latihan mandiri dan kunci jawaban

Kerjakan dahulu tanpa membuka Excel:

1. C_t=2000,C_(t+1)=2002,σ24=0,001. Apa label utama?
2. q persis sama dengan +δ. BUY atau HOLD?
3. Mengapa 24 return membutuhkan25 close?
4. Train [1,kosong,3],uji [1000,kosong]. Apa imputasi kosong pada uji?
5. n=6,BUY1,HOLD4,SELL1. Apa bobot kelas?
6. Apakah RSI=70 otomatis membuat label BUY?
7. Pada softmax, semua logit ditambah10. Apakah peluang berubah?
8. Mengapa daun XGBoost boleh negatif, sedangkan probabilitas tidak?
9. Rilis=13:30,keputusan=13:30. Apakah surprise boleh masuk?
10. F1 K1=0,40,K2=0,39. Apakah eksperimen gagal?
11. Satu fold tidak memiliki kelas SELL benar. Apakah balanced accuracy3kelas sah?
12. Apa yang perlu ditunjukkan untuk P1 selain jumlah kode?

**Jawaban:** (1) q=ln1,001≈0,0009995003>0,0005 → BUY. (2) HOLD karena batas inklusif. (3) return memakai pasangan dua close. (4)2 dari median train. (5)BUY2,HOLD0,5,SELL2. (6)Tidak; label dibentuk dari target return, RSI fitur. (7)Tidak; faktor e^10 saling membatalkan. (8)Daun adalah tambahan logit, bukan probabilitas. (9)Tidak; join ketat `<`. (10)Tidak;Δ=−0,01 adalah temuan. (11)Tidak;recallSELL tak terdefinisi. (12)Dokumentasi metode, bukti pengujian/hasil, perhitungan manual, pemahaman mandiri dan review pembimbing.

## Rujukan rumus/software

Protokol fitur/label: naskah Bab3 dan source features.py. Softmax/L2: [dokumentasi scikit-learn](https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression). F1: [definisi scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html). Daun/gain: [tutorial resmi XGBoost](https://xgboost.readthedocs.io/en/stable/tutorials/model.html). Hessian multikelas: [kode objektif XGBoost2.1.4](https://raw.githubusercontent.com/dmlc/xgboost/v2.1.4/src/objective/multiclass_obj.cu). Diakses8Oktober2026. Implementasi manual sengaja lebih kecil daripada model produksi.
