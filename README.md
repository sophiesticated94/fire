# IGNIS — laboratorium ognia 3D

Lokalna aplikacja po polsku: świeca, palnik metanowy i piroliza drewna. Rzeczywisty **NIST FDS 6.11.1** oblicza pola przestrzenne, a Three.js rekonstruuje płomień, dym i warstwy pomiarowe. Obliczenia i odtwarzanie wyników są rozdzielone.

**IGNIS 1.3:** przełącznik **GPU Interactive** otwiera osobny solver 3D gorącego powietrza na WebGPU. Grzałka i wiatr zmieniają przepływ podczas obliczeń; dostępne są temperatura, prędkość, gęstość i sonda. Ten etap nie obejmuje jeszcze spalania GPU. FDS zachowuje dotychczasową fizykę i wyniki. [Model, obsługa i testy GPU](docs/gpu-flow-0.1.md) · [Pomiary i odbiór](docs/benchmark-gpu-1.3.md).

**Prace nad 1.4:** model `gpu-flow-0.2` dodaje sterowanie otoczeniem, grawitacją i właściwościami gazu podczas obliczeń, wiatr do 0,6 m/s, pełne cofanie nieudanego kroku oraz eksperymentalny batched SOR. [Opis i obsługa](docs/gpu-flow-0.2.md). Pełny GRI30 (53 składniki, 325 reakcji) ma własne kernele WGSL i referencje Cantery, ale **bramka reaktora pozostaje niezamknięta**. Palnik GPU nie został włączony. [Status chemii i odtworzenie testów](docs/gri30-status.md) · [Pomiary 1.4](docs/benchmark-gpu-1.4.md).

## Uruchomienie

W PowerShell, w folderze projektu:

```powershell
.\scripts\setup.ps1  # tylko przy pierwszym przygotowaniu środowiska
.\start.ps1
```

Otwórz **http://127.0.0.1:8765**. W tym środowisku zależności i solver są już przygotowane. `start.ps1` kompiluje interfejs, uruchamia lokalny serwer i otwiera przeglądarkę; `start.ps1 -NoBrowser` pomija otwarcie przeglądarki. Ctrl+C zatrzymuje serwer i jego aktywne obliczenie.

Wymagania: Windows x64, Python 3.14, Node.js 22.12+ lub 24+, WebGL2 do grafiki. Setup tworzy `.venv`, pobiera biblioteki i oficjalne archiwum FDS, sprawdza SHA256 i rozpakowuje je wyłącznie do `tools/`. Nie uruchamia instalatora, nie zmienia PATH systemu i nie wymaga Dockera. Po przygotowaniu środowiska aplikacja, biblioteki i fonty działają offline.

## Obsługa

- Wybierz doświadczenie. Zapisany przykład otwiera się bez ponownego liczenia.
- Nowy eksperyment domyślnie trwa 2 s dla palnika/świecy i 15 s dla drewna. Krótszy przykład startowy nie nadpisuje tych ustawień; podpis sceny pokazuje parametry oglądanego wyniku.
- Przeciągaj scenę, aby obracać kamerę; kółko przybliża. Dostępne są widoki 3D, bok i góra.
- Przełączaj płomień, temperaturę, przepływ i tlen. Przekrój odsłania wnętrze pola. Kliknięcie sceny wybiera sondę w najbliższej komórce na płaszczyźnie przekroju.
- Suwaki i pola liczbowe edytują warunki nowego eksperymentu. **Oblicz doświadczenie** uruchamia FDS. Zmiany nie zmieniają poprzednich danych ani ich odczytów.
- Podczas obliczeń możesz oglądać poprzedni wynik. Anulowanie nie usuwa zapisanych doświadczeń.
- Czas, pauza, przewijanie i szybkość dotyczą odtwarzania zapisanych klatek. Spacja przełącza odtwarzanie, jeśli fokus nie jest w kontrolce. Ukryta karta nie nadrabia czasu.
- **Zapłon / Zgaś** włącza i wyłącza płomień oraz jego światło niezależnie od pauzy. To sterowanie pokazem: odczyty nadal dotyczą zapisu CFD. **Ciągły pokaz** odtwarza naprzemiennie fragment ze spalaniem (HRR co najmniej 50% maksimum), bez powracania do zimnego początku. **Pełny przebieg** zatrzymuje się na końcu; przewijanie i suwak czasu wybierają ten tryb.
- Podczas obliczeń **Podgląd obliczeń** otwiera rzeczywiste, kompletne klatki siedmiu pól. Można wrócić do poprzedniego wyniku. Wynik częściowy czeka na nowe klatki; po anulowaniu pozostaje dostępny, lecz nie stanowi ukończonego wyniku w cache.
- Tryb prezentacji ukrywa panele. Esc przywraca interfejs.
- Przełącznik oszczędnego renderowania zmniejsza obciążenie GPU; nie zmienia siatki ani wyników CFD.
- Bez WebGL2 nadal działają obliczenia, historia, odczyty i wykres mocy.

