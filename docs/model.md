# Model fizyczny IGNIS

IGNIS jest lokalnym demonstratorem edukacyjnym. Jego silnik to oryginalny NIST Fire Dynamics Simulator 6.11.1, a nie animacja udająca obliczenia CFD. Nie jest jednak zwalidowanym narzędziem do projektowania, przewidywania zagrożeń lub pomiarów rzeczywistego płomienia.

## Rozdział danych i obrazu

FDS oblicza przepływ o małych liczbach Macha, wymianę ciepła, promieniowanie oraz transport składników i spalanie w ramach swoich modeli. IGNIS zapisuje siedem objętościowych pól `CELL_CENTERED`: temperaturę [°C], HRRPUV [kW/m³], gęstość sadzy [kg/m³], udział objętościowy tlenu [mol/mol] i trzy składowe prędkości [m/s]. Od receptury 1.0.2 jawnie ustawiamy `DT_SL3D=0.1`, czyli 10 klatek pól na sekundę. Szeregi czasowe są zapisywane co 0,1 s. Dokładne czasy zapisów są odczytywane z wyników, a nie wyliczane z numeru klatki. Ostatni zapis może mieć krótszy odstęp. Starsze przebiegi kontrolne 1.0.0/1.0.1 zachowują sześć zapisów objętościowych: domyślny odstęp FDS to `T_END/5`, niezależny od `DT_SLCF` dla przekrojów 2D.

`fdsreader` odczytuje pliki `.sf` i ich współrzędne. Konwerter zachowuje float32 i zapisuje każdą klatkę w kolejności z, y, x, kanał (x zmienia się najszybciej). Sonda wybiera najbliższy środek komórki na płaszczyźnie przekroju. Współrzędna z FDS jest pionem sceny. Dane nie są wygładzane przed pomiarem. Wartości w obiektach stałych nie mają interpretacji jako temperatura gazu.

Renderer wykorzystuje interpolację tekstury 3D wyłącznie do obrazu. Integruje emisję i absorpcję wzdłuż promienia. Pomarańczowa emisja opiera się na temperaturze i sadzy, a niebieska jest ilustracją świecenia strefy reakcji. Nie obliczamy widma, chemiluminescencji CH*/C2* ani dokładnych kolorów aparatu fotograficznego. Bloom, światło podstawy i ekspozycja należą do prezentacji.

Maksymalna temperatura i prędkość to maksima w danej klatce pól. Moc pochodzi bezpośrednio z `ignis_hrr.csv`, z najbliższego czasu do wyświetlanej klatki; kW są przeliczane na W. Wykres pokazuje ten sam szereg, nie funkcję dobraną do wyglądu płomienia. Przewijanie nie uruchamia solvera.

## Palnik

Paliwem jest metan. Strumień wejściowy [mg/s] jest przeliczany na kg/(m²·s) z rzeczywistej powierzchni prostokątnego źródła wyrównanego do siatki. Domieszka powietrza pierwotnego jest zadawana jako ułamek stechiometrycznej ilości powietrza (przybliżenie 4 kg O2/kg CH4). Parametr λ=0 oznacza źródło samego paliwa. Azot stanowi pozostałą część dopływającego powietrza.

Uproszczona reakcja metanu i model wygaszania FDS nie zastępują szczegółowej kinetyki cienkiego płomienia wstępnie zmieszanego. Współczynniki SOOT_YIELD=0,008 i CO_YIELD=0,005 są założeniami demonstracyjnymi, nie prognozą tworzenia sadzy i CO przy dowolnym λ.

## Świeca

Źródło jest idealizowanym wlotem par o przekroju 10 × 10 mm. Paliwem zastępczym jest n-heptan, dostępny w bazie FDS. Nie jest to szczegółowy model chemiczny parafiny. Nie są rozwiązywane topienie wosku, transport kapilarny w knocie, geometria włókien ani sprzężenie parowania z płomieniem. Suwak bezpośrednio zadaje dopływ par. SOOT_YIELD=0,04 i CO_YIELD=0,005 są zadane.

W wersji receptury 1.0.1 źródło wyrównano do obu siatek, aby różnica geometrii nie zakłócała porównania rozdzielczości. Starsze wyniki zachowują swój oryginalny plik wejściowy i wersję receptury.

