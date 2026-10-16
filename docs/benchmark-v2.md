# Natywne pomiary profilu execution-2

Pomiary lokalne Windows x64, Intel Core i5-12500H, FDS 6.11.1. Zachowano model fizyczny i siatkę.
Każdy wariant ma jedną rozgrzewkę oraz trzy pomiary. Czas całkowity obejmuje pracę solvera i przygotowanie danych;
czas konwersji przyrostowej częściowo nakłada się na solver i nie należy go ponownie dodawać. Niezależna kontrola fdsreader odbywa się poza pomiarem.

Źródło: `benchmark-v2.json`. Zapisano 60 ukończonych prób. Docelowa macierz preview zawiera 60 prób.

Pełne dane pomiarowe, sondy, maski affinity i profilowanie FDS: [benchmark-v2-data.json](benchmark-v2-data.json).

| Scena / czas | Wariant | Mediana całości s | Min–max s | Odch. s | Przyspieszenie | Bramka pól i energii |
|---|---|---:|---:|---:|---:|---|
| burner / 2 s / preview | openmp | 190.42 | 179.08–190.57 | 6.59 | 1.000× | PASS |
| burner / 2 s / preview | mpi2 | 159.33 | 156.92–164.29 | 3.75 | 1.195× | FAIL |
| burner / 2 s / preview | mpi4 | 133.62 | 132.38–149.18 | 9.37 | 1.425× | FAIL |
| candle / 2 s / preview | openmp | 227.43 | 226.07–230.56 | 2.30 | 1.000× | PASS |
| candle / 2 s / preview | mpi2 | 142.50 | 142.44–143.16 | 0.40 | 1.596× | PASS |
| candle / 2 s / preview | mpi4 | 129.53 | 128.23–131.05 | 1.41 | 1.756× | PASS |
| burner / 6 s / preview | openmp | 826.78 | 825.70–831.04 | 2.83 | 1.000× | PASS |
| burner / 6 s / preview | mpi2 | 554.68 | 552.43–557.16 | 2.37 | 1.491× | FAIL |
| burner / 6 s / preview | mpi4 | 440.24 | 439.91–441.06 | 0.59 | 1.878× | FAIL |
| candle / 6 s / preview | openmp | 668.13 | 657.52–673.97 | 8.34 | 1.000× | PASS |
| candle / 6 s / preview | mpi2 | 419.32 | 417.08–422.15 | 2.54 | 1.593× | PASS |
| candle / 6 s / preview | mpi4 | 339.90 | 339.88–342.55 | 1.54 | 1.966× | PASS |
| wood / 15 s / preview | openmp | 1049.99 | 970.84–1055.12 | 47.25 | 1.000× | PASS |
| wood / 15 s / preview | mpi2 | 610.87 | 606.95–614.18 | 3.62 | 1.719× | FAIL |
| wood / 15 s / preview | mpi4 | 507.55 | 504.95–510.88 | 2.97 | 2.069× | FAIL |

Automatyczna promocja wymaga PASS dla każdego pomiaru i oszczędności mediany co najmniej 5%. Brak wyniku w tabeli oznacza brak dowodu, a nie pozytywną walidację.

## Szczegóły prób

