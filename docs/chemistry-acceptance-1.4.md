# IGNIS 1.4 — odbiór chemii GPU, 17 października 2026

**Bramka pełnej chemii nie została zaliczona. Palnik 3D pozostaje zablokowany.**

Wdrożono indywidualne automaty reaktorów, równoległe redukcje, transakcyjne checkpointy, harmonogram do 65 536 reaktorów i kampanię z trwałym limitem 8 h. To infrastruktura do odbioru, a nie deklaracja poprawności pełnych reaktorów. Mechanizm nadal obejmuje 53 składniki i 325 reakcji. Nie zmieniono tolerancji i nie zastosowano chemii na CPU w ścieżce symulacji.

## Weryfikacja implementacji

| Kontrola | Wynik |
|---|---|
| Kompilacja TypeScript i Vite | PASS |
| Pełny zestaw GPU/UI | 33 PASS przed końcowym rozszerzeniem testów chemii |
| Końcowe testy chemii GPU | 5 PASS: niezależność reaktorów, RETRY, wznowienie, utrata urządzenia, LU/double-single i 513 reaktorów |
| Walidator Cantery w osobnym środowisku | 4 PASS |
| Trwały magazyn, budżet i eksport historii, Node | 4 PASS |
| Python/backend | 172 PASS; jeden timeout profilu FDS `openmp-pcores`, następnie PASS w osobnym uruchomieniu (18,45 s) |
| Przeglądarka/FDS | 7 PASS; jeden timeout testu prezentacji, następnie PASS osobno (34,6 s) |

Pełny zestaw Python dodatkowo pominął moduł testów wymagający Cantery, której nie instalujemy w środowisku FDS. Wszystkie cztery testy tego modułu wykonano w `tools/chemistry-venv`. Zestawy GPU/UI i końcowej chemii częściowo się pokrywają — nie należy sumować ich liczników. Test 513 reaktorów trwa 10⁻⁸ s fizycznego czasu i sprawdza trzy kafle 256/256/1; nie zastępuje skalowania pełnych horyzontów.

## Natywna kampania RTX 4050

Końcowe pomiary uruchomiono kolejno, bez równoległych testów. Adapter WebGPU `nvidia / lovelace / 0x28a1` odpowiada urządzeniu DXGI NVIDIA RTX 4050 Laptop GPU. Każdy wariant rozpoczął od niezależnego porównania RHS/Jacobianu w 12 stanach, następnie od rzeczywistego reaktora CH₄/powietrze, 1500 K, φ=1, stałe ciśnienie, wymagany horyzont 0,5 s, bez początkowych rodników.

Wyniki maszynowe, odciski źródeł, budżet, próbki trajektorii i ostatnie układy Newtona znajdują się w [danych odbioru](chemistry-acceptance-1.4.json). Zawierają dane pozwalające ponownie wykonać niezależną walidację, a nie tylko etykietę PASS/FAIL. Zapisane checkpointy obejmują również niedokończone przebiegi. Potwierdzona niezgodność zatrzymuje kampanię przed kosztownym skalowaniem.

| Wariant | Osiągnięty czas fizyczny | Czas wywołań integratora | Temperatura / limit | Rodniki / limit | Wynik |
|---|---:|---:|---:|---:|---|
| LU | 0.001168429 s z 0,5 s | 87.055 s | 10.21 | 4.32 | **FAIL** |
| LU + 2 poprawienia | 0.001168081 s z 0,5 s | 87.049 s | 9.68 | 3.96 | **FAIL** |

Wartość powyżej 1 w kolumnach błędów oznacza przekroczenie kryterium. Każdy wariant wykonał trzy odcinki po około 29 s; czas tabeli obejmuje wywołania integratora, a nie cały rozruch i walidację. Jacobian stanowił 94.3% czasu zmierzonych kerneli podstawowego LU oraz 90.9% wariantu poprawianego. Najważniejszymi powodami odrzuceń były Newton i tłumienie.

Uwarunkowanie pobranych układów: 5.96–1134.92; maksymalny niezależny błąd wsteczny LU: 1.41e-06, przy limicie 1e-5. Sonda double-single uzyskała na tych macierzach maksymalny błąd wsteczny 5.78e-15. To wynik sondy liniowej, nie pełnego reaktora.

