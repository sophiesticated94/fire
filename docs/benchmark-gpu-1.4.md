# IGNIS 1.4 — pomiary i stan odbioru

Pomiary: 16 października 2026; końcowa kontrola i raport: 17 października 2026. Komputer: i5-12500H, Iris Xe i RTX 4050 Laptop. Model przepływu `gpu-flow-0.2`, 32 × 32 × 64 komórki. [Dane pomiarowe i dowody adaptera](benchmark-gpu-1.4.json).

## Metoda porównania SOR

Osobny Edge, WebGPU przez natywny backend, brak innych testów uruchamianych równolegle podczas końcowych pomiarów SOR. Aplikacje pulpitu i zarządzanie taktowaniem GPU nie były wyłączane; nie jest to pomiar na laboratoryjnie odizolowanym komputerze. Dla każdego adaptera wykonywano kolejno `reference` i `batched`, najpierw bez renderowania, potem z renderowaniem.

Każdy wariant miał co najmniej 10 s rozgrzewki i trzy okna co najmniej 30 s. W oknie powtarzano od resetu odcinek co najmniej 0,5 s fizycznej symulacji, z domyślnymi warunkami powietrza i grzałką 1 W. Czas ścienny zawiera reset. Dzięki temu porównujemy te same fazy przepływu, zamiast zestawiać zimny gaz z późniejszym, silniej rozwiniętym przepływem. Wartości są medianami okien, a zakres pokazuje minimum i maksimum tych trzech pomiarów.

Scena benchmarku: 800 × 600 CSS px, pixel ratio ograniczony do 1,5, przeglądarka headless. FPS mierzy liczbę wywołań renderowania na sekundę; przepustowość solvera to fizyczne sekundy podzielone przez czas ścienny. FPS nie oznacza symulacji w czasie rzeczywistym. Stare pomiary 1.3 miały inny przebieg i nie są używane do wyliczania przyspieszenia tej wersji.

## RTX 4050 — potwierdzony

WebGPU zwrócił `nvidia / lovelace / 0x28a1`, DXGI wykazał ten sam identyfikator urządzenia, a liczniki procesu GPU przeglądarki wykazały dodatnie wykorzystanie na odpowiadającym mu LUID. Surowy raport przechowuje te dowody; samo `powerPreference` nie wystarcza do odbioru.

| Rendering | SOR | s fizyczne / s rzeczywiste | Zakres 3 okien | FPS |
|---|---|---:|---:|---:|
| Wyłączony | Referencja | 0,4199 | 0,4181–0,4243 | — |
| Wyłączony | Batched | 0,4768 | 0,4265–0,5465 | — |
| Włączony | Referencja | 0,07914 | 0,07912–0,08308 | 96,4 |
| Włączony | Batched | 0,08524 | 0,08509–0,08811 | 97,0 |

Mediana przepustowości wzrosła odpowiednio o 13,6% i 7,7%. Rozrzut wariantu bez renderowania jest znaczny; nie traktujemy pojedynczego okna jako gwarantowanej wydajności. Z renderowaniem solver potrzebuje nadal około 11,7 s ściennych na sekundę fizyczną w tym zadaniu.

Średnia liczba odczytów statusu projekcji spadła z 1,15 do 1,017 na krok. Średnia liczba faktycznych iteracji pozostała 18,4. Mediana czasu ściennego projekcji z renderowaniem spadła z 35,8 do 30,15 ms. Pełny krok trwał medianowo około 103 i 99 ms, przy 7,47 i 7,68 ms z timestampów GPU. Czas ścienny obejmuje oczekiwanie na kolejkę i interakcję z rendererem; różnica nie jest samym kosztem kopiowania danych.

Oba warianty osiągnęły maksymalny względny błąd masy 1,50×10⁻⁷ i maksymalną znormalizowaną dywergencję 4,89×10⁻⁵ w zapisanych odcinkach. Odczyty całych objętości podczas pomiaru: zero. Pola z kopiami transakcyjnymi zajmują około 7,80 MiB.

## Iris Xe — ten sam benchmark

WebGPU: `intel / gen-12lp`. Przeglądarka nie ujawniła identyfikatora urządzenia ani opisu, więc raport nie przypisuje ich na podstawie samej preferencji adaptera. DXGI i próbki liczników procesu pozostają w danych źródłowych.

| Rendering | SOR | s fizyczne / s rzeczywiste | Zakres 3 okien | FPS |
|---|---|---:|---:|---:|
| Wyłączony | Referencja | 0,08449 | 0,08435–0,08467 | — |
| Wyłączony | Batched | 0,08355 | 0,08296–0,08373 | — |
| Włączony | Referencja | 0,01350 | 0,01347–0,01353 | 39,1 |
| Włączony | Batched | 0,01406 | 0,01393–0,01416 | 39,0 |

Batched był o 1,1% wolniejszy bez renderowania i o 4,2% szybszy z renderowaniem. Iris zachowuje referencję. Dla tego samego zadania RTX był około 4,97× szybszy bez renderowania i 5,86× z renderowaniem przy porównaniu wariantów referencyjnych. Nie przenosimy tego współczynnika na chemię ani na inne etapy przepływu.

Domyślny batched jest ograniczony do rozpoznanego RTX 4050 i zmierzonej siatki. Referencja pozostaje dostępna; nieznane adaptery, ukryty identyfikator oraz pozostałe siatki wracają do referencji. Odciski w JSON odpowiadają kodowi pomiaru; po nim dodano kontrolę wyboru domyślnego i uzupełniono obsługę cofania metadanych, bez zmiany matematyki zmierzonych wariantów SOR.

