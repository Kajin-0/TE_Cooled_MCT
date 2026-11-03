# CURRENT PROJECT CONTRACT

This is the authoritative continuation contract, updated 2026-11-02. Historical
work orders and milestone instructions describe their own checkpoints; their
"current", "next" and report-freeze language does not override this contract.
Their numerical evidence, original errors and acceptance criteria remain intact.

**2026-11-03 authorized derived-geometry milestone (CURRENT, GEOMETRY ONLY):**
A separate **uncommitted** analysis geometry in
`data/v3_derived_multiphysics_20261103` and its linked
`docs/V3_DERIVED_MULTIPHYSICS_GEOMETRY_20261103.md` provides actual native
OCC BREP derivatives (437 physical analytical domains +1 connected cavity gas),
438 conformal volumes and 2,456 fully classified faces (1,848 gas-solid,
565 solid-solid, 43 exterior), all 378 declared finite contacts, preserved
physical source names/ports and two bounded 3D meshability fixtures.
The 98 composite material domains now use explicit COMPOSITE_MULTILAYER
classification with source constituent layers and a required future constitutive
law; they MUST NOT silently inherit bulk Cu/Au/Ni properties.
Final full-suite QA, immutable publication and exact-commit CI remain required
before release; no full multiphysics mesh, material equivalence, PDE, TEC
performance or seal certification is claimed. Source V3 R1 STEP, Rev3, Gate B
STOP and issue #2 remain unchanged. Preserve untracked historical trials.

**2026-11-03 geometry-readiness consolidation (NEWEST):** V3 R1 physical STEP
remains the immutable 824-solid reference. A separate source-to-STEP
[geometry-readiness report](docs/V3_MULTIPHYSICS_GEOMETRY_READINESS_20261103.md)
and [machine-readable domain/port registry](data/v3_geometry_readiness_20261103/domain_interface_registry.json)
map all 824 original bodies, 378 declared source contact witnesses, candidate
physics roles, 13 declared thermal/source ports, and thin-layer/curve strategies.
This is analysis PREPARATION, NOT validated analysis geometry: no native gas
void, unambiguous STEP-face/port mapping, parametric CAD rebuild or new mesh/PDE.
Height upper reserve6um and nominal tab-strain proxy20% remain physical risk
screens, not geometry defects proven or resolved. The original geometry and
canonical Rev3 stay frozen; Gate B electrical STOP, thermal C/D NOT RUN and
issue#2 OPEN. Do not launch another electrical mesh campaign from this packet.

**2026-11-03 archive-integrity hardening (NEWEST):** A separate prospective
[scientific-field archive contract](docs/V3_FLUX_ARCHIVE_INTEGRITY_20261103.md)
checks actual typed array shapes/units/identities, mesh face incidence, RT0
cell balances and reconstructed J from saved face currents, shared execution
lineage, independent arithmetic replay of archived analytical L2 errors, and
fail-closed incomplete/tampered archives. Synthetic-fixture tests are software
controls, NOT actual original solver-field proof. No old field is reconstructed,
no new PDE or mesh. A genuinely independent read-only model review remains
**NOT RUN** because sim:0.0 quota is exhausted. Gate B remains STOP, C/D NOT RUN;
issue#2 OPEN, Rev3 unchanged. Before new numerical qualification, require an
independent immutable review plus separately authorized source/solver work.

**2026-11-03 no-solve successor (NEWEST):** The separate diagnostic
[forensics record](docs/V3_FLUX_NO_SOLVE_FORENSICS_20261103.md) and
[retained-field evidence](data/v3_flux_forensics_20261103/saved_diagnostics.json)
report the pin_finish mixed-potential minimum and recovered bulk/contact loss
breakdown without any new PDE or mesh. A new independent archive-writer module
requires separate p1/recovered_rt0/mixed_rt0 method paths and rejects collisions;
the original sealed producer and lost mixed flux remain untouched. Infrastructure
verification is not electrical qualification. The new independent model review
has **NOT RUN** while the Codex session is usage-limited; Gate B remains STOP,
thermal C/D NOT RUN and issue#2 OPEN. New numerical calculations require a
separate authorization after prospective method-specific review.

