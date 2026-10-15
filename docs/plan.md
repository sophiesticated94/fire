# IGNIS Fire: audyt wydajności i ostateczny plan optymalizacji

Przejrzałam kod repozytorium [IGNIS Fire na GitHubie](https://github.com/sophiesticated94/fire?utm_source=chatgpt.com), przede wszystkim `models.py`, `engine.py`, `converter.py`, frontend, testy i dokumentację weryfikacji. Porównałam go z analizą Gemini.

Główna diagnoza Gemini jest trafna: problemem jest FDS, nie Python ani Three.js. Jednak proponowane przyspieszenia są miejscami przeszacowane, a niektóre zmiany mogą istotnie zniekształcić obliczaną fizykę.

Najważniejsze jest rozdzielenie trzech celów:

1. Przyspieszenie solvera bez zmiany problemu fizycznego.
2. Tańsze przybliżenia przez świadome zmniejszenie dokładności lub czasu symulacji.
3. Szybszy dostęp do wyników przez podgląd w trakcie obliczeń.

Te trzy rzeczy wymagają osobnych pomiarów. Inaczej łatwo ogłosić dziesięciokrotne przyspieszenie, skracając symulowany eksperyment dziesięciokrotnie. Matematycznie poprawne, inżyniersko trochę bezczelne.

## 1. Co wykazał audyt

Zidentyfikowane główne wąskie gardło

FDS CPU

| Generowanie wejścia   | Pomijalny koszt według pomiarów Gemini        |
| --------------------- | --------------------------------------------- |
| Symulacja FDS         | Dominujący koszt obliczeniowy                 |
| Konwersja siedmiu pól | Około 0,5 s dla 21 klatek w teście Gemini     |
| Frontend              | Nie odpowiada za wielominutowe obliczenia CFD |

Własna dokumentacja projektu pokazuje również, że wyniki istotnie zależą od rozdzielczości siatki:

| Scena  | Różnica mocy między siatkami | Różnica temperatury sondy |
| ------ | ---------------------------- | ------------------------- |
| Palnik | 0,2%                         | 8,9%                      |
| Świeca | 0,2%                         | 6,1%                      |
| Drewno | 104,3%                       | 114,2%                    |

Źródło: [docs/mesh-study.md](https://github.com/sophiesticated94/fire/blob/main/docs/mesh-study.md?utm_source=chatgpt.com).

To szczególnie ważne dla drewna. Zmniejszenie liczby komórek może radykalnie przyspieszyć symulację, ale wyniki ilościowe już teraz nie są stabilne względem zagęszczenia siatki.

Dlatego nie rekomenduję prostego zastąpienia aktualnej siatki podglądowej jeszcze rzadszą siatką jako domyślnego sposobu liczenia wszystkich doświadczeń.

## 2. Co należy poprawić w analizie Gemini

### A. MPI nie dało dwukrotnego przyspieszenia

Gemini zestawił MPI z niekorzystnym wariantem dwuwątkowego OpenMP, zamiast z najszybszą zmierzoną konfiguracją.

Czasy solvera z raportu Gemini

Ten sam krótki test 0,2 s czasu fizycznego. Mniej znaczy lepiej. Wyniki wymagają niezależnego powtórzenia.

0 s3 s6 s9 s12 sSerialOpenMP 4OpenMP 6OpenMP 8MPI 2

MPI 2 było szybsze od OpenMP 6 o około 7,1% czasu wykonania, a od aktualnego OpenMP 8 o około 14%. To interesujący wynik, lecz nie uzasadnia obietnicy 2–3×.

Co więcej, w historii testów Gemini pojawiają się eksperymenty współdzielące katalog `scratch_perf`, a część prób nie sprawdza kodu zakończenia solvera. Stwarza to ryzyko kolizji plików lub porównania niepełnych przebiegów.

Wniosek: MPI pozostaje kandydatem do optymalizacji, nie domyślną architekturą przed rebenchmarkiem.

Dokumentacja FDS rzeczywiście wskazuje zalety MPI, ale również ograniczenia OpenMP i koszty komunikacji pomiędzy siatkami.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github-wiki-see.page\&sz=32)

firemodels/fds GitHub Wiki

+1



### B. Tryb `draft` może zmienić fizykę źródła

Gemini proponuje siatkę `20×20×40`. W aktualnym `geometry()`:

| Scena  | Obecne Δx | Proponowane Δx | Szerokość źródła |
| ------ | --------- | -------------- | ---------------- |
| Palnik | 5 mm      | 8 mm           | 20 mm            |
| Świeca | 2,5 mm    | 4 mm           | 10 mm            |

W `make_deck()` wymiary źródła są zaokrąglane do siatki. Przy 20 komórkach szerokość źródła w obu scenach może zostać zmniejszona o 20%.

Co prawda całkowity strumień masy paliwa jest normalizowany do rzeczywistej powierzchni numerycznej, ale zmieniają się geometria i lokalna intensywność dopływu.

To nie jest tylko mniej dokładne liczenie tego samego przypadku.

Decyzja: nie wprowadzać `draft` jako naukowo równoważnego trybu. Można go dodać później jako wyraźnie oznaczony tryb poglądowy, po sprawdzeniu geometrii i porównaniu pól.

### C. Skrócenie czasu eksperymentu z drewnem zmienia ogrzewanie

W `models.py` znajduje się:

```
min(10, c.duration * 0.65)
```

Zatem skrócenie `duration` z 15 do 5 sekund zmienia czas działania zewnętrznego ogrzewania z 9,75 do 3,25 sekundy.

To zmiana warunków fizycznych, nie tylko przyspieszenie obliczeń.

Decyzja: harmonogram ogrzewania powinien być niezależnym parametrem modelu, a krótsze eksperymenty z drewnem należy traktować jako obserwację początkowej fazy procesu.

### D. Radiacja wymaga osobnego testu poprawności

Gemini słusznie wskazał `TIME_STEP_INCREMENT` w sekcji `&RADI`. To poprawny parametr FDS.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



Jednak zmniejszenie `NUMBER_RADIATION_ANGLES` z 50 do 36 oraz rzadsze aktualizowanie radiacji zmieniają aproksymację promieniowania.

Jeżeli udział radiacji w czasie procesora wynosi rzeczywiście około 12%, nawet dwukrotne obniżenie jej kosztu oznacza najwyżej około 6% oszczędności całkowitego czasu, przy pozostałych kosztach bez zmian.

Nie ma podstaw, by przed pomiarem deklarować błąd temperatury poniżej 1%.

## 3. Ostateczny plan wdrożenia

Etap 1. Powtarzalne benchmarki i profilowanie

Priorytet P0

Pliki: `scripts/benchmark.py` (nowy), `engine.py`.

Zaimplementować izolowany benchmark z osobnymi katalogami roboczymi, kontrolą `returncode` i potwierdzeniem poprawnego zakończenia FDS. Każdą konfigurację wykonywać co najmniej trzykrotnie po rozgrzewce.

Porównać `serial`, OpenMP `2/4/6/8`, MPI `2/4` i dopiero potem tryby hybrydowe. Osobno palnik, świecę i drewno. Mierzyć czas całkowity, czas na krok CFD, liczbę kroków, zużycie CPU/RAM, I/O oraz czasy podsystemów z plików profilowania FDS.

Ważne: testować również przypisanie procesów do rdzeni P, bez zakładania, że Windows automatycznie wybierze najlepsze.

Etap 2. Szybki eksperyment bez ukrytej zmiany fizyki

Priorytet P0

Pliki: `src/types.ts`, `backend/models.py`, `src/main.ts`.

Ustawić szybki, dwusekundowy przebieg jako domyślną opcję interaktywną dla palnika i świecy, pozostawiając dłuższe przebiegi do analizy ewolucji płomienia. Zachować obecną siatkę `preview` 32×32×64.

Dla drewna pozostawić dłuższy przebieg jako główny, oddzielić czas ogrzewania od `duration` i dopiero wtedy umożliwić krótkie doświadczenia. W interfejsie rozróżnić „Szybki eksperyment” i „Pełny przebieg”.

Dopasowanie domyślnych parametrów do dostarczonych wyników dwusekundowych może też umożliwić natychmiastowy odczyt istniejącego cache.

Etap 3. Adaptacyjny wybór silnika i MPI

Priorytet P1

Pliki: `backend/models.py`, `backend/engine.py`, nowy `backend/solver_config.py`.

Wydzielić konfigurację uruchomienia solvera i wybór wariantu `serial / OpenMP / MPI / hybrid`. Nie kodować na stałe założenia, że większa liczba procesów daje szybszy wynik.

Przy MPI generować prawidłowy podział domeny z zachowaniem globalnej rozdzielczości. Przetestować podziały w różnych osiach, równoważenie obciążenia i zachowanie przepływu na granicach siatek.

Zintegrować uruchamianie przez `mpiexec`, a na Windows zapewnić zatrzymanie całego drzewa procesów, najlepiej mechanizmem Job Objects. Obecne `terminate()` dotyczy bezpośrednio uruchomionego procesu, co przy MPI może nie wystarczyć.

Następnie porównać siedem połączonych pól z wynikiem jednosieciowym oraz sondy, przebiegi HRR i bilanse. `fdsreader.to_global()` zweryfikować dla wszystkich siedmiu kanałów.

Etap 4. Strojenie parametrów numerycznych

Priorytet P1

Pliki: `backend/models.py`, `tests/test_model.py`.

Przeprowadzić eksperymenty ze zmianami `RADI.TIME_STEP_INCREMENT` 3 → 6 i `NUMBER_RADIATION_ANGLES` 50 → 36, osobno oraz łącznie.

Porównywać nie tylko maksymalną temperaturę, lecz także HRR, sondy, pola przestrzenne, strumień promieniowania do powierzchni i przebieg zapłonu drewna.

Przyjąć nowe ustawienia wyłącznie wtedy, gdy oszczędność jest powtarzalna i mieści się w wcześniej ustalonych tolerancjach modelu. Nie wyłączać promieniowania tylko dla uzyskania większego FPS.

Etap 5. Wyniki progresywne

Priorytet P2

Pliki: `backend/converter.py`, `backend/app.py`, `backend/engine.py`, `src/main.ts`.

Odczytywać kompletne klatki FDS w trakcie obliczeń i publikować je poprzez oddzielny manifest podglądu. Frontend będzie mógł prezentować pierwsze rzeczywiste pola, podczas gdy solver oblicza kolejne.

Dodać endpointy `preview/manifest` i `preview/frames/{n}`, atomowe publikowanie klatek, obsługę przerwania i finalne przejście do `result.json`.

Nie uruchamiać ponownie pełnego `to_global()` dla wszystkich dotychczasowych klatek przy każdej aktualizacji. Konwersja musi być inkrementalna, inaczej narzut może rosnąć kwadratowo wraz z liczbą zapisów.

Etap 6. Regresje, cache i utrwalenie wyników

Warunek wydania

Pliki: `backend/models.py`, `backend/engine.py`, `tests/`, `docs/`.

Wprowadzić wersjonowany profil solvera i odcisk parametrów wpływających na wyniki do tożsamości eksperymentu. Zmiana receptury nie może po cichu użyć starego cache.

Poprawić ponawianie obliczeń: obecny `create()` usuwa pliki w katalogu zadania, ale pozostawia podkatalog `frames/`, potencjalnie ze starymi klatkami.

Każda optymalizacja musi przejść testy Python, Playwright, uruchomienie natywnego FDS i kontrolę pól numerycznych.

## 4. Warunki zaakceptowania optymalizacji

Nie uznawałabym zmiany za sukces wyłącznie dlatego, że solver skończył szybciej.

| Kryterium        | Warunek                                                                      |
| ---------------- | ---------------------------------------------------------------------------- |
| Wydajność        | Mediana z co najmniej 3 poprawnych przebiegów, wraz z rozrzutem              |
| Porównywalność   | Te same parametry fizyczne, domena, siatka i czas symulacji                  |
| MPI              | Zachowana poprawność i ciągłość przepływu na granicach siatek                |
| Radiacja         | Zmierzone odchylenia temperatur, HRR i strumieni cieplnych                   |
| Transport danych | Identyczne wymiary, czasy i kolejność siedmiu kanałów                        |
| Anulowanie       | Brak osieroconych procesów FDS i pozostawionych niekompletnych wyników       |
| Cache            | Brak ponownego wykorzystania wyniku przy zmienionej recepturze obliczeniowej |

Dla pola temperatury i spalania należy analizować błędy przestrzenne oraz statystyki w oknach czasowych, nie tylko pojedyncze maksima. Bezwzględna zgodność bitowa pomiędzy MPI i OpenMP nie jest rozsądnym wymaganiem, ale zgodność numeryczna musi być wykazana.

## 5. Czego nie robić na tym etapie

- Nie przepisywać solvera FDS na Python, C++ lub GPU. To oznaczałoby budowę nowego modelu CFD, nie optymalizację obecnego.
- Nie zmieniać automatycznie siatki na 20×20×40 dla wszystkich scen.
- Nie zwiększać sztucznie dopuszczalnego kroku czasowego przez poluzowanie warunków stabilności.
- Nie usuwać radiacji z modelu drewna.
- Nie wdrażać domyślnie MPI na podstawie jednego krótkiego benchmarku.
- Nie traktować krótszego czasu fizycznego jako wzrostu wydajności numerycznej.

## 6. Docelowa architektura

Frontend

Tryb doświadczenia, jakość, parametry fizyczne

Experiment Planner

Wersjonowanie receptury • cache • geometria • walidacja

Solver Runner

Serial

OpenMP

MPI / Hybrid

Wybór na podstawie sprawdzonego profilu wydajnościowego

Incremental Result Pipeline

Walidacja klatek • konwersja • manifest • zapis atomowy

Live Preview

Niepełny wynik

Final Result

Komplet i cache

## 7. Ostateczna decyzja

Kolejność prac ma być następująca:

Benchmark → dobór OpenMP/MPI → krótki przebieg gazowych scen → walidacja radiacji → podgląd progresywny → regresje i dokumentacja.

Nie deklaruję przyspieszenia 10× ani zejścia do 15–30 sekund. Aktualne dane tego nie dowodzą. Przybliżony zysk 3× ze skrócenia czasu symulacji jest możliwy w zakresie, gdzie koszt rośnie proporcjonalnie do czasu fizycznego, ale nie oznacza przyspieszenia samego FDS.

Największą wartość widzę w automatycznie dobranym, zweryfikowanym trybie równoległym i progresywnym udostępnianiu prawdziwych klatek, a nie w agresywnym upraszczaniu fizyki. Dzięki temu IGNIS może pozostać sensownym laboratorium numerycznym, zamiast zmienić się w efektowną animację z naukową etykietą.