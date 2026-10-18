# IGNIS 1.4 — kampania pełnej chemii na GPU

Palnik 3D pozostaje zablokowany. Przejście testów infrastruktury nie jest odbiorem reaktorów. Pełne GRI30, NASA7, niejawny Euler i tolerancje `rtol=1e-5`, `atol(Y)=1e-12`, `atol(T)=1e-3 K` pozostają wymagane.

Aktualna [diagnoza zapłonu](chemistry-forensics-1.4.md) opisuje niezależny BE float64 i eksperymentalny wariant `--precision compensated-state --error-target 0.015625`. Bazowe współczynniki tolerancji pozostają niezmienione; ten wariant zaostrza wewnętrzny estymator i Newtona. Domyślny wariant nadal używa float32 i celu 1. Checkpointy nowego integratora mają schemat 4; dawnych prób nie konwertuje się automatycznie. Użyj nowego katalogu dla zmienionych źródeł lub wersji, zachowując dotychczasowy licznik budżetu.

Bramka sprawdza również efektywne źródła 53 składników w zapisanych stanach Newtona, z uwzględnieniem części low. Próg i podłoga normalizacji są takie jak w istniejącym teście punktowym: `0.001` oraz `1e-8 s⁻¹`. Potwierdzony FAIL pozostaje FAIL przy ponownym uruchomieniu i blokuje pełne 0D oraz skalowanie; brak danych kontrolnych daje INCOMPLETE. PASS dwunastu początkowych stanów nie zastępuje tej kontroli.

## Uruchomienie i wznowienie

```powershell
tools/chemistry-venv/Scripts/python -m pip install -r requirements-chemistry.txt
$env:IGNIS_GPU_ADAPTER='rtx'
npm run test:chemistry:storage
npm run test:chemistry:state
npm run chemistry:campaign -- --output artifacts/gpu-v14/campaign-v2
```

Powtórzenie ostatniej komendy wznawia zgodny checkpoint. `npm run test:gpu:chemistry` uruchamia najpierw krótkie testy, a następnie tę pełną kampanię; pojedynczy krótki reaktor nie wystarcza do sukcesu komendy. Do eksperymentu z poprawianiem rozwiązania LU służy `--linear-solver refined-lu` i odrębny katalog wyników. Oba warianty domyślnie korzystają ze **wspólnego** licznika `artifacts/gpu-v14/chemistry-budget.json`; zmiana katalogu nie odnawia ośmiu godzin. `--budget-ms` pozwala obniżyć limit nowej kampanii. Nie podnosi limitu istniejącego licznika. Kody zakończenia: 0 = PASS, 1 = FAIL, 2 = INCOMPLETE. `--budget-file` przeznaczony jest do jawnie odrębnych kampanii, np. testów infrastruktury.

Anulowanie: Ctrl+C lub utworzenie pustego pliku `cancel` w katalogu wyników. Sterownik kończy bieżącą ograniczoną paczkę, zachowuje zaakceptowane stany i zapisuje INCOMPLETE. Przed wznowieniem usuń plik `cancel`. Nie można przerwać już wykonywanego dispatchu WebGPU; koszty domknięcia i przekroczenie rezerwy są widoczne w rozliczeniu.

Budżet obejmuje kompilację, diagnostykę, walidację i zapis. Czas między poprawnie zamkniętymi sesjami nie jest naliczany. Licznik jest utrwalany co sekundę. Przy awarii procesu trwała dzierżawa konserwatywnie dolicza najwyżej 5 sekund od ostatniego heartbeat albo rezerwę właśnie wykonywanej operacji synchronicznej; nie nalicza całego okresu bezczynności do następnego uruchomienia. Zapobiega to odnowieniu budżetu przez zabicie procesu. Blokada wyklucza jednoczesne kampanie współdzielące licznik.

## Kontrakt obliczeń

Każdy reaktor ma 54 niewiadome, indywidualny czas i krok oraz automat: ocena → LU → aktualizacja/tłumienie → pełny krok i dwa półkroki → estymator → akceptacja albo RETRY. RETRY nie wyłącza reaktora. Dopiero ukończenie lub trwałe zatrzymanie powoduje pomijanie jego pracy. Guardy przed barierami są jednolite dla całego workgroup.

Paczka zawiera 29 dispatchy, a z inspekcją LU 31. Jeden krok fizyczny może wymagać wielu paczek. Metryki powstają równolegle dla każdego reaktora; podsumowanie kafla redukuje 64 wątków. Maksimum kafla służy raportowaniu, nie ustalaniu kroku innych reaktorów.

Estymator dwóch półkroków używa maksimum znormalizowanych błędów składowych. To ostrzejsza norma niż RMS prototypu; współczynniki tolerancji nie zostały zmienione. Newton zachowuje próg RMS 0,1, limit 12 iteracji i 8 prób tłumienia. Korekta dodatniości jest mierzona; ponad 0,1 tolerancji składowej odrzuca próbę. Nie stosujemy renormalizacji udziałów maskującej błąd.

RHS podczas tłumienia jest liczony oddzielnie od pełnego Jacobianu. Jacobian i LU pozostają odrębnymi kernelami. Wariant `refined-lu` wykonuje dwa poprawienia reszty przy zachowaniu pivotowania; nie zmienia kinetyki ani kryteriów odbioru.

## API i pamięć