**Current outcome: conservative electrical study STOP at first coupon.**
Read [the registered attempt](docs/V3_CONSERVATIVE_FLUX_20261102.md), baseline5317bf1.
All16 control cases PASS; the first207,396-tet mesh meets the frozen volume gates
(0.084875% total,0.118348% lead9). A coupon output-label KeyError lost the direct
mixed flux export. Retained P1 raw cuts81.2417% and voltage undershoot FAIL;
recovered current closes but IV/loss error0.769154% FAILS0.5%. No qualification.
Separate [read-only numerical review](data/v3_conservative_flux_20261102/independent_review.md)
of immutable b2be519 / exact CI PASS confirms STOP and additionally finds the
surviving mixed cell minimum −2.65228e-5 V fails the registered −1e-8 V floor.
Control fields were not archived: their saved summaries/formulas, not independent
field-level L2 recomputation, were reviewed. Do not present a writer-only fix as
sufficient qualification. 120 focused /576 applicable checks and all protected
hashes pass; preserve the original review and final receipt separately.
132 source/input identities were sealed before the first new control; preserve
the complete failed producer and mislabelled artifacts, never repair them in place.
L2 mesh, thermal C/D and all other physics NOT RUN. Only existing-field audit,
verification/publication and serial read-only review of a frozen checkpoint remain
authorized. No source fix, retry, further mesh/solve or performance claim now.

**Historical outcome: V3 R1 local conductor Gate B FAIL / STOP (2026-11-02).**
Read the [registered experiment and results](docs/V3_INTERCONNECT_ELECTROTHERMAL_20261102.md).
Gate A source/port definitions and layered analytic controls passed their numerical
scope. Exactly two electrical coupon meshes were run: 10,819 / 28,691 tets.
The fine-mesh worst raw current-cut mismatch is **85.6255% > 0.1%**; voltage
boundedness also fails. Resistance refinement (0.3158%) and power closure
(9.919e-13 relative) pass, but cannot replace raw flux qualification. A separate
saved-field cofactor/normal audit confirms the failed cuts without another solve.
**C passive thermal and D electrothermal are NOT RUN.** No thermal conductance,
Joule heat partition, full TEC resistance, current rating or device temperature
is qualified. LOW/HIGH material sensitivities are NOT RUN.

The [separate read-only numerical/source review](docs/V3_INTERCONNECT_INDEPENDENT_REVIEW_20261102.md)
of immutable **962c78a** independently confirms STOP, source/SI scope and the
distinction between weak conservation and raw flux. It also preserves the exact
CI failure (optional `meshio` import in a development-only test) and the disclosed
pre-control sealing limitation. The independently inspected test-only ASCII-MSH
successor **f85638b has exact CI PASS**; its
[serial supplement](data/v3_interconnect_et_20261102/independent_portability_supplement.md)
confirms unchanged physics/fields/gates and faithful verbatim preservation.
113 focused / 569 applicable checks (same 12 exclusions), archive/master,
both legacy and both frozen-blob guards PASS. The bounded experiment is complete
at B STOP; only final receipt publication/exact CI remains, then halt.
Complete operator/source freezing must precede every control in a future
separately authorized study. No new experiment is granted by this receipt.

At that historical checkpoint only verification, documentation, publication and serial
read-only review of this failed checkpoint remain authorized. No further mesh,
solve, refinement or parameter change to force a pass. A future discretization
experiment requires new user authorization. Preserve all V1/V2/V3 source/STEP,
the exact 38-page Rev3, old FAIL/STOP and 5,128 baseline identities; issue#2 OPEN.
The bounded local A→B→C→D authorization granted no automatic further campaign.

Prior V3R1 physical-design outcome remains CONDITIONAL core/header/detector,
[review](docs/SYNTHETIC_V3_CORRECTIVE_INDEPENDENT_REVIEW_20261102.md),not
supplier capability,sealed package,1A,detector properties orperformance.

Actual separate V3:824 solids,88 legs/176 full P/N contacts/89 internal nets,
real formed feet/joints,solderable underside/hot mount,pin1/9 Cu leads and7/8
photoconductor bonds;5/6 vacant. Fresh mm author/separate SI reader PASS
(maxrelative volume1.141e−11,bbox1.000e−7m);923 imported contact witnesses,
58 Boolean checks and1250 conservative exclusions PASS. Nominal STEP and
all V1/V2/fields/exact38-page Rev3 remain unchanged by the R1 correction.

