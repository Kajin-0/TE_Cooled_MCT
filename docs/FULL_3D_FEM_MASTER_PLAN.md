# Fully coupled 3D TEC FEM and TO-66 package thermal-model roadmap

Status (2026-10-28): G1 single-couple coupled 3D FEM is implemented and numerically
verified; G2a four-couple single-stage FEM is also verified. See
[G1 evidence](PHASE1_G1_RESULT.md) and [G2a results](PHASE1_G2A_RESULT.md).
G2b now has an [88-leg geometry/netlist/mesh feasibility proof](PHASE1_G2B_FEASIBILITY.md)
with three isolated stage circuits and six ports; its coupled full-TEC solution
and G3–G5 remain separate gates.
The full 88-leg, three-stage TEC/package has not been simulated.

## Objectives
Create a reproducible, genuinely spatial thermoelectric finite-element simulation of the three-stage 44-couple TEC, alumina plates, copper links, solder, detector, Kovar header, enclosure, and gas/radiation environment. Report datasheet validation and novel spatial insights. Use a compact HgCdTe die material/heat-load model. LSDDTS integration is deferred indefinitely by user direction.

## Recommended stack
- CAD: parameterized OpenCascade/CadQuery; keep visual reference and separate solver-grade geometry.
- Meshing: Gmsh OpenCASCADE BooleanFragments and physical volumes/face tags; conformal shared interfaces; no artificial micron-scale contact gaps.
- Coupled thermoelectric FEM: Elmer FEM ThermoElectricSolver (actual strongly coupled temperature/electric potential equations and Seebeck/Peltier/Joule). Thermal conduction, radiation and gas properties should be integrated in stages. Python orchestration and PyVista/Matplotlib outputs.
- Independent validation: current 4-node model and single-pellet finite-volume model; the existing LSDDTS uses DOLFINx/PETSc but a new thermoelectric weak form there is a higher-implementation-risk alternative.
- Compute: Linux headless MPI where supported, explicit memory and mesh budgets; visualize over SSH, export VTK/XDMF and HTML plots.

## PDE and energy bookkeeping
Choose and document a single electric sign convention throughout:
E=-grad(phi)
J = sigma(T) [E - S(T) grad(T)]
q = -k(T) grad(T) + T S(T) J
div(J)=0
div(q)=J dot E  (consistent constitutive conventions and boundary flux signs)
Thomson coefficient tau=T dS/dT: include temperature dependence in actual coupled solver, not as decorative post-processing. Verify against P/N single-couple analytical solution, both current signs, open-circuit Seebeck, I=0 passive conduction, Joule/Peltier heat balance.

## Verification and implementation gates
G0 Sources and geometry: preserve sourced hot side 6.4x6.4 mm, cold 2.4x2.4 mm, overall 3.8+/-0.15 mm, 44 P-N couples. 28/12/4 stage allocation is an inference, not a published manufacturer netlist. Obtain or explicitly reconstruct physically valid series wiring, individual pads, ceramic, solder and metal contacts and nine package pins. Repair Rev6 15/10/6 micron gaps and material continuity before FEM.

G1 Single full P/N couple: solve nonlinear 3D current and heat on same conforming mesh, validate Seebeck polarity, Peltier, Joule, sensible heat. Proposed gates: <1% global heat error, <0.5% current mismatch, <1% cold T change between two finest meshes (these are target criteria, not attained).

G2 Full three-stage TEC: 88 legs, all copper pads and actual stage series connections, four ceramic plates and solder. Verify currents do not leak across non-contacting metal, stable solution at 0..1A, benchmark voltage/current and DeltaT/current no load, Qcold vs DeltaT, Qmax and Imax at specified non-simultaneous conditions, and stage T(I). Use digitized full OEM curves; hold out points independent of fitted endpoints. Proposed <5% withheld voltage and <10% withheld DeltaT or lift error over declared range; do not fit and validate on the same two endpoints.

G3 Complete package heat paths: Kovar header, solder-to-header, die attach, Au wires, thermistor, MCT die, cap and spectral window. Add radiative view-factor matrix and equivalent optical baffles; run inert gas conduction first (N2 Ar Kr and mixtures, plus pressure and Knudsen limits). Add CFD only if convection is shown material by Rayleigh/geometry assessment. Identify heat flow to hot side and ambient.

