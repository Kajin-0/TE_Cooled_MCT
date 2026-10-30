# Reproduce the corrected solid-only coupled checkpoint

Run in TE_Cooled_MCT with the existing pinned Docker image/session. No install,
remeshing, old enclosure import or report rebuild is needed. The mesh preparation
copies the exact protected NPZ arrays/manifest/wire registry, re-encodes Gmsh22,
runs ElmerGrid and verifies actual node/tetrahedron/body correspondence.

```bash
./fem/run.sh python fem/archive_geometry_complete.py --verify
./fem/run_g2b.sh python -m tecooledmct.corrected_thermal_prepare --out outputs/thermal-repro-mesh
./fem/run_g2b.sh python -m tecooledmct.corrected_thermal \
 --mesh outputs/thermal-repro-mesh --case outputs/thermal-repro-passive --current 0 --load 0
./fem/run_g2b.sh python -m tecooledmct.corrected_thermal \
 --mesh outputs/thermal-repro-mesh --case outputs/thermal-repro-off --restart outputs/thermal-repro-passive
./fem/run_g2b.sh python -m tecooledmct.corrected_thermal \
 --mesh outputs/thermal-repro-mesh --case outputs/thermal-repro-on --cu --restart outputs/thermal-repro-off
./fem/run_g2b.sh python -m tecooledmct.corrected_thermal \
 --mesh outputs/thermal-repro-mesh --case outputs/thermal-repro-low-sigma --cu --sigma 1e-14 --restart outputs/thermal-repro-on
./fem/run.sh python -m tecooledmct.corrected_thermal_interfaces \
 --mesh outputs/thermal-repro-mesh --case outputs/thermal-repro-off
./fem/run.sh python -m tecooledmct.corrected_thermal_interfaces \
 --mesh outputs/thermal-repro-mesh --case outputs/thermal-repro-on
./fem/run.sh python -m tecooledmct.corrected_thermal_figures \
 --mesh outputs/thermal-repro-mesh --cases outputs/thermal-repro-off outputs/thermal-repro-on --out outputs/thermal-repro-figures
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q
./fem/run.sh python -m tecooledmct.cli --quick --out outputs/thermal-repro-cli
./fem/run.sh python -m tecooledmct.geometry_demo --out outputs/thermal-repro-pellet
./fem/run.sh python fem/archive_corrected_thermal.py --verify
```

Always choose new output labels. Restart only from an actual completed case on
that same reconstructed mesh/node order; the sequence above guarantees this.
Default no-restart initialization is300 K/phi0 and still solves the actual PDE.
Never transfer an earlier assumed-package solution.result onto this mesh.
The runner records actual restart bytes, source snapshots, SIF/field/mesh hashes,
UTC timestamps, solver iterations/wall/CPU/RSS and generated Fortran/compiler logs.
Actual numerical failure is retained as a failed execution. A converged solve
with failed numerical gates retains its fields and failed metrics; process exit
alone is not a qualification signal.

The comparison's Cu OFF state disables G and wire I²R; ON enables both, with I
still imposed at the same hot pad faces. Au is OFF throughout, as are all gas and
radiation paths. Pin3D conduction is solved, with exposed pin ends adiabatic and
the Kovar underside the only thermal clamp. Physical pin shaft current/Joule is
not modelled. One bias power representation plus parametric absorption is a
uniform volumetric MCT source, not externally transmitted optical flux.

Postprocessing independently maps actual raw VTU T/phi to the exact mesh,
reconstructs J, Fourier/Peltier q, J·E, Joule and nodal residuals using degree2
tetrahedron quadrature and nodal coefficient interpolation. It integrates actual
177 interior cuts, Kovar bath triangles, all nonlocal face sources and three
whole-assembly P1 control volumes. The separate interface audit evaluates nodal
k(T) at face centroids, retaining local5% diagnostic failures. Its layer-average
identities never substitute for raw bath/interface fluxes.

The archive includes compressed actual raw T/phi and derived3D J/q fields,
complete per-case metrics, exact endpoint weights and generated Fortran, input
restart digests, solver status/history and plots with section data. Uncompressed
field digests accompany deterministic gzip files. The mesh is referenced by its
protected geometry-checkpoint digest rather than duplicated. Recompute derived
fields only in fresh copies of case folders; that is verification/replay, not a
new PDE execution. New node orders are permitted in fresh ElmerGrid runs, and
callbacks recompute endpoint IDs/weights from the actual new mapping.

The publication audit rejects changed source/SIF/raw fields, wrong mesh or load,
missing177 cuts, inconsistent fixed-parameter OFF/ON cases, source misallocation,
absent tests and false full-qualification claims. It retains the failed local
die/attach face checks and historical raw bath failures. Primary per-case PASS
does not mean spatial/OEM qualification: all current results remain exploratory
pending targeted cold-interface and bath refinement. The earlier15-page PDF and
all historical archives are preserved by their existing ledgers.