The [first independent STOP](docs/SYNTHETIC_V3_INDEPENDENT_REVIEW_20261102.md)
on07fe3cb remains correct:fixed tabs could not accommodate18/36um rise errors
with10um joint differential. R1 measures finished lands andcustom-forms tabs
OFF-device,with postrelease inspection/no forcefit:128 corners/384 continuous
paths,15–25um joints,18um measured-stroke reserve. Corrected height3.664–3.944mm;
heel/neck is an explicit bounded CAD idealization,not a literal wedge program.
Read `tec_assembly_v3_fit.py`,R1 requirements andregistry overlay before changes.

96 focused/552 applicable tests PASS (same12 runtime exclusions),full archive/
master/both legacy and5128 baseline blobs PASS. The0830fd7 CI failure is preserved:
one2ULP derived-volume equality underPython3.11;test-only portability fix keeps
coordinates exact,pinned full-source replay bitwise andSTEP hashes unchanged.
0ababcc exact CI PASS and148 packet/32 cache identities matched before/after
serial re-review;both original verdicts are preserved verbatim. Selected dimensions
are inspectable drawing requirements,not measured OEM values or current ratings.

**Historical prior outcome: independently reviewed V2 physical-geometry STOP.**
Read [current audit/status](docs/PHYSICAL_GEOMETRY_QUALIFICATION_20261102.md),
[verbatim independent review](docs/PHYSICAL_PLAUSIBILITY_INDEPENDENT_REVIEW_20261102.md),
then [V2 prototype](docs/COMPACT_TEC_V2_20261102.md). Separate read-only model-assisted
review of immutable **8339307** confirmed nominal circuit/polarity/STEP scale,
but **STOPPED physical promotion**: actual pin1/9 leads and detector bonds absent;
foil joint/process, mounting/tolerances, current capability and multi-ceramic
heat allocation unqualified. Issue#2 remains OPEN; no Cu FEM, fitting, sink or
other physical campaign is authorized. Builder cannot clear its own STOP.
Safe **e1c431c** and packet **8339307** have exact CI PASS; V2 and all unexecuted
Cu drafts are committed, not pending. Only five reviewed PR#1 source files were
integrated without merge/approval. The 23-source/96-parameter review packet is
preserved; a versioned IA-08 metadata correction adds one internal hypothesis
source, normalizes degrees to radians and retains inferred-contour certainty.
At that prior checkpoint the correction was builder-verified; the b824212
source-gate review now independently closes IA-08's metadata scope. No CAD/law/
field/PDF bytes changed. Preserve every old STOP/FAIL and exact38-page Rev3.
At that historical checkpoint a dimensioned process-backed assembly was proposed;
the new current order above authorizes its implementation only. A coupon/new
physical simulation still needs separate authorization. Never run obsolete-post fixtures.
Complete review/metadata checkpoint **dc5234a / exact CI PASS** is published;
the audit is complete with physical STOP. Subsequent receipt-only commits do
not grant fabrication, current, package or scientific acceptance.

## Cold-start protocol — no prior chat context required

1. In `/home/User/TE_Cooled_MCT`, check `git branch --show-current`,
   `git rev-parse HEAD` and `git status --short` before editing. Inspect staged,
   unstaged and untracked work against the latest chronology; preserve unfinished
   changes and establish their scope. Never reset, discard or overwrite to get clean.
2. Inspect `tmux list-sessions` and `tmux list-panes -t sim` read-only; identify
   existing **sim:0.0** before continuing. Do not create/duplicate/restart sessions,
   spawn another agent or send commands to unrelated panes/repositories.
3. Read this whole contract, latest [chronology](docs/ENGINEERING_CHRONOLOGY.md),
   [README](README.md), the [canonical Rev3](reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf),
   then the read-first guides and task-relevant source/evidence/validation below.
   Reconcile stale instructions using this contract and verified event/source records.
4. Reconstruct the current task and its authorization: **PASS** means the named
   checks passed, **FAIL** a failed criterion, **STOP** a halted scope/gate,
   **NOT RUN** unexecuted work, **PENDING** incomplete verification. A proposed
   next experiment is not authorization; do not restart stopped work automatically.
