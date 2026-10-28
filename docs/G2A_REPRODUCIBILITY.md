# Reproduce the real multi-couple G2a FEM

Use the existing pinned `tecooledmct-fem:26.2.1` image from G1. No reinstall is
needed on srv1323456. All commands below are run from TE_Cooled_MCT:

```bash
./fem/run.sh python -m tecooledmct.fem_g2a_run --out outputs/fem-g2a
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q
./fem/run.sh python -m tecooledmct.cli --quick --out outputs/check-g2a
./fem/run.sh python -m tecooledmct.geometry_demo --out outputs/pellet-study-g2a
```

`--quick` runs a single 0.10 mm mesh, a +0.15 A point, −0.1/0/+0.1 A loaded
cases and open-circuit Seebeck. It checks real Elmer fields but does not establish
mesh convergence. The full run adds 0.16/0.10/0.065 mm meshes, seven loaded current
points and both current polarities with isothermal outer thermal faces.

Geometry is configurable through `Stage` in `tecooledmct/fem_g2a.py` and the CLI:
`--couples`, `--columns`, `--leg-width-mm`, `--leg-height-mm`, `--gap-mm`.
The columns must divide twice the couple count. The published G2a run uses four
couples; other geometries must be rerun and verified, not assumed validated.

## Connected specimen and explicit netlist

The default has eight 0.4 × 0.4 × 1.0 mm legs on a 0.8 mm pitch in two rows of
four. Traverse row 0 left to right, then row 1 right to left: N, P, N, P, N, P,
N, P. Seven rectangular Cu bridges alternate between cold and hot faces, each
0.1 mm thick. Two separate hot Cu terminal pads complete the single path.
The two alumina substrates are 3.0 × 1.4 × 0.2 mm. All dimensions are assumptions
for numerical verification; none are a reconstructed manufacturer netlist.

| IDs | Domains / boundaries |
|---|---|
| 1–8 | Separately tagged legs, N on even path index, P on odd index |
| 9–15 | Separate Cu bridges, cold/hot alternating along the path |
| 16, 17 | Current-in N hot pad, grounded P hot pad; only external electrical contacts |
| 18, 19 | Hot and cold alumina supports |
| 101 | Bottom alumina bath, 300 K |
| 102 | Top alumina, uniform 8 mW inward heat load for loaded sweep |
| 103, 104 | Specified inward current and grounded potential |
| 105 | Other exposed faces, natural zero total q·n and J·n |
| 1001–1025 | Explicit conformal material-contact groups |

`mesh_*/manifest.json` records every body, box, material property, BC, contact
area, cut plane and the ordered conductor path. A separately computed box
intersection check rejects overlaps and unintended face/edge/point shorts.
After OpenCascade fragmentation and meshing, actual tetrahedron face adjacency
must match the intended netlist and contact areas. Shared mesh nodes are also
checked for illegal conductor connections at only an edge or point. All material
volumes must match their analytical boxes. The conductor graph has 17 vertices,
16 edges, exactly two degree-one terminals and 15 degree-two internal vertices;
connectedness and this degree sequence prove one unique unbranched path.

The Cu links touch both leg end faces and their ceramic support. They do not
overlap other metal volumes. Thermal/electric contacts are ideal (zero resistance),
solder is omitted and sidewall losses are zero. Alumina uses k = 30 W/(m K) and
sigma = 1e-12 S/m, the G1 insulating approximation; leakage is quantified.

## Actual coupled physics and independent reference

`ThermoElectricSolver` solves T and phi on all 19 bodies in one spatial system:
E = −grad(phi), J = sigma(E − S grad(T)), q = −k grad(T) + TSJ,
div(J) = 0, div(q) = J·E. Continuous total heat flux and discontinuous S produce
junction Peltier conversion. Ordinary HeatSolve or prescribed lumped temperatures
are not substituted. Positive drive follows N up, cold bridge, P down, hot
bridge, then the next N up, through all four couples.

Material constants are the unchanged illustrative G1 inputs: Goldsmid Table 1
P/N S and sigma near 300 K, generic Ferrotec k, assumed Cu and proxy alumina.
Sources and limits: [G1 provenance](FEM_G1_REPRODUCIBILITY.md). In particular the
temperature curves and OEM actual contacts are unknown. Constants in the
benchmark are not calibrated physical material curves.