## Potwierdzenie końcowego kodu na RTX

Po poprawieniu sumowania statystyk powtórzono na RTX obydwa warianty **z renderowaniem**, ponownie z rozgrzewką i trzema oknami co najmniej 30 s. Oryginalna arytmetyka projekcji pozostała bez zmian; statystyki korzystają teraz z sumowania kompensowanego.

| SOR | Mediana s fizycznych / s rzeczywistych | Zakres | FPS |
|---|---:|---:|---:|
| Referencja | 0,07720 | 0,07555–0,07883 | 95,9 |
| Batched | 0,08200 | 0,07887–0,08857 | 95,9 |

Końcowe potwierdzenie daje **6,2% przewagi mediany batched**. To uzasadnia jego wybór dla rozpoznanego RTX na badanej siatce; nie stanowi gwarancji dla innych parametrów i sterowników. Raport JSON zachowuje oddzielnie serię początkową i potwierdzenie wraz z odpowiednimi odciskami kodu.

Test diagnostyki maksymalnego wiatru 0,6 m/s, ogrzewania całej domeny i zerowego wyporu/transportu molekularnego obejmuje 80 kroków, 0,33257 s fizycznych. Po poprawce maksymalny błąd masy pojedynczego kroku wyniósł 9,93×10⁻⁷, skumulowany 1,38×10⁻⁶, a ważony błąd bilansu energii 3,58×10⁻⁴. Limity pozostały bez zmian. W odrzuconej wcześniej próbie niezależny odczyt float64 potwierdził błąd transportu masy 1,94×10⁻⁹; alarm był błędem sumowania diagnostyki, nie utratą masy w adwekcji.

## Chemia — etap nieodebrany

Pełne źródła i analityczny Jacobian GRI30 porównano dla 12 stanów z niezależną Canterą. Maksymalny znormalizowany błąd RHS: 9,51×10⁻⁵, Jacobianu: 9,03×10⁻⁴; próg tego testu wynosi 10⁻³. Normalizacja i punktowe stany są zapisane w kodzie testu. Ten próg nie zastępuje tolerancji całego reaktora.

Próba reaktora CH₄/powietrze, φ=1, 1500 K, stałe ciśnienie i entalpia, osiągnęła **0,000871824 s z wymaganych 0,5 s** w budżecie 180 s. Referencyjny zapłon Cantery wypada około 0,001163 s, więc próba nie obejmuje nawet zapłonu. Był to eksperyment diagnostyczny częściowo równoległy z regresją CPU, a nie izolowany benchmark przepustowości chemii.

Na faktycznie osiągniętej chwili błąd temperatury względem Cantery wyniósł 0,0713 K. Największy ważony błąd śladowych rodników wyniósł 0,0769 przy limicie 1. Względny błąd entalpii wyniósł 1,06×10⁻⁷, pierwiastków 7,94×10⁻⁷, a suma udziałów masowych odchyliła się od jedności o 2,02×10⁻⁷. **To poprawny krótki odcinek, nie pozytywny odbiór reaktora.**

Wykonano 1745 prób, 371 odrzuceń i 18 687 iteracji Newtona. Maksymalna reszta normowa poprawnych rozwiązań LU wyniosła 4,66×10⁻⁷. Niezależne liczby uwarunkowania skalowanych układów dochodzą do 4,4×10¹³. Nie obniżono tolerancji Newtona ani integratora, nie zastąpiono mechanizmu i nie włączono palnika 3D.

Pełne horyzonty, zapłon, szczyt OH i skalowanie 512/4096/65 536 komórek pozostają nieodebrane. Szczegóły i polecenia: [bramka GRI30](gri30-status.md).

## Odtworzenie

Końcowa regresja: **173 testy Python**, **28 testów przepływu/GPU/UI**, **1 krótki reaktor GPU**, **8 testów przeglądarkowych FDS** i kompilacja produkcyjna — PASS. Dodatkowo na Iris przeszło 5 kontroli wyboru SOR/cofania kroku i zgodności pól oraz test 80 kroków maksymalnego wiatru z ogrzewaniem. Test reaktora przez 10⁻⁸ s potwierdza uruchomienie najnowszych kerneli; nie zastępuje pełnej bramki 0D.

| Etap planu | Stan |
|---|---|
| Weryfikacja RTX i batched SOR | Wdrożony, zmierzony; referencja zachowana |
| Parametry otoczenia podczas obliczeń | Wdrożone i sprawdzone z kontynuacją CPU float64 |
| Pełny GRI30 i odbiór reaktorów | Kernele i prototyp istnieją; odbiór nieukończony |
| Sprzężony palnik metanowy 3D | Zablokowany przez bramkę chemii, zgodnie z planem |

```powershell
$env:IGNIS_GPU_ADAPTER='rtx'
npm run test:gpu:sor
Remove-Item Env:IGNIS_GPU_ADAPTER
npm run test:gpu:sor
$env:IGNIS_GPU_ADAPTER='rtx'
$env:IGNIS_SOR_RENDER_ONLY='1'
npm run test:gpu:sor  # osobny plik potwierdzenia końcowego kodu
Remove-Item Env:IGNIS_SOR_RENDER_ONLY
```

Raport końcowy generuje `scripts/report_gpu_v14.py` z zachowanych plików `artifacts/gpu-v14/`. Surowe próbki są ignorowane przez Git ze względu na rozmiar; podsumowanie zawiera ich SHA256, dowody adaptera, wyniki trzech okien i odciski mierzonego kodu. Raporty 1.3 pozostają historycznymi plikami i nie są nadpisywane.