Zadeklarowane bufory jednego reaktora z mechanizmem i historią 165 próbek: 213 212 B. Pamięć workgroup LU: 12 780 B, wariant poprawiany: 13 212 B. Licznik kampanii zakończył serię przy około 20.9 min aktywnego czasu, łącznie z wcześniejszymi próbami diagnostycznymi. Limit 8 h nie został odnawiany; potwierdzony FAIL zakończył badanie wcześniej.

| Kryterium | Status |
|---|---|
| Punktowe RHS/Jacobian, 12 stanów | PASS |
| Pełne reaktory 0D | FAIL — niezgodność już w częściowym przebiegu |
| Pełna skala 1 reaktora | INCOMPLETE |
| Pełne skale 512 / 4096 / 65 536 | INCOMPLETE — zablokowane bramką 0D |
| Cała bramka | **FAIL** |


## Co ustalono, a co pozostaje otwarte

Punktowe RHS/Jacobian przechodzą dotychczasowe progi. Pełna trajektoria reaktora przekracza progi porównania z Canterą w pobliżu zapłonu. Poprawne bilanse i poprawna reszta LU nie wystarczają do odbioru temperatury, rodników i pozostałych składników.

W próbkach rzeczywistych układów Newtona niezależne reszty liniowe mieszczą się w limicie. Ich uwarunkowanie nie jest równe najgorszemu 4,4×10¹³ z wcześniejszego, syntetycznego badania. Próby double-single dotyczą rozwiązania tych samych macierzy na GPU. Nie dowodzą poprawności zwiększonej precyzji całej kinetyki, termodynamiki ani akumulacji stanu.

Nie ustalono jeszcze jednoznacznej przyczyny błędu całej integracji. Pozostają do rozdzielenia błąd czasowy niejawnego Eulera, dokładność RHS/Jacobianu w rzeczywistych stanach i zaokrąglenia aktualizacji float32. Stanowe porównania Jacobianu metodą różnic skończonych są diagnostyką; wymagają analizy wrażliwości na krok FD, zwłaszcza dla śladowych składników. Nie zmieniamy na tej podstawie tolerancji.

Błąd czasu zapłonu z częściowego przebiegu nie zastępuje odbioru pełnego horyzontu. Maksimum OH również nie jest odebrane, dopóki przebieg i zagęszczanie próbek nie zostaną ukończone. Nie można ekstrapolować kosztu pojedynczego reaktora na 65 536 komórek: wykorzystanie GPU zmienia się z wielkością paczki.

Pełna chemia w zwiększonej precyzji nie została zaimplementowana. Dostępny jest wariant float32 z poprawianiem LU oraz osobna sonda double-single; żaden z nich nie jest ukrytym zamiennikiem pełnego mechanizmu. Wszystkie pełne horyzonty i skale 1/512/4096/65 536 pozostają nieodebrane. Nie uruchamiano ich po negatywnym odbiorze 0D.

## Odtworzenie

Obiekt `measurements[i].reproduction` z danych JSON można zapisać do osobnego pliku i przekazać bezpośrednio do `scripts/validate_gpu_chemistry.py`; obie zapisane reprodukcje sprawdzono ponownie z Canterą i otrzymano ten sam FAIL.

Instrukcja, kontrakt checkpointów i polecenia są w [gri30-campaign.md](gri30-campaign.md). `npm run test:gpu:chemistry` wymaga nowej pełnej kampanii; historyczna próba referencyjna ma osobną komendę. PASS całości wymaga wszystkich kryteriów, w tym niezależnego potwierdzenia LU. Brak diagnostyki blokuje promocję.

Profile czasu GPU pochodzą z timestamp queries. Oczekiwanie `mapAsync` obejmuje wykonanie GPU, więc nie sumujemy go z czasem kerneli i nie przedstawiamy jako samego transferu. Podane zasoby to rozmiary zadeklarowanych buforów i pamięci workgroup. Nie zmierzono szczytowego RAM całej przeglądarki ani prywatnych alokacji sterownika. Nie ogłaszamy przyspieszenia produkcyjnego na podstawie przebiegu, który nie przeszedł bramki.