5. Preserve sealed inputs, fields, original failures/gates and historical PDFs
   (Rev2, original 15-page and prior 28-/34-/36-page Rev3). The ONE live Rev3 evolves only
   for authorized substantive science; do not rebuild it for administrative edits.
6. Append observed UTC PENDING at task begin and actual PASS/FAIL/STOP at end,
   including source, evidence, immutable impact and blocker/next authorized step.
   Use existing scope-appropriate verification and archive/master guards below;
   inspect results, commit only verified scope and verify CI for the exact pushed
   commit before claiming completion. Do not launch physics for documentation checks.

Orient from [five-node balances](tecooledmct/integrated_reference.py),
[nonlinear legs](tecooledmct/nonlinear_tec.py) and [material laws](tecooledmct/graded_tec.py):
commercial grade is unidentified (source 40–300 K, active model 180–390 K);
300–390 K is assumed continuation, not measured.
[Native gas](tecooledmct/native_gas_conduction.py) and its
[forensics](tecooledmct/native_gas_flux_forensics.py) retain **32.6274% FAIL vs 1%**;
no qualified device gas budget follows. Solid release still requires raw bath
**<1%** and cold-interface **<5%** on one mesh plus a refined comparator and all
other gates. Conservative reactions and reduced-model acceptance cannot replace them.

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
The explicit2026-11-02 user order permits one **serial read-only independent
auditor** on an immutable committed target, with builder writes paused; it does
not permit another editing agent or worktree. Preserve that role's restrictions.
Do not touch, invoke or integrate LSDDTS or another repository. Use the existing
pinned environment within **4 CPUs / 12 GiB**; prioritize bounded reduced studies.
No new million-tet campaign merely to advance an exploratory scenario.

## Timestamped operational chronology

