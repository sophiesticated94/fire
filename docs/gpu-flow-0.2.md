# Gorące powietrze GPU — gpu-flow-0.2

Ten model zachowuje fizykę `gpu-flow-0.1`: otwarta domena 0,16 × 0,16 × 0,32 m, siatka MAC, transport masy i pędu, przewodzenie, wypór i projekcja zmiennej gęstości. Nie zawiera spalania. FDS pozostaje osobnym silnikiem.

## Parametry podczas obliczeń

| Parametr | Zakres | Jednostka |
|---|---:|---|
| Moc grzałki | 0–2 | W |
| Wiatr w kierunku +X | 0–0,6 | m/s |
| Docelowa temperatura otoczenia | 0–50 | °C |
| Grawitacja | 0–20 | m/s² |
| Lepkość dynamiczna | 0–50 | µPa·s |
| Przewodność cieplna | 0–0,1 | W/(m·K) |

Właściwości materiałowe są niezależnymi, stałymi współczynnikami tego eksperymentalnego modelu powietrza. Zaawansowane ustawienia nie udają zależności transportowych rzeczywistej mieszaniny reagującej. Wszystkie zmiany obowiązują od następnego kroku. Krok korzysta z jednej kopii konfiguracji; zmiana dokonana podczas oczekiwania na GPU pozostaje do kolejnego kroku.

Zmiana temperatury to **zewnętrzne, objętościowe ogrzewanie lub chłodzenie całej domeny**, z ograniczeniem 10 K/s czasu fizycznego. Źródło wynosi `rho cp dTamb/dt`. Zmieniają się również temperatura napływu, gęstość otoczenia i odniesienie wyporu. Pola nie są resetowane ani przesuwane w celu sztucznego zachowania nadwyżki temperatury. Przycisk „Od początku” tworzy stan początkowy przy aktualnej temperaturze docelowej.

Bilans entalpii używa niezmiennej temperatury odniesienia z początku eksperymentu. HUD osobno podaje moc i całkę objętościowego wymuszenia; wykres i legenda uwzględniają aktualne otoczenie. Krok jest ograniczany przez adwekcję CFL, źródła i dyfuzję, także przy zerowej lepkości lub przewodności.

Redukcje statystyk korzystają z sumowania kompensowanego float32. Przy ogrzewaniu całej domeny zwykła suma 1024 wartości częściowych potrafiła zgłosić fałszywe przekroczenie bilansu: niezależny odczyt float64 wykazał względny błąd transportu 1,94×10⁻⁹. Poprawka dotyczy dokładności diagnostyki; nie rozluźnia limitów i nie zmienia redukcji używanej przez projekcję ciśnienia. Test maksymalnego wiatru obejmuje przejście gazu przez całą szerokość domeny na pełnej siatce.

## Projekcja i cofanie kroku

`GridOptions.pressureMode` przyjmuje `reference` lub `batched`. Referencja sprawdza resztę po 16 iteracjach SOR. Wariant zbiorczy nadal sprawdza ten sam warunek co 16 iteracji na GPU, zatrzymuje aktualizowanie rozwiązania po zbieżności i odczytuje status po maksymalnie 64 iteracjach. Kontrola CPU zachowuje dotychczasowe tolerancje. Pole `iterations` oznacza wykonane iteracje, nie rozmiar paczki. Diagnostyka obejmuje liczbę odczytów projekcji i jej czas ścienny.

Domyślny wybór stosuje `batched` dla rozpoznanego `nvidia / 0x28a1` (RTX 4050 Laptop) na siatce 32×32×64. Zysk z renderowaniem wyniósł 7,7% w pierwszej serii i 6,2% w potwierdzeniu końcowego kodu. Pozostałe urządzenia i siatki używają referencji. Iris Xe nie uzyskał dostatecznie jednoznacznego zysku w obu trybach. Jawny `pressureMode` pozwala odtworzyć każdy wariant niezależnie od wyboru domyślnego. Jest to kwalifikacja zmierzonego urządzenia i zadania, nie gwarancja wydajności po zmianie sterownika lub warunków eksperymentu.

Przed krokiem powstaje kopia **wszystkich** buforów GPU: obu stanów gęstości, trzech prędkości, ciśnienia, źródeł, prawej strony, redukcji i flag zbieżności. Błąd przywraca również indeksy, całki bilansów, temperaturę otoczenia i uniformy. Ponowienie CFL rozpoczyna się od tego samego zaakceptowanego stanu. Koszt to dodatkowa pamięć i kopie GPU; nie ma odczytu objętości do CPU. Pełny odczyt jest dostępny wyłącznie po jawnym `testReadback`.

## Testy i pomiary

```powershell
npm run build
$env:IGNIS_GPU_ADAPTER='rtx'
npm run test:gpu
npm run test:gpu:sor
```

Wybór `high-performance` w WebGPU jest wskazówką. Test RTX uruchamia osobny Edge z flagami preferencji, a następnie wymaga zgodności identyfikatora WebGPU, inwentarza DXGI oraz dodatniego wykorzystania silnika GPU procesu przeglądarki na tym samym LUID. Nie zmienia globalnych ustawień Windows. Brak dowodów kończy pomiar błędem, zamiast podpisywać Iris Xe jako RTX.

Testy obejmują referencję CPU float64, warunki brzegowe, projekcję, kontrolowane błędy, cofanie całego stanu, zmianę parametrów podczas kroku, ogrzewanie i chłodzenie oraz zachowanie UI podczas przełączania FDS/GPU. Długi benchmark stabilności i porównania wydajności są oddzielone od zwykłej regresji.

Pełna chemia pozostaje za [bramką GRI30](gri30-status.md). Ten widok nie przedstawia płomienia ani HRR obliczanego przez GPU.