Obliczenia mają własny czas fizyczny. Kilka sekund spalania może wymagać wielu minut pracy CPU. Postęp pokazuje czas rzeczywiście osiągnięty przez solver, nie prognozowany czas oczekiwania. Wyższa rozdzielczość ma około 3,4 razy więcej komórek i może wymagać więcej niż 3,4 razy dłuższych obliczeń z powodu mniejszego kroku czasu.

## Dane i API

Nowe wyniki są zapisywane w `runs/<id>/attempts/<attempt>/`: wejście `ignis.fds`, oryginalne wyjście solvera, log, konfiguracja, status, `preview/manifest.json`, klatki `preview/frames/*.bin` i końcowy `result.json`. `latest.json` wskazuje ostatnią próbę. Ponowienie nie usuwa wcześniejszych plików. Stare katalogi i przykłady w `samples/` pozostają obsługiwane. Nowy klucz cache uwzględnia konfigurację, wersje modelu, profilu i transportu, liczbę procesów/wątków, podział siatek oraz SHA256 binariów FDS/MPI. Stare przykłady można oglądać, ale nie zastępują obliczeń nowego profilu.

Lokalny serwer nasłuchuje wyłącznie na 127.0.0.1. Nie ma kont, publikacji ani zewnętrznych usług.

| Metoda | Endpoint | Zastosowanie |
|---|---|---|
| GET | `/api/health` | dostępność FDS i aktywny eksperyment |
| GET | `/api/experiments` | historia i przykłady |
| POST | `/api/experiments` | konfiguracja nowego eksperymentu lub trafienie w cache |
| GET | `/api/experiments/{id}` | postęp i status |
| POST | `/api/experiments/{id}/cancel` | anulowanie aktywnego obliczenia |
| GET | `/api/experiments/{id}/result` | metadane, współrzędne, czasy i szeregi |
| GET | `/api/experiments/{id}/frames/{n}` | siedem kanałów float32, kolejność opisana w modelu |
| GET | `/api/experiments/{id}/preview/manifest` | rosnący manifest, rewizja, identyfikator próby i kompletność; bez cache HTTP |
| GET | `/api/experiments/{id}/preview/frames/{n}?attempt=…` | niezmienna, opublikowana klatka konkretnej próby |
| GET | `/api/experiments/{id}/input` | oryginalny plik wejściowy FDS |
| GET | `/api/experiments/{id}/log` | diagnostyka solvera |

Podgląd deweloperski: uruchom `.venv\Scripts\python -m uvicorn backend.app:app --host 127.0.0.1 --port 8765` i w drugim terminalu `npm run dev`. Vite przekazuje `/api` do serwera. Pakiet produkcyjny powstaje w `dist/`.

Opcjonalnie `IGNIS_FDS` wskazuje własny plik wykonywalny FDS 6.11.1. `IGNIS_SOLVER` przyjmuje `auto` (domyślnie), `openmp`, `mpi2`, `mpi4` oraz nowe warianty opisane w [execution-v3](docs/execution-v3.md): np. `mpi2-x2`, `mpi4-y4`, `mpi4-xy22`, `mpi2-z13`, `hybrid2x2-z`. Profil zawiera podział siatek, hashe binariów i bibliotek, liczbę procesów/wątków oraz ewentualne affinity. Brak wymuszonego wariantu powoduje czytelny błąd. `IGNIS_THREADS` ustawia 1–16 wątków w wymuszonym OpenMP; automatyka pozostaje przy 4.

**Walidacja v3 oczekuje na przegląd nowych progów. `auto` używa OpenMP 4, także dla świecy.** Historyczne kwalifikacje nie są przenoszone. [Ponowna analiza 105 par](docs/validation-v3.md) dodaje chwilowy błąd czasowo-przestrzenny, zmienność i rzeczywiste granice siatek. Nowe przebiegi zawierają natywne strumienie masy/entalpii, promieniowanie, ciśnienie i dywergencję. Promocja wymaga osobno zatwierdzonej polityki, wszystkich porównań z trzema referencjami oraz co najmniej 5% poprawy mediany. Rodziny parametrów mają własną, wielopunktową kwalifikację; `fine` wymaga oddzielnych badań.

`OMP_PLACES=cores` i `OMP_PROC_BIND=close` nie gwarantują wyboru rdzeni Performance. Warianty badawcze `-pcores` korzystają z topologii Windows i maski Job Object; telemetria sprawdza faktyczne affinity procesów oraz wątków. `IGNIS_TIMEOUT` ustawia limit obliczeń w sekundach (domyślnie 7200). Solver FDS nie korzysta z GPU. Osobny model GPU Interactive wykonuje obliczenia i renderowanie na adapterze wybranym przez przeglądarkę. Jednocześnie aplikacja lub benchmark wykonuje jeden eksperyment, zabezpieczony wspólną blokadą, także przy izolowanych serwerach API. Na Windows proces jest tworzony wstrzymany, przypisywany do Job Object, dopiero potem wznawiany. Zamknięcie serwera lub anulowanie zatrzymuje całe drzewo procesów.

