# TE_Cooled_MCT

**Current continuation (2026-10-30):** [OEM-first physical-validation track](docs/OEM_FIRST_VALIDATION_TRACK_20261030.md). The prospective bounded 1D source-material screen is implemented in `tecooledmct/oem_phase_a.py` with independent tests. The archived 88-leg FEM results remain numerical evidence, not a manufacturer-validated detector prediction. The original bath/temperature-interface release criteria and approved Rev3 REVIEW DRAFT are unchanged. The current scientific priority is matched-grade, multi-current/load physical validation, not more million-element bath refinement by default.

Open, reproducible **proof-of-concept multiphysics model** of a three-stage thermoelectrically cooled HgCdTe (MCT) detector in a nine-pin TO-66-style hermetic package.

**Phase 0: research prototype, NOT a validated digital twin.** The initial solver is a 4-node steady-state thermoelectric/thermal network and includes exploratory material, gas, radiation, detector loading, electrical, sensitivity and cooldown calculations.

**G1 update (2026-10-28):** a genuine, separately verified **coupled 3D P/N
thermocouple FEM** now uses Gmsh and Elmer ThermoElectricSolver. It includes two
Bi-Te legs, a continuous copper bridge, separate terminal pads and thermally
conducting alumina supports. It is a single-couple numerical benchmark with
illustrative material properties, not the full three-stage package.
See [verified G1 results](docs/PHASE1_G1_RESULT.md) and
[reproduction instructions](docs/FEM_G1_REPRODUCIBILITY.md).

**G2a update:** a real four-couple (eight-leg) series stage now passes coupled
3D Elmer verification, with explicit alternating hot/cold Cu routing, every-leg
current/Joule checks and three mesh levels. See [G2a results](docs/PHASE1_G2A_RESULT.md)
and [reproduction](docs/G2A_REPRODUCIBILITY.md). G1 is preserved; neither milestone
is a calibrated 44-couple three-stage package simulation.

An [88-leg G2b geometry/mesh proof](docs/PHASE1_G2B_FEASIBILITY.md) now passes
contact and per-stage circuit audits. It has three isolated stage circuits and
six ports and remains a separate geometry checkpoint.

**G2b two-terminal update:** a separate inferred construction connects all 88
legs through two insulated internal Cu routes and passes actual mesh topology
and fully coupled 3D Elmer verification. Three meshes, both current signs,
zero drive, cold loading and ceramic-leakage sensitivity are checked. See
[verified results and limits](docs/PHASE1_G2B_TWO_TERMINAL_RESULT.md) and
[reproduction](docs/G2B_COUPLED_REPRODUCIBILITY.md). G1/G2a are preserved.
Routing fabrication, OEM calibration and the complete package remain unvalidated.


**G2c material qualification:** opt-in temperature-dependent profiles now retain
original source markers, SI units and strict intervals for identified published
hot-extruded P/N samples: default v1 covers 200–300 K; additive v2 covers 40–300 K. Local-temperature Elmer, Thomson and explicit
resistive-transition checks are separate from OEM device validation. The 2019
OEM curves have a reserved calibration/holdout split; no fit or grade match is
claimed. See [G2c status](docs/PHASE1_G2C_RESULT.md),
[source provenance](docs/G2C_MATERIAL_PROVENANCE.md) and
[reproduction](docs/G2C_REPRODUCIBILITY.md).

## Run

```bash
python -m pip install -e '.[dev]'
pytest -q
python -m tecooledmct.cli --scenario examples/base_argon.json --out outputs/demo
```

Produces JSON results and six diagnostic plots: detector temperature versus TEC current, gas pressure, added warm aperture area and detector bias; gas comparison; and illustrative cooldown.

## Scope and epistemic status

- **Datasheet anchored**: 2019 TEC Microsystems 3MC04-044-05, 6.4 × 6.4 mm hot side, 2.4 × 2.4 mm cold side, 3.8 ± 0.15 mm height, 44 couples, nominal AC resistance ~2.9 Ω. The manufacturer reports at 300 K, vacuum reference: ΔTmax ~113 K and Qmax ~0.5 W; they are different limit conditions, not a simultaneous operating point.
- **Inferred**: individual stage allocation (28/12/4 couples), leg heights, effective Seebeck/thermal conductance and package thermal geometry.
- **Not validated**: absolute cold-stage temperatures, gas mixtures, pressure effects, thermal contacts, current-dependent efficiency, and transient constants.
- **CAD**: the earlier Revision 6 visual design has internal micron-scale contact gaps and is NOT FEM-ready. See `docs/rev6_cad_audit.md`.

### Initial calculations

The baseline example assumes 300 K ambient, 0.65 A TEC, 2 K/W hot-side sink, 1 atm argon, 0.5 V detector bias across a constant 100 Ω MCT element and 0.1 mW absorbed optical power. Under these *assumptions* the model estimates ~261.5 K, 225.5 K and 195.5 K at successive TEC stages. This is a **demonstration output, not a measured device specification**.

The detector's electrical self-heating in that scenario is 2.5 mW (= V²/R); additional parasitic loads include gas conduction, radiation, bond wires and thermistor power. Krypton conducts less heat than argon or nitrogen under the present gas model, but production backfill decisions need a much broader reliability and process assessment.

