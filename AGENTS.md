# CURRENT PROJECT CONTRACT

This is the authoritative continuation contract, updated 2026-10-31. Historical
work orders and milestone instructions describe their own checkpoints; their
"current", "next" and report-freeze language does not override this contract.
Their numerical evidence, original errors and acceptance criteria remain intact.

## Objective and execution ownership

This TO-66 / three-stage TEC / HgCdTe reference is a **VIRTUAL MULTIPHYSICS
EXPERIMENTAL/DESIGN PLATFORM**, beyond a single-point temperature calculation or OEM replica.
Future parametric goals include:

- Pure N2/Ar/Kr/Xe gases, mixtures and vacuum; pressure, external ambience and
  orientation; conduction/convection/radiation in physically appropriate continuum,
  transition/free-molecular regimes. Apply Rayleigh/Knudsen gates; never presume convection.
- Header alloys and interfaces; TEC P/N grades, pellet count/area/length and stage
  allocation; MCT area/thickness/composition/bias and self-heating; heat-sink conditions.
- Coupled temperature/electrical responses, thermal-path budgets, lowest physically
  feasible T, Qmax, DeltaTmax, Seebeck(T), R, V-I, COP and Qc-versus-DeltaT maps,
  with explicitly matched operating conditions.

Prioritize first-principles insight, mechanistic sensitivity, credible assumptions
and experimental uncertainties, and controlled paired parameter studies. Report actual
solved 3D fields versus reduced estimates honestly. Use meaningful technical visuals,
equations, 3D meshes, plots and diagrams to explain physics, never as decoration.
The ONE continually enhanced standalone Rev3 remains canonical; add only validated
quantitative results and actual solved fields as work warrants. These long-term goals
do not claim present implementation or change the ordered next science priorities.

Develop an **engineering-plausible synthetic** three-stage TEC-cooled HgCdTe
reference device in a nine-pin, two-ear TO-66 package. Fill unknown construction
and material details with labeled assumptions, rationale and scenario ranges.
OEM reverse engineering, proprietary curve fitting and OEM calibration are
**not release gates**. Numerical verification is distinct from physical accuracy.

All edits, simulations, tests, commits and pushes belong to the **existing VPS
sim:0.0 Codex session**, working ONLY in `/home/User/TE_Cooled_MCT`. Do not spawn
competing agents, another Codex/tmux session or external implementation work.
Do not touch, invoke or integrate LSDDTS or another repository. Use the existing
pinned environment within **4 CPUs / 12 GiB**; prioritize bounded reduced studies.
No new million-tet campaign merely to advance an exploratory scenario.

## ONE continuously maintained professional report

The already established standalone master is
`reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf`.
Continuously improve **that Revision 3 in place**. Its legacy filename is stable;
the public content is the Revision 3 engineering assessment, not a project diary.
Never create a competing Rev4, alternative report or new public report edition.

Keep it deep and self-contained: architecture, geometry/mesh, source versus
assumption and modeled versus omitted physics, material domains, equations/units,
boundary conditions, actual fields, heat budgets, methods in scientific
principles, numerical failures, sensitivity, limitations and engineering conclusions.
No usernames, repository references, hashes, paths/filenames, agents, commands,
CI or administrative material in public pages or personal metadata. Public
technical citations/DOIs are expected. Do not imply OEM validation or certification.

Preserve prior exact PDF bytes as historical evidence. The original 15-page
snapshot is identified by `reports/historical/rev3_original.json`; its original
hash and sealed manifest must still verify. Rev2 and all numerical/source/field
archives remain immutable. The live Rev3 is expressly authorized to evolve.
Use `reports/master` and its build guide: derive figures from actual evidence,
validate provenance/text/typesetting, reproduce PDF/figures, render and visually
inspect every page of a rebuilt master before publication.

## Present implementation and verification

