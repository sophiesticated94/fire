# IGNIS 1.3 — GPU Interactive

Pierwszy etap GPU jest oddzielnym, badawczym solverem gorącego powietrza. FDS Scientific zachowuje swój model, dane, cache, profile i backend. GPU nie oblicza jeszcze spalania metanu/świecy, tlenu, sadzy, promieniowania ani pirolizy drewna. Te procesy i porównanie dwóch silników należą do następnego etapu, po ocenie obecnych pomiarów. Naprawa screeningu i przegląd progów FDS pozostają osobnym pakietem.

## Uruchomienie i obsługa

Po zwykłym `start.ps1` wybierz **GPU Interactive 1.3**. Moduł ładuje się dopiero przy pierwszym wybraniu. Potrzebny jest dostępny adapter WebGPU (Chrome/Edge z akceleracją sprzętową). Brak WebGPU, błąd inicjalizacji lub utrata urządzenia daje komunikat, a przycisk FDS pozostaje dostępny. Po utracie urządzenia odśwież stronę. Nie ma cichego przełączenia obliczeń GPU na WebGL.

Symulacja startuje w pauzie. **Uruchom przepływ**, **Wstrzymaj**, **Jeden krok** i **Od początku** dotyczą obliczeń na żywo. Suwaki zmieniają moc grzałki 0–2 W i tło przepływu +X 0–0,1 m/s. Zmiana wiatru dodaje zmianę prędkości tła do pola X i ponownie wykonuje projekcję; nie jest modelem czasowego narastania wentylatora. Wyłączenie grzałki usuwa źródło ciepła, zachowując już ogrzany gaz. To odrębna kontrola od prezentacyjnego przycisku zapłonu w FDS.

Temperatura, prędkość i gęstość pochodzą z obliczonych pól. Strzałki pokazują kierunek prędkości, kolor objętościowy jej moduł. Przekrój usuwa połowę objętości. Kliknięcie wybiera środek komórki na środkowym pionowym przekroju (y = 8,25 cm). Sonda zwraca temperaturę, gęstość i składowe prędkości; jest próbkowaniem siatki. Przełączanie silników zachowuje ich kamery i czas. Niewidoczny silnik nie renderuje ani nie rozpoczyna kolejnych kroków; rozpoczęty krok może się zakończyć. Ukryta karta nie nadrabia czasu.

## Równania i dyskretyzacja

Model `gpu-flow-0.1`: domena 0,16 × 0,16 × 0,32 m, 32 × 32 × 64 komórek, oś Z w górę. Pola komórkowe: gęstość, temperatura wynikająca z równania stanu, impuls ciśnienia i źródło rozszerzalności. Prędkości są na ścianach siatki MAC. Dane GPU są float32. W Three.js współrzędna pionowa jest mapowana na Y.

Przyjęto powietrze idealne przy stałym ciśnieniu termodynamicznym p₀ = 101325 Pa, R = 287,05 J/(kg K), cp = 1005 J/(kg K), T₀ = 293,15 K, μ = 1,81·10⁻⁵ Pa s, k = 0,0257 W/(m K), g = 9,81 m/s². To stałe założenia modelu demonstracyjnego. Gęstość nie jest przybliżana modelem Boussinesqa:

```
ρ = p₀ / (RT)
∂ρ/∂t + ∇·(ρu) = 0
∇·u = S = [∇·(k∇T) + q] / (ρ cp T)
```

Źródło Gaussa jest centrowane w (8, 8, 1,5) cm, σx = σy = 1 cm, σz = 0,5 cm. Normalizacja dyskretna daje zadaną całkowitą moc; źródło nie dodaje masy. Nawet bez grawitacji ogrzewanie powoduje rozszerzanie gazu.

Masa jest transportowana metodą objętości skończonych z upwindem pierwszego rzędu. Pęd na podwójnych objętościach MAC korzysta ze średnich tych samych strumieni masy i z nowej gęstości na ścianach, co zachowuje stałą prędkość przy transporcie zmiennej gęstości. Jawna dyfuzja pędu zawiera μ(Δu + ∇div(u)/3); wypór jest liczony względem hydrostatycznego otoczenia. Temperatura wynika z przetransportowanej gęstości. Przed pierwszym transportem i po zmianie źródła wykonywana jest projekcja rozszerzalności. Po transporcie nowy stan dostarcza nowego S i następuje kolejna projekcja.

Boki i góra: zerowy impuls ciśnienia perturbacyjnego na ścianie, z połówkową odległością w operatorze projekcji. Napływowa masa i entalpia korzystają ze stanu otoczenia; wypływ ma zerowy gradient temperatury. Przewodzenie korzysta z temperatury otoczenia w zewnętrznej komórce napływowej, bez gradientu przy wypływie. Dno: zerowa prędkość normalna, swobodny poślizg i izolacja. Nie jest to model naczynia ze ścianami bez poślizgu.

Projekcja rozwiązuje `div((1/ρ) grad ψ) = div(u*) − S`, a następnie `u = u* − (1/ρ)grad ψ`. **ψ ma jednostkę Pa·s**, nie jest samą wartością ciśnienia w Pa. Operator używa zmiennego współczynnika 2/(ρL+ρR). Solver: red-black SOR, ω = 1,8, kontrola co 16 iteracji, limit 1024. Nie ma wielosiatkowości ani sztucznego zerowania dywergencji źródła ciepła.

## Stabilność i budżety

Krok jest ograniczony do 1/120 s, CFL ≤ 0,5, jawnego warunku dyfuzji i `dt·max|S| ≤ 0,05`. Interfejs wykonuje do ośmiu podkroków w jednym zleceniu. Czas fizyczny rośnie wyłącznie o zakończone kroki; przy wolnym urządzeniu symulacja zwalnia względem zegara. Przekroczenie CFL powtarza krok maksymalnie cztery razy z mniejszym dt. Nieudany krok nie publikuje nowej pary pól i zatrzymuje obliczenia.

