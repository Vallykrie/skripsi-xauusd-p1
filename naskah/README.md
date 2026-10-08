# Naskah P1

Bab 1–4 disalin dari naskah kerja 8 Oktober 2026; ini draf publik untuk pembahasan, bukan naskah resmi yang disahkan. Proposal LaTeX privat tetap sumber otoritatif protokol. Bab 4 memuat hasil asli terarsip, bukan contoh sintetis.

Bangun dengan TeX Live, Latin Modern Roman, XeLaTeX, Biber, dan latexmk:
```bash
cd naskah
latexmk -xelatex -halt-on-error -outdir=build p1.tex
```
Tampilan ini memakai report generik tanpa logo/halaman pengesahan; sumber kelas FILKOM dan data administrasi tidak dipublikasikan. PDF kurasi tersedia sebagai `P1_Dokumentasi.pdf`.