| Component | Actual present scope | Limits that must remain explicit |
| --- | --- | --- |
| Corrected 88-leg Elmer | Genuine coupled 3D Peltier/Joule/Fourier solid fields; header, explicit joints/attach and MCT; principal mesh 216 domains / 647,657 tets | Constant verification P/N properties; principal 0.1 A / 2 mW / 300 K underside case has external Cu/Au paths OFF; no enclosed-package gas/radiation field |
| `integrated_reference.py` | **Five-node** conservative package; three TEC stages, die attach, hot-side Cu leads, Au bonds, sink and reservoir loads | Reduced spatial description; preserve `g1_constant` and affine `zhang2025_analog` compatibility |
| `nonlinear_tec.py`, `graded_tec.py` | Opt-in `zhang2025_nonlinear`: conservative bounded nonlinear 1D P/N profiles, analytic banded Newton and exact-key cache; independent bounded BVP comparisons | Research specimens measured 40–300 K; active 180–390 K; **assumed quarter-tangent** continuation above 300 K; not an identified commercial grade |
| Corrected enclosure / exchange | Source-aligned candidate STEP/mesh and native-face audit; **preliminary filled stepped-core** diffuse-gray radiation and gas chord network (14 surfaces / 8 effective nodes) | Full native-surface visibility, interleg/pin/wire exchange, gas diffusion, optical transmission and coupled 3D cavity fields are **not implemented** |
| `nonlocal_solid_network.py` diagnostic | Opt-in geometry-derived local Cu/alumina multiport plus unchanged affine P/N stages; actual interfaces, nonlocal return and P174 side contact | Isothermal ceramic/pad closure is unqualified; not full-device FEM; 7.277% side-port sensitivity exceeds registered 5% screen |
| `model.py`, `cli.py`, `experiments.py` | Original **four-node legacy demonstrations**, retained for compatibility | Not the current corrected package; older OEM-anchored assumptions are historical |

- Archived 177-cut/current, weak heat and global/stage balance checks pass, but
  numerical release remains **incomplete**: original cold-interface mismatch
  6.48% fails 5%; best independent bath-normal error 1.069% fails 1%; later
  transverse cases remain about 1.29%. Independent cold-normal 4.795% passes
  only on its separate mesh. No combined qualified mesh/comparator is demonstrated.
- Preserve the raw **bath <1% / cold-interface <5%** requirements and other
  archived current/residual/convergence gates. Never substitute conservative
  reactions/recovered flux, stable temperatures or reduced budgets for raw checks.
  Never rewrite failed results, alter old gates or claim unearned qualification.
- Current reduced evidence: `data/nonlinear_exchange_20261030`; 52/63 proxy
  cases accepted, 11 rejected with diagnostics. At nominal 0.15 A Kr, die
  232.209 K and terminal 1.15193 V are conditional reduced predictions.
  Maximum last-level view-factor correction is 0.04043 absolute, not an accuracy bound.
- Use the corrected source geometry: two-ear VIGO profile, nine 0.76 mm C pins,
  pins 1/9 to TEC **hot pads**, pins 7/8 to detector. Housing plus independent
  cooler reference and inferred 28/12/4 stages remain a hypothetical assembly.
  Do not reuse old elliptical/pin geometry or G3b enclosure geometry.
- Conserve `Qh-Qc=I*V`; use SI internally. Keep sigma identically `1/rho` and
  Thomson identically `T*dS/dT` of the active piecewise law: source interior
  knots use right derivatives, exactly 300 K the measured left derivative,
  above 300 K the quarter tangent, exactly 390 K its left limit. Domain-check
  interior Joule overshoot. Never clamp accepted results, bridge rejected plot
  intervals, erase failure diagnostics or turn chosen ranges into confidence intervals.
- Latest recorded report checkpoint: **28 pages**, all rendered/inspected;
  PDF and 40 figure files reproduce exactly; 32 focused and **300 full opt-in
  tests pass**, including actual Elmer smoke. Archive verifier and legacy demos
  pass. Records: `reports/master/verification/summary.json`. Check CI for each
  newly pushed commit; historical test counts are not new executions.
- Current nonlocal diagnostic verification: **62 focused / 331 full opt-in**
  tests pass, including existing Elmer smoke; archive/master integrity and both
  legacy demos pass. Record: `data/nonlocal_solid_network_20261031/verification.json`.
  Those software gates do not pass the flagged side-port sensitivity or qualify
  ceramic spreading. The 28-page master and historical evidence are unchanged.

## Read-first order

