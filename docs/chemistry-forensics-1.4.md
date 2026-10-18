# GRI30 — diagnoza zapłonu i eksperymenty naprawcze

18 października 2026. Pełny mechanizm: 53 składniki, 325 reakcji. Historyczny odbiór pozostaje **FAIL**. Diagnoza dominującego błędu temperatury w zbadanym oknie: **IDENTIFIED — skumulowany błąd czasowy backward Euler**. Nie oznacza to zamknięcia wszystkich problemów precyzji ani zaliczenia pełnego reaktora.

## Eksperyment różnicowy

Na potwierdzonym WebGPU NVIDIA RTX 4050 / DXGI `0x28a1` zapisano 4508 zaakceptowanych kroków reaktora CH₄/powietrze, 1500 K, φ=1. Każdy krok porównano z Canterą 3.2.0 w tej samej chwili. Zapis obejmuje również próby Newtona i tłumienia. Jest pasywny: test GPU potwierdza identyczne zaakceptowane pola i kontroler ze śledzeniem oraz bez niego.

Pierwsze przekroczenie kryterium trajektorii występuje przy **0,001114858562 s**, w temperaturze. To pierwszy wykryty błąd trajektorii według kryteriów odbioru, a nie twierdzenie o pierwszym błędzie arytmetycznym. Różnice źródeł chemicznych są raportowane osobno.

| Porównanie na końcu okna 0,001164342907 s | Temperatura / limit | Składniki / limit | Rodniki / limit |
|---|---:|---:|---:|
| GPU float32 względem Cantery | 6,2172 | 2,7090 | 2,1560 |
| Niezależny float64 BE, identyczne kroki, względem Cantery | 6,0758 | 2,6472 | 2,1050 |
| GPU względem float64 BE | 0,1374 | 0,0600 | 0,0463 |
| Float64 BE, każdy podkrok podzielony na 8, względem Cantery | 0,7319 | 0,3163 | 0,2441 |

Float64 odtwarza równania gatunków, warunek stałej całkowitej entalpii oraz pełny krok i dwa półkroki. Stosuje niezależne różnice skończone, skalowany układ i dokładniej rozwiązany Newton. Nie wykorzystuje macierzy GPU do obliczania referencji. Błąd pojedynczych sprawdzonych kroków GPU względem jego pierwiastka wynosił najwyżej około 0,273 bazowej tolerancji integratora; nie jest to ta sama jednostka co kolumny kryteriów trajektorii powyżej.

Zaokrąglenie danych początkowych również sprawdzono: zmiana entalpii wyniosła −0,0017817 J/kg. Dodatkowy błąd początkowej entalpii obliczonej na GPU wyniósł około −0,020924 J/kg względem Cantery dla odczytanego stanu float32. W pierwszym punkcie przekroczenia zmiana referencyjnej temperatury wynikająca z początkowego float32 odpowiadała około 0,000031 limitu. Nie wyjaśnia ona obserwowanego FAIL.

## Pozostałe ograniczenia precyzji

Punktowe RHS w rzeczywistych stanach zapłonu nie przechodzą progu 0,001 dla wszystkich składników. Największe względne różnice dotyczą m.in. małego źródła netto NNH: około 39% przy 0,835 ms, dla wartości referencyjnej około 2,07×10⁻⁸ s⁻¹. Jest to inna kontrola niż odbiór temperatury i udziałów masowych. Nie wymazuje wcześniejszego PASS dwunastu ustalonych stanów, ale ogranicza zakres jego interpretacji.

W pełnym historycznym śledzeniu zaakceptowanych kroków pierwszy błąd punktowego źródła przekracza próg przy około **0,365 µs** (NNH). Jest to inne kryterium niż późniejsze przekroczenie błędu temperatury trajektorii.

Kontrola została następnie wykonana dla efektywnego RHS nowego wariantu, łącznie z korektą low. Końcowa próba zatrzymała się przy około **19,43 µs** i potwierdziła wynik **0,002037 przy progu 0,001** dla NNH: błąd bezwzględny około 2,04×10⁻¹¹ s⁻¹ przy źródle referencyjnym około 2,88×10⁻¹⁰ s⁻¹. Kontrola nie wykorzystuje różnic skończonych. Została dodana do kampanii i zatrzymuje ją jako FAIL przed skalowaniem. Nie ustalono jeszcze oddzielnie udziału zaokrąglenia współczynników, funkcji transcendentalnych i odejmowania szybkości reakcji odwracalnych.

Różnice Jacobianu w tych stanach są silnie zależne od kroku różnic skończonych. Ich status diagnostyczny pozostaje **INCOMPLETE**; sam duży wskaźnik FD nie dowodzi błędu analitycznego AD. Nie rozluźniono progu w celu uzyskania PASS.

## Implementacja i zakres poprawki

