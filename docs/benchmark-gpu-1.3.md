# IGNIS 1.3 — odbiór fundamentu GPU

Pomiar lokalny, 16 października 2026. Model `gpu-flow-0.1`, siatka 32 × 32 × 64, domena 16 × 16 × 32 cm, grzałka 1 W, wiatr 0 m/s. Nie jest to benchmark spalania ani porównanie równoważności GPU z FDS.

## Środowisko

Windows x64, Intel i5-12500H. Edge **156.0.4314.23**, headless, ANGLE D3D11. Adapter zgłoszony przez WebGPU: **Intel / gen-12lp**, `isFallbackAdapter=false`; system identyfikuje go jako Intel Iris Xe, sterownik 32.0.101.7082. RTX 4050 jest obecny w komputerze, lecz przeglądarka wybrała Intel mimo `powerPreference: high-performance`. **Nie zmierzono wydajności RTX 4050.**

Three.js 0.186.1. Solver i renderer używają współdzielonych buforów. Pola aplikacji zajmują **4 092 032 B (3,90 MiB)**; nie obejmuje to pozostałej pamięci sterownika, renderera i buforów odczytu. Liczba pełnych odczytów objętości w obu benchmarkach: **0**.

## Stabilność i bilanse

| Wielkość | Zmierzono | Kryterium |
|---|---:|---:|
| Czas fizyczny | 60,0045 s / 8847 kroków | ≥ 60 s |
| Końcowy względny błąd bilansu masy | 1,51·10⁻⁵ | ≤ 10⁻⁴ |
| Końcowy znormalizowany RMS div(u) − S | 3,80·10⁻⁸ | ≤ 10⁻³ |
| Końcowy znormalizowany błąd maksymalny | 7,95·10⁻⁷ | ≤ 10⁻² |
| Końcowy błąd całkowitego strumienia rozszerzalności | 1,23·10⁻⁵ | ≤ 0,01 |
| Reszta bilansu entalpii po 5,0028 s | −0,01216 J / **0,243%** energii wejściowej | ≤ 5% |
| Końcowa temperatura maksymalna | 37,6785 °C | 200–1000 K |
| Końcowa maksymalna prędkość gazu | 0,3626 m/s | Mach < 0,1 |

Każdy zaakceptowany krok przechodził kontrole solvera; próbki zapisywano co 120 kroków. Raport nie wyprowadza maksymalnego błędu wszystkich chwil wyłącznie z tych rzadszych próbek. Długi przebieg trwał około 19 minut wraz z rozgrzewką i trzema końcowymi oknami pomiarowymi. Część próby stabilności nakładała się na krótkie testy regresji; tego czasu nie traktujemy jako izolowanego benchmarku wydajności.

W długiej próbie działała wcześniejsza wersja zbierania timestampów Three.js, która raportowała ostatnią klatkę zamiast sumy passów całego kroku. Jej wartości GPU ms zostały odrzucone. Poprawione zbieranie timestampów i dodatkowe kontrole przeszły końcowe testy; osobny pomiar renderowania poniżej używa sumy passów kroku. Jądra transportu, źródła i projekcji dla domyślnego przypadku w długiej próbie odpowiadają odebranemu modelowi; późniejsze poprawki obsługują telemetrię, sondy, reset i zmiany wiatru.

## Wydajność renderowania i obliczeń

Pomiar jest wykonywany osobno, po zakończeniu innych testów GPU: 10 s rozgrzewki, trzy kolejne okna po 30 s zegara, viewport 800 × 600 pikseli CSS, pixel ratio 1. Okna obejmują rozwijający się przepływ, więc różne koszty projekcji w kolejnych oknach nie oznaczają zmiany sprzętu.

Wyniki liczbowe zapisuje [benchmark-gpu-1.3.json](benchmark-gpu-1.3.json). `step_gpu_ms_*` pochodzi z opcjonalnych timestampów GPU, `step_wall_ms_*` obejmuje CPU, kompilację, synchronizację i odczyty. FPS liczy wywołania renderowania w `requestAnimationFrame`; czas fizyczny rośnie wyłącznie o obliczone kroki. Cel 30 FPS dotyczy prezentacji i nie oznacza solvera działającego w czasie rzeczywistym.

