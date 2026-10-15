# Porównanie dwóch siatek

To badanie wrażliwości początkowego przebiegu, nie dowód zbieżności ani walidacja eksperymentalna. Moc to średnia w drugiej połowie badanego okna. Temperatura sondy pochodzi z urządzenia FDS w tym samym fizycznym punkcie. Tmax jest interpolacją maksimów zapisanych klatek.

| Scena / czas | Siatka | Moc W | Sonda °C | Tmax °C | Czas obliczeń s |
|---|---|---:|---:|---:|---:|
| burner / 0.8 s | 32 × 32 × 64 | 552.89 | 1325.44 | 1518.24 | 90.9 |
| burner / 0.8 s | 48 × 48 × 96 | 553.94 | 1207.13 | 1614.82 | 1044.7 |
| Zmiana względem podglądu | | 0.2% | 8.9% | 6.4% | — |
| candle / 0.8 s | 32 × 32 × 64 | 51.26 | 511.83 | 1320.70 | 1102.2 |
| candle / 0.8 s | 48 × 48 × 96 | 51.16 | 542.89 | 1401.75 | 965.6 |
| Zmiana względem podglądu | | 0.2% | 6.1% | 6.1% | — |
| wood / 2 s | 32 × 32 × 56 | 108.42 | 60.84 | 115.05 | 124.1 |
| wood / 2 s | 48 × 48 × 84 | 221.53 | 130.31 | 147.53 | 591.8 |
| Zmiana względem podglądu | | 104.3% | 114.2% | 28.2% | — |

Duże różnice temperatur lub mocy oznaczają, że ta rozdzielczość nie uzasadnia ilościowych przewidywań dla rzeczywistego płomienia. Nawet mała różnica na dwóch siatkach nie zastępuje testu trzeciej siatki, wielkości domeny, bilansów i porównania z pomiarami. Badanie drewna jest krótkim przebiegiem nagrzewania/zapłonu; nie ocenia pełnego wypalenia ani utleniania żaru. Czasy pracy zawierają wpływ równoległych prac na komputerze i nie są benchmarkiem wyłącznego dostępu do CPU.

Identyfikatory danych: 9106076d541a5df2c8c8, 967a98c6a42853a6a838, 159b5e1a1a90477d1399, 6c973fdacb9c8e2c9bcf, 0258078bdc3a86827874, 523304c5607523954462