[ENGINEERING_CHRONOLOGY.md](docs/ENGINEERING_CHRONOLOGY.md) is the ONE authoritative,
concise, append-only internal progress chronology. During all future active work,
append records at substantive milestone begin/end and important stop gates, using
actual ISO8601 UTC event timestamps captured when observed. Backfill only verified
Git `%cI` timestamps, explicitly labeled commit times, never inferred run times.
Each record states PASS/FAIL/STOP/NOT RUN/PENDING, what changed, exact source
commit/link and diagnostic, validation evidence, immutable-artifact impact,
blocker and next authorized step; distinguish proposals from authorization.
Keep entries to 1–2 informative sentences; append corrections, never erase failed
attempts or call incomplete work released. No polling ticks or repeated no-change
entries. Detailed equations/plots stay in milestone records; the ONE professional
Rev3 remains free of operational diary material. Keep this chronology current
during active sessions; no process writes entries while the session is inactive
unless separately established automation exists (none is introduced here).

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
| `tec_material_plausibility.py` | Separate registered scale-hypothesis study using unchanged nonlinear/G1 algorithms; 141/181 admitted, 40 rejected; conditional literal-27-C module comparison | Nominal fixed-300-K/2-mW/wires-ON sample reaches 186.484 K at 0.4 A within measured leg coverage; no full-device or commercial-grade qualification; substantial joint OEM lift/voltage mismatch |
| `tec_identifiability.py` | Separate preregistered reduced diagnostic, 260/269 admitted; exact nonlinear geometry/material gauge and normalized raw SVD; no fitting | Common A/L cannot be distinguished from reciprocal rho/k factors by endpoint transport; g=1.7 still overcools/overvolts and fails all 176 unchanged native full-pad contacts; no altered CAD or identified grade |
| `finite_sink_study.py` | Separate registered sink/current study on unchanged geometry/laws, wires ON, exchange OFF; 203/288 grid cases admitted, 85 retained failures; six actually solved nominal 200 K crossings | At 10 K/W, target input 0.622176 W vs ideal 0.548425 W (+13.4478%); hot 305.826317 K requires assumed continuation; Qsink differs from IV through explicit lead paths; no actual-device feasibility or global optimum |
| `physical_input_qualification.py`, `physical_input_evidence.py` | Registered local evidence-priority audit: 102/102 admitted calls in 44.531 s; 11 actual 200 K targets at 2 K/W; independent derivatives/balances and cached primary-source audit | Fixed-geometry conditional target-power elasticities S −2.490, k +2.214, rho +1.245; not physical uncertainty or separate grade/geometry identification. Gas/nonlocal/contact power sensitivities NOT RUN; current Rev3 unchanged |
| `tec_candidate_geometry.py`, `tec_candidate_study.py` | **Separate candidate**: source-inspired29/11/4,.5mm; one361-solid STEP/independent SI gate PASS;155 reduced calls150 admitted/5 rejected, two-factor calibration explicitly user-authorized here only | Full curve alignment **FAIL**: no-fit18/20, selected20/20 but25.111K maximum lift error>15K. Geometric PASS is not qualified1A operation: omitted Cu/contact/spreading remains; original reference unchanged; Rev3 unchanged |
| `tec_candidate_v2.py` | **Separate compact v2 prototype**, source-only physical contact/circuit/clearance gates; 359 bodies, 88 legs/176 P/N contacts, 89 metal nets, two hot lands; short foil gap plus ceramic-supported edge film | CAD/SI status in current v2 record; no Cu FEM/transport result, manufacturing/current rating or package pin-wire qualification; all v1 drafts/results preserved |
| Corrected enclosure / exchange | Source-aligned candidate STEP/mesh and native-face audit; **preliminary filled stepped-core** diffuse-gray radiation and gas chord network (14 surfaces / 8 effective nodes) | Integrated native gas diffusion, full native visibility, optical transmission and coupled solids/cavity fields remain absent; standalone stopped gas control below |
| `nonlocal_solid_network.py` diagnostic | Opt-in geometry-derived local Cu/alumina multiport plus unchanged affine P/N stages; actual interfaces, nonlocal return and P174 side contact | Isothermal ceramic/pad closure is unqualified; not full-device FEM; 7.277% side-port sensitivity exceeds registered 5% screen |
| `passive_plate_audit.py` | Source-only audit of four plates, original Cu pads and routes/supports; 104 bodies | Seven-port follow-up **STOPPED before grid/solves**: two unmapped cuts and incompatible P174 side/hot-foot trace on a 0.220 mm edge; no spreading attribution |
| `native_gas_audit.py`, `cap_export_validation.py` | Historical unit gates, original and quarantined failed STEP bytes preserved | Original STEP 1,000× too small; first correction 1,000× too large; neither is an accepted gas geometry input |
| `isolated_cap_*`, `native_gas_csg.py` | Fresh mm writer / separate SI reader; accepted derivative; actual 216+3-solid partition, one connected gas void, 927 owned faces | Nominal ideal seals, external wires OFF; geometry validation is not manufactured-assembly validation |
| `native_gas_conduction.py` | One actual gas-only Elmer Laplace control, 228,710 positive tets, analytic 250–300 K walls | **STOP: raw flux 32.6274% FAILS 1%**, despite conservative reactions; N2 at 101325 Pa, constant k; buoyancy suppressed; no qualified gas budget or new device T |
| `native_gas_flux_forensics.py` | Read-only independent cofactor/face incidence and sparse P1 audit: +11.347300 mW interior normal-flux jumps explain −11.347300 mW raw boundary sum | No extraction/trace error found; shared-node redistribution sums to zero; no new solve, convergence result or raw-gate qualification |
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
- Current master: **38 pages**, every page rendered and visually inspected;
  PDF, 50 figure files and all 38 rendered pages reproduce exactly across two
  independent builds. All 46 predecessor figures are byte-identical. The verified
  nonlinear scaling ambiguity, raw-rank caveat, signed manufacturer residuals
  and failed native-pad realization are integrated with the earlier material
  hypotheses and distinct proxy baseline; the finite-sink target/power and signed
  heat budgets are integrated without device validation or numerical release.
  Exact prior 36-page PDF/provenance are retained under
  `reports/historical/rev3_pre_finite_sink_20261101`, alongside earlier 34-/28-page
  snapshots, original 15-page Rev3 and Rev2. Current scoped verification:
  `data/finite_sink_20261101/verification.json`; earlier study/CI failure records
  remain intact. Existing scientific laws,
  geometry, fields, failures and all historical report hashes remain unchanged.
