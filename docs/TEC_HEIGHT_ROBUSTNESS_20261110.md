# Paired model-path robustness of the 0.60 mm TEC design

## Registered comparison

The question is whether the V3.20 **-3.705321 K** 0.60-minus-0.50 mm mount-temperature difference persists when selected uncertain paths are changed. The original two V3.20 cases are controls, not new samples. All new cases keep 29/11/4 couples, 88 signed nonlinear P/N legs, the four source-mapped 3D ceramic TET4 fields, source-derived Cu multiports and wire geometry, 300 K ambient, 100 Pa krypton, imposed 2 mW detector heat and **0.5956680349614825 W terminal input**. Actual current is solved along with the temperatures. The net88 middle foot stays a thermal port but is not a series electrical contact. The original 3D electrical Gate B remains FAIL/STOP.

Before any new solve, the [contract](../data/tec_height_robustness_20261110/contract.json) fixed three paired one-factor scenarios and their execution and audit code hashes: (1) interstage gas factor 0, outer 3 mm path retained; (2) outer effective gas gap 1.5 mm, interstage factor 1; and (3) +5 K/W external mounting thermal resistance, with both gas paths unchanged. Each pair uses identical parameters for both geometries. The latter adds to, rather than replaces, the original 4.83338696 K/W external resistance; both are engineering scenarios, not measured hardware.

At most six new full-system solves are permitted, two per pair, with no unbounded retries; each is limited to 300 s, 2 CPUs and 4 GiB, and no more than two run at once. They warm-start from the actual same-geometry V3.20 solution but recompute all nonlinear legs, spatial ceramic loads and residuals; no field or offset is frozen. `scripts/tec_height_v321_runner.py` deterministically constructs the auditable source transformation from unchanged V3.20 source, seals its resulting source hash, and changes only these three registered physical parameters and initial state. The terminal power and original source convergence criteria remain in force. `scripts/tec_height_v321_audit.py` reconstructs each result independently from actual saved leg, copper, lead, die, radiative, gas and sink values, with stage/global <=1e-8 W and power error <=1e-8 W.

These are deliberately sparse model scenarios, not confidence intervals or a proof of robustness against all possible parameters. The 3 mm/1.5 mm external gas path and interstage links are engineering proxies that could occupy overlapping real cavity volume; no native gas field or exact partition is asserted. The P/N source specimens are distinct research samples, not a matched commercial grade, and the >300 K continuation is assumed. No 3D metal current field or detector semiconductor model is solved.

## Independently audited results

| Case | 0.50 mm die K | 0.60 mm die K | Δ die K | Δ top ceramic K |
|---|---:|---:|---:|---:|
| V3.20 reference | 219.368939 | 215.663617 | -3.705321 | -3.705882 |
| Interstage gas off | 218.898416 | 215.159111 | -3.739304 | -3.739873 |
| Outer gas gap 1.5 mm | 219.743334 | 216.110166 | -3.633168 | -3.633848 |
| Sink resistance +5 K/W | 221.201510 | 217.437009 | -3.764501 | -3.765103 |

| Case | Height mm | I A | V V | Input W | Hot ceramic K | Sink W | Cold-leg Qc mW | Outer gas mW | Internal gas mW | Cu Joule mW | Max stage residual W | Global residual W |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V3.20 reference | 0.5 | 0.400298 | 1.488062 | 0.595668035 | 303.761291 | 0.592285 | 6.099082 | 3.401815 | 10.141145 | 2.060049 | 1.2e-09 | -1.04e-09 |
| V3.20 reference | 0.6 | 0.370631 | 1.607175 | 0.595668035 | 303.764120 | 0.592474 | 6.051364 | 3.549955 | 9.423429 | 1.852711 | 7.73e-10 | -6.65e-10 |
| Interstage gas off | 0.5 | 0.400009 | 1.489136 | 0.595668035 | 303.762307 | 0.592331 | 4.907987 | 3.419624 | 0.000000 | 2.055791 | 1.33e-09 | 1.16e-09 |
| Interstage gas off | 0.6 | 0.370379 | 1.608266 | 0.595668035 | 303.765194 | 0.592522 | 4.949485 | 3.569128 | 0.000000 | 1.848918 | 7.41e-10 | -6.37e-10 |
| Outer gas gap 1.5 mm | 0.5 | 0.400434 | 1.487555 | 0.595668035 | 303.777960 | 0.595064 | 7.087928 | 6.263363 | 10.111695 | 2.062256 | 1.39e-09 | -1.2e-09 |
| Outer gas gap 1.5 mm | 0.6 | 0.370764 | 1.606594 | 0.595668035 | 303.781465 | 0.595372 | 7.078805 | 6.536048 | 9.391881 | 1.854915 | 1.09e-09 | -9.34e-10 |
| Sink resistance +5 K/W | 0.5 | 0.396975 | 1.500518 | 0.595668035 | 306.564358 | 0.576280 | 6.060918 | 3.250240 | 10.297827 | 2.045467 | 1.77e-09 | 1.54e-09 |
| Sink resistance +5 K/W | 0.6 | 0.367566 | 1.620575 | 0.595668035 | 306.568285 | 0.576475 | 6.015946 | 3.401800 | 9.575321 | 1.839737 | 6.86e-10 | 5.91e-10 |

**Result:** 6 new independently audited solves, 3 paired scenarios. The sampled die difference spans -3.764501 to -3.633168 K. The custom design is colder in all sampled cases. This is conditional on the listed model paths and not an uncertainty interval or empirical proof. Detailed individual copper-stage, lead, gas and radiation terms, iterations, timestamps, input hashes and audit residuals are in the machine-readable summary and per-case records.

## Separate fixed-field copper sensitivity

With the original V3.20 face temperatures and currents held fixed, contact area resistances of $10^{-6}$, $10^{-5}$ and $10^{-4}$ m² K/W give Cu C2 heat of 86.714, 62.614 and 17.532 mW for 0.50 mm and 84.288, 61.899 and 17.832 mW for 0.60 mm. An independent incidence-matrix calculation passes; these are transport-only calculations, not coupled die-temperature results or measured contact properties.
