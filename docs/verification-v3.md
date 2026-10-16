# Weryfikacja implementacji execution-3

Środowisko: Windows x64, Intel i5-12500H, lokalny FDS 6.11.1, Python z `.venv`. Model fizyczny pozostaje 1.0.2. Poniższe wyniki dotyczą poprawności aplikacji i transportu; kwalifikacja szybszych profili jest osobnym etapem.

| Kontrola | Wynik |
|---|---|
| Pełna seria Python przed wznowieniem pomiarów | 168 passed (193,60 s) |
| Atomowa publikacja manifestu podczas równoczesnych odczytów HTTP | PASS, 40 odczytów bez niespójności Content-Length |
| Licznik rzeczywistych kroków i oddzielny profil diagnostyki każdego kroku | PASS w pełnej serii, w tym natywna kontrola kompletnego zapisu każdego kroku |
| TypeScript + Vite | PASS |
| Playwright | 8 passed (2,0 min) |
| Składnia PowerShell | PASS |
| Historyczne porównania numeryczne | 105 par; [raport](validation-v3.md) |

Natywne testy sprawdzają wszystkie siedem kanałów, czasy i współrzędne względem `fdsreader`, łącznie z granicami X/Y/XY oraz nierównych siatek Z. Archiwa są odtwarzane i porównywane hash po hashu z pierwotnym eksportem. Hybryda korzysta z rzeczywistego `fds_openmp.exe` uruchomionego przez MPI. W wariantach P-cores testy wymagają zaobserwowanych masek procesów i wątków mieszczących się w masce rozpoznanej topologii; samo ustawienie zmiennych środowiska nie wystarcza.

Test HTTP uruchamia izolowany serwer, POST eksperymentu bez cache, odbiera rosnący manifest i klatki oraz porównuje ich bajty z plikami. Następnie sprawdza natywne dane. Jednosekundowe przypadki bez paliwa są kontrolą infrastruktury, nie pomiarem wydajności spalania.

Playwright obejmuje warstwy i trzy przykłady, długi pokaz bez zimnego restartu, trwałe gaszenie/rozpalanie, powiększający się podgląd i zachowanie poprzedniego wyniku, błędy, układ mobilny oraz pracę bez WebGL. Logi są w `artifacts/*-v3*.log`. Pozostaje ostrzeżenie deprecjacji zależności FastAPI/TestClient oraz ostrzeżenie rozmiaru paczki Vite; testy i build kończą się poprawnie.

## Badania natywne

Pierwsza kampania z limitem **8 h czasu pracy / 4 GiB nowych danych** zakończyła 23 natywne próby w około 5,7 h. Kolejny przypadek nie mieścił się w rezerwacji miejsca; zachowane dane zajmują około 3,13 GiB, a scratch analizy wymaga dodatkowego miejsca. Dziennik: `artifacts/campaign-v3/campaign.json`. [Końcowa weryfikacja](verification-v3-final.md), [czasy i zasoby](benchmark-v3.md), [45 kompletnych porównań](numerical-v3.md) oraz [przenośne dane z hashami](benchmark-v3-data.json) dotyczą nowych pomiarów, oddzielnych od historycznych 60 prób v2.

Każda próba przeszła kontrolę siedmiu kanałów względem natywnego odczytu i bezstratnej archiwizacji. Pełne serie warmup+3: OpenMP dla obu scen, X2 dla palnika i XY 2×2 dla drewna. Mediany odpowiednio 925,91 / 1098,43 s dla OpenMP, 765,65 s dla palnika X2 oraz 724,41 s dla drewna XY 2×2. Przyspieszenia 1,209× i 1,516× są eksperymentalne: obie serie MPI nie przechodzą starych bramek pól. Maksymalna różnica energii wyniosła 0,0035% i 0,308%; nie zastępuje to oceny pól. Nie wykazano przyczynowego związku błędów z konkretnym podsystemem solvera.

Kryterium P1 nie zostało osiągnięte w przebadanych wariantach. Zbadano X2/Y2/XY 2×2 dla obu scen oraz pojedynczy X4 dla palnika; brakujące warianty wymienia raport. Nie wykonano kampanii rodzin 17-punktowych ani własnego buildu FDS: preflight wykazał brak zgodnego zestawu ifx/VS2022 i bibliotek deweloperskich. Dalsze kampanie wymagają oddzielnych budżetów. Procedura oraz zależności są w [execution-v3](execution-v3.md).

Polityka `validation-v3` pozostaje `pending-review`, a `auto` używa OpenMP 4. Zmiana tego stanu wymaga przeglądu nowych kryteriów i kompletnego pozytywnego materiału pomiarowego. Dotychczasowych limitów nie rozluźniono.

[Raport kroków](steps-v3.md) koryguje pierwotny błąd nowego profilera: liczba wierszy diagnostycznych nie jest liczbą wykonanych kroków. Liczniki i średnie koszty pochodzą teraz z końcowego `Time Step`. Ta korekta nie zmienia czasów eksperymentów, pól CFD ani bramek zgodności. Archiwalne dane pochodne bez wersji `step-profile-2` są oznaczone jako zastąpione; oryginalne dane natywne pozostają zachowane.
