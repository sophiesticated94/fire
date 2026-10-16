# Zgodność numeryczna bieżącej kampanii

Polityka: `pending-review`. Raport odczytuje wyłącznie istniejące porównania dla aktualnego kodu i polityki; brak obliczenia jest jawny. Nie zatwierdza profili.

RMS czasowo-przestrzenny zachowuje różnice chwilowe. Wszystkie błędy pól są znormalizowane zgodnie z raportem walidacji; tlen jest bezwzględnym RMS w mol/mol. Zmienność trajektorii OpenMP jest referencją interpretacyjną, nie automatycznym usprawiedliwieniem odchyleń MPI.

## burner — 6 s

| Kandydat | Referencja | Stare bramki | Energia, błąd wzgl. | Zapłon, różnica s |
|---|---:|---|---:|---:|
| OpenMP / OpenMP | 1 | PASS | 2.01968e-05 | 0.0 |
| OpenMP / OpenMP | 1 | PASS | 6.38736e-07 | 0.0 |
| OpenMP / OpenMP | 2 | PASS | 2.0836e-05 | 0.0 |
| mpi2-x2 / screen -1 | 1 | FAIL | 3.35548e-05 | 6.871999999999434e-05 |
| mpi2-x2 / screen -1 | 2 | FAIL | 1.33583e-05 | 6.871999999999434e-05 |
| mpi2-x2 / screen -1 | 3 | FAIL | 3.41935e-05 | 6.871999999999434e-05 |
| mpi2-y2 / screen -1 | 1 | FAIL | 0.000119185 | 0.0030282499999999962 |
| mpi2-y2 / screen -1 | 2 | FAIL | 0.000139385 | 0.0030282499999999962 |
| mpi2-y2 / screen -1 | 3 | FAIL | 0.000118546 | 0.0030282499999999962 |
| mpi4-xy22 / screen -1 | 1 | FAIL | 1.17473e-05 | 0.00020746000000000653 |
| mpi4-xy22 / screen -1 | 2 | FAIL | 3.19448e-05 | 0.00020746000000000653 |
| mpi4-xy22 / screen -1 | 3 | FAIL | 1.11086e-05 | 0.00020746000000000653 |
| mpi2-x2 / finalist 1 | 1 | FAIL | 3.35548e-05 | 6.871999999999434e-05 |
| mpi2-x2 / finalist 1 | 2 | FAIL | 1.33583e-05 | 6.871999999999434e-05 |
| mpi2-x2 / finalist 1 | 3 | FAIL | 3.41935e-05 | 6.871999999999434e-05 |
| mpi2-x2 / finalist 2 | 1 | FAIL | 3.35548e-05 | 6.871999999999434e-05 |
| mpi2-x2 / finalist 2 | 2 | FAIL | 1.33583e-05 | 6.871999999999434e-05 |
| mpi2-x2 / finalist 2 | 3 | FAIL | 3.41935e-05 | 6.871999999999434e-05 |
| mpi2-x2 / finalist 3 | 1 | FAIL | 3.35548e-05 | 6.871999999999434e-05 |
| mpi2-x2 / finalist 3 | 2 | FAIL | 1.33583e-05 | 6.871999999999434e-05 |
| mpi2-x2 / finalist 3 | 3 | FAIL | 3.41935e-05 | 6.871999999999434e-05 |
| mpi4-x4 / screen -1 | 1 | FAIL | 0.00014622 | 0.004346470000000005 |
| mpi4-x4 / screen -1 | 2 | FAIL | 0.00016642 | 0.004346470000000005 |
| mpi4-x4 / screen -1 | 3 | FAIL | 0.000145581 | 0.004346470000000005 |

Maksimum błędu po dostępnych parach w danej grupie; wartości poszczególnych par pozostają w `comparisons/*.json`.

| Grupa | Okno | Kanał | Największy błąd |
|---|---|---|---:|
| OpenMP / OpenMP | full | HRRPUV | 0.0407856 |
| OpenMP / OpenMP | full | OXYGEN VOLUME FRACTION | 0.0010111 |
| OpenMP / OpenMP | full | SOOT DENSITY | 0.0932253 |
| OpenMP / OpenMP | full | TEMPERATURE | 0.0828388 |
| OpenMP / OpenMP | full | U-VELOCITY | 0.472084 |
| OpenMP / OpenMP | full | V-VELOCITY | 0.469897 |
| OpenMP / OpenMP | full | W-VELOCITY | 0.133205 |
| OpenMP / OpenMP | late | HRRPUV | 0.0569325 |
| OpenMP / OpenMP | late | OXYGEN VOLUME FRACTION | 0.00141832 |
| OpenMP / OpenMP | late | SOOT DENSITY | 0.128833 |
| OpenMP / OpenMP | late | TEMPERATURE | 0.113849 |
| OpenMP / OpenMP | late | U-VELOCITY | 0.662213 |
| OpenMP / OpenMP | late | V-VELOCITY | 0.659145 |
| OpenMP / OpenMP | late | W-VELOCITY | 0.180584 |
| OpenMP / OpenMP | variability | HRRPUV | 0.0990052 |
| OpenMP / OpenMP | variability | OXYGEN VOLUME FRACTION | 0.000232229 |
| OpenMP / OpenMP | variability | SOOT DENSITY | 0.131839 |
| OpenMP / OpenMP | variability | TEMPERATURE | 0.0430365 |
| OpenMP / OpenMP | variability | U-VELOCITY | 0.101791 |
| OpenMP / OpenMP | variability | V-VELOCITY | 0.10598 |
| OpenMP / OpenMP | variability | W-VELOCITY | 0.142438 |
| mpi2-x2 | full | HRRPUV | 0.127555 |
| mpi2-x2 | full | OXYGEN VOLUME FRACTION | 0.00271682 |
| mpi2-x2 | full | SOOT DENSITY | 0.234341 |
| mpi2-x2 | full | TEMPERATURE | 0.218471 |
| mpi2-x2 | full | U-VELOCITY | 1.01431 |
| mpi2-x2 | full | V-VELOCITY | 1.01783 |
| mpi2-x2 | full | W-VELOCITY | 0.30606 |
| mpi2-x2 | interfacesFull | HRRPUV | 0.15405 |
| mpi2-x2 | interfacesFull | OXYGEN VOLUME FRACTION | 0.0063447 |
| mpi2-x2 | interfacesFull | SOOT DENSITY | 0.163916 |
| mpi2-x2 | interfacesFull | TEMPERATURE | 0.174843 |
| mpi2-x2 | interfacesFull | U-VELOCITY | 1.43917 |
| mpi2-x2 | interfacesFull | V-VELOCITY | 1.23045 |
| mpi2-x2 | interfacesFull | W-VELOCITY | 0.223242 |
| mpi2-x2 | interfacesLate | HRRPUV | 0.179729 |
| mpi2-x2 | interfacesLate | OXYGEN VOLUME FRACTION | 0.00656624 |
| mpi2-x2 | interfacesLate | SOOT DENSITY | 0.164922 |
| mpi2-x2 | interfacesLate | TEMPERATURE | 0.174981 |
| mpi2-x2 | interfacesLate | U-VELOCITY | 1.36951 |
| mpi2-x2 | interfacesLate | V-VELOCITY | 1.28079 |
| mpi2-x2 | interfacesLate | W-VELOCITY | 0.21738 |
| mpi2-x2 | late | HRRPUV | 0.149322 |
| mpi2-x2 | late | OXYGEN VOLUME FRACTION | 0.00278472 |
| mpi2-x2 | late | SOOT DENSITY | 0.228519 |
| mpi2-x2 | late | TEMPERATURE | 0.218449 |
| mpi2-x2 | late | U-VELOCITY | 1.00198 |
| mpi2-x2 | late | V-VELOCITY | 1.01474 |
| mpi2-x2 | late | W-VELOCITY | 0.295257 |
| mpi2-x2 | variability | HRRPUV | 0.136467 |
| mpi2-x2 | variability | OXYGEN VOLUME FRACTION | 0.000386706 |
| mpi2-x2 | variability | SOOT DENSITY | 0.213386 |
| mpi2-x2 | variability | TEMPERATURE | 0.0712132 |
| mpi2-x2 | variability | U-VELOCITY | 0.157551 |
| mpi2-x2 | variability | V-VELOCITY | 0.160694 |
| mpi2-x2 | variability | W-VELOCITY | 0.212496 |
| mpi2-y2 | full | HRRPUV | 0.102082 |
| mpi2-y2 | full | OXYGEN VOLUME FRACTION | 0.00241343 |
| mpi2-y2 | full | SOOT DENSITY | 0.214927 |
| mpi2-y2 | full | TEMPERATURE | 0.196139 |
| mpi2-y2 | full | U-VELOCITY | 0.956375 |
| mpi2-y2 | full | V-VELOCITY | 0.966173 |
| mpi2-y2 | full | W-VELOCITY | 0.2872 |
| mpi2-y2 | interfacesFull | HRRPUV | 0.118838 |
| mpi2-y2 | interfacesFull | OXYGEN VOLUME FRACTION | 0.00545253 |
| mpi2-y2 | interfacesFull | SOOT DENSITY | 0.145171 |
| mpi2-y2 | interfacesFull | TEMPERATURE | 0.153049 |
| mpi2-y2 | interfacesFull | U-VELOCITY | 1.15804 |
| mpi2-y2 | interfacesFull | V-VELOCITY | 1.37113 |
| mpi2-y2 | interfacesFull | W-VELOCITY | 0.199178 |
| mpi2-y2 | interfacesLate | HRRPUV | 0.124545 |
| mpi2-y2 | interfacesLate | OXYGEN VOLUME FRACTION | 0.00539246 |
| mpi2-y2 | interfacesLate | SOOT DENSITY | 0.14052 |
| mpi2-y2 | interfacesLate | TEMPERATURE | 0.148403 |
| mpi2-y2 | interfacesLate | U-VELOCITY | 1.17294 |
| mpi2-y2 | interfacesLate | V-VELOCITY | 1.33696 |
| mpi2-y2 | interfacesLate | W-VELOCITY | 0.186334 |
| mpi2-y2 | late | HRRPUV | 0.0993663 |
| mpi2-y2 | late | OXYGEN VOLUME FRACTION | 0.00235452 |
| mpi2-y2 | late | SOOT DENSITY | 0.201904 |
| mpi2-y2 | late | TEMPERATURE | 0.188062 |
| mpi2-y2 | late | U-VELOCITY | 0.953131 |
| mpi2-y2 | late | V-VELOCITY | 0.94025 |
| mpi2-y2 | late | W-VELOCITY | 0.270556 |
| mpi2-y2 | variability | HRRPUV | 0.13516 |
| mpi2-y2 | variability | OXYGEN VOLUME FRACTION | 0.000459077 |
| mpi2-y2 | variability | SOOT DENSITY | 0.27382 |
| mpi2-y2 | variability | TEMPERATURE | 0.0848701 |
| mpi2-y2 | variability | U-VELOCITY | 0.176452 |
| mpi2-y2 | variability | V-VELOCITY | 0.19035 |
| mpi2-y2 | variability | W-VELOCITY | 0.264462 |
| mpi4-x4 | full | HRRPUV | 0.154959 |
| mpi4-x4 | full | OXYGEN VOLUME FRACTION | 0.0027442 |
| mpi4-x4 | full | SOOT DENSITY | 0.232906 |
| mpi4-x4 | full | TEMPERATURE | 0.219485 |
| mpi4-x4 | full | U-VELOCITY | 0.982711 |
| mpi4-x4 | full | V-VELOCITY | 0.997527 |
| mpi4-x4 | full | W-VELOCITY | 0.299809 |
| mpi4-x4 | interfacesFull | HRRPUV | 0.172893 |
| mpi4-x4 | interfacesFull | OXYGEN VOLUME FRACTION | 0.00372126 |
| mpi4-x4 | interfacesFull | SOOT DENSITY | 0.1683 |
| mpi4-x4 | interfacesFull | TEMPERATURE | 0.176666 |
| mpi4-x4 | interfacesFull | U-VELOCITY | 1.15223 |
| mpi4-x4 | interfacesFull | V-VELOCITY | 0.951702 |
| mpi4-x4 | interfacesFull | W-VELOCITY | 0.218111 |
| mpi4-x4 | interfacesLate | HRRPUV | 0.206745 |
| mpi4-x4 | interfacesLate | OXYGEN VOLUME FRACTION | 0.00399003 |
| mpi4-x4 | interfacesLate | SOOT DENSITY | 0.164138 |
| mpi4-x4 | interfacesLate | TEMPERATURE | 0.182765 |
| mpi4-x4 | interfacesLate | U-VELOCITY | 1.11949 |
| mpi4-x4 | interfacesLate | V-VELOCITY | 0.904855 |
| mpi4-x4 | interfacesLate | W-VELOCITY | 0.205277 |
| mpi4-x4 | late | HRRPUV | 0.175635 |
| mpi4-x4 | late | OXYGEN VOLUME FRACTION | 0.00288168 |
| mpi4-x4 | late | SOOT DENSITY | 0.225614 |
| mpi4-x4 | late | TEMPERATURE | 0.224194 |
| mpi4-x4 | late | U-VELOCITY | 0.963518 |
| mpi4-x4 | late | V-VELOCITY | 0.970006 |
| mpi4-x4 | late | W-VELOCITY | 0.285707 |
| mpi4-x4 | variability | HRRPUV | 0.133455 |
| mpi4-x4 | variability | OXYGEN VOLUME FRACTION | 0.000419984 |
| mpi4-x4 | variability | SOOT DENSITY | 0.240078 |
| mpi4-x4 | variability | TEMPERATURE | 0.0774761 |
| mpi4-x4 | variability | U-VELOCITY | 0.181431 |
| mpi4-x4 | variability | V-VELOCITY | 0.171488 |
| mpi4-x4 | variability | W-VELOCITY | 0.221114 |
| mpi4-xy22 | full | HRRPUV | 0.145848 |
| mpi4-xy22 | full | OXYGEN VOLUME FRACTION | 0.00271531 |
| mpi4-xy22 | full | SOOT DENSITY | 0.226195 |
| mpi4-xy22 | full | TEMPERATURE | 0.217565 |
| mpi4-xy22 | full | U-VELOCITY | 0.991527 |
| mpi4-xy22 | full | V-VELOCITY | 0.969182 |
| mpi4-xy22 | full | W-VELOCITY | 0.29541 |
| mpi4-xy22 | interfacesFull | HRRPUV | 0.151325 |
| mpi4-xy22 | interfacesFull | OXYGEN VOLUME FRACTION | 0.00611679 |
| mpi4-xy22 | interfacesFull | SOOT DENSITY | 0.174648 |
| mpi4-xy22 | interfacesFull | TEMPERATURE | 0.187857 |
| mpi4-xy22 | interfacesFull | U-VELOCITY | 1.30807 |
| mpi4-xy22 | interfacesFull | V-VELOCITY | 1.25071 |
| mpi4-xy22 | interfacesFull | W-VELOCITY | 0.23046 |
| mpi4-xy22 | interfacesLate | HRRPUV | 0.183278 |
| mpi4-xy22 | interfacesLate | OXYGEN VOLUME FRACTION | 0.00678823 |
| mpi4-xy22 | interfacesLate | SOOT DENSITY | 0.181407 |
| mpi4-xy22 | interfacesLate | TEMPERATURE | 0.201524 |
| mpi4-xy22 | interfacesLate | U-VELOCITY | 1.35477 |
| mpi4-xy22 | interfacesLate | V-VELOCITY | 1.2885 |
| mpi4-xy22 | interfacesLate | W-VELOCITY | 0.227605 |
| mpi4-xy22 | late | HRRPUV | 0.174723 |
| mpi4-xy22 | late | OXYGEN VOLUME FRACTION | 0.00297215 |
| mpi4-xy22 | late | SOOT DENSITY | 0.231972 |
| mpi4-xy22 | late | TEMPERATURE | 0.231532 |
| mpi4-xy22 | late | U-VELOCITY | 1.02722 |
| mpi4-xy22 | late | V-VELOCITY | 0.988237 |
| mpi4-xy22 | late | W-VELOCITY | 0.293548 |
| mpi4-xy22 | variability | HRRPUV | 0.159908 |
| mpi4-xy22 | variability | OXYGEN VOLUME FRACTION | 0.000514081 |
| mpi4-xy22 | variability | SOOT DENSITY | 0.27991 |
| mpi4-xy22 | variability | TEMPERATURE | 0.0947543 |
| mpi4-xy22 | variability | U-VELOCITY | 0.179683 |
| mpi4-xy22 | variability | V-VELOCITY | 0.17646 |
| mpi4-xy22 | variability | W-VELOCITY | 0.25493 |

### Natywne sondy i strumienie

Największy bezwzględny RMS po dostępnych parach; zachowujemy położenie sondy i natywne jednostki.

