# Historyczny raport krótkiego benchmarku FDS (Etap 1)

**Uwaga po audycie:** poniższe liczby pochodzą z wcześniejszych pomiarów 0,30 s. Nie dowodzą przewagi dla pełnych doświadczeń ani równoważności numerycznej MPI. Nowa seria i bramki są opisane w [execution-v2.md](execution-v2.md); surowe, wznawialne pomiary zapisuje `artifacts/benchmark-v2.json`. Automatyczny wybór MPI wymaga osobnej pozytywnej walidacji.

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
| **`openmp_4` (4 wątki, affinity niepotwierdzone)** | **16,60** | 16,45 | 16,64 | **0,10** | **2,04×** | 95 | 5,3 | 3,3 | 1,9 |
| **`openmp_8` (8 wątków - dawniej domyślny)** | 28,82 | 22,88 | 29,31 | 3,58 | 1,17× | 95 | 7,8 | 5,0 | 4,6 |
| **`mpi_2` (2 siatki, Intel MPI)** | 15,89 | 15,72 | 16,74 | 0,55 | 2,13× | 97 | 10,4 | 6,3 | 2,6 |
| **`mpi_4` (4 siatki, Intel MPI)** | **13,84** | 13,78 | 13,88 | **0,05** | **2,44×** | 94 | 14,0 | 8,7 | 3,4 |

## Wnioski i decyzje

1. **Problem 8 wątków OpenMP na architekturze hybrydowej**:
   - Dawne domyślne ustawienie `IGNIS_THREADS=8` było skrajnie nieefektywne: mediana 28,82 s vs 16,60 s na 4 wątkach.
   - Przyczyna różnicy nie została zmierzona. Wpływ rdzeni E/P, synchronizacji i temperatury pozostaje hipotezą; sam czas wykonania nie dowodzi dławienia termicznego.
   - W tym krótkim pomiarze cztery wątki skróciły medianę względem ośmiu o około 42%. Nie jest to gwarancja dla innych scen i długości. `OMP_PLACES=cores` oraz `OMP_PROC_BIND=close` nie gwarantują pracy wyłącznie na P-cores.

2. **Skuteczność dekompozycji domenowej (MPI)**:
   - Wariant `mpi_4` (podział domeny w osi Z na 4 siatki po 16 384 komórki) osiągnął najlepszy wynik: **13,84 s** (przyspieszenie **2,44×** względem 1 rdzenia i **2,08×** względem dawnego OpenMP 8).
   - To wynik krótkiego pomiaru. Różne liczby kroków wymagają porównania pól, energii i zapłonu, zanim wariant zostanie uznany za odpowiedni dla aplikacji.

3. **Strojenie radiacji**:
   - Eksperymenty ze zmianą `TIME_STEP_INCREMENT=6` oraz `NUMBER_RADIATION_ANGLES=36` nie wykazały jednoznacznego przyspieszenia wall-clock (czasy 39,4 s vs 43,9 s / 48,0 s z powodu zmian we wzorcach iteracji FDS).
   - Zgodnie z kryteriami z `docs/plan.md`, zachowano sprawdzony i stabilny model radiacji z 50 kątami.

4. **Wpływ dopasowania parametrów UI (`defaults`)**:
   - Dostarczone przykłady dwusekundowe umożliwiają natychmiastowe obejrzenie aplikacji. Po wprowadzeniu profilu wykonania v2 pozostają dostępne do oglądania, lecz nie zastępują obliczeń o nowej tożsamości cache.
