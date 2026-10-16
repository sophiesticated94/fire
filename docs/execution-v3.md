# IGNIS 1.2 — badania wykonania FDS

Model spalania 1.0.2, domeny, liczba komórek i promieniowanie pozostają bez zmian. Profil `execution-3` i receptura diagnostyczna `flux-1` rozdzielają nowe obliczenia od historycznego cache. Dane transportowane nadal mają format siedmiu kanałów float32.

## Co jest wdrożone

- Całkowitoliczbowe podziały X/Y/Z na 2 lub 4 siatki, XY 2×2, Z 1:3 / 3:1 i 1:1:2:4 / 4:2:1:1. Jawne `MPI_PROCESS` zachowuje globalne komórki i źródła. Niedzielący się układ jest odrzucany, zamiast zmieniać rozdzielczość.
- `hybrid2x2-z`: dwa procesy, dwa wątki na proces, binarium `fds_openmp.exe`. Czyste MPI używa `fds.exe`.
- Warianty z końcówką `-pcores`: topologia Windows CPU Sets wybiera po jednym logicznym procesorze z każdego fizycznego rdzenia wyższej klasy wydajności. Job Object ogranicza całe drzewo, a telemetria mierzy maski procesów i wątków. Nie zakładamy numeracji procesorów ani skuteczności samego `OMP_PLACES`.
- Przyrostowe odczyty `.out` i obu CSV; telemetria co 2 s, status co 1 s według zegara monotonicznego. Niezmieniony manifest nie jest ponownie zapisywany; HTTP podaje plik bez parsowania JSON.
- Histogram próbkowanego kroku czasu, CFL/VN i błędy/iteracje ciśnienia z natywnych logów. Licznik kroków pochodzi z końcowego `Time Step`, nie z liczby zapisanych wierszy. Koszt podsystemu podzielony przez rzeczywistą liczbę kroków jest **estymacją średnią**, a suma czasów rang MPI nie jest czasem ściennym.
- Natywne strumienie masy i entalpii (punktowe oraz całki po płaszczyznach), promieniowanie gazu, ciśnienie i dywergencja. Płaszczyzny są wspólne dla profili, w 1/8…7/8 każdej osi. Entalpia zawiera przewodzenie i jest odniesiona do otoczenia; promieniowanie pozostaje oddzielną wielkością.

## Walidacja i wybór automatyczny

[Ponowna ocena historycznych przebiegów](validation-v3.md) obejmuje 105 porównań. Wszystkie trzy pary referencji OpenMP są oceniane, a każdy kandydat jest porównywany ze wszystkimi trzema referencjami. Oprócz dotychczasowych limitów liczymy chwilowy RMS na wspólnej osi 0,1 s dla całego przebiegu i drugiej połowy, błędy przy rzeczywistych granicach siatek, zmienność i szeregi sond/HRR. Interpolacja jest wyłącznie czasowa, bez przesuwania trajektorii i bez ekstrapolacji. Odczyt pól przechowuje najwyżej dwie klatki każdego wyniku oraz akumulatory przestrzenne.

`config/validation-v3.json` jest `pending-review`. Automatyka używa **OpenMP 4**, także dla wcześniej zaakceptowanej świecy. Nowe limity chwilowe, zmienności i strumieni wymagają jawnego przeglądu naukowego. Po zatwierdzeniu plik określa limity kanałów w oknach `full`, `late`, `interfacesFull`, `interfacesLate`, `variability` oraz bezwzględne RMS wskazanych urządzeń. Istniejące limity średnich, energii (5%) i zapłonu drewna (0,2 s) nadal obowiązują. Historyczne dane bez `flux-1` nie mogą promować profilu v3. Samo `PASS` starej bramki ani szybki czas nie stanowią kwalifikacji.

## Kampania z budżetem

```powershell
.venv/Scripts/python scripts/campaign_v3.py --hours 8 --gib 4
# Kontynuacja używa tego samego katalogu i pozostałego budżetu:
.venv/Scripts/python scripts/campaign_v3.py --hours 8 --gib 4
.venv/Scripts/python scripts/campaign_v3.py --summary-only
```

Budżet obejmuje czas ścienny sesji, pomiary, archiwizację i analizę; zamknięte przerwy między sesjami nie są czasem pracy. Osobne kontrole poprzedzają dwie rozłączne fazy: natywne dane + eksport + tworzone archiwum oraz analizę po zakończeniu archiwizacji. Przed analizą znamy dokładny rozmiar archiwum i dopiero wtedy rezerwujemy scratch; przy braku miejsca zachowujemy ukończony pomiar i zatrzymujemy analizę. Po sprawdzeniu hashy odtwarzania pierwszy wynik porównania zachowuje w scratch wyłącznie eksport i metadane; oryginalne archiwum pozostaje nietknięte. Pozostaje co najmniej 3 GiB wolnego miejsca systemowego. Heartbeat umożliwia rozliczenie przerwania; ukończone próby są wznawiane po sygnaturze, nigdy nadpisywane. Limit 8 h / 4 GiB dotyczy pierwszej kampanii, nie upoważnia do bezlimitowych następnych badań.