| Grupa | Urządzenie | Jednostka | RMS |
|---|---|---|---:|
| OpenMP / OpenMP | divergence_X1_hi | 1/s | 1.3688e-06 |
| OpenMP / OpenMP | divergence_X1_lo | 1/s | 1.15541e-06 |
| OpenMP / OpenMP | divergence_X2_hi | 1/s | 0.000161089 |
| OpenMP / OpenMP | divergence_X2_lo | 1/s | 1.51376e-05 |
| OpenMP / OpenMP | divergence_X3_hi | 1/s | 0.117633 |
| OpenMP / OpenMP | divergence_X3_lo | 1/s | 0.0483191 |
| OpenMP / OpenMP | divergence_X4_hi | 1/s | 0.0544982 |
| OpenMP / OpenMP | divergence_X4_lo | 1/s | 0.0353378 |
| OpenMP / OpenMP | divergence_X5_hi | 1/s | 0.0572587 |
| OpenMP / OpenMP | divergence_X5_lo | 1/s | 0.15649 |
| OpenMP / OpenMP | divergence_X6_hi | 1/s | 3.65356e-05 |
| OpenMP / OpenMP | divergence_X6_lo | 1/s | 0.000382795 |
| OpenMP / OpenMP | divergence_X7_hi | 1/s | 1.19853e-06 |
| OpenMP / OpenMP | divergence_X7_lo | 1/s | 1.50409e-06 |
| OpenMP / OpenMP | divergence_Y1_hi | 1/s | 1.45073e-06 |
| OpenMP / OpenMP | divergence_Y1_lo | 1/s | 1.18128e-06 |
| OpenMP / OpenMP | divergence_Y2_hi | 1/s | 0.000239099 |
| OpenMP / OpenMP | divergence_Y2_lo | 1/s | 2.43691e-05 |
| OpenMP / OpenMP | divergence_Y3_hi | 1/s | 0.133862 |
| OpenMP / OpenMP | divergence_Y3_lo | 1/s | 0.0389096 |
| OpenMP / OpenMP | divergence_Y4_hi | 1/s | 0.0544982 |
| OpenMP / OpenMP | divergence_Y4_lo | 1/s | 0.0469671 |
| OpenMP / OpenMP | divergence_Y5_hi | 1/s | 0.0551853 |
| OpenMP / OpenMP | divergence_Y5_lo | 1/s | 0.122786 |
| OpenMP / OpenMP | divergence_Y6_hi | 1/s | 2.63047e-05 |
| OpenMP / OpenMP | divergence_Y6_lo | 1/s | 0.000285502 |
| OpenMP / OpenMP | divergence_Y7_hi | 1/s | 1.13644e-06 |
| OpenMP / OpenMP | divergence_Y7_lo | 1/s | 1.36264e-06 |
| OpenMP / OpenMP | divergence_Z1_hi | 1/s | 0.00368015 |
| OpenMP / OpenMP | divergence_Z1_lo | 1/s | 2.44064e-05 |
| OpenMP / OpenMP | divergence_Z2_hi | 1/s | 0.0191912 |
| OpenMP / OpenMP | divergence_Z2_lo | 1/s | 0.016208 |
| OpenMP / OpenMP | divergence_Z3_hi | 1/s | 0.0515141 |
| OpenMP / OpenMP | divergence_Z3_lo | 1/s | 0.0463835 |
| OpenMP / OpenMP | divergence_Z4_hi | 1/s | 0.0544982 |
| OpenMP / OpenMP | divergence_Z4_lo | 1/s | 0.0510244 |
| OpenMP / OpenMP | divergence_Z5_hi | 1/s | 0.683218 |
| OpenMP / OpenMP | divergence_Z5_lo | 1/s | 0.644047 |
| OpenMP / OpenMP | divergence_Z6_hi | 1/s | 0.956179 |
| OpenMP / OpenMP | divergence_Z6_lo | 1/s | 0.870662 |
| OpenMP / OpenMP | divergence_Z7_hi | 1/s | 1.42598 |
| OpenMP / OpenMP | divergence_Z7_lo | 1/s | 1.49344 |
| OpenMP / OpenMP | enthalpy_local_X1 | kW/m2 | 7.68351e-05 |
| OpenMP / OpenMP | enthalpy_local_X2 | kW/m2 | 0.00120436 |
| OpenMP / OpenMP | enthalpy_local_X3 | kW/m2 | 1.27495 |
| OpenMP / OpenMP | enthalpy_local_X4 | kW/m2 | 1.98676 |
| OpenMP / OpenMP | enthalpy_local_X5 | kW/m2 | 0.0889784 |
| OpenMP / OpenMP | enthalpy_local_X6 | kW/m2 | 0.000184338 |
| OpenMP / OpenMP | enthalpy_local_X7 | kW/m2 | 4.1091e-05 |
| OpenMP / OpenMP | enthalpy_local_Y1 | kW/m2 | 8.62377e-05 |
| OpenMP / OpenMP | enthalpy_local_Y2 | kW/m2 | 0.00146175 |
| OpenMP / OpenMP | enthalpy_local_Y3 | kW/m2 | 1.68897 |
| OpenMP / OpenMP | enthalpy_local_Y4 | kW/m2 | 1.31616 |
| OpenMP / OpenMP | enthalpy_local_Y5 | kW/m2 | 0.0674384 |
| OpenMP / OpenMP | enthalpy_local_Y6 | kW/m2 | 0.00016533 |
| OpenMP / OpenMP | enthalpy_local_Y7 | kW/m2 | 3.85446e-05 |
| OpenMP / OpenMP | enthalpy_local_Z1 | kW/m2 | 0.00645609 |
| OpenMP / OpenMP | enthalpy_local_Z2 | kW/m2 | 0.40467 |
| OpenMP / OpenMP | enthalpy_local_Z3 | kW/m2 | 1.11246 |
| OpenMP / OpenMP | enthalpy_local_Z4 | kW/m2 | 1.89661 |
| OpenMP / OpenMP | enthalpy_local_Z5 | kW/m2 | 8.15115 |
| OpenMP / OpenMP | enthalpy_local_Z6 | kW/m2 | 22.8693 |
| OpenMP / OpenMP | enthalpy_local_Z7 | kW/m2 | 44.8314 |
| OpenMP / OpenMP | mass_local_X1 | kg/s/m2 | 0.000311814 |
| OpenMP / OpenMP | mass_local_X2 | kg/s/m2 | 0.000747318 |
| OpenMP / OpenMP | mass_local_X3 | kg/s/m2 | 0.00329752 |
| OpenMP / OpenMP | mass_local_X4 | kg/s/m2 | 0.00122763 |
| OpenMP / OpenMP | mass_local_X5 | kg/s/m2 | 0.00415252 |
| OpenMP / OpenMP | mass_local_X6 | kg/s/m2 | 0.000747729 |
| OpenMP / OpenMP | mass_local_X7 | kg/s/m2 | 0.000375729 |
| OpenMP / OpenMP | mass_local_Y1 | kg/s/m2 | 0.000347878 |
| OpenMP / OpenMP | mass_local_Y2 | kg/s/m2 | 0.000856145 |
| OpenMP / OpenMP | mass_local_Y3 | kg/s/m2 | 0.00378129 |
| OpenMP / OpenMP | mass_local_Y4 | kg/s/m2 | 0.00100506 |
| OpenMP / OpenMP | mass_local_Y5 | kg/s/m2 | 0.00386298 |
| OpenMP / OpenMP | mass_local_Y6 | kg/s/m2 | 0.00066004 |
| OpenMP / OpenMP | mass_local_Y7 | kg/s/m2 | 0.000351306 |
| OpenMP / OpenMP | mass_local_Z1 | kg/s/m2 | 1.59228e-06 |
| OpenMP / OpenMP | mass_local_Z2 | kg/s/m2 | 0.000344694 |
| OpenMP / OpenMP | mass_local_Z3 | kg/s/m2 | 0.000555816 |
| OpenMP / OpenMP | mass_local_Z4 | kg/s/m2 | 0.00104625 |
| OpenMP / OpenMP | mass_local_Z5 | kg/s/m2 | 0.00221088 |
| OpenMP / OpenMP | mass_local_Z6 | kg/s/m2 | 0.0116644 |
| OpenMP / OpenMP | mass_local_Z7 | kg/s/m2 | 0.0162796 |
| OpenMP / OpenMP | mdot_X1 | kg/s | 1.05674e-05 |
| OpenMP / OpenMP | mdot_X2 | kg/s | 1.50324e-05 |
| OpenMP / OpenMP | mdot_X3 | kg/s | 2.94359e-05 |
| OpenMP / OpenMP | mdot_X4 | kg/s | 4.50209e-05 |
| OpenMP / OpenMP | mdot_X5 | kg/s | 3.35101e-05 |
| OpenMP / OpenMP | mdot_X6 | kg/s | 2.07059e-05 |
| OpenMP / OpenMP | mdot_X7 | kg/s | 1.39281e-05 |
| OpenMP / OpenMP | mdot_Y1 | kg/s | 1.63278e-05 |
| OpenMP / OpenMP | mdot_Y2 | kg/s | 2.23236e-05 |
| OpenMP / OpenMP | mdot_Y3 | kg/s | 3.1652e-05 |
| OpenMP / OpenMP | mdot_Y4 | kg/s | 3.92917e-05 |
| OpenMP / OpenMP | mdot_Y5 | kg/s | 2.53496e-05 |
| OpenMP / OpenMP | mdot_Y6 | kg/s | 1.82761e-05 |
| OpenMP / OpenMP | mdot_Y7 | kg/s | 1.18549e-05 |
| OpenMP / OpenMP | mdot_Z1 | kg/s | 3.24174e-07 |
| OpenMP / OpenMP | mdot_Z2 | kg/s | 1.02976e-06 |
| OpenMP / OpenMP | mdot_Z3 | kg/s | 1.60365e-06 |
| OpenMP / OpenMP | mdot_Z4 | kg/s | 4.40362e-06 |
| OpenMP / OpenMP | mdot_Z5 | kg/s | 8.12189e-06 |
| OpenMP / OpenMP | mdot_Z6 | kg/s | 1.29548e-05 |
| OpenMP / OpenMP | mdot_Z7 | kg/s | 2.06709e-05 |
| OpenMP / OpenMP | pressure_X1_hi | Pa | 0.000313913 |
| OpenMP / OpenMP | pressure_X1_lo | Pa | 0.000230871 |
| OpenMP / OpenMP | pressure_X2_hi | Pa | 0.000860337 |
| OpenMP / OpenMP | pressure_X2_lo | Pa | 0.000674087 |
| OpenMP / OpenMP | pressure_X3_hi | Pa | 0.00211282 |
| OpenMP / OpenMP | pressure_X3_lo | Pa | 0.00189404 |
| OpenMP / OpenMP | pressure_X4_hi | Pa | 0.00190213 |
| OpenMP / OpenMP | pressure_X4_lo | Pa | 0.00192588 |
| OpenMP / OpenMP | pressure_X5_hi | Pa | 0.00198541 |
| OpenMP / OpenMP | pressure_X5_lo | Pa | 0.00215225 |
| OpenMP / OpenMP | pressure_X6_hi | Pa | 0.000609214 |
| OpenMP / OpenMP | pressure_X6_lo | Pa | 0.0007888 |
| OpenMP / OpenMP | pressure_X7_hi | Pa | 0.000207387 |
| OpenMP / OpenMP | pressure_X7_lo | Pa | 0.000281206 |
| OpenMP / OpenMP | pressure_Y1_hi | Pa | 0.00029457 |
| OpenMP / OpenMP | pressure_Y1_lo | Pa | 0.000218915 |
| OpenMP / OpenMP | pressure_Y2_hi | Pa | 0.000777463 |
| OpenMP / OpenMP | pressure_Y2_lo | Pa | 0.000613465 |
| OpenMP / OpenMP | pressure_Y3_hi | Pa | 0.00198084 |
| OpenMP / OpenMP | pressure_Y3_lo | Pa | 0.00174429 |
| OpenMP / OpenMP | pressure_Y4_hi | Pa | 0.00190213 |
| OpenMP / OpenMP | pressure_Y4_lo | Pa | 0.0019284 |
| OpenMP / OpenMP | pressure_Y5_hi | Pa | 0.00174551 |
| OpenMP / OpenMP | pressure_Y5_lo | Pa | 0.00217073 |
| OpenMP / OpenMP | pressure_Y6_hi | Pa | 0.000603695 |
| OpenMP / OpenMP | pressure_Y6_lo | Pa | 0.000776402 |
| OpenMP / OpenMP | pressure_Y7_hi | Pa | 0.00020416 |
| OpenMP / OpenMP | pressure_Y7_lo | Pa | 0.000277536 |
| OpenMP / OpenMP | pressure_Z1_hi | Pa | 0.000391354 |
| OpenMP / OpenMP | pressure_Z1_lo | Pa | 0.000354287 |
| OpenMP / OpenMP | pressure_Z2_hi | Pa | 0.000394622 |
| OpenMP / OpenMP | pressure_Z2_lo | Pa | 0.000373859 |
| OpenMP / OpenMP | pressure_Z3_hi | Pa | 0.000819474 |
| OpenMP / OpenMP | pressure_Z3_lo | Pa | 0.000707065 |
| OpenMP / OpenMP | pressure_Z4_hi | Pa | 0.00190213 |
| OpenMP / OpenMP | pressure_Z4_lo | Pa | 0.00163 |
| OpenMP / OpenMP | pressure_Z5_hi | Pa | 0.00255752 |
| OpenMP / OpenMP | pressure_Z5_lo | Pa | 0.00278301 |
| OpenMP / OpenMP | pressure_Z6_hi | Pa | 0.0048407 |
| OpenMP / OpenMP | pressure_Z6_lo | Pa | 0.0041704 |
| OpenMP / OpenMP | pressure_Z7_hi | Pa | 0.00717765 |
| OpenMP / OpenMP | pressure_Z7_lo | Pa | 0.00782468 |
| OpenMP / OpenMP | probe_O2 | mol/mol | 6.09079e-05 |
| OpenMP / OpenMP | probe_T | C | 1.7544 |
| OpenMP / OpenMP | qdot_X1 | kW | 1.0711e-06 |
| OpenMP / OpenMP | qdot_X2 | kW | 9.87243e-05 |
| OpenMP / OpenMP | qdot_X3 | kW | 0.00305348 |
| OpenMP / OpenMP | qdot_X4 | kW | 0.0102821 |
| OpenMP / OpenMP | qdot_X5 | kW | 0.00350116 |
| OpenMP / OpenMP | qdot_X6 | kW | 5.13014e-05 |
| OpenMP / OpenMP | qdot_X7 | kW | 1.08993e-06 |
| OpenMP / OpenMP | qdot_Y1 | kW | 1.24607e-06 |
| OpenMP / OpenMP | qdot_Y2 | kW | 0.000234041 |
| OpenMP / OpenMP | qdot_Y3 | kW | 0.0042291 |
| OpenMP / OpenMP | qdot_Y4 | kW | 0.0103512 |
| OpenMP / OpenMP | qdot_Y5 | kW | 0.00325607 |
| OpenMP / OpenMP | qdot_Y6 | kW | 5.7745e-05 |
| OpenMP / OpenMP | qdot_Y7 | kW | 1.04231e-06 |
| OpenMP / OpenMP | qdot_Z1 | kW | 1.22487e-05 |
| OpenMP / OpenMP | qdot_Z2 | kW | 0.000350009 |
| OpenMP / OpenMP | qdot_Z3 | kW | 0.000733261 |
| OpenMP / OpenMP | qdot_Z4 | kW | 0.00134488 |
| OpenMP / OpenMP | qdot_Z5 | kW | 0.00214313 |
| OpenMP / OpenMP | qdot_Z6 | kW | 0.00252548 |
| OpenMP / OpenMP | qdot_Z7 | kW | 0.00381836 |
| OpenMP / OpenMP | radiative_X1 | kW/m2 | 0.00502325 |
| OpenMP / OpenMP | radiative_X2 | kW/m2 | 0.0109646 |
| OpenMP / OpenMP | radiative_X3 | kW/m2 | 0.0290828 |
| OpenMP / OpenMP | radiative_X4 | kW/m2 | 0.0424137 |
| OpenMP / OpenMP | radiative_X5 | kW/m2 | 0.000109306 |
| OpenMP / OpenMP | radiative_X6 | kW/m2 | 1.31312e-06 |
| OpenMP / OpenMP | radiative_X7 | kW/m2 | 2.10155e-07 |
| OpenMP / OpenMP | radiative_Y1 | kW/m2 | 0.00512501 |
| OpenMP / OpenMP | radiative_Y2 | kW/m2 | 0.0111863 |
| OpenMP / OpenMP | radiative_Y3 | kW/m2 | 0.0298664 |
| OpenMP / OpenMP | radiative_Y4 | kW/m2 | 0.0361942 |
| OpenMP / OpenMP | radiative_Y5 | kW/m2 | 9.31495e-05 |
| OpenMP / OpenMP | radiative_Y6 | kW/m2 | 1.15115e-06 |
| OpenMP / OpenMP | radiative_Y7 | kW/m2 | 1.93839e-07 |
| OpenMP / OpenMP | radiative_Z1 | kW/m2 | 0.0136454 |
| OpenMP / OpenMP | radiative_Z2 | kW/m2 | 0.0412064 |
| OpenMP / OpenMP | radiative_Z3 | kW/m2 | 0.0530796 |
| OpenMP / OpenMP | radiative_Z4 | kW/m2 | 0.0342144 |
| OpenMP / OpenMP | radiative_Z5 | kW/m2 | 0.125107 |
| OpenMP / OpenMP | radiative_Z6 | kW/m2 | 0.187274 |
| OpenMP / OpenMP | radiative_Z7 | kW/m2 | 0.124985 |
| mpi2-x2 | divergence_X1_hi | 1/s | 6.31786e-06 |
| mpi2-x2 | divergence_X1_lo | 1/s | 5.93289e-06 |
| mpi2-x2 | divergence_X2_hi | 1/s | 0.00685731 |
| mpi2-x2 | divergence_X2_lo | 1/s | 0.00258724 |
| mpi2-x2 | divergence_X3_hi | 1/s | 0.674293 |
| mpi2-x2 | divergence_X3_lo | 1/s | 0.237391 |
| mpi2-x2 | divergence_X4_hi | 1/s | 0.276806 |
| mpi2-x2 | divergence_X4_lo | 1/s | 0.368568 |
| mpi2-x2 | divergence_X5_hi | 1/s | 0.245215 |
| mpi2-x2 | divergence_X5_lo | 1/s | 0.587043 |
| mpi2-x2 | divergence_X6_hi | 1/s | 0.00155469 |
| mpi2-x2 | divergence_X6_lo | 1/s | 0.0107668 |
| mpi2-x2 | divergence_X7_hi | 1/s | 9.47551e-06 |
| mpi2-x2 | divergence_X7_lo | 1/s | 1.13555e-05 |
| mpi2-x2 | divergence_Y1_hi | 1/s | 1.09024e-05 |
| mpi2-x2 | divergence_Y1_lo | 1/s | 9.56013e-06 |
| mpi2-x2 | divergence_Y2_hi | 1/s | 0.0115095 |
| mpi2-x2 | divergence_Y2_lo | 1/s | 0.00193353 |
| mpi2-x2 | divergence_Y3_hi | 1/s | 0.547376 |
| mpi2-x2 | divergence_Y3_lo | 1/s | 0.256017 |
| mpi2-x2 | divergence_Y4_hi | 1/s | 0.341849 |
| mpi2-x2 | divergence_Y4_lo | 1/s | 0.196635 |
| mpi2-x2 | divergence_Y5_hi | 1/s | 0.261125 |
| mpi2-x2 | divergence_Y5_lo | 1/s | 0.745589 |
| mpi2-x2 | divergence_Y6_hi | 1/s | 0.00208633 |
| mpi2-x2 | divergence_Y6_lo | 1/s | 0.0102305 |
| mpi2-x2 | divergence_Y7_hi | 1/s | 5.66211e-06 |
| mpi2-x2 | divergence_Y7_lo | 1/s | 5.93092e-06 |
| mpi2-x2 | divergence_Z1_hi | 1/s | 0.182955 |
| mpi2-x2 | divergence_Z1_lo | 1/s | 0.012262 |
| mpi2-x2 | divergence_Z2_hi | 1/s | 0.128906 |
| mpi2-x2 | divergence_Z2_lo | 1/s | 0.139237 |
| mpi2-x2 | divergence_Z3_hi | 1/s | 0.199732 |
| mpi2-x2 | divergence_Z3_lo | 1/s | 0.187145 |
| mpi2-x2 | divergence_Z4_hi | 1/s | 0.341849 |
| mpi2-x2 | divergence_Z4_lo | 1/s | 0.297502 |
| mpi2-x2 | divergence_Z5_hi | 1/s | 1.639 |
| mpi2-x2 | divergence_Z5_lo | 1/s | 1.74302 |
| mpi2-x2 | divergence_Z6_hi | 1/s | 2.44018 |
| mpi2-x2 | divergence_Z6_lo | 1/s | 2.21473 |
| mpi2-x2 | divergence_Z7_hi | 1/s | 3.61672 |
| mpi2-x2 | divergence_Z7_lo | 1/s | 3.45871 |
| mpi2-x2 | enthalpy_local_X1 | kW/m2 | 0.00021266 |
| mpi2-x2 | enthalpy_local_X2 | kW/m2 | 0.116132 |
| mpi2-x2 | enthalpy_local_X3 | kW/m2 | 5.38207 |
| mpi2-x2 | enthalpy_local_X4 | kW/m2 | 7.85395 |
| mpi2-x2 | enthalpy_local_X5 | kW/m2 | 0.351124 |
| mpi2-x2 | enthalpy_local_X6 | kW/m2 | 0.00207166 |
| mpi2-x2 | enthalpy_local_X7 | kW/m2 | 0.000109821 |
| mpi2-x2 | enthalpy_local_Y1 | kW/m2 | 0.000272955 |
| mpi2-x2 | enthalpy_local_Y2 | kW/m2 | 0.0390234 |
| mpi2-x2 | enthalpy_local_Y3 | kW/m2 | 4.79327 |
| mpi2-x2 | enthalpy_local_Y4 | kW/m2 | 5.71413 |
| mpi2-x2 | enthalpy_local_Y5 | kW/m2 | 0.888705 |
| mpi2-x2 | enthalpy_local_Y6 | kW/m2 | 0.0080957 |
| mpi2-x2 | enthalpy_local_Y7 | kW/m2 | 0.000124301 |
| mpi2-x2 | enthalpy_local_Z1 | kW/m2 | 0.535659 |
| mpi2-x2 | enthalpy_local_Z2 | kW/m2 | 1.74172 |
| mpi2-x2 | enthalpy_local_Z3 | kW/m2 | 4.24632 |
| mpi2-x2 | enthalpy_local_Z4 | kW/m2 | 8.63555 |
| mpi2-x2 | enthalpy_local_Z5 | kW/m2 | 31.2406 |
| mpi2-x2 | enthalpy_local_Z6 | kW/m2 | 54.31 |
| mpi2-x2 | enthalpy_local_Z7 | kW/m2 | 114.984 |
| mpi2-x2 | mass_local_X1 | kg/s/m2 | 0.00255071 |
| mpi2-x2 | mass_local_X2 | kg/s/m2 | 0.00863005 |
| mpi2-x2 | mass_local_X3 | kg/s/m2 | 0.0157556 |
| mpi2-x2 | mass_local_X4 | kg/s/m2 | 0.00262629 |
| mpi2-x2 | mass_local_X5 | kg/s/m2 | 0.0155087 |
| mpi2-x2 | mass_local_X6 | kg/s/m2 | 0.0101602 |
| mpi2-x2 | mass_local_X7 | kg/s/m2 | 0.00216316 |
| mpi2-x2 | mass_local_Y1 | kg/s/m2 | 0.00250521 |
| mpi2-x2 | mass_local_Y2 | kg/s/m2 | 0.0103904 |
| mpi2-x2 | mass_local_Y3 | kg/s/m2 | 0.0137773 |
| mpi2-x2 | mass_local_Y4 | kg/s/m2 | 0.00366494 |
| mpi2-x2 | mass_local_Y5 | kg/s/m2 | 0.0138643 |
| mpi2-x2 | mass_local_Y6 | kg/s/m2 | 0.00895118 |
| mpi2-x2 | mass_local_Y7 | kg/s/m2 | 0.00278569 |
| mpi2-x2 | mass_local_Z1 | kg/s/m2 | 4.1979e-05 |
| mpi2-x2 | mass_local_Z2 | kg/s/m2 | 0.00177417 |
| mpi2-x2 | mass_local_Z3 | kg/s/m2 | 0.00272387 |
| mpi2-x2 | mass_local_Z4 | kg/s/m2 | 0.00549339 |
| mpi2-x2 | mass_local_Z5 | kg/s/m2 | 0.0118246 |
| mpi2-x2 | mass_local_Z6 | kg/s/m2 | 0.0267854 |
| mpi2-x2 | mass_local_Z7 | kg/s/m2 | 0.0324893 |
| mpi2-x2 | mdot_X1 | kg/s | 5.57016e-05 |
| mpi2-x2 | mdot_X2 | kg/s | 7.15118e-05 |
| mpi2-x2 | mdot_X3 | kg/s | 9.44201e-05 |
| mpi2-x2 | mdot_X4 | kg/s | 0.000105446 |
| mpi2-x2 | mdot_X5 | kg/s | 8.52069e-05 |
| mpi2-x2 | mdot_X6 | kg/s | 6.99468e-05 |
| mpi2-x2 | mdot_X7 | kg/s | 5.26337e-05 |
| mpi2-x2 | mdot_Y1 | kg/s | 5.67597e-05 |
| mpi2-x2 | mdot_Y2 | kg/s | 7.83095e-05 |
| mpi2-x2 | mdot_Y3 | kg/s | 8.42368e-05 |
| mpi2-x2 | mdot_Y4 | kg/s | 0.000108539 |
| mpi2-x2 | mdot_Y5 | kg/s | 0.000105303 |
| mpi2-x2 | mdot_Y6 | kg/s | 8.10512e-05 |
| mpi2-x2 | mdot_Y7 | kg/s | 6.43999e-05 |
| mpi2-x2 | mdot_Z1 | kg/s | 2.70476e-06 |
| mpi2-x2 | mdot_Z2 | kg/s | 7.76584e-06 |
| mpi2-x2 | mdot_Z3 | kg/s | 1.1589e-05 |
| mpi2-x2 | mdot_Z4 | kg/s | 2.19012e-05 |
| mpi2-x2 | mdot_Z5 | kg/s | 3.38258e-05 |
| mpi2-x2 | mdot_Z6 | kg/s | 6.02255e-05 |
| mpi2-x2 | mdot_Z7 | kg/s | 0.000101801 |
| mpi2-x2 | pressure_X1_hi | Pa | 0.0011958 |
| mpi2-x2 | pressure_X1_lo | Pa | 0.000861021 |
| mpi2-x2 | pressure_X2_hi | Pa | 0.00457286 |
| mpi2-x2 | pressure_X2_lo | Pa | 0.00312528 |
| mpi2-x2 | pressure_X3_hi | Pa | 0.00920073 |
| mpi2-x2 | pressure_X3_lo | Pa | 0.00746609 |
| mpi2-x2 | pressure_X4_hi | Pa | 0.00777904 |
| mpi2-x2 | pressure_X4_lo | Pa | 0.00715801 |
| mpi2-x2 | pressure_X5_hi | Pa | 0.0067525 |
| mpi2-x2 | pressure_X5_lo | Pa | 0.0080118 |
| mpi2-x2 | pressure_X6_hi | Pa | 0.00204336 |
| mpi2-x2 | pressure_X6_lo | Pa | 0.0025647 |
| mpi2-x2 | pressure_X7_hi | Pa | 0.000701597 |
| mpi2-x2 | pressure_X7_lo | Pa | 0.000944787 |
| mpi2-x2 | pressure_Y1_hi | Pa | 0.00106754 |
| mpi2-x2 | pressure_Y1_lo | Pa | 0.000784159 |
| mpi2-x2 | pressure_Y2_hi | Pa | 0.00353866 |
| mpi2-x2 | pressure_Y2_lo | Pa | 0.00249997 |
| mpi2-x2 | pressure_Y3_hi | Pa | 0.00851209 |
| mpi2-x2 | pressure_Y3_lo | Pa | 0.00729542 |
| mpi2-x2 | pressure_Y4_hi | Pa | 0.00764246 |
| mpi2-x2 | pressure_Y4_lo | Pa | 0.00714472 |
| mpi2-x2 | pressure_Y5_hi | Pa | 0.00836372 |
| mpi2-x2 | pressure_Y5_lo | Pa | 0.00998038 |
| mpi2-x2 | pressure_Y6_hi | Pa | 0.00251842 |
| mpi2-x2 | pressure_Y6_lo | Pa | 0.00379764 |
| mpi2-x2 | pressure_Y7_hi | Pa | 0.000810299 |
| mpi2-x2 | pressure_Y7_lo | Pa | 0.0011131 |
| mpi2-x2 | pressure_Z1_hi | Pa | 0.00116889 |
| mpi2-x2 | pressure_Z1_lo | Pa | 0.00384946 |
| mpi2-x2 | pressure_Z2_hi | Pa | 0.00159367 |
| mpi2-x2 | pressure_Z2_lo | Pa | 0.00137752 |
| mpi2-x2 | pressure_Z3_hi | Pa | 0.00326421 |
| mpi2-x2 | pressure_Z3_lo | Pa | 0.00286479 |
| mpi2-x2 | pressure_Z4_hi | Pa | 0.00764246 |
| mpi2-x2 | pressure_Z4_lo | Pa | 0.00712747 |
| mpi2-x2 | pressure_Z5_hi | Pa | 0.0102452 |
| mpi2-x2 | pressure_Z5_lo | Pa | 0.00978404 |
| mpi2-x2 | pressure_Z6_hi | Pa | 0.01643 |
| mpi2-x2 | pressure_Z6_lo | Pa | 0.0154637 |
| mpi2-x2 | pressure_Z7_hi | Pa | 0.0170451 |
| mpi2-x2 | pressure_Z7_lo | Pa | 0.01673 |
| mpi2-x2 | probe_O2 | mol/mol | 0.000460229 |
| mpi2-x2 | probe_T | C | 5.95796 |
| mpi2-x2 | qdot_X1 | kW | 1.01281e-05 |
| mpi2-x2 | qdot_X2 | kW | 0.000512509 |
| mpi2-x2 | qdot_X3 | kW | 0.013086 |
| mpi2-x2 | qdot_X4 | kW | 0.021999 |
| mpi2-x2 | qdot_X5 | kW | 0.0115814 |
| mpi2-x2 | qdot_X6 | kW | 0.000710438 |
| mpi2-x2 | qdot_X7 | kW | 2.83473e-06 |
| mpi2-x2 | qdot_Y1 | kW | 2.893e-06 |
| mpi2-x2 | qdot_Y2 | kW | 0.000637799 |
| mpi2-x2 | qdot_Y3 | kW | 0.0102338 |
| mpi2-x2 | qdot_Y4 | kW | 0.0266685 |
| mpi2-x2 | qdot_Y5 | kW | 0.0127908 |
| mpi2-x2 | qdot_Y6 | kW | 0.00113819 |
| mpi2-x2 | qdot_Y7 | kW | 4.49818e-06 |
| mpi2-x2 | qdot_Z1 | kW | 6.14644e-05 |
| mpi2-x2 | qdot_Z2 | kW | 0.00129796 |
| mpi2-x2 | qdot_Z3 | kW | 0.00237536 |
| mpi2-x2 | qdot_Z4 | kW | 0.00444603 |
| mpi2-x2 | qdot_Z5 | kW | 0.0075642 |
| mpi2-x2 | qdot_Z6 | kW | 0.0115457 |
| mpi2-x2 | qdot_Z7 | kW | 0.0111162 |
| mpi2-x2 | radiative_X1 | kW/m2 | 0.0180927 |
| mpi2-x2 | radiative_X2 | kW/m2 | 0.0378575 |
| mpi2-x2 | radiative_X3 | kW/m2 | 0.101961 |
| mpi2-x2 | radiative_X4 | kW/m2 | 2.21412 |
| mpi2-x2 | radiative_X5 | kW/m2 | 0.000324631 |
| mpi2-x2 | radiative_X6 | kW/m2 | 1.23333e-05 |
| mpi2-x2 | radiative_X7 | kW/m2 | 1.68916e-06 |
| mpi2-x2 | radiative_Y1 | kW/m2 | 0.020272 |
| mpi2-x2 | radiative_Y2 | kW/m2 | 0.0409376 |
| mpi2-x2 | radiative_Y3 | kW/m2 | 0.106545 |
| mpi2-x2 | radiative_Y4 | kW/m2 | 0.148872 |
| mpi2-x2 | radiative_Y5 | kW/m2 | 0.00054504 |
| mpi2-x2 | radiative_Y6 | kW/m2 | 1.58013e-05 |
| mpi2-x2 | radiative_Y7 | kW/m2 | 2.25843e-06 |
| mpi2-x2 | radiative_Z1 | kW/m2 | 0.33404 |
| mpi2-x2 | radiative_Z2 | kW/m2 | 0.177249 |
| mpi2-x2 | radiative_Z3 | kW/m2 | 0.121663 |
| mpi2-x2 | radiative_Z4 | kW/m2 | 0.0920235 |
| mpi2-x2 | radiative_Z5 | kW/m2 | 0.396673 |
| mpi2-x2 | radiative_Z6 | kW/m2 | 0.380242 |
| mpi2-x2 | radiative_Z7 | kW/m2 | 0.257923 |
| mpi2-y2 | divergence_X1_hi | 1/s | 6.7463e-06 |
| mpi2-y2 | divergence_X1_lo | 1/s | 5.15113e-06 |
| mpi2-y2 | divergence_X2_hi | 1/s | 0.00318416 |
| mpi2-y2 | divergence_X2_lo | 1/s | 0.00782424 |
| mpi2-y2 | divergence_X3_hi | 1/s | 0.617754 |
| mpi2-y2 | divergence_X3_lo | 1/s | 0.191018 |
| mpi2-y2 | divergence_X4_hi | 1/s | 0.349578 |
| mpi2-y2 | divergence_X4_lo | 1/s | 0.558327 |
| mpi2-y2 | divergence_X5_hi | 1/s | 0.220699 |
| mpi2-y2 | divergence_X5_lo | 1/s | 0.617618 |
| mpi2-y2 | divergence_X6_hi | 1/s | 0.00287045 |
| mpi2-y2 | divergence_X6_lo | 1/s | 0.04134 |
| mpi2-y2 | divergence_X7_hi | 1/s | 8.54093e-06 |
| mpi2-y2 | divergence_X7_lo | 1/s | 1.05532e-05 |
| mpi2-y2 | divergence_Y1_hi | 1/s | 5.44723e-06 |
| mpi2-y2 | divergence_Y1_lo | 1/s | 4.17127e-06 |
| mpi2-y2 | divergence_Y2_hi | 1/s | 0.00365193 |
| mpi2-y2 | divergence_Y2_lo | 1/s | 0.00561055 |
| mpi2-y2 | divergence_Y3_hi | 1/s | 0.61505 |
| mpi2-y2 | divergence_Y3_lo | 1/s | 0.209203 |
| mpi2-y2 | divergence_Y4_hi | 1/s | 0.202223 |
| mpi2-y2 | divergence_Y4_lo | 1/s | 0.272236 |
| mpi2-y2 | divergence_Y5_hi | 1/s | 0.187542 |
| mpi2-y2 | divergence_Y5_lo | 1/s | 0.522544 |
| mpi2-y2 | divergence_Y6_hi | 1/s | 0.00198886 |
| mpi2-y2 | divergence_Y6_lo | 1/s | 0.00820328 |
| mpi2-y2 | divergence_Y7_hi | 1/s | 4.0725e-06 |
| mpi2-y2 | divergence_Y7_lo | 1/s | 5.43778e-06 |
| mpi2-y2 | divergence_Z1_hi | 1/s | 0.0741132 |
| mpi2-y2 | divergence_Z1_lo | 1/s | 0.00668494 |
| mpi2-y2 | divergence_Z2_hi | 1/s | 0.108249 |
| mpi2-y2 | divergence_Z2_lo | 1/s | 0.183552 |
| mpi2-y2 | divergence_Z3_hi | 1/s | 0.139493 |
| mpi2-y2 | divergence_Z3_lo | 1/s | 0.120057 |
| mpi2-y2 | divergence_Z4_hi | 1/s | 0.349578 |
| mpi2-y2 | divergence_Z4_lo | 1/s | 0.389769 |
| mpi2-y2 | divergence_Z5_hi | 1/s | 1.38214 |
| mpi2-y2 | divergence_Z5_lo | 1/s | 1.64128 |
| mpi2-y2 | divergence_Z6_hi | 1/s | 2.36143 |
| mpi2-y2 | divergence_Z6_lo | 1/s | 2.21506 |
| mpi2-y2 | divergence_Z7_hi | 1/s | 2.93324 |
| mpi2-y2 | divergence_Z7_lo | 1/s | 2.85705 |
| mpi2-y2 | enthalpy_local_X1 | kW/m2 | 0.00019978 |
| mpi2-y2 | enthalpy_local_X2 | kW/m2 | 0.13759 |
| mpi2-y2 | enthalpy_local_X3 | kW/m2 | 5.8541 |
| mpi2-y2 | enthalpy_local_X4 | kW/m2 | 5.37301 |
| mpi2-y2 | enthalpy_local_X5 | kW/m2 | 0.39683 |
| mpi2-y2 | enthalpy_local_X6 | kW/m2 | 0.0101375 |
| mpi2-y2 | enthalpy_local_X7 | kW/m2 | 0.000100867 |
| mpi2-y2 | enthalpy_local_Y1 | kW/m2 | 0.000211355 |
| mpi2-y2 | enthalpy_local_Y2 | kW/m2 | 0.162224 |
| mpi2-y2 | enthalpy_local_Y3 | kW/m2 | 3.72334 |
| mpi2-y2 | enthalpy_local_Y4 | kW/m2 | 7.65686 |
| mpi2-y2 | enthalpy_local_Y5 | kW/m2 | 0.649831 |
| mpi2-y2 | enthalpy_local_Y6 | kW/m2 | 0.00541897 |
| mpi2-y2 | enthalpy_local_Y7 | kW/m2 | 0.000103082 |
| mpi2-y2 | enthalpy_local_Z1 | kW/m2 | 0.610868 |
| mpi2-y2 | enthalpy_local_Z2 | kW/m2 | 1.6998 |
| mpi2-y2 | enthalpy_local_Z3 | kW/m2 | 3.45237 |
| mpi2-y2 | enthalpy_local_Z4 | kW/m2 | 5.71507 |
| mpi2-y2 | enthalpy_local_Z5 | kW/m2 | 18.2008 |
| mpi2-y2 | enthalpy_local_Z6 | kW/m2 | 50.9355 |
| mpi2-y2 | enthalpy_local_Z7 | kW/m2 | 85.4144 |
| mpi2-y2 | mass_local_X1 | kg/s/m2 | 0.00195006 |
| mpi2-y2 | mass_local_X2 | kg/s/m2 | 0.00596147 |
| mpi2-y2 | mass_local_X3 | kg/s/m2 | 0.0127277 |
| mpi2-y2 | mass_local_X4 | kg/s/m2 | 0.00345918 |
| mpi2-y2 | mass_local_X5 | kg/s/m2 | 0.0182043 |
| mpi2-y2 | mass_local_X6 | kg/s/m2 | 0.00837695 |
| mpi2-y2 | mass_local_X7 | kg/s/m2 | 0.00288377 |
| mpi2-y2 | mass_local_Y1 | kg/s/m2 | 0.00267528 |
| mpi2-y2 | mass_local_Y2 | kg/s/m2 | 0.00712519 |
| mpi2-y2 | mass_local_Y3 | kg/s/m2 | 0.0127503 |
| mpi2-y2 | mass_local_Y4 | kg/s/m2 | 0.00320475 |
| mpi2-y2 | mass_local_Y5 | kg/s/m2 | 0.0126674 |
| mpi2-y2 | mass_local_Y6 | kg/s/m2 | 0.00739672 |
| mpi2-y2 | mass_local_Y7 | kg/s/m2 | 0.00178041 |
| mpi2-y2 | mass_local_Z1 | kg/s/m2 | 6.33419e-05 |
| mpi2-y2 | mass_local_Z2 | kg/s/m2 | 0.00225092 |
| mpi2-y2 | mass_local_Z3 | kg/s/m2 | 0.00210793 |
| mpi2-y2 | mass_local_Z4 | kg/s/m2 | 0.00476282 |
| mpi2-y2 | mass_local_Z5 | kg/s/m2 | 0.00856956 |
| mpi2-y2 | mass_local_Z6 | kg/s/m2 | 0.0224436 |
| mpi2-y2 | mass_local_Z7 | kg/s/m2 | 0.0341235 |
| mpi2-y2 | mdot_X1 | kg/s | 4.54187e-05 |
| mpi2-y2 | mdot_X2 | kg/s | 6.62783e-05 |
| mpi2-y2 | mdot_X3 | kg/s | 7.67214e-05 |
| mpi2-y2 | mdot_X4 | kg/s | 8.59077e-05 |
| mpi2-y2 | mdot_X5 | kg/s | 6.71369e-05 |
| mpi2-y2 | mdot_X6 | kg/s | 7.46698e-05 |
| mpi2-y2 | mdot_X7 | kg/s | 6.20252e-05 |
| mpi2-y2 | mdot_Y1 | kg/s | 5.35818e-05 |
| mpi2-y2 | mdot_Y2 | kg/s | 7.51525e-05 |
| mpi2-y2 | mdot_Y3 | kg/s | 6.81494e-05 |
| mpi2-y2 | mdot_Y4 | kg/s | 7.57472e-05 |
| mpi2-y2 | mdot_Y5 | kg/s | 9.90136e-05 |
| mpi2-y2 | mdot_Y6 | kg/s | 7.10134e-05 |
| mpi2-y2 | mdot_Y7 | kg/s | 5.58641e-05 |
| mpi2-y2 | mdot_Z1 | kg/s | 1.26629e-06 |
| mpi2-y2 | mdot_Z2 | kg/s | 5.3912e-06 |
| mpi2-y2 | mdot_Z3 | kg/s | 1.0119e-05 |
| mpi2-y2 | mdot_Z4 | kg/s | 2.24323e-05 |
| mpi2-y2 | mdot_Z5 | kg/s | 3.58932e-05 |
| mpi2-y2 | mdot_Z6 | kg/s | 6.33308e-05 |
| mpi2-y2 | mdot_Z7 | kg/s | 0.0001106 |
| mpi2-y2 | pressure_X1_hi | Pa | 0.000816467 |
| mpi2-y2 | pressure_X1_lo | Pa | 0.000592203 |
| mpi2-y2 | pressure_X2_hi | Pa | 0.00322588 |
| mpi2-y2 | pressure_X2_lo | Pa | 0.00221889 |
| mpi2-y2 | pressure_X3_hi | Pa | 0.00840407 |
| mpi2-y2 | pressure_X3_lo | Pa | 0.00655653 |
| mpi2-y2 | pressure_X4_hi | Pa | 0.00681537 |
| mpi2-y2 | pressure_X4_lo | Pa | 0.00654305 |
| mpi2-y2 | pressure_X5_hi | Pa | 0.0065395 |
| mpi2-y2 | pressure_X5_lo | Pa | 0.00741858 |
| mpi2-y2 | pressure_X6_hi | Pa | 0.00185653 |
| mpi2-y2 | pressure_X6_lo | Pa | 0.00224181 |
| mpi2-y2 | pressure_X7_hi | Pa | 0.000636767 |
| mpi2-y2 | pressure_X7_lo | Pa | 0.000865099 |
| mpi2-y2 | pressure_Y1_hi | Pa | 0.000965023 |
| mpi2-y2 | pressure_Y1_lo | Pa | 0.000693513 |
| mpi2-y2 | pressure_Y2_hi | Pa | 0.00338215 |
| mpi2-y2 | pressure_Y2_lo | Pa | 0.00237286 |
| mpi2-y2 | pressure_Y3_hi | Pa | 0.00756977 |
| mpi2-y2 | pressure_Y3_lo | Pa | 0.00691936 |
| mpi2-y2 | pressure_Y4_hi | Pa | 0.00667416 |
| mpi2-y2 | pressure_Y4_lo | Pa | 0.00663619 |
| mpi2-y2 | pressure_Y5_hi | Pa | 0.00673047 |
| mpi2-y2 | pressure_Y5_lo | Pa | 0.00798327 |
| mpi2-y2 | pressure_Y6_hi | Pa | 0.00194395 |
| mpi2-y2 | pressure_Y6_lo | Pa | 0.00261535 |
| mpi2-y2 | pressure_Y7_hi | Pa | 0.000625996 |
| mpi2-y2 | pressure_Y7_lo | Pa | 0.000855708 |
| mpi2-y2 | pressure_Z1_hi | Pa | 0.00107458 |
| mpi2-y2 | pressure_Z1_lo | Pa | 0.00350942 |
| mpi2-y2 | pressure_Z2_hi | Pa | 0.00162433 |
| mpi2-y2 | pressure_Z2_lo | Pa | 0.0014223 |
| mpi2-y2 | pressure_Z3_hi | Pa | 0.00234342 |
| mpi2-y2 | pressure_Z3_lo | Pa | 0.00209145 |
| mpi2-y2 | pressure_Z4_hi | Pa | 0.00681537 |
| mpi2-y2 | pressure_Z4_lo | Pa | 0.00647123 |
| mpi2-y2 | pressure_Z5_hi | Pa | 0.00920327 |
| mpi2-y2 | pressure_Z5_lo | Pa | 0.00864951 |
| mpi2-y2 | pressure_Z6_hi | Pa | 0.0150543 |
| mpi2-y2 | pressure_Z6_lo | Pa | 0.0142571 |
| mpi2-y2 | pressure_Z7_hi | Pa | 0.0185282 |
| mpi2-y2 | pressure_Z7_lo | Pa | 0.0175298 |
| mpi2-y2 | probe_O2 | mol/mol | 0.000626544 |
| mpi2-y2 | probe_T | C | 5.27421 |
| mpi2-y2 | qdot_X1 | kW | 3.03868e-06 |
| mpi2-y2 | qdot_X2 | kW | 0.000261561 |
| mpi2-y2 | qdot_X3 | kW | 0.00883627 |
| mpi2-y2 | qdot_X4 | kW | 0.0203636 |
| mpi2-y2 | qdot_X5 | kW | 0.00888121 |
| mpi2-y2 | qdot_X6 | kW | 0.000527533 |
| mpi2-y2 | qdot_X7 | kW | 1.77265e-05 |
| mpi2-y2 | qdot_Y1 | kW | 3.01273e-06 |
| mpi2-y2 | qdot_Y2 | kW | 0.00068188 |
| mpi2-y2 | qdot_Y3 | kW | 0.0110753 |
| mpi2-y2 | qdot_Y4 | kW | 0.02298 |
| mpi2-y2 | qdot_Y5 | kW | 0.0115115 |
| mpi2-y2 | qdot_Y6 | kW | 0.00102258 |
| mpi2-y2 | qdot_Y7 | kW | 4.59662e-06 |
| mpi2-y2 | qdot_Z1 | kW | 6.17197e-05 |
| mpi2-y2 | qdot_Z2 | kW | 0.00174645 |
| mpi2-y2 | qdot_Z3 | kW | 0.00173936 |
| mpi2-y2 | qdot_Z4 | kW | 0.00381465 |
| mpi2-y2 | qdot_Z5 | kW | 0.00579947 |
| mpi2-y2 | qdot_Z6 | kW | 0.0101461 |
| mpi2-y2 | qdot_Z7 | kW | 0.00962722 |
| mpi2-y2 | radiative_X1 | kW/m2 | 0.0144885 |
| mpi2-y2 | radiative_X2 | kW/m2 | 0.0318053 |
| mpi2-y2 | radiative_X3 | kW/m2 | 0.101694 |
| mpi2-y2 | radiative_X4 | kW/m2 | 0.105154 |
| mpi2-y2 | radiative_X5 | kW/m2 | 0.000514248 |
| mpi2-y2 | radiative_X6 | kW/m2 | 2.24618e-05 |
| mpi2-y2 | radiative_X7 | kW/m2 | 3.21933e-06 |
| mpi2-y2 | radiative_Y1 | kW/m2 | 0.0138276 |
| mpi2-y2 | radiative_Y2 | kW/m2 | 0.0278412 |
| mpi2-y2 | radiative_Y3 | kW/m2 | 0.0797101 |
| mpi2-y2 | radiative_Y4 | kW/m2 | 2.20674 |
| mpi2-y2 | radiative_Y5 | kW/m2 | 0.000360953 |
| mpi2-y2 | radiative_Y6 | kW/m2 | 7.04858e-06 |
| mpi2-y2 | radiative_Y7 | kW/m2 | 9.4861e-07 |
| mpi2-y2 | radiative_Z1 | kW/m2 | 0.452166 |
| mpi2-y2 | radiative_Z2 | kW/m2 | 0.123516 |
| mpi2-y2 | radiative_Z3 | kW/m2 | 0.106001 |
| mpi2-y2 | radiative_Z4 | kW/m2 | 0.0836231 |
| mpi2-y2 | radiative_Z5 | kW/m2 | 0.272322 |
| mpi2-y2 | radiative_Z6 | kW/m2 | 0.301325 |
| mpi2-y2 | radiative_Z7 | kW/m2 | 0.208762 |
| mpi4-x4 | divergence_X1_hi | 1/s | 1.08183e-05 |
| mpi4-x4 | divergence_X1_lo | 1/s | 8.14587e-06 |
| mpi4-x4 | divergence_X2_hi | 1/s | 0.055194 |
| mpi4-x4 | divergence_X2_lo | 1/s | 0.00610532 |
| mpi4-x4 | divergence_X3_hi | 1/s | 0.572514 |
| mpi4-x4 | divergence_X3_lo | 1/s | 0.210077 |
| mpi4-x4 | divergence_X4_hi | 1/s | 0.25114 |
| mpi4-x4 | divergence_X4_lo | 1/s | 0.308858 |
| mpi4-x4 | divergence_X5_hi | 1/s | 0.293182 |
| mpi4-x4 | divergence_X5_lo | 1/s | 0.893341 |
| mpi4-x4 | divergence_X6_hi | 1/s | 0.00811337 |
| mpi4-x4 | divergence_X6_lo | 1/s | 0.00611303 |
| mpi4-x4 | divergence_X7_hi | 1/s | 8.11473e-06 |
| mpi4-x4 | divergence_X7_lo | 1/s | 1.05294e-05 |
| mpi4-x4 | divergence_Y1_hi | 1/s | 9.90306e-06 |
| mpi4-x4 | divergence_Y1_lo | 1/s | 7.181e-06 |
| mpi4-x4 | divergence_Y2_hi | 1/s | 0.0172144 |
| mpi4-x4 | divergence_Y2_lo | 1/s | 0.00421739 |
| mpi4-x4 | divergence_Y3_hi | 1/s | 0.539022 |
| mpi4-x4 | divergence_Y3_lo | 1/s | 0.252909 |
| mpi4-x4 | divergence_Y4_hi | 1/s | 0.264221 |
| mpi4-x4 | divergence_Y4_lo | 1/s | 0.307096 |
| mpi4-x4 | divergence_Y5_hi | 1/s | 0.280427 |
| mpi4-x4 | divergence_Y5_lo | 1/s | 0.700884 |
| mpi4-x4 | divergence_Y6_hi | 1/s | 0.00691665 |
| mpi4-x4 | divergence_Y6_lo | 1/s | 0.00293502 |
| mpi4-x4 | divergence_Y7_hi | 1/s | 6.62841e-06 |
| mpi4-x4 | divergence_Y7_lo | 1/s | 8.89101e-06 |
| mpi4-x4 | divergence_Z1_hi | 1/s | 0.204651 |
| mpi4-x4 | divergence_Z1_lo | 1/s | 0.0149306 |
| mpi4-x4 | divergence_Z2_hi | 1/s | 0.112075 |
| mpi4-x4 | divergence_Z2_lo | 1/s | 0.0852625 |
| mpi4-x4 | divergence_Z3_hi | 1/s | 0.195563 |
| mpi4-x4 | divergence_Z3_lo | 1/s | 0.385271 |
| mpi4-x4 | divergence_Z4_hi | 1/s | 0.264221 |
| mpi4-x4 | divergence_Z4_lo | 1/s | 0.277515 |
| mpi4-x4 | divergence_Z5_hi | 1/s | 1.6406 |
| mpi4-x4 | divergence_Z5_lo | 1/s | 1.96274 |
| mpi4-x4 | divergence_Z6_hi | 1/s | 2.4504 |
| mpi4-x4 | divergence_Z6_lo | 1/s | 2.3586 |
| mpi4-x4 | divergence_Z7_hi | 1/s | 2.62684 |
| mpi4-x4 | divergence_Z7_lo | 1/s | 2.62496 |
| mpi4-x4 | enthalpy_local_X1 | kW/m2 | 0.000252543 |
| mpi4-x4 | enthalpy_local_X2 | kW/m2 | 0.415664 |
| mpi4-x4 | enthalpy_local_X3 | kW/m2 | 5.23101 |
| mpi4-x4 | enthalpy_local_X4 | kW/m2 | 7.56153 |
| mpi4-x4 | enthalpy_local_X5 | kW/m2 | 0.419135 |
| mpi4-x4 | enthalpy_local_X6 | kW/m2 | 0.0563042 |
| mpi4-x4 | enthalpy_local_X7 | kW/m2 | 0.000717837 |
| mpi4-x4 | enthalpy_local_Y1 | kW/m2 | 0.000239385 |
| mpi4-x4 | enthalpy_local_Y2 | kW/m2 | 0.0204818 |
| mpi4-x4 | enthalpy_local_Y3 | kW/m2 | 5.50567 |
| mpi4-x4 | enthalpy_local_Y4 | kW/m2 | 5.13004 |
| mpi4-x4 | enthalpy_local_Y5 | kW/m2 | 1.1136 |
| mpi4-x4 | enthalpy_local_Y6 | kW/m2 | 0.0228306 |
| mpi4-x4 | enthalpy_local_Y7 | kW/m2 | 0.00011409 |
| mpi4-x4 | enthalpy_local_Z1 | kW/m2 | 0.327279 |
| mpi4-x4 | enthalpy_local_Z2 | kW/m2 | 2.17579 |
| mpi4-x4 | enthalpy_local_Z3 | kW/m2 | 6.80912 |
| mpi4-x4 | enthalpy_local_Z4 | kW/m2 | 9.52767 |
| mpi4-x4 | enthalpy_local_Z5 | kW/m2 | 26.9101 |
| mpi4-x4 | enthalpy_local_Z6 | kW/m2 | 62.8163 |
| mpi4-x4 | enthalpy_local_Z7 | kW/m2 | 89.4209 |
| mpi4-x4 | mass_local_X1 | kg/s/m2 | 0.00515533 |
| mpi4-x4 | mass_local_X2 | kg/s/m2 | 0.0188531 |
| mpi4-x4 | mass_local_X3 | kg/s/m2 | 0.0138137 |
| mpi4-x4 | mass_local_X4 | kg/s/m2 | 0.00252801 |
| mpi4-x4 | mass_local_X5 | kg/s/m2 | 0.027076 |
| mpi4-x4 | mass_local_X6 | kg/s/m2 | 0.0121802 |
| mpi4-x4 | mass_local_X7 | kg/s/m2 | 0.00285086 |
| mpi4-x4 | mass_local_Y1 | kg/s/m2 | 0.00248194 |
| mpi4-x4 | mass_local_Y2 | kg/s/m2 | 0.00605506 |
| mpi4-x4 | mass_local_Y3 | kg/s/m2 | 0.0126738 |
| mpi4-x4 | mass_local_Y4 | kg/s/m2 | 0.00289519 |
| mpi4-x4 | mass_local_Y5 | kg/s/m2 | 0.0189087 |
| mpi4-x4 | mass_local_Y6 | kg/s/m2 | 0.0139688 |
| mpi4-x4 | mass_local_Y7 | kg/s/m2 | 0.00390138 |
| mpi4-x4 | mass_local_Z1 | kg/s/m2 | 8.73935e-05 |
| mpi4-x4 | mass_local_Z2 | kg/s/m2 | 0.00325867 |
| mpi4-x4 | mass_local_Z3 | kg/s/m2 | 0.00418775 |
| mpi4-x4 | mass_local_Z4 | kg/s/m2 | 0.00536871 |
| mpi4-x4 | mass_local_Z5 | kg/s/m2 | 0.00896979 |
| mpi4-x4 | mass_local_Z6 | kg/s/m2 | 0.0279776 |
| mpi4-x4 | mass_local_Z7 | kg/s/m2 | 0.0439094 |
| mpi4-x4 | mdot_X1 | kg/s | 3.76239e-05 |
| mpi4-x4 | mdot_X2 | kg/s | 5.10442e-05 |
| mpi4-x4 | mdot_X3 | kg/s | 7.56797e-05 |
| mpi4-x4 | mdot_X4 | kg/s | 0.000115551 |
| mpi4-x4 | mdot_X5 | kg/s | 7.3086e-05 |
| mpi4-x4 | mdot_X6 | kg/s | 9.03871e-05 |
| mpi4-x4 | mdot_X7 | kg/s | 7.62331e-05 |
| mpi4-x4 | mdot_Y1 | kg/s | 6.86584e-05 |
| mpi4-x4 | mdot_Y2 | kg/s | 8.92177e-05 |
| mpi4-x4 | mdot_Y3 | kg/s | 7.05033e-05 |
| mpi4-x4 | mdot_Y4 | kg/s | 9.51417e-05 |
| mpi4-x4 | mdot_Y5 | kg/s | 8.54164e-05 |
| mpi4-x4 | mdot_Y6 | kg/s | 6.48902e-05 |
| mpi4-x4 | mdot_Y7 | kg/s | 5.13996e-05 |
| mpi4-x4 | mdot_Z1 | kg/s | 2.43689e-06 |
| mpi4-x4 | mdot_Z2 | kg/s | 6.80068e-06 |
| mpi4-x4 | mdot_Z3 | kg/s | 1.58317e-05 |
| mpi4-x4 | mdot_Z4 | kg/s | 3.14553e-05 |
| mpi4-x4 | mdot_Z5 | kg/s | 4.41669e-05 |
| mpi4-x4 | mdot_Z6 | kg/s | 6.01763e-05 |
| mpi4-x4 | mdot_Z7 | kg/s | 0.000101891 |
| mpi4-x4 | pressure_X1_hi | Pa | 0.00174665 |
| mpi4-x4 | pressure_X1_lo | Pa | 0.00124839 |
| mpi4-x4 | pressure_X2_hi | Pa | 0.00698095 |
| mpi4-x4 | pressure_X2_lo | Pa | 0.00474108 |
| mpi4-x4 | pressure_X3_hi | Pa | 0.0103432 |
| mpi4-x4 | pressure_X3_lo | Pa | 0.00900681 |
| mpi4-x4 | pressure_X4_hi | Pa | 0.00791738 |
| mpi4-x4 | pressure_X4_lo | Pa | 0.007589 |
| mpi4-x4 | pressure_X5_hi | Pa | 0.0070673 |
| mpi4-x4 | pressure_X5_lo | Pa | 0.00943648 |
| mpi4-x4 | pressure_X6_hi | Pa | 0.00207778 |
| mpi4-x4 | pressure_X6_lo | Pa | 0.00256403 |
| mpi4-x4 | pressure_X7_hi | Pa | 0.000768682 |
| mpi4-x4 | pressure_X7_lo | Pa | 0.00102063 |
| mpi4-x4 | pressure_Y1_hi | Pa | 0.00108724 |
| mpi4-x4 | pressure_Y1_lo | Pa | 0.000811472 |
| mpi4-x4 | pressure_Y2_hi | Pa | 0.00296845 |
| mpi4-x4 | pressure_Y2_lo | Pa | 0.00224772 |
| mpi4-x4 | pressure_Y3_hi | Pa | 0.00720187 |
| mpi4-x4 | pressure_Y3_lo | Pa | 0.00579034 |
| mpi4-x4 | pressure_Y4_hi | Pa | 0.00798898 |
| mpi4-x4 | pressure_Y4_lo | Pa | 0.00801668 |
| mpi4-x4 | pressure_Y5_hi | Pa | 0.00893171 |
| mpi4-x4 | pressure_Y5_lo | Pa | 0.0102844 |
| mpi4-x4 | pressure_Y6_hi | Pa | 0.004574 |
| mpi4-x4 | pressure_Y6_lo | Pa | 0.00657415 |
| mpi4-x4 | pressure_Y7_hi | Pa | 0.00127958 |
| mpi4-x4 | pressure_Y7_lo | Pa | 0.00177986 |
| mpi4-x4 | pressure_Z1_hi | Pa | 0.00137283 |
| mpi4-x4 | pressure_Z1_lo | Pa | 0.00384224 |
| mpi4-x4 | pressure_Z2_hi | Pa | 0.00131563 |
| mpi4-x4 | pressure_Z2_lo | Pa | 0.00105026 |
| mpi4-x4 | pressure_Z3_hi | Pa | 0.00343674 |
| mpi4-x4 | pressure_Z3_lo | Pa | 0.00317713 |
| mpi4-x4 | pressure_Z4_hi | Pa | 0.00798898 |
| mpi4-x4 | pressure_Z4_lo | Pa | 0.00766212 |
| mpi4-x4 | pressure_Z5_hi | Pa | 0.0106592 |
| mpi4-x4 | pressure_Z5_lo | Pa | 0.01073 |
| mpi4-x4 | pressure_Z6_hi | Pa | 0.0137692 |
| mpi4-x4 | pressure_Z6_lo | Pa | 0.0129265 |
| mpi4-x4 | pressure_Z7_hi | Pa | 0.0180469 |
| mpi4-x4 | pressure_Z7_lo | Pa | 0.0182647 |
| mpi4-x4 | probe_O2 | mol/mol | 0.000666453 |
| mpi4-x4 | probe_T | C | 7.47995 |
| mpi4-x4 | qdot_X1 | kW | 2.72073e-06 |
| mpi4-x4 | qdot_X2 | kW | 0.000280824 |
| mpi4-x4 | qdot_X3 | kW | 0.0116094 |
| mpi4-x4 | qdot_X4 | kW | 0.0244346 |
| mpi4-x4 | qdot_X5 | kW | 0.0121091 |
| mpi4-x4 | qdot_X6 | kW | 0.00129632 |
| mpi4-x4 | qdot_X7 | kW | 2.30386e-05 |
| mpi4-x4 | qdot_Y1 | kW | 3.10032e-06 |
| mpi4-x4 | qdot_Y2 | kW | 0.000780383 |
| mpi4-x4 | qdot_Y3 | kW | 0.0113662 |
| mpi4-x4 | qdot_Y4 | kW | 0.0286986 |
| mpi4-x4 | qdot_Y5 | kW | 0.00914342 |
| mpi4-x4 | qdot_Y6 | kW | 0.000917068 |
| mpi4-x4 | qdot_Y7 | kW | 9.30021e-06 |
| mpi4-x4 | qdot_Z1 | kW | 5.41537e-05 |
| mpi4-x4 | qdot_Z2 | kW | 0.000868907 |
| mpi4-x4 | qdot_Z3 | kW | 0.00241208 |
| mpi4-x4 | qdot_Z4 | kW | 0.00498116 |
| mpi4-x4 | qdot_Z5 | kW | 0.00848143 |
| mpi4-x4 | qdot_Z6 | kW | 0.0100685 |
| mpi4-x4 | qdot_Z7 | kW | 0.011295 |
| mpi4-x4 | radiative_X1 | kW/m2 | 0.0266392 |
| mpi4-x4 | radiative_X2 | kW/m2 | 0.384284 |
| mpi4-x4 | radiative_X3 | kW/m2 | 0.101621 |
| mpi4-x4 | radiative_X4 | kW/m2 | 2.2447 |
| mpi4-x4 | radiative_X5 | kW/m2 | 0.000482492 |
| mpi4-x4 | radiative_X6 | kW/m2 | 0.000177307 |
| mpi4-x4 | radiative_X7 | kW/m2 | 7.52612e-05 |
| mpi4-x4 | radiative_Y1 | kW/m2 | 0.0204473 |
| mpi4-x4 | radiative_Y2 | kW/m2 | 0.0418316 |
| mpi4-x4 | radiative_Y3 | kW/m2 | 0.112379 |
| mpi4-x4 | radiative_Y4 | kW/m2 | 0.11677 |
| mpi4-x4 | radiative_Y5 | kW/m2 | 0.00076174 |
| mpi4-x4 | radiative_Y6 | kW/m2 | 2.71649e-05 |
| mpi4-x4 | radiative_Y7 | kW/m2 | 3.64775e-06 |
| mpi4-x4 | radiative_Z1 | kW/m2 | 0.186601 |
| mpi4-x4 | radiative_Z2 | kW/m2 | 0.165205 |
| mpi4-x4 | radiative_Z3 | kW/m2 | 0.149642 |
| mpi4-x4 | radiative_Z4 | kW/m2 | 0.108695 |
| mpi4-x4 | radiative_Z5 | kW/m2 | 0.346186 |
| mpi4-x4 | radiative_Z6 | kW/m2 | 0.397107 |
| mpi4-x4 | radiative_Z7 | kW/m2 | 0.265215 |
| mpi4-xy22 | divergence_X1_hi | 1/s | 8.26964e-06 |
| mpi4-xy22 | divergence_X1_lo | 1/s | 6.11656e-06 |
| mpi4-xy22 | divergence_X2_hi | 1/s | 0.0452361 |
| mpi4-xy22 | divergence_X2_lo | 1/s | 0.00890297 |
| mpi4-xy22 | divergence_X3_hi | 1/s | 0.724582 |
| mpi4-xy22 | divergence_X3_lo | 1/s | 0.282205 |
| mpi4-xy22 | divergence_X4_hi | 1/s | 0.331426 |
| mpi4-xy22 | divergence_X4_lo | 1/s | 0.318912 |
| mpi4-xy22 | divergence_X5_hi | 1/s | 0.270045 |
| mpi4-xy22 | divergence_X5_lo | 1/s | 0.755165 |
| mpi4-xy22 | divergence_X6_hi | 1/s | 0.00374153 |
| mpi4-xy22 | divergence_X6_lo | 1/s | 0.023079 |
| mpi4-xy22 | divergence_X7_hi | 1/s | 8.87941e-06 |
| mpi4-xy22 | divergence_X7_lo | 1/s | 8.99749e-06 |
| mpi4-xy22 | divergence_Y1_hi | 1/s | 7.85474e-06 |
| mpi4-xy22 | divergence_Y1_lo | 1/s | 6.67822e-06 |
| mpi4-xy22 | divergence_Y2_hi | 1/s | 0.00847703 |
| mpi4-xy22 | divergence_Y2_lo | 1/s | 0.00929159 |
| mpi4-xy22 | divergence_Y3_hi | 1/s | 0.556677 |
| mpi4-xy22 | divergence_Y3_lo | 1/s | 0.239587 |
| mpi4-xy22 | divergence_Y4_hi | 1/s | 0.260006 |
| mpi4-xy22 | divergence_Y4_lo | 1/s | 0.260052 |
| mpi4-xy22 | divergence_Y5_hi | 1/s | 0.244811 |
| mpi4-xy22 | divergence_Y5_lo | 1/s | 0.544085 |
| mpi4-xy22 | divergence_Y6_hi | 1/s | 0.00953712 |
| mpi4-xy22 | divergence_Y6_lo | 1/s | 0.0324619 |
| mpi4-xy22 | divergence_Y7_hi | 1/s | 7.6316e-06 |
| mpi4-xy22 | divergence_Y7_lo | 1/s | 8.0603e-06 |
| mpi4-xy22 | divergence_Z1_hi | 1/s | 0.143339 |
| mpi4-xy22 | divergence_Z1_lo | 1/s | 0.00511447 |
| mpi4-xy22 | divergence_Z2_hi | 1/s | 0.101793 |
| mpi4-xy22 | divergence_Z2_lo | 1/s | 0.113824 |
| mpi4-xy22 | divergence_Z3_hi | 1/s | 0.140426 |
| mpi4-xy22 | divergence_Z3_lo | 1/s | 0.132787 |
| mpi4-xy22 | divergence_Z4_hi | 1/s | 0.293151 |
| mpi4-xy22 | divergence_Z4_lo | 1/s | 0.347069 |
| mpi4-xy22 | divergence_Z5_hi | 1/s | 1.57602 |
| mpi4-xy22 | divergence_Z5_lo | 1/s | 1.77736 |
| mpi4-xy22 | divergence_Z6_hi | 1/s | 1.70876 |
| mpi4-xy22 | divergence_Z6_lo | 1/s | 1.58726 |
| mpi4-xy22 | divergence_Z7_hi | 1/s | 3.05319 |
| mpi4-xy22 | divergence_Z7_lo | 1/s | 2.98614 |
| mpi4-xy22 | enthalpy_local_X1 | kW/m2 | 0.000310422 |
| mpi4-xy22 | enthalpy_local_X2 | kW/m2 | 0.807448 |
| mpi4-xy22 | enthalpy_local_X3 | kW/m2 | 5.09174 |
| mpi4-xy22 | enthalpy_local_X4 | kW/m2 | 8.85606 |
| mpi4-xy22 | enthalpy_local_X5 | kW/m2 | 0.753171 |
| mpi4-xy22 | enthalpy_local_X6 | kW/m2 | 0.00658035 |
| mpi4-xy22 | enthalpy_local_X7 | kW/m2 | 0.000183768 |
| mpi4-xy22 | enthalpy_local_Y1 | kW/m2 | 0.000288047 |
| mpi4-xy22 | enthalpy_local_Y2 | kW/m2 | 0.0137587 |
| mpi4-xy22 | enthalpy_local_Y3 | kW/m2 | 3.80274 |
| mpi4-xy22 | enthalpy_local_Y4 | kW/m2 | 7.92696 |
| mpi4-xy22 | enthalpy_local_Y5 | kW/m2 | 1.03685 |
| mpi4-xy22 | enthalpy_local_Y6 | kW/m2 | 0.0120632 |
| mpi4-xy22 | enthalpy_local_Y7 | kW/m2 | 0.000147298 |
| mpi4-xy22 | enthalpy_local_Z1 | kW/m2 | 0.497249 |
| mpi4-xy22 | enthalpy_local_Z2 | kW/m2 | 2.27087 |
| mpi4-xy22 | enthalpy_local_Z3 | kW/m2 | 5.16234 |
| mpi4-xy22 | enthalpy_local_Z4 | kW/m2 | 7.78309 |
| mpi4-xy22 | enthalpy_local_Z5 | kW/m2 | 20.7012 |
| mpi4-xy22 | enthalpy_local_Z6 | kW/m2 | 41.1173 |
| mpi4-xy22 | enthalpy_local_Z7 | kW/m2 | 109.083 |
| mpi4-xy22 | mass_local_X1 | kg/s/m2 | 0.0033404 |
| mpi4-xy22 | mass_local_X2 | kg/s/m2 | 0.0128313 |
| mpi4-xy22 | mass_local_X3 | kg/s/m2 | 0.0145945 |
| mpi4-xy22 | mass_local_X4 | kg/s/m2 | 0.00359872 |
| mpi4-xy22 | mass_local_X5 | kg/s/m2 | 0.019178 |
| mpi4-xy22 | mass_local_X6 | kg/s/m2 | 0.0170698 |
| mpi4-xy22 | mass_local_X7 | kg/s/m2 | 0.0030117 |
| mpi4-xy22 | mass_local_Y1 | kg/s/m2 | 0.00186323 |
| mpi4-xy22 | mass_local_Y2 | kg/s/m2 | 0.00416721 |
| mpi4-xy22 | mass_local_Y3 | kg/s/m2 | 0.0106847 |
| mpi4-xy22 | mass_local_Y4 | kg/s/m2 | 0.00329149 |
| mpi4-xy22 | mass_local_Y5 | kg/s/m2 | 0.0165208 |
| mpi4-xy22 | mass_local_Y6 | kg/s/m2 | 0.0095938 |
| mpi4-xy22 | mass_local_Y7 | kg/s/m2 | 0.00215611 |
| mpi4-xy22 | mass_local_Z1 | kg/s/m2 | 3.37966e-05 |
| mpi4-xy22 | mass_local_Z2 | kg/s/m2 | 0.00230057 |
| mpi4-xy22 | mass_local_Z3 | kg/s/m2 | 0.00244041 |
| mpi4-xy22 | mass_local_Z4 | kg/s/m2 | 0.00590091 |
| mpi4-xy22 | mass_local_Z5 | kg/s/m2 | 0.0102195 |
| mpi4-xy22 | mass_local_Z6 | kg/s/m2 | 0.0246821 |
| mpi4-xy22 | mass_local_Z7 | kg/s/m2 | 0.0348416 |
| mpi4-xy22 | mdot_X1 | kg/s | 4.88967e-05 |
| mpi4-xy22 | mdot_X2 | kg/s | 6.15606e-05 |
| mpi4-xy22 | mdot_X3 | kg/s | 7.61495e-05 |
| mpi4-xy22 | mdot_X4 | kg/s | 9.65819e-05 |
| mpi4-xy22 | mdot_X5 | kg/s | 7.17498e-05 |
| mpi4-xy22 | mdot_X6 | kg/s | 7.17328e-05 |
| mpi4-xy22 | mdot_X7 | kg/s | 5.76529e-05 |
| mpi4-xy22 | mdot_Y1 | kg/s | 6.28843e-05 |
| mpi4-xy22 | mdot_Y2 | kg/s | 7.92343e-05 |
| mpi4-xy22 | mdot_Y3 | kg/s | 8.382e-05 |
| mpi4-xy22 | mdot_Y4 | kg/s | 9.11195e-05 |
| mpi4-xy22 | mdot_Y5 | kg/s | 8.23063e-05 |
| mpi4-xy22 | mdot_Y6 | kg/s | 7.10225e-05 |
| mpi4-xy22 | mdot_Y7 | kg/s | 5.84298e-05 |
| mpi4-xy22 | mdot_Z1 | kg/s | 1.63157e-06 |
| mpi4-xy22 | mdot_Z2 | kg/s | 6.55463e-06 |
| mpi4-xy22 | mdot_Z3 | kg/s | 9.07453e-06 |
| mpi4-xy22 | mdot_Z4 | kg/s | 2.31824e-05 |
| mpi4-xy22 | mdot_Z5 | kg/s | 4.12389e-05 |
| mpi4-xy22 | mdot_Z6 | kg/s | 7.46188e-05 |
| mpi4-xy22 | mdot_Z7 | kg/s | 0.000122951 |
| mpi4-xy22 | pressure_X1_hi | Pa | 0.00140642 |
| mpi4-xy22 | pressure_X1_lo | Pa | 0.00103226 |
| mpi4-xy22 | pressure_X2_hi | Pa | 0.00462064 |
| mpi4-xy22 | pressure_X2_lo | Pa | 0.00315633 |
| mpi4-xy22 | pressure_X3_hi | Pa | 0.0104851 |
| mpi4-xy22 | pressure_X3_lo | Pa | 0.00890443 |
| mpi4-xy22 | pressure_X4_hi | Pa | 0.00878618 |
| mpi4-xy22 | pressure_X4_lo | Pa | 0.00859723 |
| mpi4-xy22 | pressure_X5_hi | Pa | 0.0087311 |
| mpi4-xy22 | pressure_X5_lo | Pa | 0.00997033 |
| mpi4-xy22 | pressure_X6_hi | Pa | 0.00278209 |
| mpi4-xy22 | pressure_X6_lo | Pa | 0.00383482 |
| mpi4-xy22 | pressure_X7_hi | Pa | 0.00084139 |
| mpi4-xy22 | pressure_X7_lo | Pa | 0.00114159 |
| mpi4-xy22 | pressure_Y1_hi | Pa | 0.00125048 |
| mpi4-xy22 | pressure_Y1_lo | Pa | 0.000911009 |
| mpi4-xy22 | pressure_Y2_hi | Pa | 0.00373531 |
| mpi4-xy22 | pressure_Y2_lo | Pa | 0.00287399 |
| mpi4-xy22 | pressure_Y3_hi | Pa | 0.0110095 |
| mpi4-xy22 | pressure_Y3_lo | Pa | 0.00956577 |
| mpi4-xy22 | pressure_Y4_hi | Pa | 0.00902857 |
| mpi4-xy22 | pressure_Y4_lo | Pa | 0.00916582 |
| mpi4-xy22 | pressure_Y5_hi | Pa | 0.00868335 |
| mpi4-xy22 | pressure_Y5_lo | Pa | 0.00993262 |
| mpi4-xy22 | pressure_Y6_hi | Pa | 0.00310238 |
| mpi4-xy22 | pressure_Y6_lo | Pa | 0.00403726 |
| mpi4-xy22 | pressure_Y7_hi | Pa | 0.000912226 |
| mpi4-xy22 | pressure_Y7_lo | Pa | 0.00124554 |
| mpi4-xy22 | pressure_Z1_hi | Pa | 0.00138022 |
| mpi4-xy22 | pressure_Z1_lo | Pa | 0.00523354 |
| mpi4-xy22 | pressure_Z2_hi | Pa | 0.00177981 |
| mpi4-xy22 | pressure_Z2_lo | Pa | 0.00158615 |
| mpi4-xy22 | pressure_Z3_hi | Pa | 0.00321364 |
| mpi4-xy22 | pressure_Z3_lo | Pa | 0.00279695 |
| mpi4-xy22 | pressure_Z4_hi | Pa | 0.0092183 |
| mpi4-xy22 | pressure_Z4_lo | Pa | 0.00860823 |
| mpi4-xy22 | pressure_Z5_hi | Pa | 0.0132239 |
| mpi4-xy22 | pressure_Z5_lo | Pa | 0.0127368 |
| mpi4-xy22 | pressure_Z6_hi | Pa | 0.0156771 |
| mpi4-xy22 | pressure_Z6_lo | Pa | 0.015062 |
| mpi4-xy22 | pressure_Z7_hi | Pa | 0.0164828 |
| mpi4-xy22 | pressure_Z7_lo | Pa | 0.0163927 |
| mpi4-xy22 | probe_O2 | mol/mol | 0.000536327 |
| mpi4-xy22 | probe_T | C | 5.96876 |
| mpi4-xy22 | qdot_X1 | kW | 4.94661e-06 |
| mpi4-xy22 | qdot_X2 | kW | 0.000643202 |
| mpi4-xy22 | qdot_X3 | kW | 0.0121259 |
| mpi4-xy22 | qdot_X4 | kW | 0.0272104 |
| mpi4-xy22 | qdot_X5 | kW | 0.0108691 |
| mpi4-xy22 | qdot_X6 | kW | 0.000669073 |
| mpi4-xy22 | qdot_X7 | kW | 5.09374e-06 |
| mpi4-xy22 | qdot_Y1 | kW | 4.52537e-06 |
| mpi4-xy22 | qdot_Y2 | kW | 0.000784375 |
| mpi4-xy22 | qdot_Y3 | kW | 0.0115521 |
| mpi4-xy22 | qdot_Y4 | kW | 0.0226592 |
| mpi4-xy22 | qdot_Y5 | kW | 0.00940919 |
| mpi4-xy22 | qdot_Y6 | kW | 0.000735195 |
| mpi4-xy22 | qdot_Y7 | kW | 5.18768e-06 |
| mpi4-xy22 | qdot_Z1 | kW | 7.15243e-05 |
| mpi4-xy22 | qdot_Z2 | kW | 0.00142902 |
| mpi4-xy22 | qdot_Z3 | kW | 0.00313186 |
| mpi4-xy22 | qdot_Z4 | kW | 0.00586257 |
| mpi4-xy22 | qdot_Z5 | kW | 0.00994269 |
| mpi4-xy22 | qdot_Z6 | kW | 0.0120245 |
| mpi4-xy22 | qdot_Z7 | kW | 0.0138431 |
| mpi4-xy22 | radiative_X1 | kW/m2 | 0.0220078 |
| mpi4-xy22 | radiative_X2 | kW/m2 | 0.0448845 |
| mpi4-xy22 | radiative_X3 | kW/m2 | 0.113003 |
| mpi4-xy22 | radiative_X4 | kW/m2 | 2.22177 |
| mpi4-xy22 | radiative_X5 | kW/m2 | 0.00116507 |
| mpi4-xy22 | radiative_X6 | kW/m2 | 3.17559e-05 |
| mpi4-xy22 | radiative_X7 | kW/m2 | 4.45656e-06 |
| mpi4-xy22 | radiative_Y1 | kW/m2 | 0.0234878 |
| mpi4-xy22 | radiative_Y2 | kW/m2 | 0.0462262 |
| mpi4-xy22 | radiative_Y3 | kW/m2 | 0.109949 |
| mpi4-xy22 | radiative_Y4 | kW/m2 | 2.1868 |
| mpi4-xy22 | radiative_Y5 | kW/m2 | 0.00064448 |
| mpi4-xy22 | radiative_Y6 | kW/m2 | 2.12024e-05 |
| mpi4-xy22 | radiative_Y7 | kW/m2 | 2.9418e-06 |
| mpi4-xy22 | radiative_Z1 | kW/m2 | 0.382485 |
| mpi4-xy22 | radiative_Z2 | kW/m2 | 0.211617 |
| mpi4-xy22 | radiative_Z3 | kW/m2 | 0.130506 |
| mpi4-xy22 | radiative_Z4 | kW/m2 | 0.0947154 |
| mpi4-xy22 | radiative_Z5 | kW/m2 | 0.305048 |
| mpi4-xy22 | radiative_Z6 | kW/m2 | 0.319024 |
| mpi4-xy22 | radiative_Z7 | kW/m2 | 0.263127 |
## wood — 15 s