| Scena / czas | Wariant / próba (0 = rozgrzewka) | Solver s | Konwersja s | Kroki | Pierwsza klatka s | Szczyt pamięci commit MiB | I/O odczyt/zapis MiB |
|---|---|---:|---:|---:|---:|---:|---:|
| burner / 2 | openmp / 0 | 183.90 | 0.98 | 1511 | 1.83 | 2342.4 | 0.1/63.5 |
| burner / 2 | openmp / 1 | 190.54 | 1.50 | 1511 | 2.21 | 2342.7 | 0.1/63.5 |
| burner / 2 | openmp / 2 | 190.38 | 1.15 | 1511 | 2.21 | 2342.5 | 0.1/63.5 |
| burner / 2 | openmp / 3 | 179.04 | 1.24 | 1511 | 2.21 | 2342.6 | 0.1/63.5 |
| burner / 2 | mpi2 / 0 | 165.90 | 1.70 | 1533 | 2.01 | 314.4 | 0.4/65.2 |
| burner / 2 | mpi2 / 1 | 164.24 | 1.41 | 1533 | 2.01 | 313.3 | 0.4/65.2 |
| burner / 2 | mpi2 / 2 | 159.30 | 1.29 | 1533 | 2.21 | 314.0 | 0.4/65.2 |
| burner / 2 | mpi2 / 3 | 156.89 | 1.28 | 1533 | 2.01 | 314.6 | 0.4/65.2 |
| burner / 2 | mpi4 / 0 | 198.37 | 5.93 | 1530 | 2.01 | 505.8 | 0.8/67.7 |
| burner / 2 | mpi4 / 1 | 149.16 | 4.42 | 1530 | 4.43 | 505.8 | 0.8/67.7 |
| burner / 2 | mpi4 / 2 | 133.58 | 3.75 | 1530 | 2.01 | 506.4 | 0.8/67.7 |
| burner / 2 | mpi4 / 3 | 132.35 | 3.72 | 1530 | 2.01 | 505.9 | 0.8/67.7 |
| candle / 2 | openmp / 0 | 162.04 | 1.27 | 1268 | 2.42 | 2342.5 | 0.1/60.2 |
| candle / 2 | openmp / 1 | 226.04 | 1.29 | 1268 | 2.21 | 2342.5 | 0.1/60.2 |
| candle / 2 | openmp / 2 | 227.38 | 1.25 | 1268 | 3.01 | 2342.7 | 0.2/60.2 |
| candle / 2 | openmp / 3 | 230.53 | 1.37 | 1268 | 3.41 | 2342.6 | 0.1/60.2 |
| candle / 2 | mpi2 / 0 | 143.05 | 1.86 | 1263 | 2.22 | 313.7 | 0.4/62.3 |
| candle / 2 | mpi2 / 1 | 142.40 | 1.41 | 1263 | 2.21 | 313.7 | 0.4/62.3 |
| candle / 2 | mpi2 / 2 | 143.12 | 1.32 | 1263 | 2.21 | 313.7 | 0.4/62.3 |
| candle / 2 | mpi2 / 3 | 142.46 | 1.48 | 1263 | 2.21 | 313.9 | 0.4/62.3 |
| candle / 2 | mpi4 / 0 | 129.95 | 4.49 | 1280 | 2.21 | 506.2 | 0.8/65.1 |
| candle / 2 | mpi4 / 1 | 129.50 | 4.03 | 1280 | 2.41 | 506.0 | 0.8/65.1 |
| candle / 2 | mpi4 / 2 | 131.02 | 4.13 | 1280 | 2.41 | 506.0 | 0.8/65.1 |
| candle / 2 | mpi4 / 3 | 128.20 | 3.94 | 1280 | 2.41 | 506.0 | 0.8/65.1 |
| burner / 6 | openmp / 0 | 820.54 | 5.79 | 4863 | 3.01 | 2342.7 | 0.2/140.6 |
| burner / 6 | openmp / 1 | 831.01 | 5.80 | 4883 | 3.21 | 2342.6 | 0.2/140.6 |
| burner / 6 | openmp / 2 | 825.66 | 5.27 | 4898 | 2.81 | 2342.6 | 0.2/140.6 |
| burner / 6 | openmp / 3 | 826.73 | 5.53 | 4882 | 3.22 | 2342.5 | 0.2/140.6 |
| burner / 6 | mpi2 / 0 | 567.35 | 5.99 | 4908 | 2.21 | 314.7 | 0.4/143.2 |
| burner / 6 | mpi2 / 1 | 554.64 | 5.19 | 4908 | 2.21 | 313.9 | 0.4/143.2 |
| burner / 6 | mpi2 / 2 | 552.38 | 5.02 | 4908 | 2.21 | 314.3 | 0.4/143.2 |
| burner / 6 | mpi2 / 3 | 557.11 | 5.18 | 4908 | 2.21 | 314.6 | 0.4/143.2 |
| burner / 6 | mpi4 / 0 | 452.44 | 14.35 | 4845 | 2.22 | 506.3 | 0.9/148.2 |
| burner / 6 | mpi4 / 1 | 439.83 | 13.06 | 4845 | 2.21 | 506.5 | 0.9/148.2 |
| burner / 6 | mpi4 / 2 | 440.19 | 13.03 | 4845 | 2.41 | 506.0 | 0.9/148.2 |
| burner / 6 | mpi4 / 3 | 441.04 | 13.02 | 4845 | 2.41 | 506.2 | 0.9/148.2 |
| candle / 6 | openmp / 0 | 659.93 | 5.30 | 3992 | 3.02 | 2342.7 | 0.2/137.7 |
| candle / 6 | openmp / 1 | 657.48 | 4.95 | 3992 | 2.95 | 2342.7 | 0.2/137.7 |
| candle / 6 | openmp / 2 | 673.93 | 4.33 | 3992 | 2.62 | 2342.7 | 0.2/137.7 |
| candle / 6 | openmp / 3 | 668.07 | 4.29 | 3992 | 2.81 | 2342.6 | 0.2/137.7 |
| candle / 6 | mpi2 / 0 | 418.54 | 5.23 | 3977 | 2.42 | 314.0 | 0.4/141.2 |
| candle / 6 | mpi2 / 1 | 419.26 | 4.54 | 3977 | 2.21 | 314.3 | 0.4/141.2 |
| candle / 6 | mpi2 / 2 | 422.10 | 4.60 | 3977 | 2.21 | 315.3 | 0.4/141.2 |
| candle / 6 | mpi2 / 3 | 417.04 | 4.44 | 3977 | 2.21 | 315.2 | 0.4/141.2 |
| candle / 6 | mpi4 / 0 | 339.53 | 11.60 | 4032 | 2.42 | 505.9 | 0.9/146.5 |
| candle / 6 | mpi4 / 1 | 342.52 | 11.02 | 4032 | 2.41 | 506.6 | 0.9/146.5 |
| candle / 6 | mpi4 / 2 | 339.87 | 10.96 | 4032 | 2.41 | 506.2 | 0.9/146.5 |
| candle / 6 | mpi4 / 3 | 339.80 | 11.08 | 4032 | 2.21 | 506.6 | 0.9/146.5 |
| wood / 15 | openmp / 0 | 1077.19 | 10.82 | 5176 | 3.22 | 2330.9 | 0.3/281.4 |
| wood / 15 | openmp / 1 | 970.76 | 12.50 | 5169 | 3.22 | 2330.9 | 0.3/281.2 |
| wood / 15 | openmp / 2 | 1055.10 | 10.35 | 5182 | 3.02 | 2330.9 | 0.3/281.4 |
| wood / 15 | openmp / 3 | 1049.97 | 10.02 | 5161 | 6.23 | 2330.8 | 0.3/281.4 |
| wood / 15 | mpi2 / 0 | 613.29 | 11.71 | 5145 | 2.21 | 310.5 | 0.6/286.9 |
| wood / 15 | mpi2 / 1 | 614.14 | 10.08 | 5145 | 2.21 | 309.7 | 0.6/286.9 |
| wood / 15 | mpi2 / 2 | 610.84 | 9.78 | 5145 | 2.21 | 309.7 | 0.6/286.9 |
| wood / 15 | mpi2 / 3 | 606.92 | 9.67 | 5145 | 2.21 | 310.3 | 0.6/286.9 |
| wood / 15 | mpi4 / 0 | 508.77 | 21.83 | 5179 | 2.42 | 505.3 | 1.2/297.6 |
| wood / 15 | mpi4 / 1 | 510.83 | 20.46 | 5179 | 2.42 | 506.1 | 1.2/297.6 |
| wood / 15 | mpi4 / 2 | 507.51 | 20.93 | 5179 | 2.63 | 504.9 | 1.2/297.6 |
| wood / 15 | mpi4 / 3 | 504.90 | 20.65 | 5179 | 2.41 | 505.2 | 1.2/297.6 |

