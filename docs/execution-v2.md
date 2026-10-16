# Wykonanie solvera i podgląd v2

Model fizyczny `ignis-1.0.2`, liczby komórek, paliwa, harmonogram ogrzewania drewna i 50 kątów radiacji pozostają bez zmian. Profil `execution-2` i transport `float32-7-v2` mają osobną tożsamość. Zmiana profilu nie podszywa się pod wcześniejszy cache.

## Cykl życia

Każda próba ma UUID i odrębny katalog. Jeden wspólny lease blokuje konkurencyjne uruchomienia aplikacji i benchmarku. Na Windows: typowane WinAPI, `CreateProcessW(CREATE_SUSPENDED | CREATE_NO_WINDOW)`, przypisanie do Job Object z `KILL_ON_JOB_CLOSE`, `ResumeThread`. Nieudane przypisanie kończy niewznowiony proces. Wynik staje się gotowy dopiero po zakończeniu FDS, odczycie końcowych klatek i atomowym zapisie metadanych. Anulowanie oraz publikacja są rozstrzygane pod tą samą blokadą. Lease pozostaje zajęty, jeśli nie potwierdzono zakończenia drzewa procesów; sam błąd zapisu metadanych po zakończeniu procesów nie blokuje kolejnego zadania.

## Podgląd

`fdsreader` dostarcza metadane siatek i odniesienie do niezależnej kontroli. Odczyt przyrostowy przechowuje przesunięcie każdego pliku i najwyżej jedną oczekującą klatkę na kanał/podsiatkę. Kontroluje rozmiary i końcowe znaczniki rekordów Fortran. Usuwa po jednym pomocniczym punkcie na osi tak samo jak `fdsreader`, a następnie składa równomierne podsiatki bez interpolacji. Klatka może być opublikowana dopiero przy komplecie siedmiu kanałów i wszystkich podsiatek w tej samej chwili. Niekompletny ogon pliku czeka na zapis. Narzut nie rośnie przez ponowne odczytywanie wcześniejszych klatek.

Plik binarny jest zapisywany pod nazwą tymczasową i atomowo przemianowywany przed aktualizacją manifestu. Manifest ma `attempt`, `revision`, `status`, `complete`, `profile`, konfigurację, geometrię, czasy, ekstrema i dostępne szeregi. HTTP manifestu używa `no-store`; URL klatki zawiera próbę, dlatego ponowienie nie koliduje z cache przeglądarki. Wynik końcowy korzysta z tych samych plików i ustawia `frameDirectory=preview/frames`.

Smokeview zapisuje węzły TRN w SMV z pięcioma miejscami dziesiętnymi w metrach. Dla drewna krok 0,4/56 m nie jest dokładnie reprezentowany w takim zapisie. Konwerter sprawdza pozycje węzłów względem zadanej siatki z tolerancją formatu 5,1 µm, ograniczoną dodatkowo do 5% komórki, i składa pola według indeksów całkowitych. W metadanych zachowuje dokładną równomierną siatkę wejściową. Nie interpoluje ani nie zaokrągla wartości pól. Niezgodność geometrii kompletnej podsiatki kończy zadanie od razu. Ta tolerancja odczytu współrzędnych nie zmienia żadnej bramki porównania temperatury, tlenu, prędkości, sadzy lub energii.

## Kryteria regresji MPI

Porównujemy dokładnie ten sam przypadek fizyczny i globalną siatkę, OpenMP 4 względem MPI 2/4. Nie wymagamy identyczności rozwiązań numerycznych między trybami. Wymagamy identyczności wszystkich float32 między eksporterem a natywnym odczytem `fdsreader`, w tym komórek przy granicach siatek.

Pola uśredniane są w drugiej połowie przebiegu, na wspólnej osi co 0,1 s. W razie różnych chwil zapisu używana jest liniowa interpolacja czasowa. Temperatura oznacza przyrost ponad otoczenie. Błąd pola to RMS różnicy podzielony przez większą z wartości RMS odniesienia i progu poniżej. Tlen ma błąd bezwzględny. Te same bramki obejmują dwie warstwy komórek sąsiadujących z granicami podsiatek.

| Kanał | Próg normalizacji | Dopuszczalny błąd |
|---|---:|---:|
| Przyrost temperatury | 50°C | 10% |
| HRRPUV | 10 kW/m³ | 20% |
| Sadza | 10⁻⁷ kg/m³ | 25% |
| Tlen | brak normalizacji | 0,005 mol/mol |
| U, V, W osobno | 0,05 m/s | 20% |

Całkowita energia (całka szeregu HRR metodą trapezów): odchylenie do 5%. Zapłon drewna: pierwsza chwila HRR > 10 W w trzech kolejnych zapisach, różnica do 0,2 s. Brak zapłonu w obu przebiegach jest zgodny; zapłon wyłącznie w jednym jest niezgodny. Sondy raportujemy osobno.

To progi regresji tej demonstracji, nie walidacja inżynierska. Nie są podnoszone automatycznie. Każdy z trzech pomiarów kandydata musi przejść bramki względem referencyjnego przebiegu OpenMP o medianowym czasie. Samo przyspieszenie nie wystarcza. Rejestr automatycznego wyboru dodatkowo wymaga minimum trzech pomiarów i skrócenia mediany co najmniej o 5%; dopasowanie konfiguracji, wersji i komputera jest dokładne. Siatka fine i inne parametry bez osobnego wpisu pozostają na OpenMP.

## Interpretacja czasu i zapłonu w interfejsie

Przycisk Zapłon/Zgaś steruje rekonstrukcją płomienia i światłem. Nie zmienia obliczonych pól, nie generuje sztucznego wygaszania i nie zeruje odczytów. Ciągły pokaz korzysta z najdłuższego spójnego fragmentu HRR ≥ 50% maksimum i odtwarza go naprzemiennie. Oś nadal pokazuje czas zapisu CFD. Pełny przebieg kończy się na ostatniej klatce, a podgląd bieżących obliczeń czeka tam na nowe dane. Wynik bez wydzielania ciepła pozostaje bez płomienia.