- Current native gas checkpoint: `data/isolated_cap_native_gas_20261101` and
  `docs/ISOLATED_CAP_AND_NATIVE_GAS_20261101.md`. A/B PASS, C failed raw balance;
  one export, one partition, one mesh/solve, no retry. **87 focused / 384 full
  opt-in tests pass**, including existing Elmer smoke. Software regression records
  are separate in `verification.json`; their success cannot qualify gas flux,
  pass old side-port sensitivity or establish ceramic spreading. At that checkpoint the 28-page
  master was unchanged; its exact predecessor bytes are now historical evidence.
- Frozen-field forensics: `docs/NATIVE_GAS_FLUX_FORENSICS_20261101.md` and
  `data/native_gas_flux_forensics_20261101`. Exact jump/reaction identities and
  native-group decomposition verified, **32 focused / 385 applicable opt-in
  tests pass**, with 12 runtime CAD/mesh/Elmer cases explicitly excluded. Current
  verification records distinguish applicable regression from excluded runtime
  CAD/mesh/Elmer tests under this audit's explicit no-solve limit.

## Read-first order

1. This contract, latest `docs/ENGINEERING_CHRONOLOGY.md` entries, then `README.md`
   and the ONE canonical Rev3 master PDF.
2. `docs/PLAUSIBLE_REFERENCE_MODEL_POLICY_20261030.md`: assumptions and objective.
3. `docs/INTEGRATED_REFERENCE_THERMAL_20261030.md`: five-node balances and scenarios.
4. `docs/GRADED_TEC_AND_CORRECTED_ENCLOSURE_20261030.md`: transport/exchange methods.
5. `docs/MASTER_REPORT_REPRODUCIBILITY.md`: live report and sealed-PDF integrity.
6. For geometry work, `GEOMETRY_SOURCE_OF_TRUTH_SPEC.md`, current manifests and
   native-face audits; before editing any historical implementation, inspect its
   archive ledger. Add new versions when sources are sealed; do not modify archives.

## Ordered next science milestones

**Current: STOP; publish verified subset of the conservative electrical attempt.**
Read `docs/V3_CONSERVATIVE_FLUX_20261102.md` and its frozen sources/results.
The first coupon failed numerically and its writer lost a mixed export; do not
relaunch or edit the sealed producer. Controls/geometry PASS are distinct from
unqualified current/loss accuracy. No L2, C/D or follow-on campaign is authorized.

**Historical source-gate attempt:**
Read `docs/V3_ASSEMBLY_SOURCE_GATE_20261102.md` and its independent review of
b824212 for the unspecified interfaces that the newly authorized V3 must close.
No V3 CAD existed at that checkpoint; do not mistake its two V2 projections for
new geometry. IA-08 metadata was independently closed; physical construction
and all old numerical failures remain separate.

**Prior independent physical promotion STOP; no science authorized by it.** Follow
`docs/PHYSICAL_GEOMETRY_QUALIFICATION_20261102.md` and the independent review of
8339307. Four independent manufacturer figure families and nominal CAD/circuit
PASS do not establish fabrication/current/thermal/package acceptance. The
reviewer's IA-01–07 require independent process, lead/mount, tolerance, transport
and boundary evidence; IA-08 audit metadata has a separately versioned builder
correction. Preserve the original reviewed registry/packet and verdict.
Only publish the verified audit/receipt and exact CI in this task; issue#2 stays
OPEN. A complete dimensioned joint/return/pin-wire/mount closure package and a
later V2-specific coupon are proposals, not permission for CAD or a solver run.

**Historical checkpoint context below is evidence, not current authorization.**

**Prior compact v2 source/CAD prototype gates PASS (2026-11-02); STOP before
further physics or qualification:**
read `docs/COMPACT_TEC_V2_20261102.md` and its registration/data under
`data/tec_candidate_29114_v2_20261102`, then the earlier source-referenced
connector review. The user selected implementation of a patterned-metal/short-foil
architecture; no choice question remains. Original v1 nodes58/80/88 long loops/
posts are suspended as unsupported construction; .296705873ohm applies only to
that rejected routing, not the replacement. Preserve `docs/GATED_CANDIDATE_CU_20261102.md`,
all old source/STEP/registration/results and unexecuted draft code unchanged;
its former resume command is **not an instruction to execute**.