## Drewno

Próbka to prostopadłościan z aktywną górną powierzchnią. Reakcja gazowa paliwa zastępczego: C3.4 H6.2 O2.5, ciepło spalania 12 MJ/kg. Właściwości suchego materiału i kinetyka są przepisane z przypadku **weryfikacyjnego**, nie walidacyjnego, FDS `surf_mass_part_char_cart_fuel.fds`:

| Parametr | Materiał PINE | Pozostałość CHAR |
|---|---:|---:|
| Gęstość kg/m³ | 360 | 180 |
| Przewodność W/(m K) | 0,05 | 1,0 |
| Ciepło właściwe kJ/(kg K) | 1,0 | 1,6 |
| Emisyjność | 1,0 | 1,0 |

Rozkład PINE: A=1e20 1/s, E=160000 kJ/kmol, uzysk masowy 0,5 paliwa gazowego i 0,5 CHAR, ciepło reakcji 1000 kJ/kg. CHAR jest obojętny — utlenianie żaru nie jest liczone ani dodawane jako dekoracyjny efekt.

Dodany demonstracyjny składnik wilgoci ma gęstość 1000 kg/m³, przewodność 0,6 W/(m K), ciepło właściwe 4,18 kJ/(kg K), A=1e10 1/s, E=80000 kJ/kmol oraz ciepło reakcji 2257 kJ/kg. To uproszczenie Arrheniusa, nie pełny model ruchu wilgoci i wrzenia. Wilgotność jest udziałem wody w mokrej masie. Należy porównywać wynik dla całego przebiegu; nie zakładać monotoniczności każdej chwilowej wartości temperatury.

Źródło zapłonu jest zewnętrznym strumieniem ciepła [kW/m²], a nie arbitralnie dodaną mocą płomienia. Ogrzewanie działa do `min(10 s, 0,65 czasu doświadczenia)`, po czym spada do zera w ciągu 0,1 s. Moc HRR nie zawiera tego zadanego ogrzewania jako spalania paliwa.

## Domena i rozdzielczość

| Scena | Domena m | Podgląd | Dokładniejsza |
|---|---|---|---|
| Palnik | 0,16 × 0,16 × 0,32 | 32 × 32 × 64 | 48 × 48 × 96 |
| Świeca | 0,08 × 0,08 × 0,16 | 32 × 32 × 64 | 48 × 48 × 96 |
| Drewno | 0,24 × 0,24 × 0,40 | 32 × 32 × 56 | 48 × 48 × 84 |

Pięć ścian domeny jest otwartych. Podłoże jest stałe. Boczny przepływ zastępuje otwartą ścianę XMIN zadanym napływem. Obliczenia są przy ciśnieniu otoczenia. Zawartość tlenu podawana objętościowo jest przeliczana na udział masowy dla mieszaniny O2/N2.

Mała domena może obcinać pióropusz; prosta siatka i uproszczona chemia mogą nie rozdzielać grubości płomienia, jego odrywania ani wygaszania. Wyczerpanie tlenu i zachowanie przy zubożeniu są wynikami modelu FDS, nie empirycznymi granicami palności. Nie obsługujemy detonacji, wybuchów ani spalania naddźwiękowego. Dwa poziomy siatki służą badaniu wrażliwości; ich porównanie samo w sobie nie dowodzi zbieżności.

## Źródła

- [Dokumentacja i podręczniki FDS 6.11.1](https://pages.nist.gov/fds/manuals.html)
- [Oryginalne wydanie FDS](https://github.com/firemodels/fds/releases/tag/FDS-6.11.1)
- [Przypadek weryfikacyjny materiału i pirolizy](https://github.com/firemodels/fds/blob/FDS-6.11.1/Verification/Pyrolysis/surf_mass_part_char_cart_fuel.fds)
- [Opis modeli spalania FDS](https://github.com/firemodels/fds/blob/FDS-6.11.1/Manuals/FDS_Technical_Reference_Guide/Combustion_Chapter.tex)
- [fdsreader](https://github.com/FireDynamics/fdsreader)
