# Reproduce the G1 single-couple FEM

Run from this repository on an amd64 Linux Docker host:

```bash
./fem/bootstrap.sh
./fem/run.sh python -m tecooledmct.fem_g1_run --out outputs/fem-g1
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q
./fem/run.sh python -m tecooledmct.cli --quick --out outputs/check
./fem/run.sh python -m tecooledmct.geometry_demo --out outputs/pellet-study
```

The bootstrap pins Ubuntu 24.04 by amd64 image digest, Elmer release 26.2.1
by commit, and the direct Python dependencies (including Gmsh 4.13.1). It records
the resolved apt versions, pip freeze, image identity and full build output in
`logs/bootstrap/`. Apt security dependencies are resolved at build time; the
recorded apt lock and local Docker image identify the exact run. This is source
reproducibility, not a claim of bitwise-identical builds from changing apt mirrors.
No PPA is added to the host. No Qt GUI, MPI or OpenFOAM is installed. The Gmsh
wheel dynamically requires X/OpenGL runtime libraries even in headless operation;
those libraries are confined to the container. The source build uses four jobs.
Reserve 6 GB before building; the script checks free space and records it before
and after. It never removes unrelated images, files or package caches.

`fem/run.sh` mounts only this repository at `/work`, uses the invoking user's
UID/GID, disables container networking and limits the runtime to four CPUs and
8 GiB memory. It starts no tmux session and modifies no Codex settings. The
container can be run from the existing `sim` session. Build and run artifacts
remain under this project. The Docker image contains ElmerSolver, ElmerGrid and
the official ThermoElectric test copied from the pinned source.

For a short solver smoke run:

```bash
./fem/run.sh python -m tecooledmct.fem_g1_run --quick --out outputs/fem-g1-quick
```

This executes Elmer's official reference-norm test, a coarse convergence point,
zero current, both current polarities, and open-circuit Seebeck voltage. The full
run adds three mesh levels, seven load-controlled current points, both polarities
at isothermal bath/load faces, a temperature-dependent-property demonstration,
and a 100-fold lower ceramic-conductivity check. Smoke success alone does not
establish mesh convergence.

To regenerate charts, derived fields and acceptance checks from an existing
actual run without another PDE solve:

```bash
./fem/run.sh python -m tecooledmct.fem_g1_run --postprocess-only --out outputs/fem-g1
```

For zero current, direct interior-cut errors use a declared 1 microamp absolute
gate; a relative error to zero is undefined. Driven cuts use the 0.5% gate.

## Geometry and boundary conditions

Coordinates and transport properties are SI internally. The two separately
tagged Bi-Te legs are each 0.4 × 0.4 × 1.0 mm, separated by a 0.4 mm clear lateral
gap. Their lower ends touch separate 0.1 mm thick copper pads; their upper ends
touch a continuous 1.2 × 0.4 × 0.1 mm copper bridge. Each outer alumina support
is 1.4 × 0.6 × 0.2 mm. These dimensions define a verification specimen, not the
undisclosed OEM geometry. Bond/solder layers are omitted and interface electrical
and thermal resistances are zero. Boolean fragmentation creates shared nodes
and matching faces at all seven intended contacts.

| Physical IDs | Domain or face |
|---|---|
| 1, 2 | P leg, N leg |
| 3, 4, 5 | Cold Cu bridge, P hot Cu pad, N hot Cu pad |
| 6, 7 | Hot alumina, cold alumina |
| 101 | Bottom of hot alumina, T = 300 K |
| 102 | Top of cold alumina, uniform inward 2 mW total heat load in sweep |
| 103 | Outer x face of N hot pad, specified uniform inward current I |
| 104 | Outer x face of P hot pad, potential = 0 |
| 105 | Remaining exposed faces, natural adiabatic/electrically insulating BC |
| 201–207 | Explicit matching material-interface faces (see mesh physical names) |

Positive current follows N pad → N leg → cold Cu bridge → P leg → P pad. The
current terminal is a prescribed-flux surface; its potential need not be exactly
uniform. Voltage is its area-averaged potential relative to grounded P pad, so
input power is exactly I times that mean voltage. Unspecified boundary values
are natural zero total heat/electric flux, including at terminal faces for heat.
The cold 2 mW load is a real applied face flux, not a prescribed temperature
borrowed from a reduced-order model. Separate fixed-cold runs hold the top
alumina at 280 K (open circuit) or 300 K (heat-pumping polarity check).

## Coupled physics and independent checks

Elmer's actual `ThermoElectricSolver` solves Temperature and Potential together:

```
E = -grad(phi)
J = sigma (E - S grad(T))
q = -k grad(T) + T S J
div(J) = 0
div(q) = J . E
```

At P/N–Cu contacts, continuity of **total** heat flux includes Peltier conversion;
no extra empirical junction heater is added. The material inputs are evaluated
by Elmer, rather than decorating a precomputed temperature field. Explicit
synthetic slopes for k(T), sigma(T) and S(T) are exercised in the full run;
these are a software demonstration, not measured temperature-dependent data.

