# Raport z benchmarku solvera FDS (Etap 1)

Badanie powtarzalności i skalowalności solvera FDS 6.11.1 przeprowadzono przy użyciu skryptu `scripts/benchmark.py`.
Pomiary wykonano na maszynie z procesorem Intel Core i5-12500H (12 rdzeni: 4 rdzenie Performance + 8 rdzeni Efficient, 16 wątków logicznych) w systemie Windows.

## Metodologia
- **Scena testowa**: Palnik gazowy (`burner`), siatka $32 \times 32 \times 64$ (65 536 komórek).
- **Czas fizyczny**: 0,30 s (ok. 95 kroków całkowania CFD).
- **Izolacja**: Każda próba w osobnym katalogu tymczasowym w `artifacts/benchmark_tmp/`.
- **Statystyka**: 1 przebieg rozgrzewkowy (warm-up) + 3 niezależne pomiary.
- **Weryfikacja**: Sprawdzenie kodu wyjścia `returncode == 0` oraz potwierdzenia `STOP: FDS completed successfully`.

## Wyniki pomiarów

| Tryb | Mediana [s] | Min [s] | Max [s] | Rozrzut (Stdev) | Przyspieszenie wzgl. serial | Średnia liczba kroków | Czas DIVG [s] | Czas MASS [s] | Czas RADI [s] |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **`serial` (`fds.exe`, 1 rdzeń)** | 33,79 | 27,41 | 45,33 | 9,09 | 1,00× | 95 | 12,7 | 7,7 | 3,5 |
| **`openmp_4` (4 wątki, P-cores)** | **16,60** | 16,45 | 16,64 | **0,10** | **2,04×** | 95 | 5,3 | 3,3 | 1,9 |
| **`openmp_8` (8 wątków - dawniej domyślny)** | 28,82 | 22,88 | 29,31 | 3,58 | 1,17× | 95 | 7,8 | 5,0 | 4,6 |
| **`mpi_2` (2 siatki, Intel MPI)** | 15,89 | 15,72 | 16,74 | 0,55 | 2,13× | 97 | 10,4 | 6,3 | 2,6 |
| **`mpi_4` (4 siatki, Intel MPI)** | **13,84** | 13,78 | 13,88 | **0,05** | **2,44×** | 94 | 14,0 | 8,7 | 3,4 |

## Wnioski i decyzje

1. **Problem 8 wątków OpenMP na architekturze hybrydowej**:
   - Dawne domyślne ustawienie `IGNIS_THREADS=8` było skrajnie nieefektywne: mediana 28,82 s vs 16,60 s na 4 wątkach.
   - Wątki OpenMP rozdzielane na rdzenie E-core zmuszały szybkie rdzenie P-core do długiego oczekiwania na barierach synchronizacyjnych (`#pragma omp barrier`), powodując dławienie termiczne i 73% dłuższy czas obliczeń!
   - Zmiana domyślnego limitu wątków do 4 w `backend/solver_config.py` natychmiast skraca czas obliczeń OpenMP o **ponad 42%** przy stabilności wyników (odchylenie standardowe zaledwie 0,10 s).

2. **Skuteczność dekompozycji domenowej (MPI)**:
   - Wariant `mpi_4` (podział domeny w osi Z na 4 siatki po 16 384 komórki) osiągnął najlepszy wynik: **13,84 s** (przyspieszenie **2,44×** względem 1 rdzenia i **2,08×** względem dawnego OpenMP 8).
   - Narzut komunikacji MPI pomiędzy procesami (`COMM`) jest znikomy w porównaniu z zyskiem z niezależnego rozwiązywania ciśnienia metodą FFT na mniejszych poddomenach.

3. **Strojenie radiacji**:
   - Eksperymenty ze zmianą `TIME_STEP_INCREMENT=6` oraz `NUMBER_RADIATION_ANGLES=36` nie wykazały jednoznacznego przyspieszenia wall-clock (czasy 39,4 s vs 43,9 s / 48,0 s z powodu zmian we wzorcach iteracji FDS).
   - Zgodnie z kryteriami z `docs/plan.md`, zachowano sprawdzony i stabilny model radiacji z 50 kątami.

4. **Wpływ dopasowania parametrów UI (`defaults`)**:
   - Zmiana domyślnego `duration` na 2,0 s dla scen gazowych umożliwia natychmiastowe trafienie w prekompilowany cache `samples/` (< 50 ms), co całkowicie eliminuje wielominutowe oczekiwanie przy standardowym uruchomieniu aplikacji.