## Physics

Each stage uses an effective-couple relation:

```
Qc = alpha*I*Tc - (I^2*R)/2 - K*(Th-Tc)
Qh = alpha*I*Th + (I^2*R)/2 - K*(Th-Tc)
V  = I*R + alpha*(Th-Tc)
```

The 4-node solver couples the TEC stages with detector heating, pressure-dependent gas conduction, cap radiation, wire heat leaks and hot-side thermal resistance. Stage balance and Qh-Qc=I*V are tested.

**Calibration vs. validation:** the initial effective coefficients are adjusted to reproduce two manufacturer's limiting performance numbers. Two fitted anchors do not validate loaded or intermediate-stage behavior.

## Repository layout

- `tecooledmct/model.py`: steady-state TEC model and heat-flow breakdown
- `tecooledmct/experiments.py`: gas/pressure/aperture/current sweeps, deterministic uncertainty, cooldown
- `tecooledmct/cli.py`: runnable scenarios, charts and JSON reports
- `tests/`: conservation, limits and solver tests
- `docs/`: physics, source provenance, known CAD limitations, simulation roadmap
- `geometry/revision6/`: legacy visual-CAD assumptions and reference; **not** validated solver geometry
- `AGENTS.md`: continuation instructions for subsequent agents

## Roadmap

1. Digitize manufacturer performance curves and hold out independent verification points.
2. Measure TEC current/voltage and hot/cold temperatures; instrument heatsink resistance and parasitic loads.
3. Model actual aperture shields and cavity radiation factors; parameterize MCT R(T).
4. Build contact-clean simulation geometry with proper coupled electrical/thermal connectivity.
5. Compare against FEM and gas CFD when justified by sensitivity results.

## Sources