Kolejność: OpenMP warmup+3 dla palnika 6 s i drewna 15 s; X2/Y2/XY22; warmup+3 najlepszego kandydata; pozostałe dekompozycje i hybryda; ewentualny nowy finalista; przypięcie CPU. Wybór do dalszych pomiarów preferuje spełnienie starych bramek, potem najgorszy względny błąd, a potem czas. To **screening**, bez produkcyjnej promocji. Brak zwycięzcy pozostawia OpenMP.

Jednorazowy `scripts/continue_v3.py --after-pid <PID>` czeka na uruchomioną starszą sesję, wykonuje pełną weryfikację przy wolnym solverze, koryguje pochodne profilowanie i wznawia brakujące próby z aktualnym zarządzaniem scratch. Zachowuje ten sam licznik czasu i limit danych, dolicza czas weryfikacji i zatrzymuje się przy błędzie testów. Nie zatwierdza polityki naukowej. Raport końcowy zapisuje w `docs/verification-v3-final.md`.

`artifacts/campaign-v3/campaign.json` jest dziennikiem. `archives/*.zip` przechowują bezstratnie wejście, natywne wyjścia, CSV, logi i SHA256 plików oraz eksportowanych klatek. Eksport może być usunięty dopiero po kontroli archiwum; `backend.run_data.open_run()` odtwarza go i sprawdza identyczność każdego hasha. Nie usuwa się wcześniejszych 60 prób. Nie należy usuwać katalogu kampanii podczas jej działania. Drugi proces nie może otworzyć tej samej kampanii.

## Pomiar przez rzeczywiste HTTP

`scripts/report_campaign_validation.py` publikuje w `docs/numerical-v3.md` stare bramki, energię, zapłon, błędy czasowo-przestrzenne i natywne strumienie z już zapisanych porównań. Dołącza `benchmark-v3-data.json`: konfiguracje, profile, telemetrię, hashe archiwów i komplet metryk porównań, bez lokalnych ścieżek prób. Nie uruchamia solvera ani nie uzupełnia brakujących par. Liczbę braków podaje jawnie; raport powstaje także po zatrzymaniu kampanii przez budżet.

```powershell
.venv/Scripts/python scripts/api_benchmark.py --root artifacts/campaign-v3 --scene burner --duration 6 --mode openmp --hours 8
```

Izolowany serwer używa osobnego katalogu prób i wyłącza odczyt cache. POST, status, rosnący manifest i klatki przechodzą przez HTTP. Bajty klatek są porównane z plikami, następnie wszystkie pola z `fdsreader`. Serwer i benchmark bezpośredni współdzielą globalną blokadę FDS. Czas HTTP obejmuje tworzenie zadania i odbiór ostatniej klatki; uruchomienie serwera jest osobno wyłączone. Wykrycie pierwszej klatki jest próbkowane co 1 s. Nie należy uruchamiać równocześnie z inną kampanią ani obciążać komputera innymi testami podczas pomiarów.

`peakMemoryBytes` pochodzi z Windows Job `PeakJobMemoryUsed` i opisuje szczytowy commit, nie RSS. I/O to liczniki operacji procesów, nie fizyczny pomiar SSD. W benchmarku API `serverJobTelemetry` obejmuje również izolowany backend, a `telemetry` zadanie solvera. Czasy konwersji częściowo nakładają się na solver i nie są ponownie dodawane do czasu całego eksperymentu. [Definicje Windows Job](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information).

## Rodziny przypadków — osobne budżety

```powershell
.venv/Scripts/python scripts/family_campaign.py --root artifacts/family-burner-6 --scene burner --duration 6 --mode mpi4-xy22 --hours 8 --gib 4
```

Ten przykład pokazuje składnię, nie przyznaje nowego budżetu. Każda rodzina zawiera 17 punktów (8 narożników, środek, 8 próbek Latin hypercube, seed 20261016), a w każdym warmup+3 OpenMP i kandydata. Świeca: paliwo 0,96–1,44 mg/s; palnik: 9,6–14,4 mg/s; drewno: wilgotność 6–18%. Wspólnie tlen 20–21,5%, wiatr 0–0,1 m/s. Pozostałe parametry są ustalone. Czasy gazowe 2 i 6 s kwalifikuje się oddzielnie, drewno 15 s; tylko `preview`.

