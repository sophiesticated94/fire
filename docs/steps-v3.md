# Profilowanie kroków — dane natywne

Liczba kroków pochodzi z końcowego licznika `Time Step`, nie z liczby wierszy CSV. Histogram Δt i statystyki CFL/VN są próbkowane. Koszty podsystemów podzielono przez rzeczywistą liczbę kroków; są estymacją średnią, dla MPI sumą czasów rang.

| Scena | Profil | Etap / próba | Kroki | Zapisane próbki | Średni fizyczny krok ms | CFL max | DIVG ms/krok | MASS ms/krok | RADI ms/krok |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| burner 6s | openmp | reference / 0 | 4884 | 67 | 1.2285 | 0.97 | 79.115 | 48.915 | 31.491 |
| burner 6s | openmp | reference / 1 | 4889 | 67 | 1.2272 | 0.97 | 72.592 | 45.326 | 28.349 |
| burner 6s | openmp | reference / 2 | 4851 | 67 | 1.2369 | 0.99 | 69.759 | 43.290 | 27.231 |
| burner 6s | openmp | reference / 3 | 4898 | 67 | 1.2250 | 0.99 | 68.681 | 42.283 | 26.786 |
| wood 15s | openmp | reference / 0 | 5162 | 70 | 2.9059 | 0.99 | 71.290 | 43.530 | 24.603 |
| wood 15s | openmp | reference / 1 | 5171 | 70 | 2.9008 | 1 | 78.998 | 48.366 | 27.480 |
| wood 15s | openmp | reference / 2 | 5172 | 70 | 2.9002 | 0.98 | 81.458 | 49.749 | 27.823 |
| wood 15s | openmp | reference / 3 | 5164 | 70 | 2.9047 | 0.98 | 82.688 | 50.407 | 28.718 |
| burner 6s | mpi2-x2 | screen / -1 | 4895 | 67 | 1.2257 | 0.98 | 102.983 | 59.510 | 26.545 |
| wood 15s | mpi2-x2 | screen / -1 | 5170 | 70 | 2.9014 | 0.99 | 103.366 | 60.193 | 22.631 |
| burner 6s | mpi2-y2 | screen / -1 | 4921 | 68 | 1.2193 | 0.99 | 99.675 | 57.895 | 26.249 |
| wood 15s | mpi2-y2 | screen / -1 | 5180 | 70 | 2.8958 | 0.99 | 100.058 | 58.958 | 22.409 |
| burner 6s | mpi4-xy22 | screen / -1 | 4863 | 67 | 1.2338 | 0.97 | 168.764 | 95.353 | 41.180 |
| wood 15s | mpi4-xy22 | screen / -1 | 5197 | 70 | 2.8863 | 0.99 | 165.576 | 95.363 | 34.124 |
| burner 6s | mpi2-x2 | finalist / 0 | 4895 | 67 | 1.2257 | 0.98 | 102.942 | 59.326 | 26.707 |
| burner 6s | mpi2-x2 | finalist / 1 | 4895 | 67 | 1.2257 | 0.98 | 102.656 | 59.428 | 26.384 |
| burner 6s | mpi2-x2 | finalist / 2 | 4895 | 67 | 1.2257 | 0.98 | 103.166 | 60.143 | 27.714 |
| burner 6s | mpi2-x2 | finalist / 3 | 4895 | 67 | 1.2257 | 0.98 | 103.534 | 59.898 | 27.017 |
| wood 15s | mpi4-xy22 | finalist / 0 | 5197 | 70 | 2.8863 | 0.99 | 163.537 | 93.573 | 34.199 |
| wood 15s | mpi4-xy22 | finalist / 1 | 5197 | 70 | 2.8863 | 0.99 | 166.808 | 95.613 | 34.834 |
| wood 15s | mpi4-xy22 | finalist / 2 | 5197 | 70 | 2.8863 | 0.99 | 164.556 | 94.458 | 34.010 |
| wood 15s | mpi4-xy22 | finalist / 3 | 5197 | 70 | 2.8863 | 0.99 | 165.826 | 94.535 | 34.018 |
| burner 6s | mpi4-x4 | screen / -1 | 4889 | 67 | 1.2272 | 0.98 | 194.846 | 105.932 | 48.732 |

Rozgrzewki mają numer 0 i nie wchodzą do median wydajności. Oryginalne archiwa są niezmienione. Pole `stepProfile` bez wersji `step-profile-2` w starszym dzienniku lub archiwum ma błędny mianownik; zastępują je skorygowane pliki `profiling-v2/*.json` oparte na tych samych danych natywnych.

Pełny histogram wszystkich kroków wymaga osobnej próby `DIAGNOSTICS_INTERVAL=1`. Dodatkowa diagnostyka ma koszt komunikacji/wyjścia i nie stanowi porównywalnego pomiaru produkcyjnego.

Źródło: [FDS 6.11.1 — diagnostyka i Time Step Data](https://github.com/firemodels/fds/blob/ff928dbf68a2623ced3a007be75391c6dc6c9f90/Manuals/FDS_User_Guide/FDS_User_Guide.tex).