1. This contract, then `README.md` and the ONE canonical Rev3 master PDF.
2. `docs/PLAUSIBLE_REFERENCE_MODEL_POLICY_20261030.md`: assumptions and objective.
3. `docs/INTEGRATED_REFERENCE_THERMAL_20261030.md`: five-node balances and scenarios.
4. `docs/GRADED_TEC_AND_CORRECTED_ENCLOSURE_20261030.md`: transport/exchange methods.
5. `docs/MASTER_REPORT_REPRODUCIBILITY.md`: live report and sealed-PDF integrity.
6. For geometry work, `GEOMETRY_SOURCE_OF_TRUTH_SPEC.md`, current manifests and
   native-face audits; before editing any historical implementation, inspect its
   archive ledger. Add new versions when sources are sealed; do not modify archives.

## Ordered next science milestones

1. **Matched solid-model comparison:** follow
   `docs/MATCHED_SOLID_MODEL_DIAGNOSTIC_20261031.md` and the current
   `docs/NONLOCAL_PORT_NETWORK_20261031.md`. Geometry-only Milestone 2 predicts
   8.412629 K warming against the original 7.630466 K cold-ceramic gap, leaving
   FEM minus prediction −0.782163 K and +7.810466 mV. No fitted K or new FEM.
   The registered grids stop at 40 µm: P174 side heat changes 7.277%, despite
   cold T changing only 0.090770 K. Use `all_port_review.json`, not the initial
   sharp-cut-only screen, for the overall sensitivity decision. Unknown plate
   mean-to-contact mapping prevents unique causal attribution; Rev3 stays intact.
   **One next discriminator:** bounded passive routes + original ceramic/pad
   fixture, unit-temperature P/N footprint ports, reaction/mean-to-face offsets;
   pre-register cell/time caps before execution. No fitted bypass, calibration,
   further grid chase or whole-device solve is authorized by this checkpoint.
2. **Native-surface exchange:** replace the filled-core shortcut with a bounded
   actual-surface visibility fixture/operator from corrected cap/window and
   package surfaces, exposing interleg voids, pins and wires. Audit face ownership,
   normals, areas, first-hit visibility, blocked pairs, reciprocity, closure,
   refinement and heat conservation. Retain the present proxy as a comparator;
   do not imply a new 3D thermal field or force an expensive conformal cap merge.
3. **Integrated mechanism and uncertainty comparisons:** paired gas/radiation/
   lead controls plus contact, bypass, material-grade and cap/window/sink-reservoir
   hypotheses in the bounded five-node/nonlinear model. Report accepted-domain
   coverage, rejected candidates, heat budgets and power at matched detector
   targets. Use labeled scenario spans; no OEM fit or invented observations.
4. **Conditional later 3D qualification:** pursue a justified, resource-bounded
   experiment only when required by the engineering question. A numerical release
   still requires both original raw limits on the same mesh and a systematically
   refined comparator, plus all current/heat/nonlinear/reproducibility gates.
   This is not authorization for another large refinement campaign.

At **every milestone**, assess whether verified substantive science warrants
improving the existing Rev3 in place; otherwise preserve its bytes and state the
reason internally. Do not change the master merely to record progress or an
unqualified diagnostic. Keep README, newer technical guides and this contract coherent. They are
**internal methods/reproduction documents**, not competing scientific reports.
Revise stale mutable guidance rather than adding another checkpoint near the end.

## Verification and handoff

Use focused checks appropriate to changed code, then the established gates for
code/physics/report changes; inspect actual results and exact-commit CI before
declaring completion. For documentation-only corrections, check contract content,
links, master integrity and the full archive guard; do not launch solver jobs or
rebuild an unchanged PDF just to edit prose. Standard reproduction gates:

```bash
python3 -B -m reports.master.validate --current
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q --ignore=outputs
./fem/run.sh python fem/archive_bath_spatial_device.py --verify
./fem/run.sh python -m tecooledmct.cli --quick --out outputs/new-check/legacy-cli
./fem/run.sh python -m tecooledmct.geometry_demo --out outputs/new-check/legacy-geometry
```

Choose new output paths, never sealed evidence. Commit/push scoped verified work;
leave honest partial changes uncommitted if blocked by usage or execution limits.

The former instruction document is retained verbatim as
[historical context only](docs/history/AGENTS_BEFORE_CURRENT_CONTRACT_20261030.md),
with its identity in `docs/history/agents_pre_contract.json`. It has **no current
instruction authority** and is not part of the routine read-first sequence.