Rejestr wymaga kompletu punktów, referencji, identycznego sprzętu/binariów/modelu/polityki oraz poprawy ≥5% w **każdym** punkcie. Wybór w zweryfikowanym obszarze jest empiryczny; nie dowodzi zgodności poza nim. `fine`, inny czas lub parametr poza zakresem wraca do OpenMP. Żadna rodzina nie jest obecnie zatwierdzona.

## Profilowanie kroków

Pełną diagnostykę każdego kroku uruchamia się osobno, po zakończeniu bieżącej kampanii i przyznaniu jej budżetu:

```powershell
.venv/Scripts/python scripts/profile_native.py --root artifacts/profile-burner --scene burner --duration 2 --mode openmp --all-steps --hours 1 --gib 1
.venv/Scripts/python scripts/report_steps.py
# Korekta pochodnych pól starszego dziennika, wyłącznie gdy kampania nie działa:
.venv/Scripts/python scripts/report_steps.py --repair-state
```

`DIAGNOSTICS_INTERVAL=1` nie zmienia wejściowych warunków fizycznych ani stabilności, ale zwiększa koszt diagnostyki i komunikacji MPI. Profil `flux-1-allsteps` ma osobny klucz i jest wyłączony z promocji produkcyjnej; jego czasu nie porównuje się z normalnym benchmarkiem. [Raport kroków](steps-v3.md) rozróżnia próbki i rzeczywistą liczbę kroków. Oryginalne archiwa zachowujemy, a skorygowane dane pochodne zapisujemy w `profiling-v2/`.

## Własne kompilacje CPU

```powershell
.venv/Scripts/python scripts/build_fds.py --preflight
# Dopiero w zgodnym środowisku deweloperskim:
.venv/Scripts/python scripts/build_fds.py --variant precise-o2 --output tools/fds-builds/precise-o2
.venv/Scripts/python scripts/build_fds.py --variant avx2-o3 --output tools/fds-builds/avx2-o3
```

Źródło jest przypięte do `ff928dbf68a2623ced3a007be75391c6dc6c9f90` (FDS 6.11.1). Zachowujemy upstreamowe cele Windows oraz opcjonalne biblioteki z wydania. Wymagane ifx 2025.2, Visual Studio Build Tools 2022, GNU make, deweloperskie Intel MPI, MKL, Hypre 3.0.0 i Sundials 7.5.0. Warianty używają `/fp:precise`; drugi bada O3/AVX2 i generuje raport wektoryzacji. Nie zmieniają CFL, stabilności, siatki ani receptury fizycznej. Manifest zapisuje kompilator, flagi, źródła, biblioteki i hashe obu binariów. Wynik wymaga własnego warmup+3 i pełnej walidacji, zanim może trafić do `auto`.

Preflight lokalny: brak ifx/make, brak bibliotek deweloperskich; zainstalowane Build Tools 2026, bez potwierdzonej zgodności z ifx 2025.2. Nie wykonano własnej kompilacji ani pomiaru jej przyspieszenia. [Wymagania Intel 2025](https://www.intel.com/content/www/us/en/developer/articles/system-requirements/fortran-compiler/2025.html) podają minimum około 3 GB dla kompilatora i bibliotek, oddzielnie od SDK, instalatorów i workspace. Nie instalujemy niesprawdzonego zestawu bez bilansu wszystkich zależności. [Przypięty makefile FDS](https://github.com/firemodels/fds/blob/ff928dbf68a2623ced3a007be75391c6dc6c9f90/Build/makefile) stanowi podstawę procedury.

Własne binaria testuje się przez `IGNIS_FDS=<katalog>/fds_openmp.exe` oraz `IGNIS_MPIEXEC=<zainstalowany>/mpi/mpiexec.exe`. To oddzielne profile dzięki hashom; nie dziedziczą kwalifikacji wydania NIST.

## Testy i granice wnioskowania

`scripts/verify_v3.ps1` uruchamia Python, build i Playwright (serwer 8765 musi działać). `-NativeCampaign` dodatkowo wykonuje budżetowaną kampanię **po** testach. Status badań jest oddzielony od poprawności aplikacji. Historyczne raporty v2 pozostają niezmienione; starszy `verify.ps1` przekierowuje do testów v3 i nie może poświadczać nowych profili historycznymi pomiarami.

To kryteria regresji edukacyjnej demonstracji CFD. Nie stanowią walidacji inżynierskiej. GPU, zmiana języka backendu i luzowanie stabilności nie są częścią optymalizacji. Dane zmierzone należy odróżniać od możliwych korzyści nowych układów lub kompilacji.