Exact sigma = 0 on all-insulator interior nodes gives unneeded unconstrained
potential DOFs. We use sigma = 1e-12 S/m for alumina, consistent with the
room-temperature vendor lower resistivity bound >1e14 ohm cm. This is a declared
insulating approximation. Run sigma = 1e-14 S/m and quantify leakage and changes
in T/V. No conducting path is allowed across the ceramic in the conductor
connectivity graph. Surface/mesh audits compare exact box volumes, contact areas
and face incidence; removing the bridge must disconnect the terminal branches.

The postprocessor maps actual Elmer VTU values to original mesh nodes by position,
then independently reconstructs gradients, J, q, J.E, J²/sigma and the original
nonlinear finite-element weak residuals. Ground-current and heat-bath reactions
come from the reconstructed fields, with no Dirichlet elimination. It also
checks direct constitutive heat flux at the passive alumina bath and compares
terminal I V to integrated volume J.E. It reports free-node residual norms so
global cancellation cannot disguise an unconverged field. For sign conventions,
outward heat at the hot face is positive; cold heat absorption into the model
is minus outward cold flux. Thus Qhot,out + Qcold,out = I V. For the load case,
Qcold,out = -0.002 W.

Additional direct integrations cut the interior of each Bi-Te leg at
z = 0.600013 mm and the bridge at x = 0.600017 mm. Their area and signed current
are independent of terminal reaction reconstruction. The raw P1 gradients
immediately at terminal corners converge more slowly and are explicitly reported;
they should not be confused with conservative weak-form terminal currents.

The ideal independent couple uses alpha = Sp-Sn, R = (1/sigmap+1/sigman)L/A,
K = (kp+kn)A/L, and solves Qload = alpha I Tc - I²R/2 - K(Th-Tc). Finite copper
resistance, finite thermal spreading and ceramic resistances are deliberately
absent from that limiting reference. Absolute Tc and DeltaT deviations are
reported separately; relative Tc agreement alone would conceal a lift error.
Open-circuit Seebeck comparison uses the actual average end-junction temperatures
to separate ceramic temperature drop from solver error.

## Material provenance and validity

P/N S and sigma at 300 K are Goldsmid's Table 1 examples: +160/-170 microV/K and
1.4e5/1.655e5 S/m. Bi-Te k = 1.5 W/(m K), density and heat capacity are generic
Ferrotec values, not from the same specimens. Alumina k = 30 W/(m K) and density
3900 kg/m3 are the AD-995 proxy; Cp = 880 J/(kg K) is the older 100 C table value
and has no effect in this steady calculation. Copper k = 400 W/(m K), resistivity
1.72e-8 ohm m and S = 0 are representative assumptions (including neglect of
copper thermopower). None are manufacturer-specific production-grade claims.
Constant properties are held fixed across the computed mathematical benchmark;
do not treat these extrapolations as physical material data at cryogenic or
elevated temperatures. There is no parameter fitting to OEM maxima.

Sources:

- [Pinned Elmer ThermoElectricSolver source](https://github.com/ElmerCSC/elmerfem/blob/a19504ac53ec222e3355e182b08f2ff280c2203a/fem/src/modules/ThermoElectricSolver.F90)
- [Official thermoelectric reference test](https://github.com/ElmerCSC/elmerfem/blob/a19504ac53ec222e3355e182b08f2ff280c2203a/fem/tests/ThermoElectric/ptest.sif)
- [Official Ubuntu build instructions](https://github.com/ElmerCSC/elmerfem/blob/a19504ac53ec222e3355e182b08f2ff280c2203a/compilation_instructions/Ubuntu.md)
- [Elmer Models Manual](https://www.nic.funet.fi/pub/sci/physics/elmer/doc/ElmerModelsManual.pdf) (general solver/output conventions; the pinned source/test define the thermoelectric implementation)
- [Goldsmid 2014, Table 1, DOI 10.3390/ma7042577](https://pmc.ncbi.nlm.nih.gov/articles/PMC5453363/)
- [Goldsmid full-text XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5453363/fullTextXML)
- [Ferrotec material properties, Appendix B](https://ferrotec.com.sg/product/thermo/technical_reference_guide/14/)
- [CoorsTek alumina material table](https://www2.coorstek.com/en/materials/alumina/)
- [Gmsh reference manual](https://gmsh.info/doc/texinfo/gmsh.html)

## Artifacts

`summary.json` contains every case's BCs, solver status, nonlinear convergence,
field diagnostics and pass/fail gates. `current_sweep.csv`, `mesh_convergence.csv`,
PNG/SVG charts and case `metrics.json` are machine-readable evidence. Each case
retains `case.sif`, `case.json`, `solver.log`, `solver-status.json`, `.result` and
actual Elmer VTU. Selected cases additionally include `derived.vtu` with J, q,
Joule power and temperature, `temperature_isosurfaces.vtu`, and `temperature.png`.
Each mesh retains `couple.msh`, `mesh.npz`, `audit.json`, Elmer's mesh files and
its conversion log. Checked-in representative evidence is under `fem/results/`.
Generated raw runs remain in ignored `outputs/`; no results are synthesized when
the solver is absent. Final status and limitations are in PHASE1_G1_RESULT.md.

After the complete run and regressions pass, `python3 fem/archive_results.py`
copies representative real evidence into `fem/results/g1_20261028` and records
source/artifact SHA256 hashes. It refuses quick or failed runs. The full PDE
execution log remains distinct from an optional postprocessing-only log.