`Gri30.integrate(..., {implementation: 'gpu'})` uruchamia nowy integrator; domyślne wywołanie zachowuje referencyjny integrator. Opcje obejmują `sampleTimes`, `checkpoint`, `onCheckpoint`, `inspection`, `linearSolver` i istniejące limity. Wynik dodaje typowany postęp reaktorów, profil, trajektorię i checkpoint. Dotychczasowa tablica `status` pozostaje dostępna.

`Gri30.integrateBatch(...)` obsługuje 1–65 536 reaktorów, rozmiar kafla 1–256 i harmonogram round-robin. Trudny reaktor nie jest pomijany. Para callbacków `loadTile`/`saveTile` pozwala przechowywać checkpointy na dysku i utrzymywać jeden kafel w pamięci roboczej. Bez callbacków checkpointy są jawnie zwracane w RAM; dla dużych trajektorii należy użyć trwałego magazynu. Kampania CLI przechowuje kafle oddzielnie i grupuje przypadki według wspólnego horyzontu i planu pomiarowego.

Jawny układ buforów na reaktor: 54 float32 stanu, 270 scratch, 2970 Jacobianu/RHS, 8 metryk LU i 40 kontrolera. Indeksy kontrolera są częścią wersjonowanego kontraktu. Liczniki float32 są zatrzymywane przed utratą reprezentacji całkowitej; nie mogą zawijać się lub zatrzymać adaptacji po przepełnieniu. Podsumowania GPU są małe; końcowe dokładne sumy liczników powstają z indywidualnych danych.

Checkpoint obejmuje wyłącznie zaakceptowane pola oraz trwałe dane kontrolera, entalpię docelową, stan początkowy, historię próbek, wersje, mechanizm i tolerancje. Wznowienie porzuca niedokończony Newton i odtwarza próbę od zaakceptowanego stanu. Sterownik zapisuje plik tymczasowy, wykonuje `fsync`, zachowuje poprzednią generację i atomowo publikuje nową. SHA256 chroni integralność. Błąd integralności albo niezgodność wersji zatrzymuje wznowienie. CLI dodatkowo przypina hash źródeł implementacji. Zmiana sterownika GPU nie wymaga bitowej identyczności, ale wymaga ponownej walidacji numerycznej.

## Pomiary i bramka

Wszystkie czasy mają jednostkę ms. GPU mierzymy timestamp queries; bez ich obsługi czas GPU jest niedostępny. `mapWaitMs` obejmuje również oczekiwanie na wykonanie GPU — nie jest miarą samego transferu i nie dodaje się go do czasu GPU. Profil rozdziela kompilację, alokacje, zgłoszenia, Jacobian, LU, kontroler, aktualizacje, podsumowania i inspekcję. Podaje również przyczyny odrzuceń, liczbę odczytów i bajty. Inspekcja ma jawny narzut.

Snapshot układu powstaje bezpośrednio po LU, przed zmianą pól przez kontroler. `inspect_chemistry_lu.py` rekonstruuje macierz, rozwiązuje ją niezależnie w float64, oblicza uwarunkowanie i porównuje Jacobian z Canterą w faktycznym stanie Newtona. Przy zerowych składnikach używa jednostronnej różnicy drugiego rzędu. Wskaźnik pivotów nie jest liczbą uwarunkowania. Gdy norma Newtona już spełnia próg, LU może pominąć rozwiązanie; taka próbka jest oznaczona `linearSolveRequired=false`.

`LinearPrecisionProbe` porównuje float32 z emulowanym double-single na tych samych macierzach na GPU. Bufor macierzy znajduje się w storage, bez przekraczania 16 KiB workgroup. To **eksperyment liniowy**, nie integrator chemii w zwiększonej precyzji. Poprawa LU nie dowodzi poprawności kinetyki ani akumulacji stanu w float32. Pełna chemia w większej precyzji nie jest automatycznym fallbackiem.

Cantera 3.2.0 oblicza niezależną referencję float64 w dokładnie tych samych reprezentowalnych chwilach fizycznych. GPU docina krok do następnej próbki. Porównywane są wszystkie próbki i ostatni zaakceptowany stan, także w przebiegu częściowym. Czas zapłonu (ΔT≥400 K) i maksimum OH wymagają dodatkowych przebiegów z zagęszczaniem próbek do zmiany oszacowania poniżej 1%; najwyżej trzy zagęszczenia, potem INCOMPLETE.

Progi: zapłon 5%, maksimum OH 10%, temperatura max(1 K, 0,5% przyrostu), składniki max(1e-4, 2% wartości referencyjnej), rodniki H/O/OH/HO₂/CH₃: 1e-12 + 5% wartości referencyjnej. Entalpia, pierwiastki, suma udziałów i reszta LU: 1e-5. Krótki poprawny odcinek nie zastępuje horyzontów 1/10/2/0,5 s.

Artefakty: `chemistry-profile.json`, `reactor-validation.json`, `chemistry-scale.json`, `chemistry-campaign.json`, checkpointy, trajektorie oraz próbki LU. Pliki podsumowań mają kopertę integralności `{schema, sha256, payload}`. Osobne raporty PASS/FAIL/INCOMPLETE obejmują kinetykę, pełne 0D oraz skale 1, 512, 4096, 65 536. PASS całości wymaga PASS każdej pozycji. Niezgodność jest potwierdzana ponowną niezależną walidacją. Brak zasobów, błąd urządzenia lub brak pełnego horyzontu pozostawia INCOMPLETE. Skalowanie pełnych horyzontów jest blokowane do odbioru 0D.