## Zgodność numeryczna

### burner 2 s — openmp

| Pole | Maks. błąd RMS pola | Maks. błąd przy granicach siatek | Limit |
|---|---:|---:|---:|
| TEMPERATURE | 3.78189e-05 | — | 0.1 |
| HRRPUV | 6.32377e-05 | — | 0.2 |
| SOOT DENSITY | 5.56258e-05 | — | 0.25 |
| OXYGEN VOLUME FRACTION | 6.00303e-07 | — | 0.005 |
| U-VELOCITY | 0.00011865 | — | 0.2 |
| V-VELOCITY | 0.000125337 | — | 0.2 |
| W-VELOCITY | 2.37313e-05 | — | 0.2 |

Największa względna różnica energii: 1.32562e-07; limit 0,05.

### burner 2 s — mpi2

| Pole | Maks. błąd RMS pola | Maks. błąd przy granicach siatek | Limit |
|---|---:|---:|---:|
| TEMPERATURE | 0.0590685 | 0.0444283 | 0.1 |
| HRRPUV | 0.0194318 | 0.07901 | 0.2 |
| SOOT DENSITY | 0.0649467 | 0.0333697 | 0.25 |
| OXYGEN VOLUME FRACTION | 0.000721537 | 0.00068926 | 0.005 |
| U-VELOCITY | 0.306264 | 0.241846 | 0.2 |
| V-VELOCITY | 0.296079 | 0.248885 | 0.2 |
| W-VELOCITY | 0.0871758 | 0.0515923 | 0.2 |

