# Walidacja v3 — ponowna ocena zapisanych przebiegów

Status: **oczekuje na osobny przegląd progów**. Nowe miary nie promują profili. Dotychczasowe limity pól średnich, energii i zapłonu pozostają bez zmian.

Porównania OpenMP obejmują trzy pary powtórzeń; każdy kandydat jest porównany z każdą z trzech referencji. Rozrzut jest opisowy, bez deklarowania przedziałów ufności.

W tabeli: maksymalny znormalizowany błąd chwilowy w drugiej połowie nagrania. Tlen: bezwzględny RMS mol/mol. Pełne okno, granice siatek, zmienność, sondy i HRR są w danych JSON.

| Scena / czas | Rodzaj | ΔT | HRRPUV | Sadza | O₂ | U | V | W | Stare bramki |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| burner / 2s | mpi2 | 0.21629 | 0.071935 | 0.23194 | 0.0026891 | 1.0469 | 1.0893 | 0.31929 | FAIL |
| burner / 2s | mpi4 | 0.21168 | 0.066491 | 0.23383 | 0.0026255 | 1.0721 | 1.0943 | 0.31907 | FAIL |
| burner / 2s | openmp-repeatability | 0.00012379 | 0.00020782 | 0.00016902 | 2.045e-06 | 0.00040745 | 0.0004236 | 7.9931e-05 | PASS |
| candle / 2s | mpi2 | 0.0008914 | 0.11721 | 0.0018531 | 1.3433e-05 | 0.017952 | 0.017951 | 0.0049488 | PASS |
| candle / 2s | mpi4 | 0.00097235 | 0.044541 | 0.0018503 | 1.3306e-05 | 0.0089604 | 0.008868 | 0.0028437 | PASS |
| candle / 2s | openmp-repeatability | 0 | 0 | 0 | 0 | 0 | 0 | 0 | PASS |
| burner / 6s | mpi2 | 0.20973 | 0.16268 | 0.20966 | 0.0026889 | 0.92702 | 0.93607 | 0.27126 | FAIL |
| burner / 6s | mpi4 | 0.21679 | 0.16125 | 0.22071 | 0.0027701 | 0.98516 | 0.9818 | 0.28092 | FAIL |
| burner / 6s | openmp-repeatability | 0.084727 | 0.037091 | 0.10243 | 0.0010562 | 0.55904 | 0.55656 | 0.14259 | PASS |
| candle / 6s | mpi2 | 0.0019457 | 0.011617 | 0.0034668 | 2.0889e-05 | 0.019633 | 0.019618 | 0.0061563 | PASS |
| candle / 6s | mpi4 | 0.0029317 | 0.027637 | 0.0050293 | 2.8664e-05 | 0.030866 | 0.03085 | 0.0096225 | PASS |
| candle / 6s | openmp-repeatability | 0 | 0 | 0 | 0 | 0 | 0 | 0 | PASS |
| wood / 15s | mpi2 | 0.42575 | 0.49022 | 0.4689 | 0.0051893 | 1.1846 | 1.1659 | 0.5071 | FAIL |
| wood / 15s | mpi4 | 0.42287 | 0.50729 | 0.46076 | 0.0052343 | 1.1797 | 1.171 | 0.51478 | FAIL |
| wood / 15s | openmp-repeatability | 0.31566 | 0.40906 | 0.36179 | 0.0038035 | 1.0654 | 1.0678 | 0.43549 | PASS |

## Interpretacja i decyzja

Różnica chwilowych trajektorii sama nie rozstrzyga o błędzie modelu. Zestawienie z rozrzutem OpenMP, średnimi, zmiennością i strumieniami służy osobnemu przeglądowi.
Historyczne przebiegi nie zawierają dodatkowych strumieni diagnostycznych; ich brak jest jawnie raportowany i blokuje promocję v3.
Plik polityki `config/validation-v3.json` pozostaje `pending-review`. Także wcześniej zaakceptowana świeca wymaga ponownej kwalifikacji.
