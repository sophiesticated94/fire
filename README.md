# IGNIS — laboratorium ognia 3D

Lokalna aplikacja po polsku: świeca, palnik metanowy i piroliza drewna. Rzeczywisty **NIST FDS 6.11.1** oblicza pola przestrzenne, a Three.js rekonstruuje płomień, dym i warstwy pomiarowe. Obliczenia i odtwarzanie wyników są rozdzielone.

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
- Przeciągaj scenę, aby obracać kamerę; kółko przybliża. Dostępne są widoki 3D, bok i góra.
- Przełączaj płomień, temperaturę, przepływ i tlen. Przekrój odsłania wnętrze pola. Kliknięcie sceny wybiera sondę w najbliższej komórce na płaszczyźnie przekroju.
- Suwaki i pola liczbowe edytują warunki nowego eksperymentu. **Oblicz doświadczenie** uruchamia FDS. Zmiany nie zmieniają poprzednich danych ani ich odczytów.
- Podczas obliczeń możesz oglądać poprzedni wynik. Anulowanie nie usuwa zapisanych doświadczeń.
- Czas, pauza, przewijanie i szybkość dotyczą odtwarzania zapisanych klatek. Spacja przełącza odtwarzanie, jeśli fokus nie jest w kontrolce. Ukryta karta nie nadrabia czasu.
- Tryb prezentacji ukrywa panele. Esc przywraca interfejs.
- Przełącznik oszczędnego renderowania zmniejsza obciążenie GPU; nie zmienia siatki ani wyników CFD.
- Bez WebGL2 nadal działają obliczenia, historia, odczyty i wykres mocy.

Obliczenia mają własny czas fizyczny. Kilka sekund spalania może wymagać wielu minut pracy CPU. Postęp pokazuje czas rzeczywiście osiągnięty przez solver, nie prognozowany czas oczekiwania. Wyższa rozdzielczość ma około 3,4 razy więcej komórek i może wymagać więcej niż 3,4 razy dłuższych obliczeń z powodu mniejszego kroku czasu.

## Dane i API

`runs/<id>/` zawiera wejście `ignis.fds`, oryginalne wyjście solvera, log, konfigurację, `result.json` i binarne klatki `frames/*.bin`. `samples/` zawiera dostarczone przykłady. Wyniki są identyfikowane przez konfigurację, wersję modelu i solvera. Nie należy ręcznie zmieniać plików obliczonego przypadku.

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
| GET | `/api/experiments/{id}/input` | oryginalny plik wejściowy FDS |
| GET | `/api/experiments/{id}/log` | diagnostyka solvera |

Podgląd deweloperski: uruchom `.venv\Scripts\python -m uvicorn backend.app:app --host 127.0.0.1 --port 8765` i w drugim terminalu `npm run dev`. Vite przekazuje `/api` do serwera. Pakiet produkcyjny powstaje w `dist/`.

Opcjonalnie `IGNIS_FDS` wskazuje własny plik wykonywalny FDS 6.11.1, a `IGNIS_THREADS` ustawia liczbę wątków CPU od 1 do 8 (domyślnie 8). Dla wartości 1 używany jest wariant bez OpenMP. Najlepsza liczba wątków zależy od siatki i obciążenia komputera. Solver nie korzysta z GPU; RTX służy renderowaniu. Jednocześnie aplikacja wykonuje jeden eksperyment. Zewnętrzne uruchomienia IGNIS są zabezpieczone wspólną blokadą procesu.

## Testy

```powershell
.\.venv\Scripts\python -m pytest tests/test_model.py -q
npm run build
npm run test:e2e  # przy uruchomionym serwerze na porcie 8765
```

Jeśli Chromium Playwright nie jest dostępny: `npx playwright install chromium`. Zrzuty są zapisywane w ignorowanym `artifacts/`.

Obliczenie przypadku z terminala:

```powershell
.\.venv\Scripts\python scripts/compute.py --scene burner --duration 6
.\.venv\Scripts\python scripts/compute.py --scene candle --duration 3 --quality fine
.\.venv\Scripts\python scripts/compute.py --scene wood --duration 15 --moisture 12
```

## Zakres naukowy i licencje

Przeczytaj [opis modelu i ograniczeń](docs/model.md). Jest to demonstracja edukacyjna oparta na CFD, bez deklaracji dokładności pomiarowej lub walidacji do zastosowań inżynierskich. N-heptan zastępuje pary świecy, a drewno korzysta z jawnie wskazanego przypadku weryfikacyjnego i uproszczonego modelu wilgoci. Utlenianie pozostałego żaru nie jest modelowane. Barwa i poświata są rekonstrukcją wizualną.

[Raport weryfikacji](docs/verification.md) zawiera porównanie z oryginalnym eksporterem NIST, przypadki fizyczne, badanie dwóch siatek i ograniczenie automatycznej kontroli Smokeview. Gwiazdką w historii oznaczono główne przykłady; dodatkowe przebiegi kontrolne pozostają dostępne. Główne przykłady receptury 1.0.2 zawierają rzeczywiste pola zapisywane z częstotliwością 10 Hz.

FDS/Smokeview zachowują oryginalne informacje licencyjne NIST w rozpakowanej dystrybucji. Three.js i Vite: MIT; fdsreader: LGPLv3; fonty DM Sans i Cormorant Garamond: SIL Open Font License. Pełne informacje bibliotek znajdują się w ich pakietach. Kod i dane projektu nie zmieniają licencji zależności.