| Okno | FPS renderera | Kroki/s zegara | GPU ms/krok, mediana / p95 | Czas ścienny ms/krok, mediana / p95 | Czas fizyczny / zegar |
|---|---:|---:|---:|---:|---:|
| 1 | 39,21 | 1,65 | 20,02 / 31,92 | 579,2 / 789,3 | 0,01374 |
| 2 | 38,28 | 1,35 | 31,78 / 31,98 | 734,4 / 795,8 | 0,01125 |
| 3 | 38,21 | 1,35 | 31,78 / 31,92 | 737,3 / 786,8 | 0,01125 |

Zmierzona prezentacja przekroczyła 30 FPS w tych warunkach. Solver z rendererem wykonał tylko około **0,011–0,014 s fizycznych na sekundę zegara**; to około 73–89 razy wolniej od czasu rzeczywistego. Nie jest to jeszcze solver czasu rzeczywistego. Kolejne okna miały medianę 16, 32 i 32 iteracji projekcji. Różnica między czasem GPU i ściennym uzasadnia zbadanie kolejek, punktów synchronizacji i odczytów, zamiast zakładania, że całe opóźnienie to koszt arytmetyki GPU.

Końcowe okna samego solvera po 60 s przebiegu dały 9,36–9,55 kroków/s zegara, medianę 103,9–104,8 ms/krok i 0,064–0,066 s fizycznych/s zegara. Dotyczą innej fazy przepływu niż benchmark renderowania, a cały przebieg nie był izolowany od testów regresji. Nie wyprowadzamy z tych dwóch serii współczynnika kosztu renderera.

## Weryfikacja i odtwarzanie

* **169 testów Python** — zaliczone; jedno istniejące ostrzeżenie deprecacyjne Starlette.
* **8 testów przeglądarkowych FDS** — zaliczone.
* **16 nowych testów GPU/UI** — zaliczone, w tym referencja float64/CG, stała prędkość przy zmiennej gęstości, ogrzewanie bez grawitacji, wyłączenie źródła, warunki brzegowe, rollback, zmiana parametrów, sonda, brak WebGPU, utrata urządzenia i zawieszanie nieaktywnego silnika.
* **TypeScript + Vite build** — zaliczone. Pozostaje ostrzeżenie rozmiaru paczki Three.js; moduł GPU jest ładowany osobno na żądanie.
* **Próba 60 s i budżet energii** — zaliczone na natywnym WebGPU.
* **Osobny benchmark renderowania i solvera, 10 + 3 × 30 s** — zaliczony; brak pełnych odczytów objętości.

```powershell
npm run test:gpu
npm run test:gpu:benchmark
.\.venv\Scripts\python.exe scripts/report_gpu.py
```

Pełne surowe wyniki pozostają lokalnie w `artifacts/gpu/benchmark-native.json` i `artifacts/gpu/render-benchmark-native.json`; repozytorium zawiera małe podsumowanie JSON. Nie należy uruchamiać benchmarków równolegle. Test przełączania silników czeka na rzeczywiste zakończenie rozpoczętego kroku, zamiast zakładać, że zawsze zmieści się on w stałych 800 ms.

## Wnioski i granice

Fundament wykonuje rzeczywisty przepływ 3D ze zmienną gęstością, kontroluje bilanse i prezentuje pola bez przesyłania całej objętości do RAM. Zaliczenie referencji CPU potwierdza implementację tej dyskretyzacji; nie jest walidacją eksperymentalną. Na wybranym adapterze Intel solver pozostaje wolniejszy od czasu rzeczywistego. Następne decyzje powinny opierać się na kosztach projekcji i synchronizacji oraz osobnym pomiarze na docelowej karcie. Nie zwiększano kroku przez rozluźnianie limitów.

Spalanie, paliwo/tlen/sadza, radiacja, piroliza drewna GPU, porównanie GPU/FDS i optymalizacja CPU/FDS pozostają kolejnymi etapami. Ten odbiór nie stanowi zgody na zastąpienie FDS nowym modelem.