Największa względna różnica energii: 0.000167015; limit 0,05.
Bramka obejmuje również warstwy komórek przy granicach podsiatek; szczegółowe błędy i sondy są w JSON.

### burner 2 s — mpi4

| Pole | Maks. błąd RMS pola | Maks. błąd przy granicach siatek | Limit |
|---|---:|---:|---:|
| TEMPERATURE | 0.0646046 | 0.0471507 | 0.1 |
| HRRPUV | 0.0164524 | 0.0239996 | 0.2 |
| SOOT DENSITY | 0.0732457 | 0.0509898 | 0.25 |
| OXYGEN VOLUME FRACTION | 0.000789814 | 0.000661963 | 0.005 |
| U-VELOCITY | 0.314178 | 0.271117 | 0.2 |
| V-VELOCITY | 0.333761 | 0.260901 | 0.2 |
| W-VELOCITY | 0.100784 | 0.0728226 | 0.2 |

Największa względna różnica energii: 0.000184006; limit 0,05.
Bramka obejmuje również warstwy komórek przy granicach podsiatek; szczegółowe błędy i sondy są w JSON.

### candle 2 s — openmp

| Pole | Maks. błąd RMS pola | Maks. błąd przy granicach siatek | Limit |
|---|---:|---:|---:|
| TEMPERATURE | 0 | — | 0.1 |
| HRRPUV | 0 | — | 0.2 |
| SOOT DENSITY | 0 | — | 0.25 |
| OXYGEN VOLUME FRACTION | 0 | — | 0.005 |
| U-VELOCITY | 0 | — | 0.2 |
| V-VELOCITY | 0 | — | 0.2 |
| W-VELOCITY | 0 | — | 0.2 |

Największa względna różnica energii: 0; limit 0,05.

### candle 2 s — mpi2

| Pole | Maks. błąd RMS pola | Maks. błąd przy granicach siatek | Limit |
|---|---:|---:|---:|
| TEMPERATURE | 0.000558169 | 0.000430109 | 0.1 |
| HRRPUV | 0.0358582 | 5.01872e-07 | 0.2 |
| SOOT DENSITY | 0.0010222 | 0.000638164 | 0.25 |
| OXYGEN VOLUME FRACTION | 6.33669e-06 | 5.2839e-06 | 0.005 |
| U-VELOCITY | 0.00534986 | 0.00104143 | 0.2 |
| V-VELOCITY | 0.0053885 | 0.000903543 | 0.2 |
| W-VELOCITY | 0.00157484 | 0.000649895 | 0.2 |

Największa względna różnica energii: 5.55265e-05; limit 0,05.
Bramka obejmuje również warstwy komórek przy granicach podsiatek; szczegółowe błędy i sondy są w JSON.

### candle 2 s — mpi4

| Pole | Maks. błąd RMS pola | Maks. błąd przy granicach siatek | Limit |
|---|---:|---:|---:|
| TEMPERATURE | 0.00065768 | 0.000862787 | 0.1 |
| HRRPUV | 0.0127784 | 0.0199972 | 0.2 |
| SOOT DENSITY | 0.00100404 | 0.000742574 | 0.25 |
| OXYGEN VOLUME FRACTION | 7.44439e-06 | 6.44962e-06 | 0.005 |
| U-VELOCITY | 0.00245647 | 0.0017114 | 0.2 |
| V-VELOCITY | 0.00246904 | 0.00146479 | 0.2 |
| W-VELOCITY | 0.00112755 | 0.00108128 | 0.2 |

Największa względna różnica energii: 6.33719e-05; limit 0,05.
Bramka obejmuje również warstwy komórek przy granicach podsiatek; szczegółowe błędy i sondy są w JSON.

### burner 6 s — openmp