| Kandydat | Referencja | Stare bramki | Energia, błąd wzgl. | Zapłon, różnica s |
|---|---:|---|---:|---:|
| OpenMP / OpenMP | 1 | PASS | 9.60526e-07 | 0.0 |
| OpenMP / OpenMP | 1 | PASS | 0.000443425 | 0.0 |
| OpenMP / OpenMP | 2 | PASS | 0.000444386 | 0.0 |
| mpi2-x2 / screen -1 | 1 | FAIL | 0.000163526 | 0.0 |
| mpi2-x2 / screen -1 | 2 | FAIL | 0.000164487 | 0.0 |
| mpi2-x2 / screen -1 | 3 | FAIL | 0.000279775 | 0.0 |
| mpi2-y2 / screen -1 | 1 | FAIL | 0.00122713 | 0.0 |
| mpi2-y2 / screen -1 | 2 | FAIL | 0.00122617 | 0.0 |
| mpi2-y2 / screen -1 | 3 | FAIL | 0.00166981 | 0.0 |
| mpi4-xy22 / screen -1 | 1 | FAIL | 0.00263323 | 0.0 |
| mpi4-xy22 / screen -1 | 2 | FAIL | 0.00263227 | 0.0 |
| mpi4-xy22 / screen -1 | 3 | FAIL | 0.00307529 | 0.0 |
| mpi4-xy22 / finalist 1 | 1 | FAIL | 0.00263323 | 0.0 |
| mpi4-xy22 / finalist 1 | 2 | FAIL | 0.00263227 | 0.0 |
| mpi4-xy22 / finalist 1 | 3 | FAIL | 0.00307529 | 0.0 |
| mpi4-xy22 / finalist 2 | 1 | FAIL | 0.00263323 | 0.0 |
| mpi4-xy22 / finalist 2 | 2 | FAIL | 0.00263227 | 0.0 |
| mpi4-xy22 / finalist 2 | 3 | FAIL | 0.00307529 | 0.0 |
| mpi4-xy22 / finalist 3 | 1 | FAIL | 0.00263323 | 0.0 |
| mpi4-xy22 / finalist 3 | 2 | FAIL | 0.00263227 | 0.0 |
| mpi4-xy22 / finalist 3 | 3 | FAIL | 0.00307529 | 0.0 |

