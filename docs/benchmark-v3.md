# Kampania execution-3

Stan: budget-stopped. Natywne próby: 23. Czas nowych zadań: 5.707 h.

Polityka validation-v3 jest osobno zatwierdzana. Brak promocji nie oznacza nieudanego pomiaru. Czasy archiwizacji i niezależnej kontroli są raportowane osobno.

| Scena | Profil | Etap | Próba | Całość s | Archiwum MiB |
|---|---|---|---:|---:|---:|
| burner 6s | openmp | reference | 0 | 1050.28 | 87.3 |
| burner 6s | openmp | reference | 1 | 968.26 | 87.2 |
| burner 6s | openmp | reference | 2 | 925.91 | 87.3 |
| burner 6s | openmp | reference | 3 | 917.56 | 87.3 |
| wood 15s | openmp | reference | 0 | 971.42 | 182.6 |
| wood 15s | openmp | reference | 1 | 1070.47 | 182.6 |
| wood 15s | openmp | reference | 2 | 1098.43 | 182.7 |
| wood 15s | openmp | reference | 3 | 1113.62 | 182.7 |
| burner 6s | mpi2-x2 | screen | -1 | 757.01 | 92.5 |
| wood 15s | mpi2-x2 | screen | -1 | 770.15 | 190.4 |
| burner 6s | mpi2-y2 | screen | -1 | 733.32 | 91.2 |
| wood 15s | mpi2-y2 | screen | -1 | 743.46 | 189.1 |
| burner 6s | mpi4-xy22 | screen | -1 | 718.53 | 96.6 |
| wood 15s | mpi4-xy22 | screen | -1 | 723.20 | 197.5 |
| burner 6s | mpi2-x2 | finalist | 0 | 757.67 | 92.5 |
| burner 6s | mpi2-x2 | finalist | 1 | 754.15 | 92.5 |
| burner 6s | mpi2-x2 | finalist | 2 | 765.65 | 92.5 |
| burner 6s | mpi2-x2 | finalist | 3 | 766.25 | 92.5 |
| wood 15s | mpi4-xy22 | finalist | 0 | 712.86 | 197.5 |
| wood 15s | mpi4-xy22 | finalist | 1 | 729.48 | 197.5 |
| wood 15s | mpi4-xy22 | finalist | 2 | 718.81 | 197.5 |
| wood 15s | mpi4-xy22 | finalist | 3 | 724.41 | 197.5 |
| burner 6s | mpi4-x4 | screen | -1 | 831.12 | 96.6 |

Niewykonane próby w tej kampanii: `mpi4-x4` (wood), `mpi4-y4` (burner, wood), `mpi2-z13` (burner, wood), `mpi2-z31` (burner, wood), `mpi4-z1124` (burner, wood), `mpi4-z4211` (burner, wood), `hybrid2x2-z` (burner, wood), `mpi2` (burner, wood), `mpi4` (burner, wood), `openmp-pcores` (burner, wood), `mpi4-z4-pcores` (burner, wood), `hybrid2x2-z-pcores` (burner, wood). Brak pomiaru nie jest dowodem zgodności ani przyspieszenia.

## Czas i zasoby

Konwersja częściowo zachodzi podczas pracy solvera; nie sumujemy jej ponownie do czasu całości. Pamięć oznacza szczytowy commit Windows Job, nie RSS. Liczniki I/O dotyczą procesów FDS/MPI, nie przepustowości fizycznego dysku.

| Scena | Profil | Etap / próba | Solver s | Konwersja s | Pierwsza klatka s | Commit MiB | Odczyt MiB | Zapis MiB |
|---|---|---|---:|---:|---:|---:|---:|---:|
| burner | openmp | reference / 0 | 1050.11 | 6.85 | 3.49 | 2372.14 | 1.33 | 141.24 |
| burner | openmp | reference / 1 | 968.09 | 6.07 | 3.46 | 2372.38 | 1.33 | 141.22 |
| burner | openmp | reference / 2 | 925.74 | 6.01 | 3.49 | 2372.27 | 1.33 | 141.23 |
| burner | openmp | reference / 3 | 917.33 | 6.02 | 3.49 | 2372.30 | 1.33 | 141.24 |
| wood | openmp | reference / 0 | 971.24 | 13.42 | 3.27 | 2364.24 | 1.45 | 282.20 |
| wood | openmp | reference / 1 | 1070.28 | 14.76 | 3.11 | 2364.26 | 1.45 | 282.09 |
| wood | openmp | reference / 2 | 1098.24 | 16.29 | 3.53 | 2364.23 | 1.48 | 282.21 |
| wood | openmp | reference / 3 | 1113.47 | 12.96 | 3.29 | 2364.32 | 1.45 | 282.27 |
| burner | mpi2-x2 | screen / -1 | 756.83 | 7.44 | 2.53 | 375.20 | 3.01 | 153.04 |
| wood | mpi2-x2 | screen / -1 | 769.98 | 13.97 | 2.14 | 367.82 | 3.23 | 296.52 |
| burner | mpi2-y2 | screen / -1 | 733.15 | 7.57 | 2.72 | 375.30 | 3.01 | 147.26 |
| wood | mpi2-y2 | screen / -1 | 743.29 | 15.32 | 2.14 | 367.51 | 3.23 | 291.72 |
| burner | mpi4-xy22 | screen / -1 | 718.29 | 18.86 | 2.18 | 628.34 | 7.12 | 159.14 |
| wood | mpi4-xy22 | screen / -1 | 722.78 | 32.19 | 2.18 | 614.86 | 7.65 | 307.04 |
| burner | mpi2-x2 | finalist / 0 | 757.48 | 7.53 | 2.53 | 375.23 | 2.98 | 153.04 |
| burner | mpi2-x2 | finalist / 1 | 753.99 | 7.30 | 2.59 | 375.14 | 2.98 | 153.04 |
| burner | mpi2-x2 | finalist / 2 | 765.48 | 7.51 | 2.50 | 375.25 | 2.98 | 153.04 |
| burner | mpi2-x2 | finalist / 3 | 766.08 | 8.38 | 2.52 | 375.34 | 2.98 | 153.04 |
| wood | mpi4-xy22 | finalist / 0 | 712.66 | 31.36 | 2.63 | 614.72 | 7.65 | 307.04 |
| wood | mpi4-xy22 | finalist / 1 | 729.26 | 31.49 | 2.66 | 615.16 | 7.65 | 307.04 |
| wood | mpi4-xy22 | finalist / 2 | 718.61 | 30.95 | 2.19 | 614.76 | 7.68 | 307.04 |
| wood | mpi4-xy22 | finalist / 3 | 724.18 | 31.09 | 2.17 | 615.04 | 7.65 | 307.04 |
| burner | mpi4-x4 | screen / -1 | 830.86 | 22.19 | 2.82 | 627.46 | 6.30 | 163.32 |

## Zestawy z pełnymi pomiarami

- burner: openmp, mediana 925.91s, 1.000×; stare bramki PASS, kwalifikacja v3: pending-review.
- wood: openmp, mediana 1098.43s, 1.000×; stare bramki PASS, kwalifikacja v3: pending-review.
- burner: mpi2-x2, mediana 765.65s, 1.209×; stare bramki FAIL, kwalifikacja v3: pending-review.
- wood: mpi4-xy22, mediana 724.41s, 1.516×; stare bramki FAIL, kwalifikacja v3: pending-review.

Szczegółowe błędy pól, sond i strumieni: [zgodność numeryczna](numerical-v3.md). Raport rozróżnia dostępne porównania i brakujące pary.
