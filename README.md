# TE_Cooled_MCT

Open, reproducible **proof-of-concept multiphysics model** of a three-stage thermoelectrically cooled HgCdTe (MCT) detector in a nine-pin TO-66-style hermetic package.

**Phase 0: research prototype, NOT a validated digital twin.** The initial solver is a 4-node steady-state thermoelectric/thermal network and includes exploratory material, gas, radiation, detector loading, electrical, sensitivity and cooldown calculations.

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