Maksimum błędu po dostępnych parach w danej grupie; wartości poszczególnych par pozostają w `comparisons/*.json`.

| Grupa | Okno | Kanał | Największy błąd |
|---|---|---|---:|
| OpenMP / OpenMP | full | HRRPUV | 0.268237 |
| OpenMP / OpenMP | full | OXYGEN VOLUME FRACTION | 0.00272703 |
| OpenMP / OpenMP | full | SOOT DENSITY | 0.230466 |
| OpenMP / OpenMP | full | TEMPERATURE | 0.201334 |
| OpenMP / OpenMP | full | U-VELOCITY | 0.737784 |
| OpenMP / OpenMP | full | V-VELOCITY | 0.7373 |
| OpenMP / OpenMP | full | W-VELOCITY | 0.2908 |
| OpenMP / OpenMP | late | HRRPUV | 0.388546 |
| OpenMP / OpenMP | late | OXYGEN VOLUME FRACTION | 0.00365481 |
| OpenMP / OpenMP | late | SOOT DENSITY | 0.351206 |
| OpenMP / OpenMP | late | TEMPERATURE | 0.305358 |
| OpenMP / OpenMP | late | U-VELOCITY | 1.05204 |
| OpenMP / OpenMP | late | V-VELOCITY | 1.05246 |
| OpenMP / OpenMP | late | W-VELOCITY | 0.428576 |
| OpenMP / OpenMP | variability | HRRPUV | 0.23574 |
| OpenMP / OpenMP | variability | OXYGEN VOLUME FRACTION | 0.00137163 |
| OpenMP / OpenMP | variability | SOOT DENSITY | 0.14245 |
| OpenMP / OpenMP | variability | TEMPERATURE | 0.109942 |
| OpenMP / OpenMP | variability | U-VELOCITY | 0.192853 |
| OpenMP / OpenMP | variability | V-VELOCITY | 0.197037 |
| OpenMP / OpenMP | variability | W-VELOCITY | 0.142911 |
| mpi2-x2 | full | HRRPUV | 0.528804 |
| mpi2-x2 | full | OXYGEN VOLUME FRACTION | 0.00571588 |
| mpi2-x2 | full | SOOT DENSITY | 0.444105 |
| mpi2-x2 | full | TEMPERATURE | 0.405323 |
| mpi2-x2 | full | U-VELOCITY | 1.1739 |
| mpi2-x2 | full | V-VELOCITY | 1.17685 |
| mpi2-x2 | full | W-VELOCITY | 0.496825 |
| mpi2-x2 | interfacesFull | HRRPUV | 0.719583 |
| mpi2-x2 | interfacesFull | OXYGEN VOLUME FRACTION | 0.0115976 |
| mpi2-x2 | interfacesFull | SOOT DENSITY | 0.358868 |
| mpi2-x2 | interfacesFull | TEMPERATURE | 0.367794 |
| mpi2-x2 | interfacesFull | U-VELOCITY | 1.35059 |
| mpi2-x2 | interfacesFull | V-VELOCITY | 1.12806 |
| mpi2-x2 | interfacesFull | W-VELOCITY | 0.392363 |
| mpi2-x2 | interfacesLate | HRRPUV | 0.675781 |
| mpi2-x2 | interfacesLate | OXYGEN VOLUME FRACTION | 0.010355 |
| mpi2-x2 | interfacesLate | SOOT DENSITY | 0.368424 |
| mpi2-x2 | interfacesLate | TEMPERATURE | 0.384262 |
| mpi2-x2 | interfacesLate | U-VELOCITY | 1.37716 |
| mpi2-x2 | interfacesLate | V-VELOCITY | 1.11747 |
| mpi2-x2 | interfacesLate | W-VELOCITY | 0.401657 |
| mpi2-x2 | late | HRRPUV | 0.537602 |
| mpi2-x2 | late | OXYGEN VOLUME FRACTION | 0.00535552 |
| mpi2-x2 | late | SOOT DENSITY | 0.464705 |
| mpi2-x2 | late | TEMPERATURE | 0.434155 |
| mpi2-x2 | late | U-VELOCITY | 1.16648 |
| mpi2-x2 | late | V-VELOCITY | 1.16766 |
| mpi2-x2 | late | W-VELOCITY | 0.499703 |
| mpi2-x2 | variability | HRRPUV | 0.304111 |
| mpi2-x2 | variability | OXYGEN VOLUME FRACTION | 0.00213002 |
| mpi2-x2 | variability | SOOT DENSITY | 0.206253 |
| mpi2-x2 | variability | TEMPERATURE | 0.167211 |
| mpi2-x2 | variability | U-VELOCITY | 0.228748 |
| mpi2-x2 | variability | V-VELOCITY | 0.235442 |
| mpi2-x2 | variability | W-VELOCITY | 0.174744 |
| mpi2-y2 | full | HRRPUV | 0.503899 |
| mpi2-y2 | full | OXYGEN VOLUME FRACTION | 0.005445 |
| mpi2-y2 | full | SOOT DENSITY | 0.433205 |
| mpi2-y2 | full | TEMPERATURE | 0.389484 |
| mpi2-y2 | full | U-VELOCITY | 1.18232 |
| mpi2-y2 | full | V-VELOCITY | 1.16554 |
| mpi2-y2 | full | W-VELOCITY | 0.494053 |
| mpi2-y2 | interfacesFull | HRRPUV | 0.69562 |
| mpi2-y2 | interfacesFull | OXYGEN VOLUME FRACTION | 0.0107572 |
| mpi2-y2 | interfacesFull | SOOT DENSITY | 0.345236 |
| mpi2-y2 | interfacesFull | TEMPERATURE | 0.348072 |
| mpi2-y2 | interfacesFull | U-VELOCITY | 1.1272 |
| mpi2-y2 | interfacesFull | V-VELOCITY | 1.39548 |
| mpi2-y2 | interfacesFull | W-VELOCITY | 0.386856 |
| mpi2-y2 | interfacesLate | HRRPUV | 0.676764 |
| mpi2-y2 | interfacesLate | OXYGEN VOLUME FRACTION | 0.00985584 |
| mpi2-y2 | interfacesLate | SOOT DENSITY | 0.361108 |
| mpi2-y2 | interfacesLate | TEMPERATURE | 0.364832 |
| mpi2-y2 | interfacesLate | U-VELOCITY | 1.14889 |
| mpi2-y2 | interfacesLate | V-VELOCITY | 1.44202 |
| mpi2-y2 | interfacesLate | W-VELOCITY | 0.39371 |
| mpi2-y2 | late | HRRPUV | 0.524168 |
| mpi2-y2 | late | OXYGEN VOLUME FRACTION | 0.00513366 |
| mpi2-y2 | late | SOOT DENSITY | 0.455218 |
| mpi2-y2 | late | TEMPERATURE | 0.419414 |
| mpi2-y2 | late | U-VELOCITY | 1.19211 |
| mpi2-y2 | late | V-VELOCITY | 1.17179 |
| mpi2-y2 | late | W-VELOCITY | 0.504617 |
| mpi2-y2 | variability | HRRPUV | 0.301499 |
| mpi2-y2 | variability | OXYGEN VOLUME FRACTION | 0.00218279 |
| mpi2-y2 | variability | SOOT DENSITY | 0.217407 |
| mpi2-y2 | variability | TEMPERATURE | 0.174106 |
| mpi2-y2 | variability | U-VELOCITY | 0.223119 |
| mpi2-y2 | variability | V-VELOCITY | 0.21759 |
| mpi2-y2 | variability | W-VELOCITY | 0.18923 |
| mpi4-xy22 | full | HRRPUV | 0.520884 |
| mpi4-xy22 | full | OXYGEN VOLUME FRACTION | 0.00571108 |
| mpi4-xy22 | full | SOOT DENSITY | 0.446327 |
| mpi4-xy22 | full | TEMPERATURE | 0.406592 |
| mpi4-xy22 | full | U-VELOCITY | 1.19448 |
| mpi4-xy22 | full | V-VELOCITY | 1.18089 |
| mpi4-xy22 | full | W-VELOCITY | 0.503174 |
| mpi4-xy22 | interfacesFull | HRRPUV | 0.676428 |
| mpi4-xy22 | interfacesFull | OXYGEN VOLUME FRACTION | 0.0108575 |
| mpi4-xy22 | interfacesFull | SOOT DENSITY | 0.383792 |
| mpi4-xy22 | interfacesFull | TEMPERATURE | 0.386664 |
| mpi4-xy22 | interfacesFull | U-VELOCITY | 1.26581 |
| mpi4-xy22 | interfacesFull | V-VELOCITY | 1.25292 |
| mpi4-xy22 | interfacesFull | W-VELOCITY | 0.423275 |
| mpi4-xy22 | interfacesLate | HRRPUV | 0.678184 |
| mpi4-xy22 | interfacesLate | OXYGEN VOLUME FRACTION | 0.0101923 |
| mpi4-xy22 | interfacesLate | SOOT DENSITY | 0.409136 |
| mpi4-xy22 | interfacesLate | TEMPERATURE | 0.422715 |
| mpi4-xy22 | interfacesLate | U-VELOCITY | 1.30594 |
| mpi4-xy22 | interfacesLate | V-VELOCITY | 1.28104 |
| mpi4-xy22 | interfacesLate | W-VELOCITY | 0.435001 |
| mpi4-xy22 | late | HRRPUV | 0.550329 |
| mpi4-xy22 | late | OXYGEN VOLUME FRACTION | 0.00556377 |
| mpi4-xy22 | late | SOOT DENSITY | 0.483185 |
| mpi4-xy22 | late | TEMPERATURE | 0.452946 |
| mpi4-xy22 | late | U-VELOCITY | 1.21158 |
| mpi4-xy22 | late | V-VELOCITY | 1.21064 |
| mpi4-xy22 | late | W-VELOCITY | 0.522964 |
| mpi4-xy22 | variability | HRRPUV | 0.278777 |
| mpi4-xy22 | variability | OXYGEN VOLUME FRACTION | 0.00190387 |
| mpi4-xy22 | variability | SOOT DENSITY | 0.195128 |
| mpi4-xy22 | variability | TEMPERATURE | 0.152751 |
| mpi4-xy22 | variability | U-VELOCITY | 0.234457 |
| mpi4-xy22 | variability | V-VELOCITY | 0.236753 |
| mpi4-xy22 | variability | W-VELOCITY | 0.19001 |

