# IGNIS 1.4 — bramka pełnej chemii GRI30

**Etap badawczy nie został odebrany. Palnik GPU nie jest włączony.** Kod chemii jest używany przez laboratorium testowe, nie przez produkcyjny solver gorącego powietrza. Nie zastosowano mechanizmu zastępczego ani danych HRR z FDS.

[Diagnoza rozbieżności i eksperymenty naprawcze](chemistry-forensics-1.4.md) rozdzielają historyczny FAIL od odbioru nowych wariantów. Dominuje skumulowany błąd czasowy BE; dostępne są pasywne śledzenie, niezależny BE float64 i eksperymentalna kompensacja stanu/entalpii. Nie jest to pełna chemia double-single ani zaliczona bramka 0D.

Nowy integrator GPU, checkpointy i harmonogram do 65 536 reaktorów są opisane w [instrukcji kampanii](gri30-campaign.md). Referencyjny prototyp opisany poniżej pozostaje dostępny. Krótki test 513 reaktorów sprawdza harmonogram, a nie pełne horyzonty skalowania. Bieżący raport odbioru znajduje się w [chemistry-acceptance-1.4.md](chemistry-acceptance-1.4.md).

## Mechanizm i implementacja

Przypięto pełny [Cantera 3.2.0 gri30.yaml](https://github.com/Cantera/cantera/blob/v3.2.0/data/gri30.yaml), wraz z oryginalnym nagłówkiem, pochodzeniem, licencją pakietu i SHA256:

`06650b1e0ee0012f6903d5328b1bb218cb6007d07f8ebe375d18f24811039345`

53 składniki, 325 reakcji: 275 Arrheniusa, 21 z trzecim ciałem, 26 Troe i 3 Lindemanna. Odwracalność i oznaczenia duplikatów są zachowane. Generator odmawia pracy z innym hashem. Tablice mają jednostki SI z kmolem jako jednostką ilości substancji; konwersję współczynników źródłowych wykonuje Cantera podczas generowania.

WGSL oblicza NASA7, stałe równowagi, pełne szybkości reakcji i analityczny Jacobian przez różniczkowanie automatyczne w trybie forward. Referencja testowa korzysta niezależnie z różnic skończonych float64 w Canterze przy stałym ciśnieniu i z tym samym jawnym przedłużeniem `Y/sum(Y)` poza rozmaitość znormalizowanych udziałów. Sumowanie źródeł i entalpii jest kompensowane. To kontrola punktowego RHS/Jacobianu, nie dowód poprawności integracji w czasie.

Wspólny deklarowany zakres termodynamiki mechanizmu w Canterze wynosi 300–3000 K. Szerszy bezpiecznik prototypu 200–3500 K nie rozszerza ważności danych: skrajne przedziały byłyby ekstrapolacją i nie zostały odebrane. Punktowe testy obejmują 300–2500 K.

Prototyp reaktora używa niejawnego Eulera, podwojenia kroku do estymacji błędu, tłumionego Newtona, skalowania niewiadomych i LU z pivotingiem. Wiersz temperatury zastępuje warunek stałej całkowitej entalpii, obejmującej entalpie tworzenia. Nie dodaje drugi raz HRR. Tolerancje pozostają `rtol=1e-5`, `atol(Y)=1e-12`, `atol(T)=1e-3 K`. Korekta dodatniości w prototypie może obcinać wartości ujemne do zera; jej niezależny budżet pozostaje wymaganiem przed odbiorem.

Ocena Jacobianu, LU i aktualizacja Newtona są osobnymi dispatchami. LU używa jednej macierzy rozszerzonej i 12 776 B pamięci workgroup. Kafel zawiera maksymalnie 256 reaktorów; większa liczba wymaga jawnego harmonogramu kafli. API odmawia cichego dispatchowania 65 536 grup w jednym wymiarze. Wczesny monolityczny prototyp powodował `DXGI_ERROR_DEVICE_HUNG`; został usunięty. Rozdzielone kernele nie wykazały tego problemu w zapisanych próbach.

Reszta LU jest normowym błędem wstecznym skalowanego układu. Raport rozróżnia próby odrzucone i poprawne rozwiązania. Stosunek pivotów jest wyłącznie wskaźnikiem; **nie** jest liczbą uwarunkowania. `chemistry_conditioning.py` wyznacza niezależnie rzeczywiste `cond(A, inf)` w float64. W 36 zbadanych układach osiąga ono około 4,4×10¹³, co wskazuje na ryzyko utraty dokładności w float32.

## Odtworzenie

```powershell
python -m venv tools/chemistry-venv
tools/chemistry-venv/Scripts/python -m pip install -r requirements-chemistry.txt
tools/chemistry-venv/Scripts/python scripts/generate_gri30.py
tools/chemistry-venv/Scripts/python scripts/generate_reactor_references.py
tools/chemistry-venv/Scripts/python scripts/chemistry_conditioning.py
$env:IGNIS_GPU_ADAPTER='rtx'
npm run test:gpu:chemistry:reference
tools/chemistry-venv/Scripts/python scripts/compare_gpu_reactor.py
```

Test akceptacyjny **pozostaje czerwony**, jeżeli prototyp nie ukończy horyzontu. Limit pojedynczej próby wynosi 180 s czasu ściennego; jest ograniczeniem eksperymentu, nie fizycznym kryterium zgodności ani dowodem niemożliwości WebGPU. Nie zmniejszamy wymaganego horyzontu na potrzeby uzyskania PASS. Zwykłe `test:gpu` sprawdza stabilny przepływ, punktową kinetykę i infrastrukturę. `test:gpu:chemistry:reference` zachowuje historyczną próbę prototypu; aktualne `test:gpu:chemistry` wymaga nowej, pełnej kampanii i nie może zakończyć się PASS na podstawie jednego krótkiego reaktora.

Niezależne referencje obejmują mieszaniny CH₄/powietrze przy φ=0,5/1/2, 1000 K przez 10 s, 1200 K przez 2 s i 1500 K przez 0,5 s oraz zimny przypadek 500 K przez 1 s. Początkowe rodniki wynoszą zero. Cantera używa `rtol=1e-10`, `atol=1e-20`; zapłon oznacza pierwsze ΔT≥400 K. Brak przekroczenia w horyzoncie jest oznaczony jako wynik ucięty.

## Niezamknięte kryteria

Nadal wymagane są pełne przebiegi wszystkich reaktorów, zgodność czasów zapłonu, maksimum OH, temperatury, głównych składników i śladowych rodników, bilanse pierwiastków i entalpii oraz niezależna kontrola rozwiązania LU. Krótki poprawny odcinek nie zastępuje tych testów.

| Skala | Status pełnej niejawnej chemii |
|---:|---|
| 1 | Prototyp i pomiary; bramka reaktora niezamknięta |
| 512 | Nieodebrane — istniejący harmonogram czeka na pełny odbiór 0D |
| 4096 | Nieodebrane |
| 65 536 | Nieodebrane; brak prognozy wydajności |

Nie wykonano integracji palnika 3D, transportu 53 składników, reagującego EOS i projekcji ani sterownika zapłonu. Te prace są zależne od odbioru chemii 0D. Obecnego reaktora nie wolno uznawać za równoważny FDS, a ocena punktowego Jacobianu nie promuje go do aplikacji.