| Pole | Maks. błąd RMS pola | Maks. błąd przy granicach siatek | Limit |
|---|---:|---:|---:|
| TEMPERATURE | 0.0166054 | — | 0.1 |
| HRRPUV | 0.00529592 | — | 0.2 |
| SOOT DENSITY | 0.0208754 | — | 0.25 |
| OXYGEN VOLUME FRACTION | 0.000201476 | — | 0.005 |
| U-VELOCITY | 0.111796 | — | 0.2 |
| V-VELOCITY | 0.105697 | — | 0.2 |
| W-VELOCITY | 0.030274 | — | 0.2 |

Największa względna różnica energii: 2.05384e-05; limit 0,05.

### burner 6 s — mpi2

| Pole | Maks. błąd RMS pola | Maks. błąd przy granicach siatek | Limit |
|---|---:|---:|---:|
| TEMPERATURE | 0.0526922 | 0.0492097 | 0.1 |
| HRRPUV | 0.0157467 | 0.0396009 | 0.2 |
| SOOT DENSITY | 0.0563993 | 0.0385371 | 0.25 |
| OXYGEN VOLUME FRACTION | 0.000644772 | 0.000704756 | 0.005 |
| U-VELOCITY | 0.219508 | 0.296085 | 0.2 |
| V-VELOCITY | 0.206816 | 0.282189 | 0.2 |
| W-VELOCITY | 0.0855795 | 0.0570403 | 0.2 |

Największa względna różnica energii: 5.16558e-05; limit 0,05.
Bramka obejmuje również warstwy komórek przy granicach podsiatek; szczegółowe błędy i sondy są w JSON.

### burner 6 s — mpi4

| Pole | Maks. błąd RMS pola | Maks. błąd przy granicach siatek | Limit |
|---|---:|---:|---:|
| TEMPERATURE | 0.0430885 | 0.0362497 | 0.1 |
| HRRPUV | 0.0173805 | 0.0141391 | 0.2 |
| SOOT DENSITY | 0.0441316 | 0.0339546 | 0.25 |
| OXYGEN VOLUME FRACTION | 0.000529541 | 0.000507047 | 0.005 |
| U-VELOCITY | 0.220306 | 0.208375 | 0.2 |
| V-VELOCITY | 0.208883 | 0.1862 | 0.2 |
| W-VELOCITY | 0.0590399 | 0.0539033 | 0.2 |

Największa względna różnica energii: 4.95191e-05; limit 0,05.
Bramka obejmuje również warstwy komórek przy granicach podsiatek; szczegółowe błędy i sondy są w JSON.

### candle 6 s — openmp

| Pole | Maks. błąd RMS pola | Maks. błąd przy granicach siatek | Limit |
|---|---:|---:|---:|
| TEMPERATURE | 0 | — | 0.1 |
| HRRPUV | 0 | — | 0.2 |
| SOOT DENSITY | 0 | — | 0.25 |
| OXYGEN VOLUME FRACTION | 0 | — | 0.005 |
| U-VELOCITY | 0 | — | 0.2 |
| V-VELOCITY | 0 | — | 0.2 |
| W-VELOCITY | 0 | — | 0.2 |

Największa względna różnica energii: 0; limit 0,05.

### candle 6 s — mpi2

| Pole | Maks. błąd RMS pola | Maks. błąd przy granicach siatek | Limit |
|---|---:|---:|---:|
| TEMPERATURE | 0.000479785 | 0.000170157 | 0.1 |
| HRRPUV | 0.0024602 | 1.93529e-07 | 0.2 |
| SOOT DENSITY | 0.000730911 | 0.000323833 | 0.25 |
| OXYGEN VOLUME FRACTION | 4.16662e-06 | 2.55747e-06 | 0.005 |
| U-VELOCITY | 0.00108809 | 0.000668797 | 0.2 |
| V-VELOCITY | 0.00101055 | 0.000582524 | 0.2 |
| W-VELOCITY | 0.000637308 | 0.000390991 | 0.2 |

Największa względna różnica energii: 8.89269e-06; limit 0,05.
Bramka obejmuje również warstwy komórek przy granicach podsiatek; szczegółowe błędy i sondy są w JSON.

### candle 6 s — mpi4