New source-only v2 gates cover 176 full P/N contacts and the physical contact
graph, four0.6mm foil gaps with0.5mm ceramic-edge support, explicit1.1mm joins
and2.2mm return, insulation and package envelope. Thin-film/foil/solder sizes are
engineering assumptions; current density and heat shunts remain unqualified.
The one unchanged-Dockerfile build succeeded in488.056s; pinned base/direct
versions/Elmer source checked, new image identity and actual package inventories
recorded rather than old dependency-byte equivalence claimed. One fresh-mm
STEP export and separate SI import PASS:359 solids, maxrelative volume error
2.043e-14.13 v2/29 focused and485 applicable opt-in tests PASS; same12 runtime
cases deselected, original archive/master and both legacy demos PASS. Do not
relaunch the completed build/export. No substitute/host install, Cu FEM, fit or
sink work occurred. The prior runtime STOP/cache-only failure is historical.
Prototype success must never trigger the old fixture or B/C. Preserve the exact
38-page master, old failed gates and all drafts. They were uncommitted at that
historical event; safe checkpoint e1c431c now preserves them with exact CI PASS.
A future architecture-accepted Stage A needs independent fabrication/contact
bounds and a new v2-specific registration, not old post cuts/heat allocations.

Prior separate candidate scientific STOP (2026-11-01): read
`docs/SOURCE_CONSTRAINED_TEC_CANDIDATE_20261101.md` and its frozen registration.
One361-solid candidate STEP passes footprint/circuit/envelope/SI gates; historical
RMT stage ordering remains inferred, not proven TEC2019 construction. The one
65.242s study admits150/155 calls; explicit two-factor candidate calibration
selects S=.9427924,rho=1.2,k=1 but **FAILS** the registered full-data gate
(25.111K maximum lift error). At1A the loaded response fails despite close
zero-load lift; no qualified datasheet-aligned or operable device is delivered.
The rough post-hoc .314ohm Cu omission estimate is NOT coupled/validated heat.
Preserve the first reader-token STOP, its source and the exact unchanged export;
the corrected independent parser/import passed without a second CAD export.
Calibration authorization applied **only to this separate candidate**. Do not
widen bounds, introduce another knob, alter the original28/12/4 reference or
reopen stopped fixtures. Numerical Cu/contact qualification is a proposed next
experiment, **NOT RUN / not authorized**; no further science follows this checkpoint.
The exact38-page Rev3 stays unchanged because full alignment/physical operation
is unqualified. Source acquisition, controls and scoped software checks are in
the candidate record, separate from old numerical-release failures.

Prior evidence-priority study complete (2026-11-01): read
`docs/PHYSICAL_INPUT_QUALIFICATION_20261101.md`, its registration, source audit
and scoped verification. One 44.531 s execution retained 102 admitted / zero
rejected calls and 48 unused slots; all eleven actual target crossings use assumed
>300 K continuation. Equal-fraction local temperature/target-power effects differ
from unequal-span sensitivity rankings. Independent same-grade transport plus
dimensions, then matched calorimetry/lead/contact evidence, are the acquisition
priorities; no measurement, grade identity or statistical uncertainty is claimed.
The canonical 38-page Rev3 stays byte-identical because this is an internal
qualification program, not independently established new device physics.
No further scientific experiment or external acquisition is authorized. The
same-mesh affine gas control remains one **proposed, NOT RUN** experiment;
it would not qualify the original field. Never inject failed gas/nonlocal powers.