### Natywne sondy i strumienie

Największy bezwzględny RMS po dostępnych parach; zachowujemy położenie sondy i natywne jednostki.

| Grupa | Urządzenie | Jednostka | RMS |
|---|---|---|---:|
| OpenMP / OpenMP | divergence_X1_hi | 1/s | 0.00655081 |
| OpenMP / OpenMP | divergence_X1_lo | 1/s | 0.000191835 |
| OpenMP / OpenMP | divergence_X2_hi | 1/s | 0.0991244 |
| OpenMP / OpenMP | divergence_X2_lo | 1/s | 0.178863 |
| OpenMP / OpenMP | divergence_X3_hi | 1/s | 0.47426 |
| OpenMP / OpenMP | divergence_X3_lo | 1/s | 0.254273 |
| OpenMP / OpenMP | divergence_X4_hi | 1/s | 0.896789 |
| OpenMP / OpenMP | divergence_X4_lo | 1/s | 0.913068 |
| OpenMP / OpenMP | divergence_X5_hi | 1/s | 0.400706 |
| OpenMP / OpenMP | divergence_X5_lo | 1/s | 0.424083 |
| OpenMP / OpenMP | divergence_X6_hi | 1/s | 0.05175 |
| OpenMP / OpenMP | divergence_X6_lo | 1/s | 0.19355 |
| OpenMP / OpenMP | divergence_X7_hi | 1/s | 2.73626e-05 |
| OpenMP / OpenMP | divergence_X7_lo | 1/s | 7.97404e-05 |
| OpenMP / OpenMP | divergence_Y1_hi | 1/s | 0.000177877 |
| OpenMP / OpenMP | divergence_Y1_lo | 1/s | 2.80028e-05 |
| OpenMP / OpenMP | divergence_Y2_hi | 1/s | 0.199682 |
| OpenMP / OpenMP | divergence_Y2_lo | 1/s | 0.149394 |
| OpenMP / OpenMP | divergence_Y3_hi | 1/s | 0.479549 |
| OpenMP / OpenMP | divergence_Y3_lo | 1/s | 0.330135 |
| OpenMP / OpenMP | divergence_Y4_hi | 1/s | 0.896789 |
| OpenMP / OpenMP | divergence_Y4_lo | 1/s | 0.983065 |
| OpenMP / OpenMP | divergence_Y5_hi | 1/s | 0.227734 |
| OpenMP / OpenMP | divergence_Y5_lo | 1/s | 0.400035 |
| OpenMP / OpenMP | divergence_Y6_hi | 1/s | 0.0721786 |
| OpenMP / OpenMP | divergence_Y6_lo | 1/s | 0.167067 |
| OpenMP / OpenMP | divergence_Y7_hi | 1/s | 2.70512e-05 |
| OpenMP / OpenMP | divergence_Y7_lo | 1/s | 0.000387282 |
| OpenMP / OpenMP | divergence_Z1_hi | 1/s | 0.147813 |
| OpenMP / OpenMP | divergence_Z1_lo | 1/s | 0.255405 |
| OpenMP / OpenMP | divergence_Z2_hi | 1/s | 1.07321 |
| OpenMP / OpenMP | divergence_Z2_lo | 1/s | 0.966548 |
| OpenMP / OpenMP | divergence_Z3_hi | 1/s | 0.86334 |
| OpenMP / OpenMP | divergence_Z3_lo | 1/s | 0.894921 |
| OpenMP / OpenMP | divergence_Z4_hi | 1/s | 0.896789 |
| OpenMP / OpenMP | divergence_Z4_lo | 1/s | 1.03085 |
| OpenMP / OpenMP | divergence_Z5_hi | 1/s | 0.875765 |
| OpenMP / OpenMP | divergence_Z5_lo | 1/s | 0.855458 |
| OpenMP / OpenMP | divergence_Z6_hi | 1/s | 0.778043 |
| OpenMP / OpenMP | divergence_Z6_lo | 1/s | 0.741436 |
| OpenMP / OpenMP | divergence_Z7_hi | 1/s | 0.571066 |
| OpenMP / OpenMP | divergence_Z7_lo | 1/s | 0.547169 |
| OpenMP / OpenMP | enthalpy_local_X1 | kW/m2 | 0.0622108 |
| OpenMP / OpenMP | enthalpy_local_X2 | kW/m2 | 2.03623 |
| OpenMP / OpenMP | enthalpy_local_X3 | kW/m2 | 3.23769 |
| OpenMP / OpenMP | enthalpy_local_X4 | kW/m2 | 7.37039 |
| OpenMP / OpenMP | enthalpy_local_X5 | kW/m2 | 2.62765 |
| OpenMP / OpenMP | enthalpy_local_X6 | kW/m2 | 0.171843 |
| OpenMP / OpenMP | enthalpy_local_X7 | kW/m2 | 0.000634326 |
| OpenMP / OpenMP | enthalpy_local_Y1 | kW/m2 | 0.00462594 |
| OpenMP / OpenMP | enthalpy_local_Y2 | kW/m2 | 2.74853 |
| OpenMP / OpenMP | enthalpy_local_Y3 | kW/m2 | 3.63057 |
| OpenMP / OpenMP | enthalpy_local_Y4 | kW/m2 | 6.82958 |
| OpenMP / OpenMP | enthalpy_local_Y5 | kW/m2 | 2.36673 |
| OpenMP / OpenMP | enthalpy_local_Y6 | kW/m2 | 0.233783 |
| OpenMP / OpenMP | enthalpy_local_Y7 | kW/m2 | 0.000542794 |
| OpenMP / OpenMP | enthalpy_local_Z1 | kW/m2 | 3.55194 |
| OpenMP / OpenMP | enthalpy_local_Z2 | kW/m2 | 10.5147 |
| OpenMP / OpenMP | enthalpy_local_Z3 | kW/m2 | 17.9919 |
| OpenMP / OpenMP | enthalpy_local_Z4 | kW/m2 | 28.8924 |
| OpenMP / OpenMP | enthalpy_local_Z5 | kW/m2 | 38.572 |
| OpenMP / OpenMP | enthalpy_local_Z6 | kW/m2 | 43.0324 |
| OpenMP / OpenMP | enthalpy_local_Z7 | kW/m2 | 49.3339 |
| OpenMP / OpenMP | mass_local_X1 | kg/s/m2 | 0.00857676 |
| OpenMP / OpenMP | mass_local_X2 | kg/s/m2 | 0.0265797 |
| OpenMP / OpenMP | mass_local_X3 | kg/s/m2 | 0.042497 |
| OpenMP / OpenMP | mass_local_X4 | kg/s/m2 | 0.0206937 |
| OpenMP / OpenMP | mass_local_X5 | kg/s/m2 | 0.0552537 |
| OpenMP / OpenMP | mass_local_X6 | kg/s/m2 | 0.0282392 |
| OpenMP / OpenMP | mass_local_X7 | kg/s/m2 | 0.00921852 |
| OpenMP / OpenMP | mass_local_Y1 | kg/s/m2 | 0.0104997 |
| OpenMP / OpenMP | mass_local_Y2 | kg/s/m2 | 0.0324739 |
| OpenMP / OpenMP | mass_local_Y3 | kg/s/m2 | 0.0402129 |
| OpenMP / OpenMP | mass_local_Y4 | kg/s/m2 | 0.024122 |
| OpenMP / OpenMP | mass_local_Y5 | kg/s/m2 | 0.0387832 |
| OpenMP / OpenMP | mass_local_Y6 | kg/s/m2 | 0.0356509 |
| OpenMP / OpenMP | mass_local_Y7 | kg/s/m2 | 0.00924531 |
| OpenMP / OpenMP | mass_local_Z1 | kg/s/m2 | 0.00465997 |
| OpenMP / OpenMP | mass_local_Z2 | kg/s/m2 | 0.0116994 |
| OpenMP / OpenMP | mass_local_Z3 | kg/s/m2 | 0.0214834 |
| OpenMP / OpenMP | mass_local_Z4 | kg/s/m2 | 0.0316102 |
| OpenMP / OpenMP | mass_local_Z5 | kg/s/m2 | 0.0423706 |
| OpenMP / OpenMP | mass_local_Z6 | kg/s/m2 | 0.0681972 |
| OpenMP / OpenMP | mass_local_Z7 | kg/s/m2 | 0.101002 |
| OpenMP / OpenMP | mdot_X1 | kg/s | 0.000195934 |
| OpenMP / OpenMP | mdot_X2 | kg/s | 0.000205803 |
| OpenMP / OpenMP | mdot_X3 | kg/s | 0.000255301 |
| OpenMP / OpenMP | mdot_X4 | kg/s | 0.000321266 |
| OpenMP / OpenMP | mdot_X5 | kg/s | 0.000278526 |
| OpenMP / OpenMP | mdot_X6 | kg/s | 0.00018789 |
| OpenMP / OpenMP | mdot_X7 | kg/s | 0.00019455 |
| OpenMP / OpenMP | mdot_Y1 | kg/s | 0.000238149 |
| OpenMP / OpenMP | mdot_Y2 | kg/s | 0.00020876 |
| OpenMP / OpenMP | mdot_Y3 | kg/s | 0.000298057 |
| OpenMP / OpenMP | mdot_Y4 | kg/s | 0.000332202 |
| OpenMP / OpenMP | mdot_Y5 | kg/s | 0.000295173 |
| OpenMP / OpenMP | mdot_Y6 | kg/s | 0.000283075 |
| OpenMP / OpenMP | mdot_Y7 | kg/s | 0.000266203 |
| OpenMP / OpenMP | mdot_Z1 | kg/s | 1.78015e-05 |
| OpenMP / OpenMP | mdot_Z2 | kg/s | 4.61094e-05 |
| OpenMP / OpenMP | mdot_Z3 | kg/s | 6.86404e-05 |
| OpenMP / OpenMP | mdot_Z4 | kg/s | 0.000132614 |
| OpenMP / OpenMP | mdot_Z5 | kg/s | 0.000229817 |
| OpenMP / OpenMP | mdot_Z6 | kg/s | 0.000308914 |
| OpenMP / OpenMP | mdot_Z7 | kg/s | 0.000379271 |
| OpenMP / OpenMP | pressure_X1_hi | Pa | 0.00221431 |
| OpenMP / OpenMP | pressure_X1_lo | Pa | 0.00157861 |
| OpenMP / OpenMP | pressure_X2_hi | Pa | 0.00923255 |
| OpenMP / OpenMP | pressure_X2_lo | Pa | 0.00657574 |
| OpenMP / OpenMP | pressure_X3_hi | Pa | 0.0130571 |
| OpenMP / OpenMP | pressure_X3_lo | Pa | 0.0153172 |
| OpenMP / OpenMP | pressure_X4_hi | Pa | 0.0100181 |
| OpenMP / OpenMP | pressure_X4_lo | Pa | 0.00898963 |
| OpenMP / OpenMP | pressure_X5_hi | Pa | 0.0152175 |
| OpenMP / OpenMP | pressure_X5_lo | Pa | 0.015379 |
| OpenMP / OpenMP | pressure_X6_hi | Pa | 0.00789525 |
| OpenMP / OpenMP | pressure_X6_lo | Pa | 0.0103781 |
| OpenMP / OpenMP | pressure_X7_hi | Pa | 0.00272078 |
| OpenMP / OpenMP | pressure_X7_lo | Pa | 0.0036135 |
| OpenMP / OpenMP | pressure_Y1_hi | Pa | 0.0028922 |
| OpenMP / OpenMP | pressure_Y1_lo | Pa | 0.00208775 |
| OpenMP / OpenMP | pressure_Y2_hi | Pa | 0.0100683 |
| OpenMP / OpenMP | pressure_Y2_lo | Pa | 0.00740649 |
| OpenMP / OpenMP | pressure_Y3_hi | Pa | 0.014426 |
| OpenMP / OpenMP | pressure_Y3_lo | Pa | 0.0120577 |
| OpenMP / OpenMP | pressure_Y4_hi | Pa | 0.0100181 |
| OpenMP / OpenMP | pressure_Y4_lo | Pa | 0.00955705 |
| OpenMP / OpenMP | pressure_Y5_hi | Pa | 0.0172018 |
| OpenMP / OpenMP | pressure_Y5_lo | Pa | 0.0160705 |
| OpenMP / OpenMP | pressure_Y6_hi | Pa | 0.00967161 |
| OpenMP / OpenMP | pressure_Y6_lo | Pa | 0.0131024 |
| OpenMP / OpenMP | pressure_Y7_hi | Pa | 0.00219634 |
| OpenMP / OpenMP | pressure_Y7_lo | Pa | 0.00308088 |
| OpenMP / OpenMP | pressure_Z1_hi | Pa | 0.00133259 |
| OpenMP / OpenMP | pressure_Z1_lo | Pa | 0.00112791 |
| OpenMP / OpenMP | pressure_Z2_hi | Pa | 0.00307987 |
| OpenMP / OpenMP | pressure_Z2_lo | Pa | 0.00293411 |
| OpenMP / OpenMP | pressure_Z3_hi | Pa | 0.00684514 |
| OpenMP / OpenMP | pressure_Z3_lo | Pa | 0.00641257 |
| OpenMP / OpenMP | pressure_Z4_hi | Pa | 0.0100181 |
| OpenMP / OpenMP | pressure_Z4_lo | Pa | 0.00942799 |
| OpenMP / OpenMP | pressure_Z5_hi | Pa | 0.0127806 |
| OpenMP / OpenMP | pressure_Z5_lo | Pa | 0.0119277 |
| OpenMP / OpenMP | pressure_Z6_hi | Pa | 0.0159582 |
| OpenMP / OpenMP | pressure_Z6_lo | Pa | 0.014684 |
| OpenMP / OpenMP | pressure_Z7_hi | Pa | 0.020574 |
| OpenMP / OpenMP | pressure_Z7_lo | Pa | 0.0214008 |
| OpenMP / OpenMP | probe_O2 | mol/mol | 0.00675899 |
| OpenMP / OpenMP | probe_T | C | 25.1619 |
| OpenMP / OpenMP | qdot_X1 | kW | 0.0011695 |
| OpenMP / OpenMP | qdot_X2 | kW | 0.00535858 |
| OpenMP / OpenMP | qdot_X3 | kW | 0.0189682 |
| OpenMP / OpenMP | qdot_X4 | kW | 0.0332524 |
| OpenMP / OpenMP | qdot_X5 | kW | 0.0198955 |
| OpenMP / OpenMP | qdot_X6 | kW | 0.0108593 |
| OpenMP / OpenMP | qdot_X7 | kW | 0.00233725 |
| OpenMP / OpenMP | qdot_Y1 | kW | 0.00234483 |
| OpenMP / OpenMP | qdot_Y2 | kW | 0.00809833 |
| OpenMP / OpenMP | qdot_Y3 | kW | 0.0208316 |
| OpenMP / OpenMP | qdot_Y4 | kW | 0.0266866 |
| OpenMP / OpenMP | qdot_Y5 | kW | 0.0214428 |
| OpenMP / OpenMP | qdot_Y6 | kW | 0.0109797 |
| OpenMP / OpenMP | qdot_Y7 | kW | 0.00439175 |
| OpenMP / OpenMP | qdot_Z1 | kW | 0.00289064 |
| OpenMP / OpenMP | qdot_Z2 | kW | 0.0105526 |
| OpenMP / OpenMP | qdot_Z3 | kW | 0.0168513 |
| OpenMP / OpenMP | qdot_Z4 | kW | 0.023627 |
| OpenMP / OpenMP | qdot_Z5 | kW | 0.0313222 |
| OpenMP / OpenMP | qdot_Z6 | kW | 0.0389316 |
| OpenMP / OpenMP | qdot_Z7 | kW | 0.0407621 |
| OpenMP / OpenMP | radiative_X1 | kW/m2 | 0.04994 |
| OpenMP / OpenMP | radiative_X2 | kW/m2 | 0.144607 |
| OpenMP / OpenMP | radiative_X3 | kW/m2 | 0.28307 |
| OpenMP / OpenMP | radiative_X4 | kW/m2 | 0.487219 |
| OpenMP / OpenMP | radiative_X5 | kW/m2 | 0.133857 |
| OpenMP / OpenMP | radiative_X6 | kW/m2 | 0.000692885 |
| OpenMP / OpenMP | radiative_X7 | kW/m2 | 3.79104e-06 |
| OpenMP / OpenMP | radiative_Y1 | kW/m2 | 0.0468561 |
| OpenMP / OpenMP | radiative_Y2 | kW/m2 | 0.114538 |
| OpenMP / OpenMP | radiative_Y3 | kW/m2 | 0.313081 |
| OpenMP / OpenMP | radiative_Y4 | kW/m2 | 0.413056 |
| OpenMP / OpenMP | radiative_Y5 | kW/m2 | 0.213833 |
| OpenMP / OpenMP | radiative_Y6 | kW/m2 | 0.000797619 |
| OpenMP / OpenMP | radiative_Y7 | kW/m2 | 3.81525e-06 |
| OpenMP / OpenMP | radiative_Z1 | kW/m2 | 0.238219 |
| OpenMP / OpenMP | radiative_Z2 | kW/m2 | 0.43617 |
| OpenMP / OpenMP | radiative_Z3 | kW/m2 | 0.539548 |
| OpenMP / OpenMP | radiative_Z4 | kW/m2 | 0.449931 |
| OpenMP / OpenMP | radiative_Z5 | kW/m2 | 0.415559 |
| OpenMP / OpenMP | radiative_Z6 | kW/m2 | 0.24691 |
| OpenMP / OpenMP | radiative_Z7 | kW/m2 | 0.122528 |
| OpenMP / OpenMP | surface | C | 0.340838 |
| mpi2-x2 | divergence_X1_hi | 1/s | 0.0198405 |
| mpi2-x2 | divergence_X1_lo | 1/s | 0.01062 |
| mpi2-x2 | divergence_X2_hi | 1/s | 0.199942 |
| mpi2-x2 | divergence_X2_lo | 1/s | 0.171487 |
| mpi2-x2 | divergence_X3_hi | 1/s | 0.945449 |
| mpi2-x2 | divergence_X3_lo | 1/s | 0.521129 |
| mpi2-x2 | divergence_X4_hi | 1/s | 1.74271 |
| mpi2-x2 | divergence_X4_lo | 1/s | 2.10397 |
| mpi2-x2 | divergence_X5_hi | 1/s | 0.658158 |
| mpi2-x2 | divergence_X5_lo | 1/s | 0.748392 |
| mpi2-x2 | divergence_X6_hi | 1/s | 0.0792256 |
| mpi2-x2 | divergence_X6_lo | 1/s | 0.267457 |
| mpi2-x2 | divergence_X7_hi | 1/s | 0.019034 |
| mpi2-x2 | divergence_X7_lo | 1/s | 0.0205097 |
| mpi2-x2 | divergence_Y1_hi | 1/s | 0.00552627 |
| mpi2-x2 | divergence_Y1_lo | 1/s | 0.00580513 |
| mpi2-x2 | divergence_Y2_hi | 1/s | 0.208018 |
| mpi2-x2 | divergence_Y2_lo | 1/s | 0.133142 |
| mpi2-x2 | divergence_Y3_hi | 1/s | 0.729928 |
| mpi2-x2 | divergence_Y3_lo | 1/s | 0.535327 |
| mpi2-x2 | divergence_Y4_hi | 1/s | 1.78442 |
| mpi2-x2 | divergence_Y4_lo | 1/s | 1.96193 |
| mpi2-x2 | divergence_Y5_hi | 1/s | 0.513941 |
| mpi2-x2 | divergence_Y5_lo | 1/s | 0.764643 |
| mpi2-x2 | divergence_Y6_hi | 1/s | 0.115414 |
| mpi2-x2 | divergence_Y6_lo | 1/s | 0.196189 |
| mpi2-x2 | divergence_Y7_hi | 1/s | 0.00826519 |
| mpi2-x2 | divergence_Y7_lo | 1/s | 0.0143472 |
| mpi2-x2 | divergence_Z1_hi | 1/s | 0.551668 |
| mpi2-x2 | divergence_Z1_lo | 1/s | 0.733796 |
| mpi2-x2 | divergence_Z2_hi | 1/s | 2.87708 |
| mpi2-x2 | divergence_Z2_lo | 1/s | 2.89309 |
| mpi2-x2 | divergence_Z3_hi | 1/s | 2.42651 |
| mpi2-x2 | divergence_Z3_lo | 1/s | 2.64743 |
| mpi2-x2 | divergence_Z4_hi | 1/s | 1.78442 |
| mpi2-x2 | divergence_Z4_lo | 1/s | 1.84839 |
| mpi2-x2 | divergence_Z5_hi | 1/s | 1.64058 |
| mpi2-x2 | divergence_Z5_lo | 1/s | 1.53311 |
| mpi2-x2 | divergence_Z6_hi | 1/s | 1.29595 |
| mpi2-x2 | divergence_Z6_lo | 1/s | 1.37928 |
| mpi2-x2 | divergence_Z7_hi | 1/s | 0.812082 |
| mpi2-x2 | divergence_Z7_lo | 1/s | 0.902126 |
| mpi2-x2 | enthalpy_local_X1 | kW/m2 | 1.04734 |
| mpi2-x2 | enthalpy_local_X2 | kW/m2 | 2.95779 |
| mpi2-x2 | enthalpy_local_X3 | kW/m2 | 10.3887 |
| mpi2-x2 | enthalpy_local_X4 | kW/m2 | 15.2605 |
| mpi2-x2 | enthalpy_local_X5 | kW/m2 | 5.88609 |
| mpi2-x2 | enthalpy_local_X6 | kW/m2 | 2.54623 |
| mpi2-x2 | enthalpy_local_X7 | kW/m2 | 0.0250764 |
| mpi2-x2 | enthalpy_local_Y1 | kW/m2 | 0.277113 |
| mpi2-x2 | enthalpy_local_Y2 | kW/m2 | 4.78378 |
| mpi2-x2 | enthalpy_local_Y3 | kW/m2 | 10.5246 |
| mpi2-x2 | enthalpy_local_Y4 | kW/m2 | 16.1888 |
| mpi2-x2 | enthalpy_local_Y5 | kW/m2 | 4.6777 |
| mpi2-x2 | enthalpy_local_Y6 | kW/m2 | 0.356338 |
| mpi2-x2 | enthalpy_local_Y7 | kW/m2 | 0.0603733 |
| mpi2-x2 | enthalpy_local_Z1 | kW/m2 | 10.7945 |
| mpi2-x2 | enthalpy_local_Z2 | kW/m2 | 27.5758 |
| mpi2-x2 | enthalpy_local_Z3 | kW/m2 | 53.667 |
| mpi2-x2 | enthalpy_local_Z4 | kW/m2 | 65.1414 |
| mpi2-x2 | enthalpy_local_Z5 | kW/m2 | 78.1389 |
| mpi2-x2 | enthalpy_local_Z6 | kW/m2 | 86.8916 |
| mpi2-x2 | enthalpy_local_Z7 | kW/m2 | 89.2999 |
| mpi2-x2 | mass_local_X1 | kg/s/m2 | 0.0307658 |
| mpi2-x2 | mass_local_X2 | kg/s/m2 | 0.0635677 |
| mpi2-x2 | mass_local_X3 | kg/s/m2 | 0.0912123 |
| mpi2-x2 | mass_local_X4 | kg/s/m2 | 0.0376946 |
| mpi2-x2 | mass_local_X5 | kg/s/m2 | 0.100059 |
| mpi2-x2 | mass_local_X6 | kg/s/m2 | 0.0648211 |
| mpi2-x2 | mass_local_X7 | kg/s/m2 | 0.0310003 |
| mpi2-x2 | mass_local_Y1 | kg/s/m2 | 0.0341854 |
| mpi2-x2 | mass_local_Y2 | kg/s/m2 | 0.0844809 |
| mpi2-x2 | mass_local_Y3 | kg/s/m2 | 0.0902456 |
| mpi2-x2 | mass_local_Y4 | kg/s/m2 | 0.0456518 |
| mpi2-x2 | mass_local_Y5 | kg/s/m2 | 0.08315 |
| mpi2-x2 | mass_local_Y6 | kg/s/m2 | 0.0691306 |
| mpi2-x2 | mass_local_Y7 | kg/s/m2 | 0.031472 |
| mpi2-x2 | mass_local_Z1 | kg/s/m2 | 0.0166938 |
| mpi2-x2 | mass_local_Z2 | kg/s/m2 | 0.0347473 |
| mpi2-x2 | mass_local_Z3 | kg/s/m2 | 0.0533754 |
| mpi2-x2 | mass_local_Z4 | kg/s/m2 | 0.0614421 |
| mpi2-x2 | mass_local_Z5 | kg/s/m2 | 0.0927859 |
| mpi2-x2 | mass_local_Z6 | kg/s/m2 | 0.145315 |
| mpi2-x2 | mass_local_Z7 | kg/s/m2 | 0.158946 |
| mpi2-x2 | mdot_X1 | kg/s | 0.000383411 |
| mpi2-x2 | mdot_X2 | kg/s | 0.00044847 |
| mpi2-x2 | mdot_X3 | kg/s | 0.0006196 |
| mpi2-x2 | mdot_X4 | kg/s | 0.000628622 |
| mpi2-x2 | mdot_X5 | kg/s | 0.000495243 |
| mpi2-x2 | mdot_X6 | kg/s | 0.000446579 |
| mpi2-x2 | mdot_X7 | kg/s | 0.000440954 |
| mpi2-x2 | mdot_Y1 | kg/s | 0.000490335 |
| mpi2-x2 | mdot_Y2 | kg/s | 0.000517021 |
| mpi2-x2 | mdot_Y3 | kg/s | 0.000579756 |
| mpi2-x2 | mdot_Y4 | kg/s | 0.000599253 |
| mpi2-x2 | mdot_Y5 | kg/s | 0.000594742 |
| mpi2-x2 | mdot_Y6 | kg/s | 0.000515743 |
| mpi2-x2 | mdot_Y7 | kg/s | 0.000462506 |
| mpi2-x2 | mdot_Z1 | kg/s | 8.08717e-05 |
| mpi2-x2 | mdot_Z2 | kg/s | 0.000195774 |
| mpi2-x2 | mdot_Z3 | kg/s | 0.000300567 |
| mpi2-x2 | mdot_Z4 | kg/s | 0.000465493 |
| mpi2-x2 | mdot_Z5 | kg/s | 0.000657275 |
| mpi2-x2 | mdot_Z6 | kg/s | 0.000846661 |
| mpi2-x2 | mdot_Z7 | kg/s | 0.00104334 |
| mpi2-x2 | pressure_X1_hi | Pa | 0.00927137 |
| mpi2-x2 | pressure_X1_lo | Pa | 0.00697371 |
| mpi2-x2 | pressure_X2_hi | Pa | 0.0240236 |
| mpi2-x2 | pressure_X2_lo | Pa | 0.0195422 |
| mpi2-x2 | pressure_X3_hi | Pa | 0.0342225 |
| mpi2-x2 | pressure_X3_lo | Pa | 0.0383023 |
| mpi2-x2 | pressure_X4_hi | Pa | 0.0303117 |
| mpi2-x2 | pressure_X4_lo | Pa | 0.0296686 |
| mpi2-x2 | pressure_X5_hi | Pa | 0.0339412 |
| mpi2-x2 | pressure_X5_lo | Pa | 0.0330786 |
| mpi2-x2 | pressure_X6_hi | Pa | 0.0226885 |
| mpi2-x2 | pressure_X6_lo | Pa | 0.0268516 |
| mpi2-x2 | pressure_X7_hi | Pa | 0.00902322 |
| mpi2-x2 | pressure_X7_lo | Pa | 0.011927 |
| mpi2-x2 | pressure_Y1_hi | Pa | 0.0121113 |
| mpi2-x2 | pressure_Y1_lo | Pa | 0.00867068 |
| mpi2-x2 | pressure_Y2_hi | Pa | 0.0316441 |
| mpi2-x2 | pressure_Y2_lo | Pa | 0.027013 |
| mpi2-x2 | pressure_Y3_hi | Pa | 0.0429544 |
| mpi2-x2 | pressure_Y3_lo | Pa | 0.0416709 |
| mpi2-x2 | pressure_Y4_hi | Pa | 0.0296506 |
| mpi2-x2 | pressure_Y4_lo | Pa | 0.0326263 |
| mpi2-x2 | pressure_Y5_hi | Pa | 0.0392213 |
| mpi2-x2 | pressure_Y5_lo | Pa | 0.0379814 |
| mpi2-x2 | pressure_Y6_hi | Pa | 0.0220221 |
| mpi2-x2 | pressure_Y6_lo | Pa | 0.0285147 |
| mpi2-x2 | pressure_Y7_hi | Pa | 0.0064285 |
| mpi2-x2 | pressure_Y7_lo | Pa | 0.008871 |
| mpi2-x2 | pressure_Z1_hi | Pa | 0.0062897 |
| mpi2-x2 | pressure_Z1_lo | Pa | 0.00542144 |
| mpi2-x2 | pressure_Z2_hi | Pa | 0.0136446 |
| mpi2-x2 | pressure_Z2_lo | Pa | 0.0132514 |
| mpi2-x2 | pressure_Z3_hi | Pa | 0.0221459 |
| mpi2-x2 | pressure_Z3_lo | Pa | 0.0211324 |
| mpi2-x2 | pressure_Z4_hi | Pa | 0.0296506 |
| mpi2-x2 | pressure_Z4_lo | Pa | 0.0296028 |
| mpi2-x2 | pressure_Z5_hi | Pa | 0.0350577 |
| mpi2-x2 | pressure_Z5_lo | Pa | 0.0319844 |
| mpi2-x2 | pressure_Z6_hi | Pa | 0.0400435 |
| mpi2-x2 | pressure_Z6_lo | Pa | 0.041976 |
| mpi2-x2 | pressure_Z7_hi | Pa | 0.0392879 |
| mpi2-x2 | pressure_Z7_lo | Pa | 0.0401056 |
| mpi2-x2 | probe_O2 | mol/mol | 0.0176106 |
| mpi2-x2 | probe_T | C | 62.3835 |
| mpi2-x2 | qdot_X1 | kW | 0.00211362 |
| mpi2-x2 | qdot_X2 | kW | 0.0140858 |
| mpi2-x2 | qdot_X3 | kW | 0.0430334 |
| mpi2-x2 | qdot_X4 | kW | 0.0587667 |
| mpi2-x2 | qdot_X5 | kW | 0.0424656 |
| mpi2-x2 | qdot_X6 | kW | 0.0183068 |
| mpi2-x2 | qdot_X7 | kW | 0.00614344 |
| mpi2-x2 | qdot_Y1 | kW | 0.00284528 |
| mpi2-x2 | qdot_Y2 | kW | 0.0130532 |
| mpi2-x2 | qdot_Y3 | kW | 0.0388416 |
| mpi2-x2 | qdot_Y4 | kW | 0.0497909 |
| mpi2-x2 | qdot_Y5 | kW | 0.0496509 |
| mpi2-x2 | qdot_Y6 | kW | 0.015824 |
| mpi2-x2 | qdot_Y7 | kW | 0.00488336 |
| mpi2-x2 | qdot_Z1 | kW | 0.012558 |
| mpi2-x2 | qdot_Z2 | kW | 0.0409357 |
| mpi2-x2 | qdot_Z3 | kW | 0.0600594 |
| mpi2-x2 | qdot_Z4 | kW | 0.0788872 |
| mpi2-x2 | qdot_Z5 | kW | 0.0880538 |
| mpi2-x2 | qdot_Z6 | kW | 0.101881 |
| mpi2-x2 | qdot_Z7 | kW | 0.0946914 |
| mpi2-x2 | radiative_X1 | kW/m2 | 0.212122 |
| mpi2-x2 | radiative_X2 | kW/m2 | 0.40632 |
| mpi2-x2 | radiative_X3 | kW/m2 | 0.869582 |
| mpi2-x2 | radiative_X4 | kW/m2 | 1.57554 |
| mpi2-x2 | radiative_X5 | kW/m2 | 0.235529 |
| mpi2-x2 | radiative_X6 | kW/m2 | 0.033876 |
| mpi2-x2 | radiative_X7 | kW/m2 | 0.000151795 |
| mpi2-x2 | radiative_Y1 | kW/m2 | 0.248974 |
| mpi2-x2 | radiative_Y2 | kW/m2 | 0.530709 |
| mpi2-x2 | radiative_Y3 | kW/m2 | 0.950925 |
| mpi2-x2 | radiative_Y4 | kW/m2 | 0.991712 |
| mpi2-x2 | radiative_Y5 | kW/m2 | 0.252363 |
| mpi2-x2 | radiative_Y6 | kW/m2 | 0.000713038 |
| mpi2-x2 | radiative_Y7 | kW/m2 | 3.54353e-05 |
| mpi2-x2 | radiative_Z1 | kW/m2 | 0.786711 |
| mpi2-x2 | radiative_Z2 | kW/m2 | 1.51657 |
| mpi2-x2 | radiative_Z3 | kW/m2 | 1.51766 |
| mpi2-x2 | radiative_Z4 | kW/m2 | 1.2285 |
| mpi2-x2 | radiative_Z5 | kW/m2 | 0.906601 |
| mpi2-x2 | radiative_Z6 | kW/m2 | 0.578477 |
| mpi2-x2 | radiative_Z7 | kW/m2 | 0.348822 |
| mpi2-x2 | surface | C | 1.27106 |
| mpi2-y2 | divergence_X1_hi | 1/s | 0.0194566 |
| mpi2-y2 | divergence_X1_lo | 1/s | 0.0106204 |
| mpi2-y2 | divergence_X2_hi | 1/s | 0.200946 |
| mpi2-y2 | divergence_X2_lo | 1/s | 0.168686 |
| mpi2-y2 | divergence_X3_hi | 1/s | 0.795622 |
| mpi2-y2 | divergence_X3_lo | 1/s | 0.431748 |
| mpi2-y2 | divergence_X4_hi | 1/s | 1.63567 |
| mpi2-y2 | divergence_X4_lo | 1/s | 1.81921 |
| mpi2-y2 | divergence_X5_hi | 1/s | 0.574363 |
| mpi2-y2 | divergence_X5_lo | 1/s | 0.74196 |
| mpi2-y2 | divergence_X6_hi | 1/s | 0.122175 |
| mpi2-y2 | divergence_X6_lo | 1/s | 0.297074 |
| mpi2-y2 | divergence_X7_hi | 1/s | 0.0191962 |
| mpi2-y2 | divergence_X7_lo | 1/s | 0.0205 |
| mpi2-y2 | divergence_Y1_hi | 1/s | 0.00536661 |
| mpi2-y2 | divergence_Y1_lo | 1/s | 0.00581429 |
| mpi2-y2 | divergence_Y2_hi | 1/s | 0.169767 |
| mpi2-y2 | divergence_Y2_lo | 1/s | 0.115095 |
| mpi2-y2 | divergence_Y3_hi | 1/s | 0.769835 |
| mpi2-y2 | divergence_Y3_lo | 1/s | 0.560054 |
| mpi2-y2 | divergence_Y4_hi | 1/s | 1.57457 |
| mpi2-y2 | divergence_Y4_lo | 1/s | 1.68705 |
| mpi2-y2 | divergence_Y5_hi | 1/s | 0.543738 |
| mpi2-y2 | divergence_Y5_lo | 1/s | 0.735345 |
| mpi2-y2 | divergence_Y6_hi | 1/s | 0.111904 |
| mpi2-y2 | divergence_Y6_lo | 1/s | 0.204084 |
| mpi2-y2 | divergence_Y7_hi | 1/s | 0.00762959 |
| mpi2-y2 | divergence_Y7_lo | 1/s | 0.00929312 |
| mpi2-y2 | divergence_Z1_hi | 1/s | 0.37219 |
| mpi2-y2 | divergence_Z1_lo | 1/s | 0.374793 |
| mpi2-y2 | divergence_Z2_hi | 1/s | 2.08004 |
| mpi2-y2 | divergence_Z2_lo | 1/s | 2.02791 |
| mpi2-y2 | divergence_Z3_hi | 1/s | 2.20658 |
| mpi2-y2 | divergence_Z3_lo | 1/s | 2.28661 |
| mpi2-y2 | divergence_Z4_hi | 1/s | 1.63567 |
| mpi2-y2 | divergence_Z4_lo | 1/s | 1.83394 |
| mpi2-y2 | divergence_Z5_hi | 1/s | 1.5784 |
| mpi2-y2 | divergence_Z5_lo | 1/s | 1.58527 |
| mpi2-y2 | divergence_Z6_hi | 1/s | 1.29875 |
| mpi2-y2 | divergence_Z6_lo | 1/s | 1.37851 |
| mpi2-y2 | divergence_Z7_hi | 1/s | 0.848884 |
| mpi2-y2 | divergence_Z7_lo | 1/s | 0.913434 |
| mpi2-y2 | enthalpy_local_X1 | kW/m2 | 1.04669 |
| mpi2-y2 | enthalpy_local_X2 | kW/m2 | 2.37932 |
| mpi2-y2 | enthalpy_local_X3 | kW/m2 | 9.20927 |
| mpi2-y2 | enthalpy_local_X4 | kW/m2 | 13.3139 |
| mpi2-y2 | enthalpy_local_X5 | kW/m2 | 5.04103 |
| mpi2-y2 | enthalpy_local_X6 | kW/m2 | 2.55927 |
| mpi2-y2 | enthalpy_local_X7 | kW/m2 | 0.0708333 |
| mpi2-y2 | enthalpy_local_Y1 | kW/m2 | 0.271743 |
| mpi2-y2 | enthalpy_local_Y2 | kW/m2 | 3.90722 |
| mpi2-y2 | enthalpy_local_Y3 | kW/m2 | 7.91414 |
| mpi2-y2 | enthalpy_local_Y4 | kW/m2 | 13.6718 |
| mpi2-y2 | enthalpy_local_Y5 | kW/m2 | 5.08628 |
| mpi2-y2 | enthalpy_local_Y6 | kW/m2 | 0.344113 |
| mpi2-y2 | enthalpy_local_Y7 | kW/m2 | 0.0593681 |
| mpi2-y2 | enthalpy_local_Z1 | kW/m2 | 9.23103 |
| mpi2-y2 | enthalpy_local_Z2 | kW/m2 | 20.9467 |
| mpi2-y2 | enthalpy_local_Z3 | kW/m2 | 45.151 |
| mpi2-y2 | enthalpy_local_Z4 | kW/m2 | 62.0774 |
| mpi2-y2 | enthalpy_local_Z5 | kW/m2 | 81.3155 |
| mpi2-y2 | enthalpy_local_Z6 | kW/m2 | 86.0442 |
| mpi2-y2 | enthalpy_local_Z7 | kW/m2 | 78.8352 |
| mpi2-y2 | mass_local_X1 | kg/s/m2 | 0.0315242 |
| mpi2-y2 | mass_local_X2 | kg/s/m2 | 0.0592791 |
| mpi2-y2 | mass_local_X3 | kg/s/m2 | 0.085473 |
| mpi2-y2 | mass_local_X4 | kg/s/m2 | 0.0366403 |
| mpi2-y2 | mass_local_X5 | kg/s/m2 | 0.0807848 |
| mpi2-y2 | mass_local_X6 | kg/s/m2 | 0.0695294 |
| mpi2-y2 | mass_local_X7 | kg/s/m2 | 0.0391816 |
| mpi2-y2 | mass_local_Y1 | kg/s/m2 | 0.0326631 |
| mpi2-y2 | mass_local_Y2 | kg/s/m2 | 0.0758518 |
| mpi2-y2 | mass_local_Y3 | kg/s/m2 | 0.0869883 |
| mpi2-y2 | mass_local_Y4 | kg/s/m2 | 0.0405207 |
| mpi2-y2 | mass_local_Y5 | kg/s/m2 | 0.0795797 |
| mpi2-y2 | mass_local_Y6 | kg/s/m2 | 0.0597176 |
| mpi2-y2 | mass_local_Y7 | kg/s/m2 | 0.0250398 |
| mpi2-y2 | mass_local_Z1 | kg/s/m2 | 0.0166776 |
| mpi2-y2 | mass_local_Z2 | kg/s/m2 | 0.0347918 |
| mpi2-y2 | mass_local_Z3 | kg/s/m2 | 0.0503884 |
| mpi2-y2 | mass_local_Z4 | kg/s/m2 | 0.0652502 |
| mpi2-y2 | mass_local_Z5 | kg/s/m2 | 0.095993 |
| mpi2-y2 | mass_local_Z6 | kg/s/m2 | 0.126863 |
| mpi2-y2 | mass_local_Z7 | kg/s/m2 | 0.151098 |
| mpi2-y2 | mdot_X1 | kg/s | 0.000419576 |
| mpi2-y2 | mdot_X2 | kg/s | 0.000416846 |
| mpi2-y2 | mdot_X3 | kg/s | 0.000648762 |
| mpi2-y2 | mdot_X4 | kg/s | 0.000698344 |
| mpi2-y2 | mdot_X5 | kg/s | 0.000510561 |
| mpi2-y2 | mdot_X6 | kg/s | 0.000389397 |
| mpi2-y2 | mdot_X7 | kg/s | 0.000458461 |
| mpi2-y2 | mdot_Y1 | kg/s | 0.000461568 |
| mpi2-y2 | mdot_Y2 | kg/s | 0.000427047 |
| mpi2-y2 | mdot_Y3 | kg/s | 0.000540776 |
| mpi2-y2 | mdot_Y4 | kg/s | 0.000711021 |
| mpi2-y2 | mdot_Y5 | kg/s | 0.000654893 |
| mpi2-y2 | mdot_Y6 | kg/s | 0.000529992 |
| mpi2-y2 | mdot_Y7 | kg/s | 0.000489504 |
| mpi2-y2 | mdot_Z1 | kg/s | 8.3162e-05 |
| mpi2-y2 | mdot_Z2 | kg/s | 0.000189329 |
| mpi2-y2 | mdot_Z3 | kg/s | 0.000312281 |
| mpi2-y2 | mdot_Z4 | kg/s | 0.000465955 |
| mpi2-y2 | mdot_Z5 | kg/s | 0.00065997 |
| mpi2-y2 | mdot_Z6 | kg/s | 0.000851618 |
| mpi2-y2 | mdot_Z7 | kg/s | 0.000985243 |
| mpi2-y2 | pressure_X1_hi | Pa | 0.00912944 |
| mpi2-y2 | pressure_X1_lo | Pa | 0.0069116 |
| mpi2-y2 | pressure_X2_hi | Pa | 0.0270084 |
| mpi2-y2 | pressure_X2_lo | Pa | 0.0204755 |
| mpi2-y2 | pressure_X3_hi | Pa | 0.0401683 |
| mpi2-y2 | pressure_X3_lo | Pa | 0.0404822 |
| mpi2-y2 | pressure_X4_hi | Pa | 0.0280011 |
| mpi2-y2 | pressure_X4_lo | Pa | 0.0273717 |
| mpi2-y2 | pressure_X5_hi | Pa | 0.0381909 |
| mpi2-y2 | pressure_X5_lo | Pa | 0.0379743 |
| mpi2-y2 | pressure_X6_hi | Pa | 0.0234817 |
| mpi2-y2 | pressure_X6_lo | Pa | 0.0268479 |
| mpi2-y2 | pressure_X7_hi | Pa | 0.00965059 |
| mpi2-y2 | pressure_X7_lo | Pa | 0.0127113 |
| mpi2-y2 | pressure_Y1_hi | Pa | 0.0111613 |
| mpi2-y2 | pressure_Y1_lo | Pa | 0.00803741 |
| mpi2-y2 | pressure_Y2_hi | Pa | 0.0282542 |
| mpi2-y2 | pressure_Y2_lo | Pa | 0.0240208 |
| mpi2-y2 | pressure_Y3_hi | Pa | 0.0410518 |
| mpi2-y2 | pressure_Y3_lo | Pa | 0.0401375 |
| mpi2-y2 | pressure_Y4_hi | Pa | 0.0268085 |
| mpi2-y2 | pressure_Y4_lo | Pa | 0.0268692 |
| mpi2-y2 | pressure_Y5_hi | Pa | 0.0429938 |
| mpi2-y2 | pressure_Y5_lo | Pa | 0.0398869 |
| mpi2-y2 | pressure_Y6_hi | Pa | 0.0205374 |
| mpi2-y2 | pressure_Y6_lo | Pa | 0.0280136 |
| mpi2-y2 | pressure_Y7_hi | Pa | 0.00585859 |
| mpi2-y2 | pressure_Y7_lo | Pa | 0.00786907 |
| mpi2-y2 | pressure_Z1_hi | Pa | 0.00471494 |
| mpi2-y2 | pressure_Z1_lo | Pa | 0.00396838 |
| mpi2-y2 | pressure_Z2_hi | Pa | 0.0134976 |
| mpi2-y2 | pressure_Z2_lo | Pa | 0.0112657 |
| mpi2-y2 | pressure_Z3_hi | Pa | 0.0172642 |
| mpi2-y2 | pressure_Z3_lo | Pa | 0.0161602 |
| mpi2-y2 | pressure_Z4_hi | Pa | 0.0280011 |
| mpi2-y2 | pressure_Z4_lo | Pa | 0.0271758 |
| mpi2-y2 | pressure_Z5_hi | Pa | 0.0357798 |
| mpi2-y2 | pressure_Z5_lo | Pa | 0.0341245 |
| mpi2-y2 | pressure_Z6_hi | Pa | 0.0329056 |
| mpi2-y2 | pressure_Z6_lo | Pa | 0.0347941 |
| mpi2-y2 | pressure_Z7_hi | Pa | 0.0361178 |
| mpi2-y2 | pressure_Z7_lo | Pa | 0.0371427 |
| mpi2-y2 | probe_O2 | mol/mol | 0.0168555 |
| mpi2-y2 | probe_T | C | 61.2959 |
| mpi2-y2 | qdot_X1 | kW | 0.00282777 |
| mpi2-y2 | qdot_X2 | kW | 0.0156908 |
| mpi2-y2 | qdot_X3 | kW | 0.0444488 |
| mpi2-y2 | qdot_X4 | kW | 0.0644467 |
| mpi2-y2 | qdot_X5 | kW | 0.0406515 |
| mpi2-y2 | qdot_X6 | kW | 0.0186921 |
| mpi2-y2 | qdot_X7 | kW | 0.0060581 |
| mpi2-y2 | qdot_Y1 | kW | 0.00248801 |
| mpi2-y2 | qdot_Y2 | kW | 0.0131873 |
| mpi2-y2 | qdot_Y3 | kW | 0.0392272 |
| mpi2-y2 | qdot_Y4 | kW | 0.0556796 |
| mpi2-y2 | qdot_Y5 | kW | 0.0441524 |
| mpi2-y2 | qdot_Y6 | kW | 0.0160914 |
| mpi2-y2 | qdot_Y7 | kW | 0.00479896 |
| mpi2-y2 | qdot_Z1 | kW | 0.0104088 |
| mpi2-y2 | qdot_Z2 | kW | 0.0296056 |
| mpi2-y2 | qdot_Z3 | kW | 0.0521958 |
| mpi2-y2 | qdot_Z4 | kW | 0.0693508 |
| mpi2-y2 | qdot_Z5 | kW | 0.0858132 |
| mpi2-y2 | qdot_Z6 | kW | 0.0881601 |
| mpi2-y2 | qdot_Z7 | kW | 0.0910506 |
| mpi2-y2 | radiative_X1 | kW/m2 | 0.180597 |
| mpi2-y2 | radiative_X2 | kW/m2 | 0.362365 |
| mpi2-y2 | radiative_X3 | kW/m2 | 0.77218 |
| mpi2-y2 | radiative_X4 | kW/m2 | 0.873541 |
| mpi2-y2 | radiative_X5 | kW/m2 | 0.343672 |
| mpi2-y2 | radiative_X6 | kW/m2 | 0.0338734 |
| mpi2-y2 | radiative_X7 | kW/m2 | 0.000151008 |
| mpi2-y2 | radiative_Y1 | kW/m2 | 0.161526 |
| mpi2-y2 | radiative_Y2 | kW/m2 | 0.309878 |
| mpi2-y2 | radiative_Y3 | kW/m2 | 0.705673 |
| mpi2-y2 | radiative_Y4 | kW/m2 | 1.52919 |
| mpi2-y2 | radiative_Y5 | kW/m2 | 0.241748 |
| mpi2-y2 | radiative_Y6 | kW/m2 | 0.000959484 |
| mpi2-y2 | radiative_Y7 | kW/m2 | 2.90254e-05 |
| mpi2-y2 | radiative_Z1 | kW/m2 | 0.84672 |
| mpi2-y2 | radiative_Z2 | kW/m2 | 1.25379 |
| mpi2-y2 | radiative_Z3 | kW/m2 | 1.18223 |
| mpi2-y2 | radiative_Z4 | kW/m2 | 1.01552 |
| mpi2-y2 | radiative_Z5 | kW/m2 | 0.881183 |
| mpi2-y2 | radiative_Z6 | kW/m2 | 0.488406 |
| mpi2-y2 | radiative_Z7 | kW/m2 | 0.320371 |
| mpi2-y2 | surface | C | 1.32521 |
| mpi4-xy22 | divergence_X1_hi | 1/s | 0.0207548 |
| mpi4-xy22 | divergence_X1_lo | 1/s | 0.011054 |
| mpi4-xy22 | divergence_X2_hi | 1/s | 0.27154 |
| mpi4-xy22 | divergence_X2_lo | 1/s | 0.177895 |
| mpi4-xy22 | divergence_X3_hi | 1/s | 0.748005 |
| mpi4-xy22 | divergence_X3_lo | 1/s | 0.620659 |
| mpi4-xy22 | divergence_X4_hi | 1/s | 1.73901 |
| mpi4-xy22 | divergence_X4_lo | 1/s | 1.89118 |
| mpi4-xy22 | divergence_X5_hi | 1/s | 0.571684 |
| mpi4-xy22 | divergence_X5_lo | 1/s | 0.749288 |
| mpi4-xy22 | divergence_X6_hi | 1/s | 0.0749273 |
| mpi4-xy22 | divergence_X6_lo | 1/s | 0.191546 |
| mpi4-xy22 | divergence_X7_hi | 1/s | 0.0190316 |
| mpi4-xy22 | divergence_X7_lo | 1/s | 0.020511 |
| mpi4-xy22 | divergence_Y1_hi | 1/s | 0.00541708 |
| mpi4-xy22 | divergence_Y1_lo | 1/s | 0.00581265 |
| mpi4-xy22 | divergence_Y2_hi | 1/s | 0.164384 |
| mpi4-xy22 | divergence_Y2_lo | 1/s | 0.105465 |
| mpi4-xy22 | divergence_Y3_hi | 1/s | 0.693107 |
| mpi4-xy22 | divergence_Y3_lo | 1/s | 0.597824 |
| mpi4-xy22 | divergence_Y4_hi | 1/s | 1.73462 |
| mpi4-xy22 | divergence_Y4_lo | 1/s | 1.80967 |
| mpi4-xy22 | divergence_Y5_hi | 1/s | 0.524912 |
| mpi4-xy22 | divergence_Y5_lo | 1/s | 0.612053 |
| mpi4-xy22 | divergence_Y6_hi | 1/s | 0.107485 |
| mpi4-xy22 | divergence_Y6_lo | 1/s | 0.22602 |
| mpi4-xy22 | divergence_Y7_hi | 1/s | 0.00763351 |
| mpi4-xy22 | divergence_Y7_lo | 1/s | 0.00933192 |
| mpi4-xy22 | divergence_Z1_hi | 1/s | 0.406672 |
| mpi4-xy22 | divergence_Z1_lo | 1/s | 0.608877 |
| mpi4-xy22 | divergence_Z2_hi | 1/s | 2.46555 |
| mpi4-xy22 | divergence_Z2_lo | 1/s | 2.49718 |
| mpi4-xy22 | divergence_Z3_hi | 1/s | 1.96453 |
| mpi4-xy22 | divergence_Z3_lo | 1/s | 2.21914 |
| mpi4-xy22 | divergence_Z4_hi | 1/s | 1.67687 |
| mpi4-xy22 | divergence_Z4_lo | 1/s | 1.75524 |
| mpi4-xy22 | divergence_Z5_hi | 1/s | 1.37108 |
| mpi4-xy22 | divergence_Z5_lo | 1/s | 1.52633 |
| mpi4-xy22 | divergence_Z6_hi | 1/s | 1.17005 |
| mpi4-xy22 | divergence_Z6_lo | 1/s | 1.22487 |
| mpi4-xy22 | divergence_Z7_hi | 1/s | 0.728816 |
| mpi4-xy22 | divergence_Z7_lo | 1/s | 0.812264 |
| mpi4-xy22 | enthalpy_local_X1 | kW/m2 | 1.05301 |
| mpi4-xy22 | enthalpy_local_X2 | kW/m2 | 4.25484 |
| mpi4-xy22 | enthalpy_local_X3 | kW/m2 | 7.46053 |
| mpi4-xy22 | enthalpy_local_X4 | kW/m2 | 12.3868 |
| mpi4-xy22 | enthalpy_local_X5 | kW/m2 | 5.30557 |
| mpi4-xy22 | enthalpy_local_X6 | kW/m2 | 2.54827 |
| mpi4-xy22 | enthalpy_local_X7 | kW/m2 | 0.0251711 |
| mpi4-xy22 | enthalpy_local_Y1 | kW/m2 | 0.271797 |
| mpi4-xy22 | enthalpy_local_Y2 | kW/m2 | 4.19185 |
| mpi4-xy22 | enthalpy_local_Y3 | kW/m2 | 12.3227 |
| mpi4-xy22 | enthalpy_local_Y4 | kW/m2 | 13.6085 |
| mpi4-xy22 | enthalpy_local_Y5 | kW/m2 | 5.24747 |
| mpi4-xy22 | enthalpy_local_Y6 | kW/m2 | 0.458104 |
| mpi4-xy22 | enthalpy_local_Y7 | kW/m2 | 0.0593652 |
| mpi4-xy22 | enthalpy_local_Z1 | kW/m2 | 11.209 |
| mpi4-xy22 | enthalpy_local_Z2 | kW/m2 | 29.5633 |
| mpi4-xy22 | enthalpy_local_Z3 | kW/m2 | 54.2572 |
| mpi4-xy22 | enthalpy_local_Z4 | kW/m2 | 63.074 |
| mpi4-xy22 | enthalpy_local_Z5 | kW/m2 | 80.0504 |
| mpi4-xy22 | enthalpy_local_Z6 | kW/m2 | 83.9453 |
| mpi4-xy22 | enthalpy_local_Z7 | kW/m2 | 81.4445 |
| mpi4-xy22 | mass_local_X1 | kg/s/m2 | 0.0291803 |
| mpi4-xy22 | mass_local_X2 | kg/s/m2 | 0.0696666 |
| mpi4-xy22 | mass_local_X3 | kg/s/m2 | 0.0820213 |
| mpi4-xy22 | mass_local_X4 | kg/s/m2 | 0.0354864 |
| mpi4-xy22 | mass_local_X5 | kg/s/m2 | 0.0921913 |
| mpi4-xy22 | mass_local_X6 | kg/s/m2 | 0.066036 |
| mpi4-xy22 | mass_local_X7 | kg/s/m2 | 0.0326131 |
| mpi4-xy22 | mass_local_Y1 | kg/s/m2 | 0.030438 |
| mpi4-xy22 | mass_local_Y2 | kg/s/m2 | 0.0774804 |
| mpi4-xy22 | mass_local_Y3 | kg/s/m2 | 0.0937172 |
| mpi4-xy22 | mass_local_Y4 | kg/s/m2 | 0.0386572 |
| mpi4-xy22 | mass_local_Y5 | kg/s/m2 | 0.0729712 |
| mpi4-xy22 | mass_local_Y6 | kg/s/m2 | 0.0617185 |
| mpi4-xy22 | mass_local_Y7 | kg/s/m2 | 0.0207836 |
| mpi4-xy22 | mass_local_Z1 | kg/s/m2 | 0.010351 |
| mpi4-xy22 | mass_local_Z2 | kg/s/m2 | 0.0294876 |
| mpi4-xy22 | mass_local_Z3 | kg/s/m2 | 0.0535304 |
| mpi4-xy22 | mass_local_Z4 | kg/s/m2 | 0.0798951 |
| mpi4-xy22 | mass_local_Z5 | kg/s/m2 | 0.105031 |
| mpi4-xy22 | mass_local_Z6 | kg/s/m2 | 0.155592 |
| mpi4-xy22 | mass_local_Z7 | kg/s/m2 | 0.158448 |
| mpi4-xy22 | mdot_X1 | kg/s | 0.000515956 |
| mpi4-xy22 | mdot_X2 | kg/s | 0.000511438 |
| mpi4-xy22 | mdot_X3 | kg/s | 0.000687465 |
| mpi4-xy22 | mdot_X4 | kg/s | 0.000917347 |
| mpi4-xy22 | mdot_X5 | kg/s | 0.000684065 |
| mpi4-xy22 | mdot_X6 | kg/s | 0.000470428 |
| mpi4-xy22 | mdot_X7 | kg/s | 0.000487899 |
| mpi4-xy22 | mdot_Y1 | kg/s | 0.000466264 |
| mpi4-xy22 | mdot_Y2 | kg/s | 0.000436732 |
| mpi4-xy22 | mdot_Y3 | kg/s | 0.000543645 |
| mpi4-xy22 | mdot_Y4 | kg/s | 0.00066144 |
| mpi4-xy22 | mdot_Y5 | kg/s | 0.000508054 |
| mpi4-xy22 | mdot_Y6 | kg/s | 0.000453401 |
| mpi4-xy22 | mdot_Y7 | kg/s | 0.000480162 |
| mpi4-xy22 | mdot_Z1 | kg/s | 0.000105764 |
| mpi4-xy22 | mdot_Z2 | kg/s | 0.000238343 |
| mpi4-xy22 | mdot_Z3 | kg/s | 0.000355977 |
| mpi4-xy22 | mdot_Z4 | kg/s | 0.000524195 |
| mpi4-xy22 | mdot_Z5 | kg/s | 0.000732717 |
| mpi4-xy22 | mdot_Z6 | kg/s | 0.00093099 |
| mpi4-xy22 | mdot_Z7 | kg/s | 0.00110396 |
| mpi4-xy22 | pressure_X1_hi | Pa | 0.00964478 |
| mpi4-xy22 | pressure_X1_lo | Pa | 0.00734967 |
| mpi4-xy22 | pressure_X2_hi | Pa | 0.025372 |
| mpi4-xy22 | pressure_X2_lo | Pa | 0.0202424 |
| mpi4-xy22 | pressure_X3_hi | Pa | 0.0463352 |
| mpi4-xy22 | pressure_X3_lo | Pa | 0.0444118 |
| mpi4-xy22 | pressure_X4_hi | Pa | 0.034844 |
| mpi4-xy22 | pressure_X4_lo | Pa | 0.0341841 |
| mpi4-xy22 | pressure_X5_hi | Pa | 0.0457329 |
| mpi4-xy22 | pressure_X5_lo | Pa | 0.0451481 |
| mpi4-xy22 | pressure_X6_hi | Pa | 0.0260563 |
| mpi4-xy22 | pressure_X6_lo | Pa | 0.0312887 |
| mpi4-xy22 | pressure_X7_hi | Pa | 0.00991885 |
| mpi4-xy22 | pressure_X7_lo | Pa | 0.0132292 |
| mpi4-xy22 | pressure_Y1_hi | Pa | 0.0120499 |
| mpi4-xy22 | pressure_Y1_lo | Pa | 0.00869893 |
| mpi4-xy22 | pressure_Y2_hi | Pa | 0.0317535 |
| mpi4-xy22 | pressure_Y2_lo | Pa | 0.0264841 |
| mpi4-xy22 | pressure_Y3_hi | Pa | 0.0449863 |
| mpi4-xy22 | pressure_Y3_lo | Pa | 0.0453641 |
| mpi4-xy22 | pressure_Y4_hi | Pa | 0.0327043 |
| mpi4-xy22 | pressure_Y4_lo | Pa | 0.0328461 |
| mpi4-xy22 | pressure_Y5_hi | Pa | 0.043622 |
| mpi4-xy22 | pressure_Y5_lo | Pa | 0.0417372 |
| mpi4-xy22 | pressure_Y6_hi | Pa | 0.0228668 |
| mpi4-xy22 | pressure_Y6_lo | Pa | 0.0295312 |
| mpi4-xy22 | pressure_Y7_hi | Pa | 0.00657885 |
| mpi4-xy22 | pressure_Y7_lo | Pa | 0.00905668 |
| mpi4-xy22 | pressure_Z1_hi | Pa | 0.00682474 |
| mpi4-xy22 | pressure_Z1_lo | Pa | 0.00589147 |
| mpi4-xy22 | pressure_Z2_hi | Pa | 0.0163545 |
| mpi4-xy22 | pressure_Z2_lo | Pa | 0.0149179 |
| mpi4-xy22 | pressure_Z3_hi | Pa | 0.0206307 |
| mpi4-xy22 | pressure_Z3_lo | Pa | 0.0184392 |
| mpi4-xy22 | pressure_Z4_hi | Pa | 0.0334098 |
| mpi4-xy22 | pressure_Z4_lo | Pa | 0.0342305 |
| mpi4-xy22 | pressure_Z5_hi | Pa | 0.0397102 |
| mpi4-xy22 | pressure_Z5_lo | Pa | 0.0355935 |
| mpi4-xy22 | pressure_Z6_hi | Pa | 0.0436659 |
| mpi4-xy22 | pressure_Z6_lo | Pa | 0.0452486 |
| mpi4-xy22 | pressure_Z7_hi | Pa | 0.0399724 |
| mpi4-xy22 | pressure_Z7_lo | Pa | 0.041736 |
| mpi4-xy22 | probe_O2 | mol/mol | 0.0176167 |
| mpi4-xy22 | probe_T | C | 63.5746 |
| mpi4-xy22 | qdot_X1 | kW | 0.00203358 |
| mpi4-xy22 | qdot_X2 | kW | 0.0163555 |
| mpi4-xy22 | qdot_X3 | kW | 0.0407088 |
| mpi4-xy22 | qdot_X4 | kW | 0.0668416 |
| mpi4-xy22 | qdot_X5 | kW | 0.0483245 |
| mpi4-xy22 | qdot_X6 | kW | 0.0179961 |
| mpi4-xy22 | qdot_X7 | kW | 0.00615329 |
| mpi4-xy22 | qdot_Y1 | kW | 0.00282656 |
| mpi4-xy22 | qdot_Y2 | kW | 0.012287 |
| mpi4-xy22 | qdot_Y3 | kW | 0.0466493 |
| mpi4-xy22 | qdot_Y4 | kW | 0.0587271 |
| mpi4-xy22 | qdot_Y5 | kW | 0.0460757 |
| mpi4-xy22 | qdot_Y6 | kW | 0.0174174 |
| mpi4-xy22 | qdot_Y7 | kW | 0.0046451 |
| mpi4-xy22 | qdot_Z1 | kW | 0.0148924 |
| mpi4-xy22 | qdot_Z2 | kW | 0.0450255 |
| mpi4-xy22 | qdot_Z3 | kW | 0.0569304 |
| mpi4-xy22 | qdot_Z4 | kW | 0.0814133 |
| mpi4-xy22 | qdot_Z5 | kW | 0.0955993 |
| mpi4-xy22 | qdot_Z6 | kW | 0.10761 |
| mpi4-xy22 | qdot_Z7 | kW | 0.115087 |
| mpi4-xy22 | radiative_X1 | kW/m2 | 0.282776 |
| mpi4-xy22 | radiative_X2 | kW/m2 | 0.55049 |
| mpi4-xy22 | radiative_X3 | kW/m2 | 1.00754 |
| mpi4-xy22 | radiative_X4 | kW/m2 | 1.66396 |
| mpi4-xy22 | radiative_X5 | kW/m2 | 0.145533 |
| mpi4-xy22 | radiative_X6 | kW/m2 | 0.0338789 |
| mpi4-xy22 | radiative_X7 | kW/m2 | 0.000152957 |
| mpi4-xy22 | radiative_Y1 | kW/m2 | 0.282921 |
| mpi4-xy22 | radiative_Y2 | kW/m2 | 0.548362 |
| mpi4-xy22 | radiative_Y3 | kW/m2 | 1.14316 |
| mpi4-xy22 | radiative_Y4 | kW/m2 | 1.58415 |
| mpi4-xy22 | radiative_Y5 | kW/m2 | 0.264823 |
| mpi4-xy22 | radiative_Y6 | kW/m2 | 0.0034844 |
| mpi4-xy22 | radiative_Y7 | kW/m2 | 3.92833e-05 |
| mpi4-xy22 | radiative_Z1 | kW/m2 | 0.957964 |
| mpi4-xy22 | radiative_Z2 | kW/m2 | 1.68491 |
| mpi4-xy22 | radiative_Z3 | kW/m2 | 1.61881 |
| mpi4-xy22 | radiative_Z4 | kW/m2 | 1.34743 |
| mpi4-xy22 | radiative_Z5 | kW/m2 | 1.04982 |
| mpi4-xy22 | radiative_Z6 | kW/m2 | 0.686069 |
| mpi4-xy22 | radiative_Z7 | kW/m2 | 0.350686 |
| mpi4-xy22 | surface | C | 1.08732 |

Zapisane porównania: 45; brakujące pary: 0. Brakujące porównania nie oznaczają zgodności.

[Dane maszynowe i hashe dowodów](benchmark-v3-data.json). Archiwa natywne pozostają na dysku komputera; JSON nie zastępuje surowych pól.

Kryteria regresji demonstracji edukacyjnej; bez deklaracji walidacji inżynierskiej.