| Pole | Maks. błąd RMS pola | Maks. błąd przy granicach siatek | Limit |
|---|---:|---:|---:|
| TEMPERATURE | 0.000601526 | 0.000765272 | 0.1 |
| HRRPUV | 0.00584633 | 0.005664 | 0.2 |
| SOOT DENSITY | 0.00090596 | 0.000480562 | 0.25 |
| OXYGEN VOLUME FRACTION | 6.67873e-06 | 4.64587e-06 | 0.005 |
| U-VELOCITY | 0.00127579 | 0.00115073 | 0.2 |
| V-VELOCITY | 0.00133926 | 0.00127708 | 0.2 |
| W-VELOCITY | 0.000601098 | 0.000476132 | 0.2 |

Największa względna różnica energii: 1.535e-05; limit 0,05.
Bramka obejmuje również warstwy komórek przy granicach podsiatek; szczegółowe błędy i sondy są w JSON.

### wood 15 s — openmp

| Pole | Maks. błąd RMS pola | Maks. błąd przy granicach siatek | Limit |
|---|---:|---:|---:|
| TEMPERATURE | 0.0393228 | — | 0.1 |
| HRRPUV | 0.085807 | — | 0.2 |
| SOOT DENSITY | 0.0695168 | — | 0.25 |
| OXYGEN VOLUME FRACTION | 0.000441085 | — | 0.005 |
| U-VELOCITY | 0.17917 | — | 0.2 |
| V-VELOCITY | 0.177801 | — | 0.2 |
| W-VELOCITY | 0.0855924 | — | 0.2 |

Największa względna różnica energii: 0.000816618; limit 0,05.
Największa różnica czasu zapłonu: 0 s; limit 0,2 s. Brak zapłonu w obu przebiegach oznacza różnicę 0 s.

### wood 15 s — mpi2

| Pole | Maks. błąd RMS pola | Maks. błąd przy granicach siatek | Limit |
|---|---:|---:|---:|
| TEMPERATURE | 0.0812598 | 0.0912019 | 0.1 |
| HRRPUV | 0.129906 | 0.482381 | 0.2 |
| SOOT DENSITY | 0.133086 | 0.160111 | 0.25 |
| OXYGEN VOLUME FRACTION | 0.000938344 | 0.000959468 | 0.005 |
| U-VELOCITY | 0.242872 | 0.225339 | 0.2 |
| V-VELOCITY | 0.247546 | 0.178962 | 0.2 |
| W-VELOCITY | 0.128462 | 0.133815 | 0.2 |

Największa względna różnica energii: 0.0030903; limit 0,05.
Największa różnica czasu zapłonu: 0 s; limit 0,2 s. Brak zapłonu w obu przebiegach oznacza różnicę 0 s.
Bramka obejmuje również warstwy komórek przy granicach podsiatek; szczegółowe błędy i sondy są w JSON.

### wood 15 s — mpi4

| Pole | Maks. błąd RMS pola | Maks. błąd przy granicach siatek | Limit |
|---|---:|---:|---:|
| TEMPERATURE | 0.0619076 | 0.0693316 | 0.1 |
| HRRPUV | 0.121577 | 0.311939 | 0.2 |
| SOOT DENSITY | 0.104377 | 0.114964 | 0.25 |
| OXYGEN VOLUME FRACTION | 0.000727084 | 0.000806078 | 0.005 |
| U-VELOCITY | 0.246247 | 0.265897 | 0.2 |
| V-VELOCITY | 0.234359 | 0.253627 | 0.2 |
| W-VELOCITY | 0.113403 | 0.110969 | 0.2 |

Największa względna różnica energii: 0.00255025; limit 0,05.
Największa różnica czasu zapłonu: 0 s; limit 0,2 s. Brak zapłonu w obu przebiegach oznacza różnicę 0 s.
Bramka obejmuje również warstwy komórek przy granicach podsiatek; szczegółowe błędy i sondy są w JSON.

## Affinity i ograniczenia

Maski procesów MPI/FDS zmierzone w trakcie pracy są zapisane jako `observedProcessAffinity` w JSON. Nie utożsamiamy ich automatycznie z rdzeniami P.
Telemetria pamięci commit i I/O obejmuje procesy należące do Job Object solvera/MPI; nie obejmuje procesu Python wykonującego konwersję.
Raport zachowuje czasy podsystemów FDS w polu `cpu`, identyfikatory binariów i konfiguracji oraz dokładną zgodność eksportu siedmiu pól (`nativeExact`).
Porównania nie stanowią walidacji inżynierskiej. Definicje progów: [execution-v2.md](execution-v2.md).