Kontrole obejmują wartości skończone, dodatnią gęstość, 200–1000 K, Mach < 0,1 i względną zgodność równania stanu ≤ 10⁻⁵. Dla E = div(u) − S:

* hmin·RMS(E)/max(Urms, 0,01 m/s) ≤ 10⁻³;
* analogiczny błąd maksymalny ≤ 10⁻²;
* względny błąd całkowitego strumienia rozszerzalności ≤ 1%, z podłogą 10⁻⁸ m³/s;
* względny bilans masy ≤ 10⁻⁵ na krok i ≤ 10⁻⁴ od początku.

Bilans masy zawiera rzeczywiste upwindowe strumienie przez otwarte ściany. Bilans nadwyżki entalpii obejmuje źródło, przewodzenie i entalpię transportowaną przez granice. Test grzałki 1 W porównuje resztę po 5 s z 5% dostarczonej energii. Te kryteria są testami regresji modelu, nie walidacją inżynierską.

## Zasoby i diagnostyka

`GpuGrid` definiuje geometrię, `GpuFields` stały zestaw pól, `GpuEngine` kolejność kroków, `GpuDiagnostics` kontrakt metryk, `WebGpuFireScene` prezentację, `GpuLaboratory` panel i cykl życia. Adwekcja masy jest osobnym kernelem; transport pędu, dyfuzja i wypór są połączone w `momentum.wgsl`. Unika to dodatkowych zapisów całych objętości.

Solver i renderer WebGPU współdzielą **te same StorageBufferAttribute/GPUBuffer**. Renderer ma z góry utworzone warianty wiązań dla buforów ping-pong, bez tworzenia materiałów przy każdym kroku. Sześcian jest renderowany ray marchingiem 96 próbek, a strzałki odczytują prędkości w shaderze wierzchołków. W normalnej pracy do CPU trafia 24-elementowa redukcja diagnostyczna i opcjonalnie 8-elementowa sonda. Najwyżej jedno zlecenie kroków i jedna zastępowalna sonda mogą oczekiwać na zakończenie. Wykres przechowuje najwyżej 300 metryk. Pełny odczyt objętości jest zablokowany poza jawnie włączonym harnessiem testowym.

`allocatedBytes` oznacza rozmiar pól aplikacji, **nie całkowitą pamięć procesu, sterownika i renderera**. `readbackBytes` obejmuje odczyty pól diagnostycznych i oszacowane dane timestampów compute; nie jest pomiarem całego ruchu magistrali. GPU ms pochodzi wyłącznie z opcjonalnego `timestamp-query`, z sumy passów compute kroku, także gdy krok obejmuje wiele klatek renderowania. Czas ścienny kroku osobno obejmuje CPU, kolejkę, kompilację, synchronizację i odczyty. Nie wolno używać tych wielkości zamiennie.

## Odtwarzanie testów

```powershell
npm run build
npm run test:gpu
npm run test:gpu:benchmark
```

Testy GPU uruchamiają lokalnego Vite z wyłączonym HMR (zmiana plików nie przerywa długiego przebiegu), przez Edge na Windows z ANGLE D3D11. `GPU_TEST_PORT` może zmienić port testowy. Produkcja nie wymusza flag przeglądarki ani konkretnej karty. Testy celowo wymagają dostępnego WebGPU, zamiast pomijać obliczenia.

Referencja CPU używa float64 i niezależnego matrix-free conjugate gradient, a nie kopii red-black SOR. Na 8 × 8 × 16 po 10 krokach dopuszcza maksymalnie 0,01 K błędu temperatury, 10⁻⁴ względnego błędu gęstości i RMS prędkości ≤ max(0,001 m/s, 1% RMS referencji). Przypadki obejmują spoczynek, wiatr, smugę i ogrzewanie bez grawitacji. Dalsze testy obejmują transport stałej prędkości przy zmiennej gęstości, wyłączenie grzałki, wytworzony gradient ciśnienia, podłogę, rollback, utratę urządzenia i UI.

Benchmark natywny: 60 s czasu fizycznego na domyślnej siatce, bilans energii po 5 s, następnie 10 s rozgrzewki i trzy okna po 30 s zegara. Drugi benchmark mierzy współpracę renderera i obliczeń (800 × 600 pikseli CSS), również po rozgrzewce. Uruchamiaj je sekwencyjnie, bez innych testów graficznych. Surowe dane trafiają do ignorowanego `artifacts/gpu/`. 30 FPS jest celem pomiarowym; nie jest obietnicą czasu rzeczywistego ani warunkiem poluzowania tolerancji.

Ograniczenia: niska rozdzielczość, dyfuzja numeryczna upwindu, stałe właściwości, prosty solver ciśnienia i synchroniczne punkty odczytu diagnostyki. Zgodność z referencją tej dyskretyzacji nie dowodzi zgodności z FDS lub doświadczeniem. Dobór wielosiatkowości, większej siatki i dodatkowej fizyki wymaga wyników benchmarku.

Źródła implementacyjne: [notatki Roberta Bridsona o MAC i projekcji](https://www.cs.ubc.ca/~rbridson/fluidsimulation/fluids_notes.pdf), [Three.js Renderer](https://threejs.org/docs/pages/Renderer.html), [WebGPU — specyfikacja](https://www.w3.org/TR/webgpu/). Równania rozszerzalności powyżej wynikają z równania stanu, zachowania masy i izobarycznego bilansu entalpii; nie są deklaracją implementacji pełnego modelu FDS.