- [TEC Microsystems 3MC04-044-05 datasheet (2019)](https://www.tec-microsystems.com/Download/Datasheets/Thermoelectric%20Coolers/MC04%20Series/3MC04-044-05_Datasheet_2019.pdf)
- [3MC04 product family](https://tec-microsystems.com/products/thermoelectric-coolers/3mc04-series-thermoelectric-coolers.html)
- See `docs/physics_and_sources.md` for equations and assumptions.

**Safety:** This repository is for operational modeling, not opening, heating or processing HgCdTe-containing hermetic packages.
## Phase 1a: geometry sensitivity and a spatial pellet solver (added 2026-10-28)

**The original Phase 0 network does not solve from CAD.** We now distinguish three workflows:

1. `tecooledmct.geometry_sweep`: a **geometry-parameterized, four-node TEC network**. Each stage's length and cross-sectional area modify effective transport coefficients through R~L/A and K~A/L. This is *not FEM* and its effective material parameters still derive from the Phase 0 fitted model.
2. `tecooledmct.pellet_fvm`: a **real 3D spatial finite-volume temperature-field solve** for *one representative thermoelectric leg*. It resolves Joule heating, spatial conduction, and gas-coupled sidewalls on a voxel mesh. Peltier terms are applied to the end-face heat budgets, not solved as an all-domain electrical PDE. Boundary temperatures come from the network, so the two solvers are **not fully coupled**.
3. `geometry/reference_cad.py`: exports reference STEP assemblies with **the same leg height/width inputs**. These are visual geometry exports, not validated FEM meshes.

Run:

```bash
python -m tecooledmct.geometry_demo --out outputs/pellet-study
# Optional CadQuery separately installed:
python geometry/reference_cad.py --pellet-scale 0.70 --out outputs/CAD_70pct
python geometry/reference_cad.py --pellet-scale 1.30 --out outputs/CAD_130pct
```

Results include temperature-versus-height, input power versus height, inferred electrical resistance, current reoptimization to a 200 K target, a 3D pellet temperature slice, mesh-resolved axial temperature profiles, CSV and JSON.

**Illustrative nominal example (300 K ambient, 0.65 A, Ar, unverified geometry):**
- 70% pellet height: 206.9 K and 1.22 W at fixed current; minimum ~1.69 W to hit 200 K.
- 100% height: 195.5 K and 1.62 W at fixed current; minimum ~1.23 W to hit 200 K.
- 130% height: 192.5 K and 1.98 W at fixed current; minimum ~1.00 W to hit 200 K.

**Interpretation:** This does not establish a physical optimum. Real electrical contact and thermal interface resistances, changing cap clearances/gas conduction, manufacturing feasibility, temperature-dependent material data, and measured performance could reverse the trend. See [geometry study notes](docs/geometry_sensitivity.md).

## Phase 1b: sourced material-property profiles (2026-10-28)

The TEC's **default** electrical/thermal solver remains calibrated to two OEM performance endpoints—not an independently measured material-specific FEM model. For material investigation a **separate, explicit uncalibrated literature profile** has been added:

```python
from tecooledmct.geometry_sweep import TECGeometry, solve_geometry
from tecooledmct.model import Scenario
from tecooledmct.material_transport import literature_stage_coefficients, compare_coefficients
g=TECGeometry()
print(compare_coefficients(g))
result=solve_geometry(Scenario(), g, coefficients=literature_stage_coefficients(g))
print(result['stage_k'])
```

Sourced bulk materials and provenance: `tecooledmct/materials.py`. Includes p/n-type Bi-Te literature examples, 96% and 99.5% alumina ceramic proxies, Kovar header alloy, 4N gold bond wire, Sn95Sb5 *proxy* solder, and copper. The source-matched 3MC04-044-05 contains hot-extruded Bi-Te, Al2O3(100%), Sn-Sb internal solder, Au plated contacts and bare AWG32 terminal wires, but proprietary material-property curves are **not disclosed**.

Read [materials and provenance](docs/materials_and_provenance.md). A 1-D material-layer resistance demonstration is supported; **these layers are not yet connected to 3D package transport or automatically to the four-node network**. The optional literature P/N solver still assumes temperature-independent values near room temperature, so its cold-stage numbers are only sensitivity examples, not production predictions. Do not compare results against the OEM profile as independent validation.

## Active project focus: standalone TO-66 thermoelectric multiphysics

Elmer FEM + Gmsh will solve the 3D cooler and solids. OpenFOAM is optional for sealed-cavity gas convection and conjugate heat transfer only if screening warrants it. The HgCdTe detector is modeled as a compact material-and-heat-load domain (k(T,x), density, heat capacity, die attach, electrical and optical heating). There is **no active LSDDTS integration**; do not change or connect that repository without a new explicit request. See docs/OPENFOAM_FEASIBILITY.md and docs/MCT_COMPACT_THERMAL_MODEL.md.

### G2d: OEM discrepancy and identifiability

[Result and limitations](docs/PHASE1_G2D_RESULT.md) ·
[Reproduction](docs/G2D_REPRODUCIBILITY.md) ·
[Traceable evidence](fem/results/g2d_20261029)

The independent calibration/holdout network audit shows exact geometry/material
nonidentifiability (normalized Jacobian rank8/9). Three genuine 88-leg Elmer
constant-law sensitivity points at300 K/.2 A pass numerical checks. The strict
40..300 K source-backed300 K probe rejects an out-of-range local iterate;
independent above300 K material tables cannot cover the cold legs or identify the
OEM grade. **OEM-family FEM qualification remains FAILED/BLOCKED.**
All earlier checkpoints remain intact; full-stack contacts and production device
accuracy are not established. Run the new opt-in analysis with
`./fem/run.sh python -m tecooledmct.g2d_analysis`; actual PDE directions use
`./fem/run_g2b.sh python -m tecooledmct.g2d_fem`.

### G3a: coupled TO-66 solid package and hybrid bond wires

[Result](docs/PHASE1_G3A_RESULT.md) · [Reproduction](docs/G3A_REPRODUCIBILITY.md) ·
[Verified evidence](fem/results/g3a_20261029)

A new199-domain conformal package retains the actual88-leg two-terminal TEC and
adds Kovar header,mount,die attach,MCT,two glass feedthroughs/pins and Au pads.
Conservative1D gold bonds couple solved3D endpoint temperatures. This is a
**3D-solid/1D-wire hybrid**, with the bath on the header underside. Eleven real
coupled package solves and an independent1D wire check pass numerical gates;
73 tests pass. At .1 A/2mW,fine die mean is263.389718 K and cold ceramic262.965994 K.

Source MCT x=.29 k(T) is bounded90..400 K. TEC/material/contact geometry remain
verification proxies; seven pins,carriers,cap/window/gas/radiation and other
omitted loads prevent manufacturer/device accuracy claims. Earlier evidence is
unchanged. Run the opt-in commands in the reproduction guide; no LSDDTS coupling.

### G3b: verified enclosure checkpoint; full flux qualification incomplete

[Result](docs/PHASE1_G3B_RESULT.md) · [Reproduction](docs/G3B_REPRODUCIBILITY.md) ·
[Scoped evidence](fem/results/g3b_checkpoint_20261029)

The215-domain model adds an attached cap/window, all nine glass/pin feedthroughs,
conservative nonlinear gray radiosity, pressure-dependent N2/Ar/Kr films and
hybrid Cu TEC supply leads around the full88-leg coupled Elmer model. Ten selected
coarse integrated executions, two independent Elmer plate references and84 full
opt-in tests pass. Actual accepted fields, source/mesh/payload hashes and failed
attempts are archived separately. G1–G3a remain byte-identical; no LSDDTS.

**Full G3b gate D is NOT QUALIFIED.** Three genuinely converged fine executions
fail the independent direct-bath1% gate:1.65587%,1.51412%,1.58383%. Temperature/
voltage stability and conservative reaction balance do not override this failure.
The published result is the narrower verified checkpoint permitted by the work
order, with the unresolved flux/refinement gate recorded explicitly.

The window is internally opaque gray and externally adiabatic; spectral LWIR
transmission is absent. Gas films and axial Au/Cu leads are reduced operators,
not CFD or resolved wire arcs. Constant verification BiTe, unmeasured contacts/
geometry/emissivities and omitted thermistor/carriers prevent OEM/device accuracy.