- Dodano jawny `localErrorTarget`, domyślnie 1. Eksperyment 1/64 zaostrza lokalny estymator i próg Newtona; bazowe współczynniki pozostają `rtol=1e-5`, `atol(Y)=1e-12`, `atol(T)=1e-3 K`. Wartości większe od 1 są odrzucane.
- `precision: 'compensated-state'` zachowuje części high/low podczas aktualizacji, pełnego kroku, półkroków, odrzucenia i checkpointowania. Nie renormalizuje składu w celu ukrycia utraty masy.
- Oddzielny kernel oblicza entalpię NASA7 w double-single, z częściami low współczynników wyznaczonymi przed utratą precyzji. Obejmuje również korektę wejściowej części low źródeł przez `J(high)·low`, przy świeżym Jacobianie każdego tłumionego stanu.
- To **nie jest pełna chemia double-single**: współczynniki reakcji, `exp`, `log`, gatunkowy Jacobian AD i LU pozostają float32. W kinetyce `vec2f` nadal oznacza wartość i pochodną; entalpia używa odrębnego `DoubleSingle`.
- Dla poprawki maksymalna paczka ma 31 dispatchy z inspekcją. `profile.gpuMs.enthalpy` obejmuje NASA7 i korektę wejściowej części low. Oczekiwania `mapAsync` nie sumuje się z czasem GPU.
- Checkpoint ma schemat 4 i integrator `gri30-gpu-state-machine-7`. Zawiera obie części zaakceptowanego stanu, dolną część entalpii docelowej, politykę błędu i historię. Niezgodna wersja, precyzja lub polityka nie są automatycznie konwertowane. Dawne wyniki pozostają danymi historycznymi.

Samo zaostrzenie estymatora w float32 dało FAIL bilansu pierwiastków już przy 20,39 µs (3,46×10⁻⁵, limit 10⁻⁵). Kompensacja bez odpowiedniego zaostrzenia Newtona dała następnie FAIL rodników. Związanie progu Newtona z budżetem estymatora usunęło te wczesne regresje w testach; kolejne warianty pozostają eksperymentami, a nie automatycznie promowanym solverem.

## Odtworzenie i dane

Pełne lokalne dane: `artifacts/gpu-v14/forensics-baseline/`. Śledzenie jest dzielone na fragmenty z sumami kontrolnymi; manifest nie skleja ich w pojedynczy wielusetmegabajtowy ciąg JSON. Pierwsza próba agregacji przekroczyła limit Node; zachowane fragmenty przeanalizowano ponownie bez powtarzania GPU.

```powershell
npm run chemistry:forensics -- --output artifacts/gpu-v14/forensics-new
npm run chemistry:forensics -- --output artifacts/gpu-v14/forensics-new --analyze-only
npm run chemistry:forensics -- --output artifacts/gpu-v14/forensics-new --replay-schedule --refinement 8
npm run chemistry:forensics -- --output artifacts/gpu-v14/forensics-new --pointwise-only

npm run chemistry:campaign -- --output artifacts/gpu-v14/repair-new --precision compensated-state --error-target 0.015625 --stop-time 0.0012
```

`--stop-time` zatrzymuje diagnostykę po zakończeniu ograniczonego odcinka; nie skraca wymaganego horyzontu 0,5 s. Pominięcie tej opcji przy zgodnym wznowieniu kontynuuje pełny przypadek. Samo przejście badanego okna nie uprawnia do PASS.

Wszystkie próby używają istniejącego `artifacts/gpu-v14/chemistry-budget.json`, bez odnowienia limitu 8 h. CPU float64 i Cantera są wyłącznie niezależnymi narzędziami kontroli; nie dostarczają zaakceptowanych stanów symulacji GPU. Palnik, pełne skalowanie i promocja optymalizacji wymagają pełnej bramki.

Czasy eksperymentów diagnostycznych nie stanowią kontrolowanego benchmarku przyspieszenia nowych wariantów. Odbiór wydajności i ponowne używanie Jacobianu odłożono do uzyskania zgodności numerycznej. Historyczne FAIL zachowano; częściowe, poprawne odcinki nowych wariantów nie zastępują pełnych horyzontów.

Maszynowy raport z osobnymi statusami diagnozy, historycznego odbioru i kolejnych wariantów: [chemistry-forensics-1.4.json](chemistry-forensics-1.4.json).

Wynik końcowy: **FAIL źródeł kinetycznych; pełne reaktory i wszystkie skale INCOMPLETE**. Około **51 min z 8 h** istniejącego budżetu zostało wykorzystane łącznie z wcześniejszymi próbami i analizą. Kampania została zatrzymana przez potwierdzoną niezgodność, bez wyczerpywania limitu.

Regresje: kompilacja PASS, backend 173 PASS (dwa moduły Cantery pominięte w środowisku FDS), osobne środowisko Cantery 12 PASS, magazyn/budżet Node 5 PASS, GPU/UI 38 PASS, przeglądarka/FDS 8 PASS. Testy infrastruktury i krótkiej poprawki nie stanowią PASS pełnej chemii.

Odtworzenie końcowego FAIL bez GPU: zapisz `repairs[-1].sourceInspectionRaw` z danych JSON jako bajty UTF-8 do pliku i uruchom `scripts/chemistry_effective_source.py input.json output.json` w środowisku Cantery. SHA256 tych bajtów odpowiada `repairs[-1].effectiveSource.inputSha256`. `repairs[i].reproduction` można niezależnie przekazać do `scripts/validate_gpu_chemistry.py`; opisuje odbiór zapisanej trajektorii, a nie osobny odbiór źródeł.
