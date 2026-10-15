# Weryfikacja IGNIS

Projekt sprawdzono na Windows, Python 3.14.4 i Node.js 24.15.0 z oryginalnym FDS 6.11.1. Wejścia, logi i wyniki przebiegów są zachowane w `runs/`. Dostarczone przykłady znajdują się w `samples/`.

Końcowa kontrola: **13 testów Python i 4 testy Playwright przeszły**, kompilacja TypeScript/Vite zakończyła się poprawnie, a aplikacja wystartowała przez `start.ps1 -NoBrowser`. Zakończono pięć natywnych przypadków brzegowych. Główne przykłady receptury 1.0.2 to dwusekundowe przebiegi, po 21 rzeczywiście obliczonych klatek każdy: palnik `d21db83645d60cad9577`, świeca `1b17aa4d2294ec13a9e7`, drewno `200774f4b12d8edbbadd`. Bezstratnie skompresowane klatki trzech przykładów zajmują łącznie około 72,4 MiB. Dodatkowe starsze nagrania pozostają w historii.

## Dane przestrzenne

Konwerter został porównany z niezależnym narzędziem **NIST fds2ascii**, z tej samej oficjalnej dystrybucji FDS. Sprawdzono wszystkie komórki i siedem kanałów ostatniej klatki: temperaturę, HRRPUV, sadzę, tlen oraz U/V/W. Uwzględniono usunięcie dodatkowej warstwy brzegowej zapisanej przez FDS dla pól `CELL_CENTERED`.

Przypadek palnika `9106076d541a5df2c8c8`: 65 536 komórek. Maksymalna różnica temperatury względem eksportu ASCII: 0,0498°C; HRRPUV: 0,4991 kW/m³. Są to zaokrąglenia eksportu tekstowego do pięciu cyfr znaczących. Porównanie float32 bezpośrednio z `fdsreader` jest dokładne bitowo.

Przypadek drewna `586292a0480818095068`: 57 344 komórki. Maksymalna różnica temperatury względem eksportu ASCII: 0,0005°C. Wszystkie siedem kanałów przeszło kontrolę `rtol=6e-5, atol=1e-6`. Skrypt `scripts/export_reference.py` odtwarza porównanie i zapisuje `reference-check.json` przy danym przebiegu.

To potwierdza poprawność transportu i indeksowania danych, nie dokładność modelu względem rzeczywistego ognia.

## Siatka i przypadki fizyczne

[Porównanie dwóch rozdzielczości](mesh-study.md) zawiera rzeczywiście obliczone wyniki dla wszystkich trzech scen. Dla palnika i świecy różnica średniej mocy we wczesnym oknie wynosi około 0,2%, a różnice temperatur około 6–9%. Dla kontrolnego przebiegu drewna różnica średniej mocy przekracza 100%. Model drewna wymaga ostrożnej interpretacji; nie osiągnięto demonstracji zbieżności ani walidacji eksperymentalnej.

`scripts/physics_checks.py` zapisuje pomiary do [physics-checks.json](physics-checks.json). Wszystkie pięć przebiegów ukończono w rzeczywistym FDS:

| Przypadek | Szczyt mocy W | Maks. temperatura gazu na końcu °C |
|---|---:|---:|
| Brak paliwa | 0 | 20,0000 |
| Tlen 12% obj. | 0 | 20,0000 |
| Napływ +X 0,2 m/s | 591,95 | 1441,79 |
| Drewno bez ogrzewania | 0,00082 | 20,0050 |
| Suche drewno, ogrzewanie 35 kW/m² | 1867,75 | 482,65 |

Średnia składowa U w przypadku napływu wyniosła +0,0814 m/s. Testy braku paliwa i ogrzewania wymagają mocy poniżej 1 mW i temperatury bliskiej otoczeniu. Wyniki dotyczą tych konkretnych wejść i krótkich przebiegów. Zmniejszenie tlenu nie jest uniwersalnym testem empirycznej granicy palności; wynik zależy od modelu wygaszania FDS.

## Aplikacja

Testy Python sprawdzają walidację, tożsamość cache, zgodność powierzchni źródła i strumienia paliwa na obu siatkach, kolejność pól, dekompresję przykładów, blokadę wielu procesów, anulowanie oraz błąd natywnego solvera.

Testy Playwright sprawdzają wszystkie trzy przykłady, warstwy, sondę, przekrój, suwaki i pola liczbowe, zachowanie poprzedniego wyniku, odtwarzanie, prezentację, dialog modelu, układ telefonu i działanie odczytów bez WebGL. Zrzuty kontrolne są w `artifacts/`.

## Ograniczenie kontroli Smokeview

Smokeview 6.11.2 z tej dystrybucji uruchamia się z `-help`, lecz próby automatycznego odczytu/renderowania bez widocznego okna zakończyły się błędem GLUT lub awarią 0xC0000005. **Nie potwierdzono porównania w interaktywnym Smokeview.** Kontrolę numeryczną przeprowadzono niezależnym oryginalnym eksporterem NIST opisanym powyżej.

Pełne pliki `.smv` i `.sf` pozostają w `runs/`, więc można je dodatkowo otworzyć w interaktywnym Smokeview. Skrypt `scripts/smokeview_check.py` zachowuje próbę odczytu wsadowego i raportuje jej niepowodzenie zamiast uznawać sam start procesu za udaną weryfikację.