The independent ideal network has alpha = N(Sp−Sn),
Rlegs = N L(1/sigmap+1/sigman)/A, K = N(kp+kn)A/L. An explicit metal estimate
adds rhoCu times bridge centre-to-centre length divided by width×thickness,
and terminal half-width lengths. It does not fit 3D resistance. The analytical
reference splits total Joule power equally between hot and cold and treats
junctions as isothermal. Actual metal heating distribution and finite ceramic/
Cu spreading make the spatial FEM differ. No OEM maxima are used for fitting.

Loaded cases apply 8 mW at the outer cold face and fix the outer hot face at
300 K. Tcold is solved, not imported from G1. Positive/negative clamped cases fix
both faces to 300 K to prove heat-pumping direction from the cold-face reaction.
Open circuit fixes them to 300/280 K with zero applied current. Its voltage is
compared with the independently summed S dT over all eight actual leg-end
temperatures. Voltage scaling is also compared with the immutable G1 clamped
and open-circuit results at identical current/outer-temperature BCs; finite
ceramic and artwork differences are explicitly retained.

## Numerical checks and raw flux limits

The independent postprocessor reconstructs E, J, q, J·E, irreversible J²/sigma
and the original nonlinear weak residuals from real Elmer VTU fields. With
constant properties, J is constant and q affine within each tetrahedron, so
weak-form integration is exact. The hot-bath and ground reactions are compared
with load/power and current. Direct bath-gradient energy flux provides a separate
check of global energy; it is not replaced with the nearly exact weak reaction.
Free-node residual norms catch internal imbalance hidden by global cancellation.

Every leg has an interior horizontal cut; every bridge has a cut in its gap
between leg footprints. Polygon intersection and triangle integration give the
direct current and exact affine heat flux. For each leg, integrate J²/sigma over
the entire volume and compare with I²L/(sigma A). Every body's Joule power is
recorded, including metal and negligible ceramic contributions. No claim of
converged terminal-corner current density or local flux peaks follows from global
balance; raw P1 terminal-gradient currents are reported separately.

Declared gates include <0.5% every driven leg/bridge current error on the fine
mesh, <1 microamp absolute cut error at zero drive, <1% finest direct bath energy
mismatch, <1% of lift change in mean and maximum cold temperature between the
two finest meshes, <1% voltage mesh change, <2% per-leg Joule error, and <2%
ideal-network driven voltage error. Open thermovoltage must agree with the
actual-junction Seebeck sum to <1%; G1 voltage scaling has a 3% tolerance because
the Cu artwork and ceramic footprints differ. Residuals and all deviations are
reported regardless of pass/fail. The temperature and circuit field are verified,
not manufacturing accuracy or asymptotic convergence order.

## Provenance and outputs

Each run checks all eight G1 source hashes and 128 published artifact hashes,
runs the official Elmer thermoelectric reference-norm test and records new source
hashes at start/end. Each case records SIF and original VTU SHA256, exit code,
nonlinear iterations/residual, actual BCs and all diagnostics. G1 source, tests
and published evidence are preserved. Default CI runs the pure geometry/reference
tests; `TE_FEM_SMOKE=1` in the existing container runs both real G1 and G2a smoke.

`summary.json` contains all cases and gates. `component_cuts.csv` includes every
leg/bridge current, heat flux and leg Joule value. Current, heat-budget and
convergence CSV/plots accompany actual topology artwork, 3D temperature/potential,
isosurfaces and a `derived.vtu` with E/J/q/Joule. Every mesh has its original
Gmsh file, compressed node/domain/face arrays, manifest and audit. Every case
retains its actual Elmer SIF, log, status and fields. Full raw data stays in
`outputs/fem-g2a`; selected verified evidence is archived under `fem/results/`.
`docs/PHASE1_G2A_RESULT.md` records final actual results and remaining limits.

After the full run and tests, `python3 fem/archive_g2a.py` verifies source, SIF and
original VTU hashes before archiving. It refuses quick/failed or modified-source
runs. Archived SIFs retain original `/work` paths; regenerate using the runner.
