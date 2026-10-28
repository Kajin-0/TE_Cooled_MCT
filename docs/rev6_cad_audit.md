# Revision 6 TO-66 / three-stage TEC CAD audit (2026-10-28)

**Verdict:** plausible detailed visualization and STEP-exportable reference, **not a simulation-ready manifold, connected model**.

## Manufacturer-supported envelope

TEC Microsystems 3MC04-044-05: 6.4×6.4 mm hot ceramic; 2.4×2.4 mm cold ceramic; height 3.8±0.15 mm; 44 P-N couples (88 legs); nominal 0.4×0.4 mm pellets; Bi-Te legs, Al2O3 and Sn-Sb internal assembly.

Nominal overall limiting values at 300 K vacuum: ΔTmax=113 K, Qmax=0.5 W, Imax~1 A, Umax~3.5 V, AC resistance ~2.9 Ω. Maxima are not simultaneous.

## Inferred geometry

- 28/12/4 P-N couples by stage, not published by OEM.
- Intermediate plates 4.55 and 3.25 mm square.
- Pellet heights 1.07, 0.82, 0.64 mm; ceramic ~0.22 mm.
- Pad/metallization thicknesses, solder geometry, contact artwork and die attach are not confirmed.
- Nine feedthroughs in a C-shaped TO-66 pattern; six functional terminals (two each for TEC, detector and thermistor).
- Two clipped heavy tinned copper TEC power leads; no exposed external TEC interstage jumper wires.

## Confirmed unwanted geometric gaps

The CAD source places small separations between materials. Typical modeled gaps: 15 µm (ceramic-to-copper), 10 µm (copper-to-solder), 6 µm (solder-to-pellet). These are **not physical domains with defined properties or explicit contact boundary conditions**. A STEP file may export successfully while thermal/electrical graph is disconnected.

The on-ceramic serpentine interconnects are schematic and do not establish a validated **through-all-three-stages** electrical circuit. The detailed CAD must be reconstructed with verified contact topology and pads.

## Missing data

S_p,n(T), sigma_p,n(T), k_p,n(T), heat capacity, density; electrical/thermal contact resistance; MCT R(T) and optical absorption; die attach; bond wires; window radiative transparency; real backfill gas and pressure; header-to-sink contact conductance; TEC stage wiring; experimental validation.

## Recommended pathway

1. Reduced-order network fitted to multiple independent performance data.
2. Separate parametric, connected solids for mesh generation and material contact tagging.
3. 3D coupled electric/thermal FEM, then thermoelastic stress; include netlist & mesh quality gates.
4. Verify I,V,T,Q against measurements before interpreting package internal T.
5. Retain Rev6 as visual artifact, not trusted FEM master.