G4 Compact HgCdTe thermal die: assign composition-dependent k(T,x), Cp(T,x), density, geometry, die attach and measured or assumed emissivity. Apply electrical heating from V*I (or V²/R; never both) and optical heating with declared thermalized absorbed fraction. Sweep die temperature, bond-wire and contact heat leakage and any user-provided compact R(T,V). Do not connect to LSDDTS.

G5 Qualification: mesh convergence at representative points, thermodynamic residual, parameter-identifiability, material uncertainty, gas law applicability, temperature dependent P/N and HgCdTe properties, comparison against withheld OEM curve points and independent physical device data.

## Report requirements

Datasheet confirmation:
1. DeltaT(I) at Th=300K and near-zero cold load, with source curves and residuals.
2. V(I) and Pin(I), and stage electrical resistance.
3. Qc vs DeltaT at several currents; Qmax, DeltaTmax under their proper separate test conditions.
4. Tcold/Tmiddle/Tbottom/hot vs current, hot-side thermal resistance cases.
5. Mesh convergence, energy/current balances, fitted vs withheld point chart.

Value-added spatial and coupled plots:
6. 3D T(x,y,z), Joule qdot(x,y,z), electric potential and current-density vectors, Peltier junction heat flux and local hotspots.
7. Heat budget per stage (Peltier, conduction, Joule, gas, radiation, wires, detector, interface) and stage-to-stage heat redistribution.
8. COP, min Pin needed for target T, Pareto frontier vs pellet length/area and drive current.
9. Gas backfill species/mixtures, pressure, cap/window temperature, aperture diameter/baffle geometry vs detector T.
10. S(T), sigma(T), k(T) perturbations, solder/contact resistances, CTE/stress, transient cooldown and controller response.
11. Detector die and mount temperature, simple bias self-heating and optical deposited power versus cooler current; no semiconductor transport model.
12. Sensitivity, uncertainty and identifiability charts; machine-readable provenance, mesh IDs, physics version, vendor datasheet source, measured-data status.

## HgCdTe die physical materials
Heckman, Gonzalez and Guha, Applied Optics 47, 578-582 (2008), report x=0.29 bulk: thermal k=2.41 W/m/K (90K), 1.61 (148K), 0.973 (298K), cp=0.130/0.146/0.176 J/g/K, density 6.83 g/cm3 (298K). For x=0.23 they report k=1.01 W/mK at 298K. Interpolate only in supported composition and temperature windows with source-tagged uncertainty; detector multilayer thermal interfaces matter as much as bulk die k.

## Resource/reproducibility plan
Run tiny single-couple mesh first, then full 3-stage with coarse mesh, then local contact refinement. Do expensive sweeps at coarse mesh with representative high-resolution rechecks, cache by hash. Pin versions of Gmsh, Elmer, material records, source SHA, compact HgCdTe thermal material and load-source identifier. Export CSV, JSON, VTK/PyVista, HTML plots; optional PDF report.

## Sources
Elmer solver: https://github.com/ElmerCSC/elmerfem/blob/devel/fem/src/modules/ThermoElectricSolver.F90
Gmsh: https://gmsh.info/doc/texinfo/gmsh.html
TEC: https://www.tec-microsystems.com/Download/Datasheets/Thermoelectric%20Coolers/MC04%20Series/3MC04-044-05_Datasheet_2019.pdf
HgCdTe: https://opg.optica.org/ao/abstract.cfm?uri=ao-47-4-578
OpenFOAM multi-region heat transfer (conditional use): https://openfoam.org/release/13/

STOP: Never describe current geometry-sensitive 4-node plus single-pellet FVM as the full coupled FEM. Do not modify, invoke or connect LSDDTS absent a new explicit request.

## OpenFOAM decision
Use Elmer FEM for full 3D thermoelectric solids (Seebeck, Peltier, Joule and Fourier conduction), not stock OpenFOAM. Use OpenFOAM separately for cavity gas flow and solid-fluid conjugate heat transfer if the Rayleigh screen and pure conduction comparison show meaningful convection. OpenFOAM Foundation 13 supports modular foamMultiRun with fluid and solid modules; OpenCFD variants provide chtMultiRegionFoam. Pin one distribution/version. For low pressure Knudsen regimes use appropriate rarefied corrections rather than no-slip continuum CFD. See docs/OPENFOAM_FEASIBILITY.md.