Prior bounded studies remain evidence: read
`docs/TEC_GEOMETRY_MATERIAL_IDENTIFIABILITY_20261101.md` and its frozen registration.
269 solves gave 260 admitted / 9 rejected; 35 admitted equivalence checks pass.
The exact gauge `(g,r,k,s)->(c*g,c*r,k/c,s)` proves structural non-identifiability;
raw 300.15 K SVD rank changes 4-to-3 at the fixed cutoff and is not a unique
dimension measurement. At 0.2 A/zero load g=1.7 leaves +6.372118 K/+0.088846 V
chart residuals and fails unchanged native pad coverage. Assumed continuation,
unknown internal contacts and real-device feasibility remain unresolved.
The subsequently authorized finite-sink study is now complete; read
`docs/FINITE_SINK_MATCHED_TARGET_20261101.md`. Its one 193.560 s execution kept
geometry/laws unchanged: 203 admitted / 85 rejected grid cases; nine analytic
controls, four independent root checks and 54 actual target midpoint solves pass.
All 33 matching ideal-sink baseline outcomes are unchanged. Every admitted
finite-resistance case requires assumed >300 K continuation; numerical target
crossings are not real-device feasibility or global power minima. The same Rev3
now includes the verified sink insight and retains its exact predecessor bytes.
Independent dimensions/same-grade transport/contact evidence remains proposed.
Do not execute fitted triples,
reopen stopped solid/gas work, optimize currents or introduce new sink/cavity
physics automatically. Existing historical stops and longer-term priorities remain.

1. **Solid comparison is stopped at its registered boundary:** follow
   `docs/MATCHED_SOLID_MODEL_DIAGNOSTIC_20261031.md` and the current
   `docs/NONLOCAL_PORT_NETWORK_20261031.md`. Geometry-only Milestone 2 predicts
   8.412629 K warming against the original 7.630466 K cold-ceramic gap, leaving
   FEM minus prediction −0.782163 K and +7.810466 mV. No fitted K or new FEM.
   Its 7.277% side-port sensitivity still fails. The one follow-up is recorded in
   `docs/PASSIVE_PLATE_PORT_AUDIT_20261031.md`: seven independent constant ports
   have incompatible native edge traces and omit hot/presolder plus cold/attach
   cuts. It stopped with **zero grids/solves**, without reading reference fields
   or adding conditions. Spreading contributions remain unidentifiable; Rev3
   remains intact. No further solid fit/grid/fixture or causal kelvin claim.
2. **Native gas is now stopped at its raw flux gate.** Read
   `docs/ISOLATED_CAP_AND_NATIVE_GAS_20261101.md` first for this branch, then the
   historical `NATIVE_GAS_DOMAIN_AUDIT_20261101.md` and
   `UNIT_CORRECT_CAP_AND_NATIVE_GAS_20261101.md`. Separate writer/reader processes
   fixed physical STEP units without changing intended geometry. All 219 actual
   solids, contacts, ownership, manifold closure and normal witnesses passed;
   gas volume 1.253174211e-6 m³. One 228,710-tet gas control completed with
   **32.6274% raw global mismatch >1%**. Reaction closure is not raw qualification.
   The field audit is now complete: read `docs/NATIVE_GAS_FLUX_FORENSICS_20261101.md`.
   Normal-flux jumps of the C0 P1 field account for the entire net defect;
   shared-node splitting cannot change it. No mapping/trace error was found.
   The one proposed next experiment is a globally affine Dirichlet control on
   the exact existing mesh (known facet fluxes), **not authorized or executed**.
   It would test the solver/output pipeline, not qualify the original curved
   field or establish convergence. No new grid/solve or fitted correction. Do not
   couple unqualified powers into device predictions. No old G3b geometry/chords,
   filled core, CFD or reopening stopped solid fixtures. N2 Kn=0.458 at 100 Pa
   fails; at 101325 Pa Kn=0.000452 but nominal Ra~2501 flags buoyancy. This was a
   deliberately flow-suppressed conduction control, not actual steady gas behavior.
3. **Native-surface radiation/exchange:** replace the filled-core shortcut with a bounded
   actual-surface visibility fixture/operator from corrected cap/window and
   package surfaces, exposing interleg voids, pins and wires. Audit face ownership,
   normals, areas, first-hit visibility, blocked pairs, reciprocity, closure,
   refinement and heat conservation. Retain the present proxy as a comparator;
   do not imply a new 3D thermal field or force an expensive conformal cap merge.
4. **Integrated mechanism and uncertainty comparisons:** paired gas/radiation/
   lead controls plus contact, bypass, material-grade and cap/window/sink-reservoir
   hypotheses in the bounded five-node/nonlinear model. Report accepted-domain
   coverage, rejected candidates, heat budgets and power at matched detector
   targets. Use labeled scenario spans; no OEM fit or invented observations.
5. **Conditional later 3D qualification:** pursue a justified, resource-bounded
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