## Testy

```powershell
.\.venv\Scripts\python -m pytest tests -q
npm run build
npm run test:e2e  # przy uruchomionym serwerze na porcie 8765
npm run test:gpu  # Edge + dostępny adapter WebGPU
npm run test:gpu:benchmark  # długi test stabilności i pomiary; sekwencyjnie
```

Jeśli Chromium Playwright nie jest dostępny: `npx playwright install chromium`. Zrzuty są zapisywane w ignorowanym `artifacts/`.

Pełny, wznawialny benchmark (60 przebiegów: rozgrzewka i trzy pomiary dla pięciu konfiguracji oraz trzech wariantów) może trwać wiele godzin:

```powershell
.\.venv\Scripts\python scripts/benchmark.py
```

Obejmuje palnik i świecę po 2 i 6 sekund oraz drewno 15 sekund na siatce podglądowej. `--quality fine` wykonuje osobną serię; wyników podglądu nie przenosi się na dokładniejszą siatkę. Można ograniczyć serię przez `--scene burner --duration 6`. `--no-preview --output-json artifacts/benchmark-no-preview.json` mierzy narzut podglądu bez promowania profili produkcyjnych. Nowe pomiary trafiają do `artifacts/benchmark-execution3.json`; historyczne `benchmark-v2.json` i 60 prób pozostają zachowane. Ten skrypt porównawczy nie wystawia kwalifikacji v3.

Nowa kampania z limitem 8 h / 4 GiB, archiwizacją bezstratną, walidacją wszystkich referencji i badaniem dekompozycji:

```powershell
.venv/Scripts/python scripts/campaign_v3.py --hours 8 --gib 4
.venv/Scripts/python scripts/analyze_v3.py  # ponowna analiza zachowanych danych v2
.\scripts\verify_v3.ps1                  # Python, build, Playwright
```

[Instrukcja badań execution-v3](docs/execution-v3.md) opisuje wznowienie kampanii, pomiar pełnego API, histogramy kroków, osobne budżety rodzin parametrów i kontrolę środowiska własnych kompilacji. Wynik screeningu nie jest produkcyjnym przyspieszeniem.

[Weryfikacja implementacji v3](docs/verification-v3.md) oddziela wykonane testy aplikacji i transportu od trwających badań zgodności oraz niewykonanych jeszcze kampanii.

Starszy `verify.ps1` przekierowuje do testów v3; `-AfterProcessId <PID>` pozwala najpierw poczekać na istniejący proces. Raporty `docs/benchmark-v2.md` i `benchmark-v2-data.json` są historycznymi dowodami 60 prób i nie poświadczają nowych profili. Negatywna bramka zgodności MPI oznacza pozostawienie OpenMP; nie jest ukrywana jako pozytywna walidacja.

Obliczenie przypadku z terminala:

```powershell
.\.venv\Scripts\python scripts/compute.py --scene burner --duration 6
.\.venv\Scripts\python scripts/compute.py --scene candle --duration 3 --quality fine
.\.venv\Scripts\python scripts/compute.py --scene wood --duration 15 --moisture 12
```

## Zakres naukowy i licencje

Eksperymentalna chemia IGNIS 1.4 ma osobną [instrukcję kampanii GRI30](docs/gri30-campaign.md): indywidualne kroki reaktorów na GPU, atomowe checkpointy, wspólny budżet 8 h i niezależna walidacja Cantery. [Raport odbioru](docs/chemistry-acceptance-1.4.md) oddziela testy infrastruktury od poprawności pełnych horyzontów. Palnik GPU pozostaje zablokowany do zaliczenia całej bramki.

Przeczytaj [opis modelu i ograniczeń](docs/model.md). Jest to demonstracja edukacyjna oparta na CFD, bez deklaracji dokładności pomiarowej lub walidacji do zastosowań inżynierskich. N-heptan zastępuje pary świecy, a drewno korzysta z jawnie wskazanego przypadku weryfikacyjnego i uproszczonego modelu wilgoci. Utlenianie pozostałego żaru nie jest modelowane. Barwa i poświata są rekonstrukcją wizualną.

[Raport weryfikacji](docs/verification.md) zawiera porównanie z oryginalnym eksporterem NIST, przypadki fizyczne, badanie dwóch siatek i ograniczenie automatycznej kontroli Smokeview. Gwiazdką w historii oznaczono główne przykłady; dodatkowe przebiegi kontrolne pozostają dostępne. Główne przykłady receptury 1.0.2 zawierają rzeczywiste pola zapisywane z częstotliwością 10 Hz.

FDS/Smokeview zachowują oryginalne informacje licencyjne NIST w rozpakowanej dystrybucji. Three.js i Vite: MIT; fdsreader: LGPLv3; fonty DM Sans i Cormorant Garamond: SIL Open Font License. Pełne informacje bibliotek znajdują się w ich pakietach. Kod i dane projektu nie zmieniają licencji zależności.
