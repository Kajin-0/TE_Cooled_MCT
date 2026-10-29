# Reproduce the G3a hybrid solid package

Work only in `/home/User/TE_Cooled_MCT`, using the existing `sim` session and
pinned `tecooledmct-fem:26.2.1` image. The unchanged `fem/run_g2b.sh` wrapper uses
four CPUs,12 GiB,network-none and a project-only mount. Elmer source is
`a19504ac53ec222e3355e182b08f2ff280c2203a`; Gmsh4.13.1. No host installation,
OpenFOAM,other repository or LSDDTS is required.

Read [the result](PHASE1_G3A_RESULT.md), [compact MCT scope](MCT_COMPACT_THERMAL_MODEL.md)
and `data/g3a` first. This is genuine thermally coupled3D solids with massless1D
Au-wire conductances, not all3D wire FEM and not a manufacturer-validated detector.
Only two representative pins are resolved; seven illustrated feedthroughs and
cap/window/gas/radiation/carriers/thermistor/TEC supply-lead heat remain omitted.
The die has only the sourced x=.29 composition and90..400 K local-k coverage.
No unsupported alloy interpolation, BiTe extrapolation or transient claim.

## Mesh, actual solves and tests

Use a fresh raw output tree on a fresh checkout, or pass `--resume` to the case
runner for existing completed cases. It rejects changed inputs,changed SIFs or
incomplete executions. Do not overwrite earlier accepted meshes/results to make
new checks pass. All published G1/G2a/G2b/G2c/G2d evidence is checked by
`fem_g3a_data.preserve`; the prior TEC construction is imported read-only.

```bash
./fem/run_g2b.sh python -m tecooledmct.fem_g3a_geometry --level 0 --out outputs/fem-g3a/mesh_0
./fem/run_g2b.sh python -m tecooledmct.fem_g3a_geometry --level 1 --out outputs/fem-g3a/mesh_1
./fem/run_g2b.sh python -m tecooledmct.fem_g3a_run --case outputs/fem-g3a/passive_0 --current 0 --pbias 0 --optical 0
./fem/run_g2b.sh python -m tecooledmct.fem_g3a_run --case outputs/fem-g3a/loaded_0 --restart outputs/fem-g3a/passive_0
./fem/run_g2b.sh python -m tecooledmct.fem_g3a_run --mesh outputs/fem-g3a/mesh_1 --case outputs/fem-g3a/loaded_1
./fem/run_g2b.sh python -m tecooledmct.fem_g3a_run --case outputs/fem-g3a/no_heat_010 --current .1 --pbias 0 --optical 0 --restart outputs/fem-g3a/loaded_0
./fem/run_g2b.sh python -m tecooledmct.fem_g3a_run --case outputs/fem-g3a/loaded_005 --current .05 --restart outputs/fem-g3a/loaded_0
./fem/run_g2b.sh python -m tecooledmct.fem_g3a_run --case outputs/fem-g3a/no_heat_005 --current .05 --pbias 0 --optical 0 --restart outputs/fem-g3a/loaded_005
./fem/run_g2b.sh python -m tecooledmct.fem_g3a_run --case outputs/fem-g3a/wires_zero --wire-scale 0 --restart outputs/fem-g3a/loaded_0
./fem/run_g2b.sh python -m tecooledmct.fem_g3a_run --case outputs/fem-g3a/wires_four --wire-scale 2 --restart outputs/fem-g3a/loaded_0
./fem/run_g2b.sh python -m tecooledmct.fem_g3a_run --case outputs/fem-g3a/attach_resistance_five --attach-scale .2 --restart outputs/fem-g3a/loaded_0
./fem/run_g2b.sh python -m tecooledmct.fem_g3a_run --case outputs/fem-g3a/mount_resistance_five --mount-scale .2 --restart outputs/fem-g3a/loaded_0
./fem/run_g2b.sh python -m tecooledmct.fem_g3a_run --case outputs/fem-g3a/package_sigma_hundredth --sigma 1e-14 --restart outputs/fem-g3a/loaded_0
./fem/run.sh python -m tecooledmct.fem_g3a_wire_check
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q
./fem/run.sh python -m tecooledmct.cli --quick --out outputs/check-g3a
./fem/run.sh python -m tecooledmct.geometry_demo --out outputs/pellet-g3a
```

