# Simulation matrix, phased validation and acceptance gates

**Working now (Phase 0):** reduced-order electrical/thermal TEC model; three junction temperatures; MCT bias, optical and thermistor heating; gas N2/Ar/Kr or mixtures; gas-pressure/rarefaction trend; radiation; warm-aperture load; bond-wire conduction; hot-side sink; TEC I/V/Joule/Qc/Qh; current, gas, pressure, aperture and detector-bias sweeps; illustrative transient and Monte Carlo sensitivity. This is a qualitative proof of concept with OEM-limits anchoring.

| Priority | Study | Future formulation | Critical missing data |
|---|---|---|---|
| P0 | TEC lift Q-I-ΔT and V-I | Calibrated cascade thermoelectric network | Full OEM performance curves and holdout measurements |
| P0 | MCT detector self-heating | R(T,V) + spectral optical absorption | Device measured R(T,V), spectrum and die attach |
| P0 | Hot-side/header conduction | Contact/thermal network | Sink Rtheta, ceramic-to-header interfaces |
| P0 | Backfill gas N2/Ar/Kr/blends | k(T,p,x), Knudsen and enclosure conduction | Gas mixtures, wall accommodation, actual cavity geometry |
| P0 | Package cap/window radiation | View-factor radiosity and spectral emissivity | Optical transmission, calibrated eps(lambda), Fij |
| P1 | Aperture and shield design | Multi-surface radiation + support conduction | Full 3D geometry, emissivity and aperture acceptance |
| P1 | Bond-wire/die attach leaks | Local thermal contact FEM | Wire and adhesive dimensions/properties |
| P1 | Transients and control | Validated capacities, PID, thermistor lag | Measured cooldown and controller response |
| P1 | Nonideal TEC thermodynamics | S(T), sigma(T), k(T), Thomson | Materials and contacts, real stage allocation |
| P1 | Package gas ageing/leaks | Mass balance and temperature drift | Leak rate, impurity, permeation and outgassing |
| P1 | Parameter inversion | Multicurve fitting, holdout, UQ | Independent I-V-T-Q data |
| P2 | 3D coupled thermoelectric FEM | Elmer/Gmsh/FEniCSx/COMSOL | Healed CAD, stage netlist, anisotropy, contacts |
| P2 | Internal gas CFD / rarefaction | OpenFOAM or kinetic treatment | Actual geometry, pressure and kinetic regime |
| P2 | Mechanical stress / reliability | Thermo-elastic + solder fatigue | CTE, E(T), solder creep, cycling |
| P2 | Optics / stray radiation | Raytrace + spectral transfer | Window AR, detector spectral absorption |
| P2 | MCT noise and D* | Shot/Johnson/1-f/GR, readout circuit | Noise spectra, photodetector physics |
| P2 | Failure-to-cool diagnostics | Inverse multiphysics + FMEA | Measured failure signatures and populations |

## Validation checkpoints

- **Gate A (working code):** deterministic tests, documented SI units, stage energy conservation and JSON plots. Initial implementation locally passed 6 tests.
- **Gate B (calibration):** digitize whole manufacturer lift and voltage performance curves. Hold out some curves. Proposed engineering *targets*: <5% V error and <10% temperature-lift error over validated domain; not guaranteed.
- **Gate C (geometry):** no inadvertent micron-scale gaps/overlaps, watertight meshed domains, verified materials and electrical continuity. Visual Rev6 FAILS this gate.
- **Gate D (spatial numerical convergence):** proposed <2% mesh dependence in detector T, <1% net energy-balance residual.
- **Gate E (physical device):** independent I,V,T_hot,T_cold, parasitics, gas and ambient data across several operating points and calibrated uncertainty coverage.

## Strategy

Start with calibrated package-level equivalent TEC heat-pump surfaces (faster, better identified), then mesh all 88 legs and copper/solder when manufacturer stage geometry and independent test data justify the complexity. Maintain separate 'visual CAD', 'solver geometry', 'materials' and 'measurements' artifacts.