Default driven cases use .1 A,1.5mW prescribed detector bias heat and .5mW thermally
absorbed optical power. The bias corresponds to .5V*.003A; do not add another
V-squared/R term. Heat is deposited in the actual die volume with Elmer's
`Volumetric Heat Source` in W/m3. Ordinary `Heat Source` is density-multiplied by
the pinned ThermoElectricSolver and would be wrong for this volume source.
All package cases execute the actual ThermoElectricSolver for common T/phi;
none substitutes the old four-node network. Restart states are hashed actual
solutions and still execute PDEs. Zero-current passive equilibrium is verified
independently from actual fields.

The header underside is the only thermal Dirichlet bath. Bottom TEC alumina,
intermediate plates and pin tops are solved unknowns. S=0 plus tiny computational
sigma on package volumes creates an electrically passive potential extension;
it does not assign physical gold/Kovar conductivity or model detector electrical
transport. Explicit Joule/current bounds and the100-fold sigma check quantify
its negligible effect. Real k and the die's bounded local-k callbacks control
thermal paths. Density/Cp are source metadata only for steady scope; the SIF's
capacity placeholders must not be treated as a calibrated transient model.

Each1D wire reads area-weighted temperatures from two actual3D endpoint patches
inside the nonlinear solve and applies equal/opposite total powers. Endpoint maps
are checked against real Elmer node numbering. `--wire-scale 2` means two parallel
wires per existing endpoint pair (four total), not additional meshed3D wires.
The independent1D Neumann rod uses coefficient k*A and solves the warm-end
response to1mW; its field and conductance check are archived separately.

## Independent verification and immutable evidence

`fem_g3a_post` reconstructs J,q,Joule/work and the weak form from actual VTU T/phi,
including local nodal MCT coefficients, die volume source and both wire endpoints.
It verifies all175 TEC interior current cuts,actual cut areas,free residuals,
current return,independent direct bath flux and an interior die-attach heat cut.
Its stage control volumes include the appropriate header/routing portions and
the warm-wire sink. `fem_g3a_interfaces` independently integrates source-free
mount and3D pin gradient cuts:

```bash
./fem/run.sh python -m tecooledmct.fem_g3a_interfaces --case outputs/fem-g3a/loaded_0
./fem/run.sh python -m tecooledmct.fem_g3a_interfaces --mesh outputs/fem-g3a/mesh_1 --case outputs/fem-g3a/loaded_1
```

Gates are recorded in `data/g3a/package_registry.json`:driven cuts .5%,zero1uA,
free/global heat1uW,current1uA,direct bath1%,package interface gradient cuts5%,
package Joule1nW,die mean/max and voltage refinement1%. The1% package curved
volume/contact tolerance accounts for linear chordal surfaces; rectangular TEC
geometry uses1e-7. An initial circle mesh failed the pin-volume gate and remains
unaccepted; final curvature-refined meshes preserve the same gate. No local
corner flux-peak convergence is claimed. Numerical tolerances are not experimental
measurement confidence or OEM accuracy.

The report/archive gate requires all eleven accepted case records,the independent
wire check,passing completed tests/CLI outputs,unchanged actual source/SIF/VTU/mesh
hashes and interface/refinement/isolation checks. Capture commands' logs under
`logs`; the publisher expects `pytest-g3a-full.log`,`cli-g3a.log`,`geometry-g3a.log`
and collects `g3a-*.log`. The tracked evidence includes original execution logs,
compiler sources/statuses,endpoint weights,mesh arrays,case/current/heat tables,
selected raw/derived fields and charts. Generated library binary hashes are
retained; binaries remain local and are rebuilt from archived Fortran.

On a completed run, reproduce the archive into an ignored directory without
rewriting the published checkpoint:

```bash
./fem/run_g2b.sh python fem/report_archive_g3a.py --out outputs/g3a-reproduced
```

The default one-time publication command writes `docs/PHASE1_G3A_RESULT.md` and
`fem/results/g3a_20261029`; it refuses to overwrite a tracked published archive.
The custom `--out` option writes its report within that new project directory.
Decompress selected actual fields for inspection, for example:

```bash
gzip -dc fem/results/g3a_20261029/fields/loaded_1/fields_t0001.vtu.gz > outputs/g3a-loaded-fine.vtu
```

`checksums.json` records source/artifact hashes,code checkpoint,eleven unique
integrated package executions and one independent1D execution. Postprocessing,
resuming verification and plot generation never count as additional solves.
CI uses Python checks; actual solver and production-field qualification is the
separate local evidence. Source/geometry assumptions and missing thermal paths
continue to limit absolute detector-temperature predictions.
