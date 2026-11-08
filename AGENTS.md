# CURRENT PROJECT CONTRACT

**SCIENTIFIC REPORT AUDIENCE (2026-11-08 USER DIRECTIVE):** The current standalone engineering report is written primarily for detector scientists, device physicists and hardware engineers, not a software/FEM engineering audience. Lead with physical construction, heat flow, cooling performance, current/voltage/power, thermal contacts, parasitic conduction, meaningful material sensitivity and uncertainty. Present simulations as evidence in support of hardware decisions; move body counts, mesh internals, solver taxonomy and repository history to later methods/provenance. Use authentic shaded source-CAD figures with correct occlusion and clear real terminal identities; no misleading wireframes for hero figures. Document architecture and temperature conclusions conservatively. Historical Rev3 stays sealed. See docs/CURRENT_MODEL_DOCUMENTATION_MAP_20261108.md.

**DOCUMENTATION CORRECTION, 2026-11-08 (USER DIRECTIVE; OVERRIDES 43-PAGE POLICY BELOW):** The original **38-page Revision 3** has been restored byte-for-byte to reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf (SHA-256 882209b09796acdc5e7d3aafc376f1722fce2843230233c7a76542ebcb273248). It is a methodology reference for the **obsolete 216-domain / 28/12/4** cooler, NOT the current physical design. The separate **current model assessment** is reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf, with reusable sources in reports/current/. It describes the 824-solid replacement formed-tab assembly, 430-domain R3 derived geometry and working V3.3 88-leg / four-ceramic hybrid. The 43-page interim edition is archived under reports/historical/rev3_v33_interim_43pp_20261108/. Crucial outstanding physics: formed tabs 58/80 and three-foot return 88 are connected CAD solids but their nonlocal electric/thermal/Joule fields are not fully modeled in V3.3. The next step is to couple this already-built geometry to the working end-to-end model, not design another arbitrary cooler. See docs/CURRENT_MODEL_DOCUMENTATION_MAP_20261108.md. Never replace the historical Rev3 again to update current physics. No solver was rerun in this documentation correction.

**SUPERSEDED 2026-11-08 CANONICAL REPORT UPDATE (HISTORICAL ONLY):** The ONE current public scientific
assessment is the [43-page Revision 3 master](reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf), updated in place with V3.3 hybrid science and seven figures from frozen data. The exact preceding 38-page PDF and provenance are separately sealed historical evidence. The earlier 11-page V3.3 document is historical source material, not a competing current report. Continue improving the one master when justified; preserve all archived numerical failures and fields. No new physics solve occurred for this report update. The active engineering priority remains the working-system-first directive immediately below.

**AUTHORITATIVE USER DIRECTIVE — 2026-11-07: ENGINEERING-PLAUSIBLE VIRTUAL DEVICE, WORKING END-TO-END, ITERATE COARSE TO FINE. OVERRIDES CONFLICTING LATER-DATED / HISTORICAL NEXT-STEP LABELS BELOW.**

**MAIN GOAL:** Build a **realistic and physically defensible reference simulation of a three-stage thermoelectrically cooled HgCdTe detector and nine-pin package**, including actual source-derived 3D geometry as feasible, its TEC electrical/thermal transport, stage heat flow, ceramic/contact/lead paths, detector and cavity/package heat loads, mounting/sink, and eventually a practical parametric design platform. The modeled 29/11/4 source-CAD topology is a **chosen engineering reference hypothesis**, not an assertion of a TEC Microsystems or VIGO production assembly. **Do NOT try to clone, uniquely fit, validate against, or obtain proprietary data from a specific manufacturer as a prerequisite for progress. No emails, sourcing requests, or user lab data are required to continue.**

**WORKFLOW:** Keep ONE continuously runnable **end-to-end** model, beginning with rudimentary reduced/simplified physics, then improving that SAME system in small working steps. Make physically plausible estimates from public engineering properties, dimensions and sound transport theory where no measurements exist. Declare assumptions, temperature ranges and model limitations; use modest bounded ranges and trial-and-error when needed. An inferred parameter is **permitted for an exploratory reference design** and is **not** a reason to stop. Source-specific matched material grades and empirical OEM validation matter **only for future as-built or OEM-identity claims**, which are not our present objective. No solver revision shall invent or conceal measurement evidence.

**WHAT COUNTS AS PROGRESS:** Each meaningful new version must still compute at minimum TEC current, terminal V and electrical power, three-stage hot/cold temperatures and heat fluxes, detector temperature, all major relevant heat-source/sink terms, and charge/energy closure. Compare at the SAME 0.4 A / 300 K / 2 mW detector reference case to previous working V3.2 (conditional T_die 209.987981 K, V 1.524071 V, P 0.609628 W), then expand to a small current/load sweep when the whole system is stable. Preserve V1–V3.2 as reproducible comparators. Increased spatial fidelity should produce **actual coupled original-geometry fields where claimed**, never be mislabeled a full 430-domain 3D electrothermal PDE while P/N transport remains axial.

**ORDER OF ENGINEERING WORK:** (1) maintain / verify the V3.2 complete working device; (2) add the most impactful missing **whole-package physics** at a deliberately coarse fidelity using existing reusable code: cavity gas/vacuum and radiation boundary heat, package/header and realistic sink thermal pathways, plus detector bias/loads; (3) recover I–V–temperature and cooling performance across a few practical operating points, test stability, physical limits and energy conservation; (4) refine material transport, contact/spreading and spatial resolution ONLY when they materially affect the integrated outputs or robust convergence. Prioritize a working plausible multiphysics device over perfect local flux diagnostics, more source registries, or new simulated subcomponents disconnected from the detector.

**EXECUTION BOUNDARIES:** Trial-and-error and reasonable proxy properties are authorized for this *synthetic reference model*. Minimize new solvers, audits, reruns and documents; implement the simplest usable next version instead of waiting for OEM input or endlessly profiling. Use existing source mesh and code; timebox compute. Historical strict original Gate B FAIL/STOP, first 3D pair raw current FAIL 8/8, prospective P2 STOP, and full 430-domain C/D NOT RUN remain historically true and cannot be reclassified; they do **not** block the explicitly conditional coarse end-to-end development. Predictive accuracy for a specific manufactured device remains **unqualified** until measured evidence is available.

**PRECEDENCE:** This directive is the active task priority. Prior appended text headed "OEM material readiness blocked", "secure matched-grade data before simulation", or similar is preserved **only as historical evidence for product-specific qualification**, not as a future work-order or stop condition for the reference-design simulator. The preexisting working-system-first contract below remains authoritative. Avoid email proposals and OEM identifiability campaigns. The next substantial response to "proceed" should advance a runnable device model, not produce another no-solve audit.


**2026-11-08 V3.3 FIRST WORKING FULL-PACKAGE KRYPTON / GRAY-RADIATION COUPLED TEC PROTOTYPE — SOURCE 29/11/4, 88 ORIGINAL LEGS AND FOUR ORIGINAL 3D CERAMICS.**
Read [complete 0.4A / 100Pa Kr source numerical
and physical report](docs/V3_3_CAVITY_GAS_RADIATION_PACKAGE_20261108.md),
[full V3.3 electrical, heat, original 3D nodal and
80+-field numerical result](data/v3_3_cavity_package_feedback_20261108/attempt02/result.json),
[registered model source and actual gas/rad inputs](data/v3_3_cavity_package_feedback_20261108/attempt02/registration.json),
[independent no-PDE reconstruction of every stage,
88 legs, Kr gas, gray radiation, original 4 ceramic
face source and global energy](data/v3_3_cavity_package_feedback_20261108/attempt02/independent_read_only_acceptance.json),
[fully runnable same source V3.2-integrated derivative](scripts/v3_3_cavity_package_feedback.py),
[SHA source/archive and unchanged original Rev3
provenance](data/v3_3_cavity_package_feedback_20261108/manifest.json).
V3.2 completely preserved as cavity OFF reference:
Tdie209.987981K, V1.524070832V, P0.609628333W,
bathQ0.590322603W at0.4A/300K/2mW die.
NEW V3.3 SAME current and full source original
88-leg29/11/4 nonlinear 32-cell transport,
4 source actual ceramic FEM plates 11791 TET4,
per-leg native pad flux plus176 SnSb+352 contact
hypothetical electrical Joule, die attach, Cu/Au,
header/TIM/radiator. Added effective 100Pa Kr
cavity with 3mm effective gap, accommodation0.8,
NIST k 200/300/400K [.0064,.0095,.0122]W/mK;
gray cap eps .20, ceramic .80, window .10, view
.5/.7, warm reservoir300K. Exposed effective
source geometry rings [12.6,8.68,4.76,1]mm2
at C1,C2,C3,die. Gas loads total3.892553mW,
radiation.624077mW; total cold4.516629mW,
source 300K reservoir removes matching load.
V3.3 Tdie210.625214K (+.637233K),
terminal1.522462416V (-.001608416V),
Pel.608984966W (-.000643367W),
bathQ.594043746W (+.003721143W).
5 spatial iterations; last original pad thermal
change1.65345e-5K within REGISTERED COARSE
2e-5K (not h-convergence), global energy
8.8674e-9W within1e-8W, stage4.9061e-9W,
ceramic net5.50e-15W, individual leg
1.2364e-13W. Independent NO-SOLVE audit passes
but saved source pad heat vs final P/N model has
NONZERO 2.535e-8W finite lag, preserved.
CRITICAL: gas/radiation is an EFFECTIVE gap/gray
reservoir approximation and its exposed cold
load is spread over ORIGINAL upper ceramic
native metal pads by area, NOT over every real
gas-solid outer boundary; no cavity gas PDE,
CFD, actual radiosity all surfaces, optical
window transmission or actual OEM product.
Current 430 domains and29/11/4 differ from
the older 216-domain 28/12/4 calculation. The
canonical Rev3 master now distinguishes both;
its preceding 38-page bytes are sealed evidence.
FIRST attempt stopped early due old V3 seed/tight
2e-7K threshold, no accepted result; trial and
stop evidence retained. Second warmed from V3.2
and used explicitly coarse 2e-5K stopping
with exact same material and gas parameters.
NEXT WORKING-SYSTEM MILESTONE: small bounded
current/load/pressure operating map on this SAME
V3.3 complete coupled model, with coarse pass,
cold/hot safety and energy checks, rather than
another material registry or OEM email.
KEEP full original P1 B FAIL/STOP, first source
P1 raw contact 8/8 FAIL, prospective P2 STOP,
full 430 C/D NOT RUN. No Codex or remesh.
DOCUMENTATION IS A SCIENTIFIC DELIVERABLE:
new versions must include a STANDALONE, source-
neutral technical document with all model
assumptions, source material tables, mechanical
dimensions, equations, BCs, solver method, tolerances,
and numerical comparison; no knowledge of the
operator or this repo can be required to reproduce
SIMILAR physical results independently. Historical
Rev3 PDF must remain immutable and any new
geometry-version results explicitly distinguished.


---

**2026-11-07 SOURCE-TRACED P/N MATERIAL READINESS GATE: OEM PHYSICAL PREDICTION BLOCKED, RUNNING V3.2 UNCHANGED.**
Read [scientific material evidence and intake report](docs/V3_2_PHYSICAL_MATERIAL_READINESS_20261107.md),
[whole V3.2 original 88-leg material-coverage and
source SHA audit](data/v3_2_material_readiness_20261107/attempt01/material_contract.json),
[standalone no-solve source provenance and endpoint auditor](scripts/v3_2_material_readiness_contract.py),
[grade-matched OEM/experimental data intake template](data/v3_2_material_readiness_20261107/attempt01/candidate_INGEST_TEMPLATE.json),
[fail-closed source-grade intake validator](scripts/v3_2_material_candidate_validator.py),
[11-evidence-item template rejection](data/v3_2_material_readiness_20261107/attempt01/candidate_template_rejection.json),
[archived hash contract](data/v3_2_material_readiness_20261107/attempt01/manifest.json).
The active V3.2 actual nonlinear P/N constitutive
transport uses unchanged Zhang2025 N-HE-1 and P-HE
research hot-extruded plots: SIX digitized figure
curves S(T),rho(T),k(T), each 14 points, 84 source
marker values in 40..300K. These are DIFFERENT
research samples, NOT manufacturer-matched P/N
grades or raw source measurement uncertainty.
Model 300..390K behavior is a deliberately assumed
25% of last 280..300K published piecewise slope;
NO published evidence for actual >300K transport.
Working source V3.2 88 leg hot/cold extrema
209.901..304.615K, all58 first-stage legs have
hot contact >300K, as much as4.615K above plot.
A fast read-only audit never labels source graph
reading +/-1.3K or property-marker digitization
bounds as actual-grade physical accuracy.
OEM-grade material must remain FAIL-CLOSED until
verified original installed module/lot identity,
P AND N six source-matched SI-unit curves and
real uncertainty/traceability covering at least
209.901..304.615K (ideally200..305K), validated
supplier pairing and full I/V/load comparison.
The input validator deliberately rejects an empty
intake template with 11 required missing items;
even complete schemas require independent review
and NEVER auto-update the working model.
NO 3D PDE, original-material source replacement,
new fitting, mesh changes or fake OEM inputs.
Current complete V3.2 working source 0.4A
Tdie209.987981K remains CONDITIONAL; source
P1 GateB FAIL/STOP, first pair raw gradient
FAIL8/8, full 430 C/D NOT RUN unchanged.
Next engineering event: source actual P/N manufacturer
material or experimental curves + matched device
I/V vs load, then separately version material
hypothesis and compare same full I/V/P/Tdie/E.
Do not spend resources on another unrelated PDE
or model-prediction claim until physically justified.
No Codex used.

**2026-11-07 USER-DIRECTED ANTI-CHURN WHOLE-SYSTEM SENSITIVITY SCREEN: FAST EVIDENCE CONFIRMS P/N TRANSPORT SHOULD TAKE PRIORITY OVER MORE GEOMETRY.**
Read [same-current 8-case nonlinear source 29/11/4
material/boundary screening report](docs/V3_2_WHOLE_SYSTEM_SENSITIVITY_DECISION_20261107.md),
[8 accepted source-hashed reduced full-device inputs and
I/V/P/Tdie sensitivity results](data/v3_2_bounded_sensitivity_20261107/attempt01/fast_results.json),
[0-PDE read-only acceptance](data/v3_2_bounded_sensitivity_20261107/attempt01/read_only_acceptance.json),
[fast 14.2-second runnable source screening
script](scripts/v3_2_fast_system_sensitivity.py),
and [source hash/failed-expensive-run manifest](data/v3_2_bounded_sensitivity_20261107/attempt01/manifest.json).
Original full V3.2 88-leg + 11,791 source 3D
ceramics and solder/contact working baseline
STAYS UNCHANGED, Tdie209.987981K at 0.4A,
Pel.609628W. Explicitly STOPPED a preregistered
6-case full V3.2 nonlinear 3D sensitivity campaign:
first S+10% case did not produce any accepted
result after approximately 6min. ZERO full-V3.2
sensitivity outcomes are available; stopped
source, log and registration archived. Do not
silently reuse the discarded case as physics.
Instead 8 original-CAD V1 reduced end-to-end
nonlinear source/Cu/Au/sink/2mW die cases all
passed exact energy/IV acceptance in14.19s,
nominal V1 Tdie209.059878K verified. Same
0.4A V1 reduced one-parameter changes:
S(P/N)+10% -> dTdie-6.600K;
rho(P/N)+20% ->+2.428K;
k(P/N)+20% ->+10.217K;
radiator 2->3K/W ->+0.264K;
detector2->4mW ->+0.627K.
Coherent lower PN scales(S.9,rho1.2,k1.2)
->+19.581K; coherent higher(S1.1,rho.8,k.8)
->-22.189K. These are DIFFERENT fidelity V1
screening DELTAS, never claim full V3.2 spatial
sensitivities, confidence intervals, or as-built
T errors; scaled published unmatched Zhang
research materials, not real OEM grade. Per1%
input change S and k large; choose to obtain
actual PN material grade and S(T),rho(T),k(T)
for both carriers around200-305K and validate
source transport instead of another fine FEM.
Current active next step: secure materials source
or physically calibrate from legitimate published/
client-provided matched measurements, then re-run
the SAME source V3.2 case; if not available,
use FAST screened high-impact alternative within
a tiny specified full V3.2 confirmation budget.
Don't expand a full spatial parameter grid.
Preserve original P1 GateB FAIL/STOP, first
original coupled pair raw current FAIL8/8,
prospective P2 STOP, full 430-domain C/D
NOT RUN and as-built predictive release UNSET.
No Codex, CAD change or original mesh change.

**2026-11-07 V3.2 WORKING INTEGRATED SOLDER + ELECTRICAL CONTACT JOULE FEEDBACK: ONE CONDITIONAL FULL SYSTEM NUMERICAL PASS.**
Read [V3.2 whole-system energy and physics scope](docs/V3_2_SOLDER_CONTACT_JOULE_FEEDBACK_20261107.md),
[original 176 SnSb and 352 interface added electrical
loss full V3.2 result](data/v3_2_joint_loss_feedback_20261107/attempt01/result.json),
[independent NO SOLVE source face and stage heat
acceptance](data/v3_2_joint_loss_feedback_20261107/attempt01/read_only_acceptance.json),
[unchanged V3.1-derived nonlinear integrated driver](scripts/v3_2_joint_loss_feedback.py),
[read-only independent acceptance](scripts/v3_2_read_only_audit.py),
[source and archived result SHA manifest](data/v3_2_joint_loss_feedback_20261107/attempt01/manifest.json).
Same 0.4 A,300 K environment,2 mW detector,
original source 29/11/4,88 real P/N legs and
11791 original CAD 3D ceramic TET4, same nonlinear
32-interval transport+native source ceramic per-pad
heat feedback as V3.1. Added source 176 SnSb bulk
solders rho=1.7e-7 Ohm*m prior hypothetical,
35um thick,0.16mm2 area, plus source352 solder
electrical interfaces hypothetical rho_c=1e-11
Ohm*m2. Additional series R=.028545Ohm,
delta nominal direct electrical V=.011418V,
I²R=.0045672W, equal positive25.95uW heat into
EACH adjacent original ceramic hot and cold
solder pad (explicit provisional thermal partition;
NOT physical measured contact thermal drop).
All source contact hot/cold current loops, native
pad Neumann heats and stage thermal balances include
the added 4.5672mW electrical Joule work; four
ceramics receive [.0015051,.0020760,.0007785,
.0002076]W. V3.2 complete calculated Tdie
209.987981K vs V3.1 209.803293K
(+.184688K), Vterminal1.524071V vs1.513297V,
electrical P.609628W vs.605319W,
bathQ.590323W vs.586174W. 12 spatial outer
iterations; max local T update1.2194e-7K,
global energy residual1.3789e-10W; independent
no-solve audit source face 88-leg/4-ceramic PASS
within declared tolerance; last saved original
source pad flux vs last leg update discrepancy
1.0431e-10W, explicitly NONZERO finite tolerance.
There is NO full original metallization bulk
series R model, no joint thermal resistance, no
contact Peltier, no 3D bulk P/N charge PDE or
as-built material qualification. Avoid calling
this a fully spatial 430-domain physical TEC.
Original P1 B FAIL/STOP, first actual pair P1 raw
current FAIL8/8, prospective P2 STOP, 430 C/D
NOT RUN. The source CAD/mesh and prior V1-V3.1
standalone working simulations remain untouched.
Do NOT revisit exhaustive contact microaudit;
prioritize whole-system measured input uncertainty
and high-impact physics before another fine mesh.
No Codex used.

**2026-11-07 SOURCE 3D P/N GEOMETRIC SUFFICIENCY CHECK: DO NOT WASTE V4 ON AXIAL A/L SHAPE FACTORS.**
Read [all-88-leg source original 3D unit-conductance
result](data/v4_source_pn_3d_geometry_20261107/attempt01/result.json),
[source registration and NO-CHURN decision](data/v4_source_pn_3d_geometry_20261107/attempt01/manifest.json),
[exact original-TET4 P1 3D scalar conductance
reproducer](scripts/v4_source_pn_3d_geometry.py).
All 88 real P/N legs, 7357 source R3.9 TET4,
source-native SnSb-facing end TRI3 surfaces used.
Unit k, one Kelvin Dirichlet between original
0.4x0.4mm end contacts, lateral insulation:
effective 3D conduction vs A/L is precisely 1
to max3.11e-15 deviation. This is expected for
rectangular homogeneous legs with equipotential
faces and isothermal boundary faces and confirms
that 3D mesh alone does not justify a new integrated
solver: V3.1 axial geometry is exact under these
constraints. DO NOT call this 3D thermoELECTRIC
coupling or evidence of actual 3D potential/heat
uniformity when end temperature and metal spreading
are nonuniform. V3.1 stays canonical executable
full-system case, 209.803293K at conditional0.4A.
Further fidelity should add actually missing physics
(solder/metal electrical Joule and thermal contact,
nonuniform end boundary/matched P/N transport) only
when it changes the same complete current, voltage,
die temperature and energy balances. No random mesh
refinements or redundant V4 integrated implementation
with correction=1. Original P1 Gate B FAIL/STOP,
first 3D pair raw current FAIL8/8, full C/D NOT RUN,
as-built temperature UNQUALIFIED. No Codex.

**V3.1 INTEGRATED NATIVE-PAD NONUNIFORM HEAT FEEDBACK (2026-11-07): WORKING END-TO-END PROVISIONAL BASELINE, NUMERICAL PASS; NOT 430-DOMAIN SPATIAL E/T.**
Read [V3.1 concise original 3D ceramics and 88-leg
nonuniform heat-feedback report](docs/V3_1_NATIVE_PAD_FEEDBACK_20261107.md),
[full V3.1 0.4A detector/TEC/pad heat source results](data/v3_1_native_pad_feedback_20261107/attempt02/result.json),
[real original-geometry ceramic nodal T fields](data/v3_1_native_pad_feedback_20261107/attempt02/source_native_ceramics_V3_1.npz),
[saved-field no-solve acceptance](data/v3_1_native_pad_feedback_20261107/attempt02/read_only_acceptance.json),
[source and original-mesh hashed manifest](data/v3_1_native_pad_feedback_20261107/manifest.json),
[reproducible integrated nonlinear plus original 3D FEM
source](scripts/v3_1_native_pad_feedback.py).
PRESERVE the separately runnable V1/V2/V3 baselines.
At same source CAD29/11/4, current0.4A,ambient300K,
detector2mW and unmatched research P/N transport:
V3.1 now applies each of the 88 leg calculated actual
hot/cold heat currents to ORIGINAL 91 source-leg ceramic
metal pads, together with source Cu lead correction
on ceramic0 native face36, original detector carrier
on ceramic3 face119 and original thermal sink via
ceramic0 underside face6. Solve the same four ORIGINAL
ceramic R3.9 meshes 11791 TET4 with k30W/mK
HYPOTHETICAL Al2O3, reusing direct source P1
Neumann FEM influence vectors. Iterate all original
88 separate 32-slice nonlinear P/N leg transport at
their actual local 3D original CAD pad temperatures
until full-source pad/ceramic thermal self-consistency.
Original V3 frozen uniform per-pad flux source defect
up to44.8% now addressed BY CONSTRUCTION for
selected source native pads. Last V3.1 solve
11 spatial outer iterations; maximum spatial field
update1.3181e-7K <2e-7K, all original ceramic
heat imbalance2.22e-15W, whole TEC and detector
thermal-electrical energy residual1.36e-10W,
max separate leg energy residual1.18e-13W,
max stage mismatch1.32e-10W.
V3.1 Tdie209.803293K vs V3 209.688407K
(+0.114887K), Vterminal1.513296654V,
Pel0.605318662W, sinkQ0.586173695W.
FAILED attempt01 loose2e-5K final stage balance
preserved as negative evidence, prospective tightened
attempt02 numerical PASS. Read-only original CAD
face and source heat audit passed; no extra PDE or
heavy regression test suite or Codex used. THIS IS
STILL HYBRID, NOT source430 full spatial TE:
original P/N legs still nonlinear axial1D and
solder/metallization local Joule/Peltier, gas/rad
and real transport k(T), P/N grades or contacts
remain unmeasured. Real as-built T UNQUALIFIED.
Original P1 Gate B FAIL/STOP, prospective P2 STOP,
first actual 3D pair P1 raw currents FAIL 8/8,
full source430-domain C/D NOT RUN. NEXT: maintain
V3.1 as a working complete baseline; prioritize
first source spatial P/N coupled device prototype
ONLY if it delivers directly comparable whole-system
I/V/P/Tdie/energy and stable resolution improvement,
not another isolated current microaudit. Continue
USER PRIORITY: coarse working system before details.

**V3 COMPLETE 88-LEG SOURCE-CAD SPATIAL NONLINEAR THERMOELECTRIC HYBRID WORKING BASELINE (2026-11-07): REPLAY PASS, LOCAL PAD HEAT FEEDBACK NOT CLOSED.**
Read [V3 full working 88 individual P/N leg + original
source ceramic integration report](docs/V3_INTEGRATED_LEG_RESOLVED_20261107.md),
[V3 exact registered case and ALL 88 saved individual 33-node
axial profiles + four 3D original ceramic fields](data/v3_integrated_leg_resolved_20261107/attempt01/result.json),
[V3 original pad flux inconsistency quantified](data/v3_integrated_leg_resolved_20261107/attempt01/local_pad_flux_assumption_audit.json),
[V3 full source SHA manifest](data/v3_integrated_leg_resolved_20261107/attempt01/manifest.json),
[working V3 nonlinear integrated solver](scripts/v3_integrated_leg_resolved.py).
Keep running V1 and V2 separately. V3 uses same 0.400A,
300K ambient,2mW detector load and original 29/11/4
source TEC; graph traces all original 88 P/N legs via
two native SnSb solders, metallization net and 91
unique original native ceramic pad faces. Sample the
original 11,791-tet source ceramic 3D temperature
response on exact TRI3 patch area means and solve the
existing 32 axial slices independently for each
original leg, then close 8 ceramic/die temperatures
and 4 stage/ceramic heat currents plus source Cu/Au
wire and mounted header/TIM sink terms. Full one-case
V3 result Tdie209.688407K, Vterminal1.511733V,
Pel0.604693W, bathQ0.586082W; relative V2
Tdie +0.030164K (NOT source numerical error bound
or physical measurement). 5 nonlinear evaluations;
whole energy residual5.32e-13W; max separate leg
energy residual7.39e-14W. Read-only original
fields replay PASS. No Codex used.
CRITICAL PROTOTYPE LIMIT: local ceramic 3D Neumann
source distributions remain prior V2 area-UNIFORM
heat patterns, NOT the individual nonuniform leg
heat fluxes computed from V3. Independent saved-field
source-pad L1 discrepancy (not T or conservation
error): top ceramic0 9.64%, ceramic1 top 21.25%,
ceramic2 top44.79%, other sides3.3-5.5%. Hot
ceramic0 also has separate Cu wire/lead heat; source
stage heat ≠ bath heat. DO NOT claim V3 is fully
bidirectional *spatially* coupled, 3D P/N bulk
current or full 430-domain FEM. NEXT coherent V3.1
is to apply real per-leg heat to original native
ceramic pads (Cu/gold/power-lead and detector paths
separate), re-solve original 3D ceramic fields,
and iterate leg-local temperatures to local heat
balance in the SAME complete I/V/P/Tdie system.
Keep one registered .4A operating point and compare
to working V3; no isolated contact micro-audit
or expensive new global mesh. Source P/N analog
unmatched, kAl2O3=30 W/mK hypothetical; >300K
law continuation assumed. Original P1 GateB FAIL/
STOP, first 3D pair raw P1 FAIL 8/8, P2 STOP,
full original 430-domain C/D NOT RUN and
as-built T unqualified. No original source edits.

**V2 INTEGRATED SPATIAL WORKING BASELINE (2026-11-07): COMPLETED, ORIGINAL 3D CERAMICS + NONLINEAR 29/11/4 TEC, HYBRID NOT FULL 3D E/T.**
Read [source-CAD V2 numerical report and V1 comparison](docs/V2_INTEGRATED_SPATIAL_HYBRID_20261107.md),
[canonical V2 one-case end-to-end I/V/Tdie/E result](data/v2_integrated_spatial_20261107/attempt02/v2_integrated_result.json),
[source-hashed 4-ceramic/11,791-original-TET4 response and full spatial fields](data/v2_integrated_spatial_20261107/attempt01/ceramic_spatial_operators.json),
[V2 source-integrity manifest](data/v2_integrated_spatial_20261107/manifest.json),
[original CAD ceramic FEM unit response code](scripts/v2_source_ceramic_spatial.py),
[nonlinear integrated V2 spatial-coupling driver](scripts/v2_integrated_spatial_hybrid.py).
Retains V1 as RUNNABLE comparator, fixed 0.4 A/300K/2mW
die, 29/11/4 original source geometry, Cu/Au wires and
unmatched Zhang P/N 32-interval nonlinear solver.
New: original source ceramic0..3 3D source R3.9 P1
thermal fields (4936+4085+1986+784 = 11791 TET4;
original native upper/lower metal pad faces), one
constant CONDITIONAL alumina k30W/mK hypothesis,
balanced original-pad source Neumann thermal fluxes.
Effective ceramic 3D R=[1.175880,2.444299,3.998256,
4.649599]K/W; these now couple TWO-WAY to eight
separate N/P junction/ceramic/die temperatures and
re-solve TE electric and thermal stage fluxes. V2
0.4A terminal1.511212V, P0.604485W, bathQ0.585882W,
source die209.658243K versus V1 209.059878K:
V2 minus V1 +0.598364K, NOT real-device uncertainty.
Hot-side equivalent6.009267K/W (V1 5.281295).
One operating-point nonlinear 6 function evaluations,
unscaled heat residual3.89e-15W, hot/cold interface T
residual1.38e-14K, whole energy accounting1.42e-13W;
read-only exact saved spatial field replay PASS.
First attempt had output key typo, separate registration
preflight rejected narrative field; both failure notes
preserved, no material/mesh/BC sweeps. V2 original
source ceramic temperature spatial spans: plate0 3.031K,
plate1 1.356K, plate2 .450K, plate3 .024K. These
3D ceramic sources remain one original mesh with
unmatched thermal-k(T), uniform heat flux per source
contact and no metal spreading/contact R; P/N electrical
currents still nonlinear 1D, not full 430-domain E/T
field, so FULL C/D NOT RUN and NO as-built T release.
Original P1 electrical Gate B FAIL/STOP, first-pair
raw current FAIL 8/8, P2 prospective STOP all intact.
No Codex used; quota preserved. NEXT V3 coarse
integrated spatial P/N + ceramics *only if* it can
improve the same complete output I/V/P/Tdie and energy
and preserve V1/V2 working baselines; NO microcontact
forensic churn.

**V1 INTEGRATED WORKING BASELINE (2026-11-07): COMPLETED, CONDITIONAL COARSE ELECTROTHERMAL NETWORK.**
Read [one source-CAD 29/11/4 integrated package report](docs/V1_INTEGRATED_FULL_PACKAGE_20261107.md),
[single-case source-hashed result](data/v1_integrated_full_package_20261107/attempt01/result.json),
[evidence manifest](data/v1_integrated_full_package_20261107/attempt01/manifest.json),
and [replayable ONE code path](scripts/v1_integrated_full_package.py).
This V1 uses actual source-CAD 29/11/4 leg, four ceramic and
20um die-attach dimensions; original CAD Cu/Au bond and power wire
lengths; one existing nonlinear P/N transport cascade (32 axial
intervals per leg), five stage/die nodes, the previous source
47,702-TET4 Kovar+TIM Robin component R=2.759313K/W, original
source 1D solder+Al2O3 analogs R=.074074+.447908K/W, and
manufacturer RECOMMENDED (not installed measured) radiator
2K/W. These parts replace old ENTIRE sink5K/W with one
single equivalent total R=5.281295K/W, NOT added to 5!
One registered 0.400A, 300K ambient/pin, 2mW die
nominal research P/N analog, CAD wires ON, vacuum gas OFF,
cavity radiation OFF: T hot303.097873K, stage1
265.083905K, stage2 234.634353K, cold208.989754K,
die209.059878K, terminal1.506395V, electrical0.602558W,
bath rejection0.586574W, stage and node conservation
<1e-8W, global residual -3.365e-13W. Source V0 same I,
wires and die, old whole path5K/W gave die208.985312K,
so +0.074566K for this single path change, NOT verified
uncertainty. 303.1K exceeds 300K research measured
limit so >300K assumed transport continuation flagged.
V1 is a WORKING integrated reduced thermal network,
NOT spatial full430-domain 3D PDE, calibrated material
or as-built device prediction. Actual solder/contact
electrical Joule and junction energy, cavity gas/radiation,
3D ceramic/solder and unknown mounting contact NOT solved.
DO NOT launch new isolated micromesh forensic studies.
NEXT: V2 one coarse spatial actual-source system prototype
keeping same operating case and V1 outputs as comparator,
only essential convergence/charge/energy checks. Preserve
original P1 Gate B FAIL/STOP, prospective P2 STOP,
source N/P first-couple P1 raw 8/8 FAIL and full 430-domain
thermal C/D NOT RUN, original CAD/Rev3 unchanged. No Codex.

**OPERATING PRINCIPLE (2026-11-07): WORKING SYSTEM FIRST; ITERATIVE COARSE-TO-FINE DEVELOPMENT. AUTHORITATIVE USER PREFERENCE.**

This is the user's normal engineering method, not just a one-off TEC exception.
**Get an entire rudimentary system to run end-to-end first, then iterate on
that SAME system through progressively better physics, geometry, resolution
and validation. Do not perfect isolated details before proving that the
integrated system operates, produces bounded outputs, and responds
sensibly to inputs.** When choosing among next steps, prefer the one that
gets the next complete working version delivered with the least complexity.

Required development discipline:

1. **Vertical slice first.** Maintain ONE canonical, reproducible working
   simulation path from real source design inputs and drive through
   coupled electrical/thermal calculations to outputs (I, V, P,
   stage temperatures/heat fluxes, detector temperature and balances).
   Start with the simplest coherent representations: the existing
   source-CAD 29/11/4 reduced nonlinear TEC is already a CONDITIONAL
   end-to-end baseline; evolve it into a single connected coarse device
   calculation including representative header, mounting, detector load
   and source current path rather than building more detached studies.
   A coarse actual-source 3D version comes next when feasible; use
   simplified material groups and explicitly declared proxy properties.
2. **Refine the working baseline, don't restart from scratch.**
   Progress V0 (working reduced conditional baseline) -> V1
   (COMPLETED 2026-11-07 integrated coarse full-device thermal/electric path) -> V2
   (first coarse source-geometry 3D coupled device, if numerically
   practicable) -> V3+ (increase detail/resolution by measured impact).
   Preserve previous version/case/output as a numerical comparator
   and keep it runnable after each change. These labels describe
   development fidelity, NOT historical V3 geometry or qualification.
3. **Test only the essentials early:** connected electrical topology,
   bounded temperature/current/voltage, convergence of the chosen
   solve, charge conservation, total-energy conservation and a
   reproducible end-to-end result. For each new iteration, compare
   the same operating condition and record delta in T_die, terminal
   I/V/P, stage heat flux and conservation, not merely smaller local
   residuals. Label assumptions and numerical uncertainty honestly.
   No arbitrary 10% or other tolerance may be called a proven error
   bound without an actual comparator.
4. **Prioritize what matters.** Do a small preregistered sensitivity
   or mesh comparison ONLY after the integrated model runs, and only
   when it can determine the next high-impact refinement. Prioritize
   terms that materially change the full-system output, physical
   stability, or thermoelectric conservation. Do not pursue repeated
   micromesh/contact/flux diagnostics, exhaustive registries, high
   order elements, supplier minutiae or special-case tests that
   cannot improve the next integrated release.
5. **Protect the prototype loop.** Timebox diagnostics and avoid
   expanding a single failed subtest into an unbounded forensic
   campaign. If a detail blocks physical qualification but not a
   clearly labeled coarse conditional prototype, preserve its
   FAIL/STOP record, continue building the system at the permitted
   provisional fidelity, and revisit it only when it blocks a
   full-system convergence or accuracy objective. Never conceal
   failure, invent a source property, reinterpret an old gate, or
   claim as-built predictive accuracy. Critical physical-law,
   charge/energy, or instability errors that invalidate *even the
   rudimentary simulation* must still be fixed.
6. **Avoid work without an output.** Prefer one working code path and
   a few directly useful smoke and conservation checks per iteration;
   don't multiply solvers, tests, reports, or runs simply for
   completeness. Keep documentation concise and update the existing
   AGENTS.md and engineering chronology when a substantive
   milestone is achieved. Do not exhaust scarce Codex or VPS
   resources on optional diagnostics. Be candid when work is churn.
7. **Distinct gates:** A CONDITIONAL/EXPLORATORY end-to-end version
   may run without passing every high-precision physical release
   test, but it MUST be labeled nonqualified and cannot override
   historical original electrical Gate B FAIL/STOP, the 8/8 P1
   raw-contact failures of the first 3D pair, prospective P2 STOP,
   or unrun 430-domain thermal C/D. A future predictive/as-built
   release has separate strict source-evidence and numerical
   accuracy gates. Do not silently lower or rename old criteria.

**HISTORICAL NEXT-STEP DECISION (completed by V1–V3.2; not the current task):** Stop further isolated interface or
header work unless it blocks integrated execution. First use the
existing 29/11/4 nonlinear conditional baseline to create ONE
reproducible integrated coarse full-package electrothermal run with
explicit detector and hot-side paths, source-contact proxies clearly
labeled, simple geometry and useful I/V/T_die/energy output. Then
progress toward coarse full-geometry 3D on the SAME operating case,
refining only after observing complete-system behavior. The
completed nine-domain coupled 3D pair is a reusable numerical
building block with documented failed raw flux, not a prerequisite
for another long micro-diagnostic campaign.

**Historical evidence and qualification:** The following dated
sections retain their original results, negative evidence and
strict scientific qualification requirements, but their historical
"next task", "current priority", and detailed audit instructions
do NOT supersede this user-directed iterative-development rule.

This is the authoritative continuation contract, with the current operating
principle updated 2026-11-07. Historical work orders and milestone instructions describe their own checkpoints; their
"current", "next" and report-freeze language does not override this contract.
Their numerical evidence, original errors and acceptance criteria remain intact.

**HISTORICAL 2026-11-06 PHYSICAL BLOCKER CLOSURE (original qualification STOP preserved; superseded as task priority by 2026-11-07 working-system-first directive).**
Read the [strict no-solve physical readiness and Gate B audit](docs/V3_PHYSICAL_BLOCKER_CLOSURE_20261106.md),
the [current 430-domain source-backed receipt](data/v3_physical_blocker_closure_20261106/attempt01/readiness_audit.json),
and [reproducible fail-closed script](scripts/v3_physical_readiness_gate.py).
V3 source 430 regions/2440 native faces/378 finite contact witnesses and
global saved conformal R3.8/R3.9 mesh are real numerical achievements,
but physical transport is NOT qualified. Current original R3 source
metadata has430/430 domain laws UNSET and2440/2440 face laws UNSET
and all source solver_ready false. Historical 438/2456-law registry
is NOT portable directly to 430/2440 without source-tag conversion and
evidence-backed physical coefficients; no bulk-material fallback.
Original V3 net88/lead9 GateB electrical coupon FAIL remains:
raw film0→lead_land current-cut worst error85.6254999% versus0.1%
registered limit, terminal-cut errors0.8363%/3.3223%, voltage
boundedness FAIL despite verified algebraic IV-loss closure and
0.315803% two-mesh resistance difference. R3.12-R3.17 prove
regional synthetic scalar P1/P2 and two-contact mathematical
functionality only, NEVER the original failed physical coupon,
physical current closure, thermal or TEC performance.
Do NOT launch additional synthetic manufactured PDE/contact examples,
global meshing, heat solvers or project-wide physical FEM until
separately identified named STOP blockers are closed.
Priority P0: original preserved coupon read-only raw current/mesh
flux-failure attribution (no reruns) with unchanged GateB receipt;
P1: exact 430-domain/2440-face material/contact/terminal law ledger
with source, temperature range, evidence class and uncertainty;
P2: smallest real physical TEC couple subassembly ONLY when physical
coefficients and electrical Gate B candidate criteria are qualified;
P3: full 430-domain multiphysics only after physical network current
and heat closure, mesh accuracy and independent source evidence.
Any new physical coupon discretization comparator must be separately
preregistered, preserve old criterion/negative evidence and cannot
relabel old B FAIL. Gate B STOP, thermal C/D NOT RUN.
Original physical824-solid STEP, protected38-page Rev3, all
R3.3-R3.17 successes/failures and open issue#2 remain immutable.
Additional P0 READ-ONLY original coupon cut ledger:
[data/v3_physical_blocker_closure_20261106/attempt01/gate_B_cut_triage.json](data/v3_physical_blocker_closure_20261106/attempt01/gate_B_cut_triage.json).
Of16 original cuts, 13 fine-mesh FAIL the preserved0.1% raw
flux gate and3 PASS; 13 coarse->fine error improvements and3
worsenings. Worst film0->lead_land145.216% coarse->85.6255%
fine, joint6->film2 81.557%, joint4->film0 79.877%,
film2->pn87_solder 79.756% fine. Worsened tab88->joint4,
lead9->lead_land, and joint5->film1. The two tab88 interior
cuts pass; lead9_mid passes at0.061289%. This ranks original
source current cuts and does not isolate a single causal mechanism,
justify relaxation of B, or prove any physical model.
**2026-11-07 FIRST ORIGINAL SOURCE 9-CONDUCTOR 3D N/P THERMOELECTRIC COUPLED PROTOTYPE: WEAK CONSERVATION PASS, ALL 8 RAW CONTACT CURRENT CUTS FAIL.**
Read [coupled original CAD source nine-domain P1 engineering report and crucial raw flux failure](docs/V3_FIRST_SOURCE_COUPLE_3D_COUPLED_20261107.md),
[complete original 3D V/T saved fields at conditional test](data/v3_first_couple_coupled_20261107/attempt04/result.json),
[independent NO SOLVE saved-field power/current/energy audit](data/v3_first_couple_coupled_20261107/attempt04/saved_field_independent_audit.json),
[all attempt histories/metadata and source SHA](data/v3_first_couple_coupled_20261107/manifest.json),
[3D coupled source operator](scripts/v3_first_couple_coupled_3d.py) and
[read-only independent field audit](scripts/v3_first_couple_saved_field_audit.py).
Real saved R3.9 source mesh original nine conductor source IDs
5,6,7,8,9,10,269,270,271; 1000 actual tetra, 454 disjoint
region/nodal DOFs per electric and temperature field.
Original internal source contact tags124/125/130/135/140/
141/146/151 = 112 TRI3 facets; mathematically defined
series current cuts faces1531/162 are NOT independently
accessible external package terminals; ceramic pad interfaces
hot8/9 and cold44 idealized Dirichlet T.
Conditional current0.05A, hot-pad298K, cold-pad296K,
P/N dissimilar Zhang original measured source 40-300K,
old nominal GateB solder and laminate bulk proxies and
COMPLETELY UNMEASURED r_e1e-11Ohm*m2,
r_th1e-7m2K/W.
Charge J=-sigma(gradV+SgradT), heat q=ST J-kgradT,
TOTAL energy F=q+VJ continuity, finite interface Joule
shared halves; interfacial Seebeck term handled by
total energy, not pure Fourier heat flux.
One source-P1 3D coupled conditional numerical field
converged 20 Picard steps: terminal V=.004210119V,
P=.00021050594W; electrical independent breakdown
bulk Joule .00016844927W + Seebeck signed
.00004058390W + interface Joule .00000147277W,
relative error1.39e-12; signed hot/cold energy reactions
+.004419430W / -.004208924W, residual4.40e-10
relative. All original eight weak contact currents
abs0.05A with worst2.21e-12 relative residual. HOWEVER
ALL EIGHT original contact RAW one-sided constitutive
P1 gradient currents FAIL prospective0.1% gate,
worst original source face146 discrepancy368.62% of
imposed source current. Do NOT call this numerically
fully qualified contact FEM. Source T=295.983..298.017K
is a conditional FIELD RESPONSE to prescribed
296/298K ceramic boundaries, NOT actual cooler temp.
Four preserved attempts: orientation diagnostic issue
attempt01, source owner order fixed attempt02,
attempt03 JSON scalar export failure retained, final
attempt04 complete saved source fields and independent
audit with NO new PDE. All current 430/2440 material
laws remain UNSET. Historical original Gate B P1
FAIL/STOP (not changed); P2 prospective STOP; real
430-domain C/D NOT RUN. Further arbitrary P1 contact
parameter sweeps are CHURN: prioritize prospective
mixed/equilibrated H(div) current flux with independent
mesh and interface checks, or obtain actual contact/
material/thermal data. Do not retrofit weak reaction
as previous raw-current pass, nor invent calibrated
detector cooling. No source mesh/CAD/Rev3 changes
or Codex usage.

**2026-11-07 ORIGINAL SOURCE TEC SOLDER + FINITE JUNCTION PHYSICS SCALE: 352 exact CAD source interfaces, explicit future full-physics contact measurement target; NO PDE.**
Read [exact original 88-leg solder electrical/thermal
planning scales and future coupled 3D gate](docs/V3_TEC_SOURCE_CONTACT_SCALE_AND_COUPLED_INPUT_GATE_20261107.md),
[source-hashed numerical contact scale receipt](data/v3_tec_contact_scale_20261107/attempt01/conditional_contact_scale.json)
and [source-keyed analytic reproducer](scripts/v3_tec_contact_scale_gate.py).
Source R3 88 mandatory P/N legs (44P/44N), 176 native
SnSb solder solids (0.4x0.4x.035mm) and exactly352
CAD solder contacts all0.16mm2: 88 N/SnSb, 88 P/SnSb,
176 SnSb/metallization. Research P/N 300K NOMINAL
unmatched transport gives R_series_legs=2.698285Ohm,
NOT actual production resistance. Older GateB solder
rho=1.7e-7Ohm*m unqualified hypothesis gives
aggregate series solder bulk R=.006545Ohm (0.243% of
leg-only 300K). Identical all352 interface
rho_c=1e-11 Ohm*m2 hypothetical gives .022Ohm series
resistance and .00352W Joule at0.4A; 1e-10 gives
.220Ohm and .0352W. Specific rho_c at which electrical
contact series is 1% of ideal leg R at300K is
1.226493e-11 Ohm*m2, quantitative measurement
planning threshold, NOT measured contact or an
as-built acceptance number. Older SnSb k45W/mK
hypothesis gives single .035mm solder slab4.861K/W
thermal axial resistance; P/N research leg axial
2843/2233K/W, four thermal interface terms at
r_t1e-7m2K/W add2.5K/W per leg.
NOTE interfacial Peltier/Thomson and local Joule
heating still essential even when scalar r_th small.
No valid 88-leg thermal series circuit; legs are
parallel thermal paths each stage. First true
nine conducting source volumes [5,6,7,8,9,10,269,
270,271], real mathematical source current cuts
faces1531 and162 (NOT package pins) and ceramic
thermal faces8/9/44 require explicit energy/contact
and stage-network cut conditions for any 3D couple.
Do NOT reuse older GateB coupon contact coefficients
as actual TEC interface evidence. Still NO full
430-domain physically qualified electrothermal
model, no material law release, no rerun synthetic
tests, no Codex. Original electrical P1 GateB FAIL/
STOP, P2 STOP and full thermal C/D NOT RUN.

**2026-11-07 ORIGINAL R3.9 3D HEADER + FINITE OEM-EXAMPLE TIM ROBIN + SEPARATE RADIATOR: ONE CONDITIONAL NUMERICAL PASS, PHYSICAL PRODUCT STILL STOP.**
Read [single registered native CAD original header TIM/Radiator model and qualification boundaries](docs/V3_R3_HEADER_TIM_ROBIN_REFERENCE_20261107.md),
[exact saved 47702-TET4 numerical receipt](data/v3_header_tim_robin_20261107/attempt01/result.json),
[hash registration/manifest](data/v3_header_tim_robin_20261107/attempt01/manifest.json)
and [source 3D Robin solver](scripts/v3_header_tim_robin_reference.py).
Uses original Kovar header volume386, original R3.9 TET4
47702/16277 nodes, face2228 uniform source Q=.58702976W
from PRIOR conditional reduced model and native underside
face2225 9617 triangles. VIGO AMS3140-01 separate-module
datasheet provides TIM EXAMPLE thickness0.1mm and
k1W/mK; NOT as-built TO66 measurement. Apply local
full original underside Robin h=k/t=10000W/m2K, exact
P1 surface mass integration, all other header faces
insulated and generic Kovar k17.3W/mK. Independently
VIGO 2025 generic 3TE recommends ~2K/W radiator
TO AMBIENT, used as distinct isothermal-lumped radiator
node T_rad=300K+Q*2=301.17406K, not combined in
parallel with TIM. DO NOT ALSO APPLY AMS empirical
nonuniformity Kf=2: would risk double counting resolved
header spatial spreading and is for unrelated geometry.
One source 3D solve area-mean TEC-side header302.79386K,
header plus finite TIM R2.75931K/W, radiator+header+
TIM R4.75931K/W, original full underside Dirichlet
header R1.57704K/W; penalty1.18228K/W (not merely
uniform TIM t/kA=.29940K/W; header spreading changed).
Relative sink conservation8.380e-12 and energy identity
2.335e-16, numerical PASS without mesh convergence
or experimental validation. This does NOT include
ceramic, solder, Ni/Au composites, finite other contacts
or full 430-domain TEC; do not add to old reduced full
R_sink5K/W or adjust existing die T208.985K.
Remaining as-built header mounting pressure/area/TIM
thickness and sink capability unmeasured, grade-matched
P/N transport and whole source face laws UNSET.
Preserve original P1 GateB FAIL/STOP, prospective P2
STOP, full coupled C/D NOT RUN, source CAD/mesh
untouched, no Codex.

**2026-11-07 VERIFIED OEM 3TE HEAT-SINK GUIDANCE: ~2K/W radiator TO AMBIENT recommendation, NOT contact or as-built 430-domain sink release.**
Read [VIGO 2025 manufacturer source / source-CAD conditional heat path and remaining TIM gap](docs/V3_R3_OEM_SINK_BOUNDARY_EVIDENCE_20261107.md),
[SHA-pinned reference thermal budget](data/v3_oem_sink_boundary_20261107/attempt01/boundary_evidence.json)
and [no-solve audit script](scripts/v3_oem_sink_boundary_evidence.py).
VIGO original manufacturer PDF rev V3.0 Sep11 2025,
https://vigophotonics.com/app/uploads/2024/07/Thermoelectric-cooling-heat-sinking.pdf,
recommends ~2K/W HEATSINK-to-ambient capability for
1TE/2TE/3TE and ~1K/W for4TE; base header firmly
attached with thin thermally conductive epoxy/grease;
cap or screw alone insufficient. This DOES NOT provide
a numerical header/grease/sink-contact R, installed
sink performance or prove VIGO + TEC Microsystems
synthetic CAD equals an as-built product.
Separating source header 3D one-condition1.577035K/W,
hypothesis mount InSn solder 1D .074074K/W, alumina
AD995 analogy 1D .447908K/W and OEM radiator design
recommendation2K/W gives an *illustrative* component
sum4.099018K/W before UNKNOWN interfacial contact,
composite k tensor and ceramic spreading; this is
not rigorous bound, validated whole-assembly R or
coupled calculated hot ceramic temperature.
Using prior conditional heat Q=.58702976W gives
illustrative component drops .926,.0435,.263,1.174 K
(~2.406 K sum), but NOT a new solved TEC temperature.
NEVER add these parts to previous reduced whole-path
effective R_sink=5K/W (double counting).
Next actual physical progress requires measured
header-base-to-ambient temperature/heat flow and
mount TIM thickness/contact footprint/pressure or
source-characterized fixture sink. No new FEM/mesh,
Codex, revised Gate B or physical law release.
Historical original P1 GateB FAIL/STOP, P2 candidate
STOP, full 430-domain thermal C/D NOT RUN.

**2026-11-07 FIRST ORIGINAL R3.9 3D KOVAR HEADER-ONLY SPREADING: NUMERICAL PASS under ONE hypothetical isothermal underside BC, PHYSICAL PORT STILL STOP.**
Read [original source-header 47702-tet numerical report](docs/V3_R3_HEADER_ONE_CONDITION_3D_SPREADING_20261107.md),
[preregistered source-hashed 3D results](data/v3_r3_header_spreading_20261107/attempt01/result.json),
[immutable evidence manifest and first-launch setup failure](data/v3_r3_header_spreading_20261107/attempt01/manifest.json),
[original TET4 3D heat solver](scripts/v3_r3_header_one_condition.py).
Source original R3.9 tets1,010,119; header386 only
47,702 TET4 and16,277 nodes, 5,195 bottom Dirichlet
nodes. Native source face2228 Ni/header input37.21mm2
(1000 TRI3), underside exterior face2225 ~333.961mm2
(9617 TRI3). One hypothetical condition: ENTIRE
UNDERSIDE fixed300K, positive uniform source Q=.587030W
from previous conditional R3 reduced nominal0.4A
wires-ON hypothetical sink5K/W case, other header faces
insulated; header Kovar k17.3W/mK generic constant
293K bulk proxy, NOT OEM measured header.
One FEM original saved P1 tetra solve yields area-weighted
top header temperature300.92576665K, maximum301.20624K,
header-only effective area-weighted spreading
R=1.57703529K/W, source/sink relative closure4.887e-12,
discrete energy-work identity6.129e-16, zero inverted
tets. This is ONE MESH with known global R3.9 shape
defects, NOT h-converged or a 3D as-built heat sink
qualification. First Docker launch failed BEFORE SOLVE
due missing bind mount, retained log; one completed
solver after mount corrected. Original Ni/Au multilayers,
solder, ceramic, external contact area/pressure, gas,
radiation and 430-domain TEC electrothermal coupling
excluded. Do NOT add header1.577K/W to prior effective
5K/W sink: double counting! This component 3D calculation
does NOT alter predicted reduced die T or establish
real mounting resistance; all material and face laws
remain UNSET. Gate B original P1 FAIL/STOP and
prospective P2 STOP, full 430-domain thermal C/D NOT RUN.
No source CAD/mesh edits, no more scenarios or Codex.

**2026-11-07 SOURCE-CAD HOT-MOUNT THERMAL READINESS: real geometric layer and header underside verified; external sink and spreading STOP.**
Read [source face-tagged package mounting resistance readiness](docs/V3_R3_HOT_MOUNT_THERMAL_READINESS_20261107.md),
[original CAD area and 1D evidence receipt](data/v3_hot_mount_readiness_20261107/attempt01/thermal_path_audit.json),
and [read-only exact replay](scripts/v3_hot_mount_thermal_path_readiness.py).
Original R3 hot path faces2228/2298/2303/6: Kovar header386,
Ni composite401, 80um In52Sn48 solder402, Au composite403,
500um ceramic0 volume1. Actual solder contact face36mm2,
real header underside exterior face2225 333.961mm2, so
mount footprint just10.78% underside area; 3D lateral
spreading and actual sink clamping NOT determined.
With explicitly NONRELEASED 300K k_InSn=30W/mK old
hypothesis, 1D solder R=.07407K/W; with CoorsTek
AD995 alumina k30W/mK analog and face37.21mm2,
1D ceramic R=.44791K/W; sum .52198K/W.
Alternate AD96 k24.7 gives .54402K/W ceramic.
Kovar thickness1.5mm, k17.3W/mK bulk analog;
uniform column 36mm2 2.408K/W versus uniform full
underside333.96mm2 .260K/W: these are incompatible
illustrative columns, NOT rigorous bounds on true header
spreading! Ni/Au effective composite tensors, solder
actual alloy/voids, every interface thermal R, actual
fixture contact patch/pressure/sink state remain UNKNOWN.
Under previously archived nominal .4A 5K/W reduced
sink heat Q=.58703W, ideal 1D solder+ceramic T drop
.3064K as comparative arithmetic ONLY; NOT new PDE
or correction to actual hot temperature. Do NOT add
these layer R to existing 5K/W effective R_sink:
that would double count one modeled heat path.
Next only independently sourced/measured external sink
footprint/contact and material laws, then preregistered
one-condition 3D header spreading if possible. No
unbounded sweeps, no Codex. Source P1 GateB FAIL/STOP,
prospective P2 STOP, full thermal C/D NOT RUN; original
CAD/Rev3 and numerical evidence preserved.

**2026-11-07 R3 29/11/4 SOURCE-CAD FINITE SINK & REAL Cu/Au LEAD SHAPE PROXY: 18-case conditional reduced PASS; as-built STILL STOP.**
Read [bounded 3x3x2 thermal sensitivity and physical exclusions](docs/V3_R3_FINITE_SINK_AND_CAD_WIRE_SENSITIVITY_20261107.md),
[source-hashed, preregistered 18-case original CAD wire ledger](data/v3_r3_sink_wire_20261107/attempt01/manifest.json)
and [one-shot reduced solver driver](scripts/v3_r3_sink_wire_sensitivity.py).
Reused original accepted CAD 29/11/4 leg dimensions, actual
TEC Cu lead1/9 curved centerline lengths3.451/4.965mm radius
100um each, detector bond7/8 Au centerline9.679mm radius9um each.
Room-temperature *bulk proxies* from old registry only:
Cu k400W/mK, rho1.72e-8Ohm*m; Au k315W/mK,
rho2.30e-8Ohm*m; no independent wire measurement.
Registered 18 cases [nominal0.25A, nominal0.4A,
higher0.4A]x sink Rtheta[0,2,5]K/W x wires[OFF,ON].
Sink resistances SCENARIOS, NOT actual mounting resistances.
Ideal ambient pin reservoir300K, die heat2mW, no gas,
radiation, stage metal bypass, 3D ceramic gradients, or
finite electrical/thermal contact R. Actual 1D direct
nonlinear 32 interval measured-source P-HE/N-HE-1
research-grade mismatch remains. All18 numerically PASS
original node/energy/terminal IV gates; only6 have
P/N temperatures wholly <=300K; remaining12 accepted
only using the explicitly ASSUMED >300K quarter-tangent
transport continuation. Nominal0.4A wires-OFF ideal
Tdie207.169K, wires-ON sink0 207.647K, wires-ON
sink5 208.985K, Thot302.935K, Au bond heat1.507mW,
terminal0.602W at 5K/W. Higher0.4A wires-ON sink5
Tdie186.813K; still NOT real detector T or true low bound.
Physical lesson: unmodeled lead heat can be comparable
to imposed die2mW even when T shift<1K in current
hypothetical numerical model. No evidence to fit hot sink
or production-grade contacts. STOP repeated arbitrary
hypothesis sweeps; next progress needs source-qualified
sink, contact, real detector load and transport.
Original electrical P1 GateB FAIL/STOP, P2 candidate STOP,
coupled 430-domain thermal C/D NOT RUN, physical inputs
430/2440 UNSET, source identity unknown. No CAD/mesh,
new 3D solver or Codex usage.

**2026-11-07 CONDITIONAL PHYSICAL REFERENCE REFINEMENT: first actual accepted R3 29/11/4 SOURCE-CAD-derived nonlinear reduced TEC envelope, 9/9 numerical PASS, as-built UNQUALIFIED.**
Read [R3 source-CAD 29/11/4 conditional 1D transport report](docs/V3_R3_REDUCED_THERMOELECTRIC_REFERENCE_20261107.md),
[sealed nine-case study summary, complete source hashes, no-OEM-fit registration](data/v3_reference_29114_reduced_20261107/attempt01/manifest.json),
and [standalone original-R3 geometry transfer/run script](scripts/v3_reference_29114_reduced_study.py).
Unlike historical 28/12/4 reduced 186.484K, study imports
source final actual R3 geometry:29/11/4 P/N couples,
0.4x0.4x0.5mm legs, ceramics6.4/5.2/3.8/2.4mm,
20um die attach over1mm2, full 88-leg source IDs; no new CAD/FEM.
Existing conservative 32 interval nonlinear 1D transport and
5-node cascade with three UNMATCHED Zhang P/N specimen law
hypotheses lower(.9,1.2,1.2), nominal(1,1,1), higher(1.1,.8,.8).
Preregistered hot ceramic300K ideally controlled R_sink=0,
die2mW, currents[.15,.25,.4]A; all wires, gas, radiation,
metal bypass OFF, attachment k=1 W/mK assumed.
Numerically9/9 PASS original node/global/stage balances and
all source leg field temperatures <=300K (no >300K
continuation). Die T conditional at .15/.25/.4A:
lower261.503/244.294/226.495K;
nominal250.347/229.072/207.169K;
higher235.750/210.391/185.124K.
At.4A hypothetical current, model law scenario spread41.371K,
NOT a confidence interval or measured true cooler bound.
Nominal.4A predicted module terminal1.47879V,
input0.591515W and Qc_cold2mW, all CONDITIONAL.
At measured source domain40-300K; commercially matched
P/N grade, source experimental validation, 3D ceramic spreading,
real electrical/thermal contact laws, hot-sink uncertainty,
gas/radiation/lead bypass NOT included/NOT qualified.
Do not call 185K actual detector temperature or OEM T.
Next source-qualified thermal contact, sink and lead/bypass
evidence before relaxing optimistic model assumptions.
Original P1 electrical GateB FAIL/STOP, P2 prospective STOP,
real 430-domain coupled thermal C/D NOT RUN, actual
production detector physical prediction UNQUALIFIED.
No CAD change, source material-release, 3D PDE or Codex use.

**2026-11-07 AS-BUILT PHYSICAL SOURCE-IDENTITY HARD GATE — STOP PRODUCT VALIDATION.**
Read [TEC/detector manufacturer source-identity evidence and real
thermistor-completeness issue](docs/V3_TEC_SOURCE_IDENTITY_AND_PHYSICAL_EVIDENCE_20261107.md),
[deterministic source-keyed receipt](data/v3_tec_source_identity_20261107/attempt01/source_identity_gate.json)
and [read-only exact replay](scripts/v3_tec_source_identity_hard_gate.py).
TEC Microsystems selected 3MC04-044-05 (2019) distinct from
VIGO 3TE-TO66 detector package + separately published PCI-12 family.
No source proves the TEC Microsystems reference is installed in
the VIGO package. Selected 44 total couples and 6.4/2.4 mm/
3.8mm package from TEC ref, but internally modeled 29/11/4
stage split and interconnect metallization are INFERRED,
not published OEM dimensions. TEC reference at300 K vacuum
DeltaTmax113K/Qmax0.5W/Imax1.0A/Umax3.5V/ACR2.9Ohm
separate non-simultaneous performance metrics, NOT as-built
hybrid limits. VIGO PCI-12 2026 family typical chip210K
at ambient293K with 3TE absolute maximum current0.45A
and voltage3.6V; those values belong to a different detector
family, NOT a certified comparison for the reference CAD.
VIGO package nine-pin drawing assigns thermistor pins5/6,
but source R3 has pin5 volume394, pin6 volume396 each
only touching its own glass, and NO thermistor model,
interconnect or R(T). NOT enough to invent hardware.
Do not label prior reduced 186.5K study or TEC-only theoretical
187K (300K-113K no load) as predicted HgCdTe detector T.
Current physically measured matched P/N transport, contact laws,
sink/mounting/loads and actual specific OEM revision remain
UNKNOWN. Separate a hypothetical reference-design sensitivity
model from real OEM device calibration and never transfer
1.0 A source TEC Imax to VIGO PCI absolute current limit.
Reference CAD topology still 88-leg/430 domains/2440 faces,
but real physical model release STOP. No PDE, no Codex.
Preserve frozen STEP/Rev3, all historical evidence,
original P1 GateB FAIL/STOP, prospective P2 STOP, C/D NOT RUN.

**CURRENT PHYSICAL PORT RESULT — November 6: exact native 88-leg electrical series network PASS, physical heat and electrical coefficients STOP.**
Read [source CAD pin and thermal-port engineering contract](docs/V3_TEC_PHYSICAL_PORT_CONTRACT_20261106.md),
[original 557 solid-solid face circuit graph and verified 88 leg articulation receipts](data/v3_tec_physical_port_contract_20261106/attempt01/port_and_series_graph.json),
and [reproducible no-solve original source graph auditor](scripts/v3_tec_electrical_port_contract.py).
Actual TEC package electric pin1 exterior face2414 volume424 and
pin9 exterior face2426 volume427 are in same native 389-volume
conductor component. All88 actual original P/N leg solids are
MANDATORY pin1-to-pin9 articulation vertices: removing any one
opens the geometric circuit. Physical stage0 29 couples,
stage1 11, stage2 4, with original interstage non-P/N formed
tab58 and tab80 paths both verified; no ideal-zero-resistance
junction law assumed. Package pins7 exterior face2418
and8 exterior face2422 are SEPARATE detector branches
joined by actual active HgCdTe volume408 using original
face2336/2337, never joined to TEC via original conductor
faces. Native TEC pin feedthroughs to first net0 and final
net88 documented; net0 and net2 within first N/P pair are
INTERNAL, not physical independent terminal faces.
Selected 11 source solids include entire ceramics0/1,
132 exterior-to-selection cut faces (73 solid-solid,
59 gas-solid), requiring explicit physical external
network/thermal coupling, NOT blind insulation.
Native hot-side heat stack original face tags
2228/2298/2303/6 (header, Ni finish, In52Sn48, Au,
ceramic0) and cold detector path119/2314/2319/2325/2330
(ceramic3, Au, EP29LPSP, sapphire, EP29LPSP, HgCdTe)
are geometric verified contacts ONLY. Header has12 real
exterior CAD sink-candidate faces; sink mounting and
temperature/contact laws remain UNASSIGNED.
Thus source electrical terminal identities/leg topology
GEOMETRIC PASS but no physical I-V, leakage, thermal
conductance, detector operating temperature or material
parameter release. Keep source430 CAD volumes/2440 faces,
original P1 GateB FAIL, P2 STOP, thermal C/D NOT RUN.
Do NOT run PDE or invent thermal/electric cut ports,
material coefficients or boundary conditions. No Codex.

**CURRENT PHYSICAL PROJECT PRIORITY (2026-11-06) — COMPLETE 430-DOMAIN AND 2440-FACE SOURCE LAW INVENTORY, ACTUAL N/P CAD PAIR CONNECTIVITY PASS; PHYSICAL SOLVE STOP.**
Review [physical electrothermal law and actual couple readiness report](docs/V3_PHYSICAL_LAW_AND_COUPLE_READINESS_20261106.md),
[all exact source-keyed volume/face law rows, source hashes, P/N chain and missing-data ledger](data/v3_physical_law_readiness_20261106/attempt01/law_and_subassembly_inventory.json)
and [reproducible strict no-solve source auditor](scripts/v3_physical_law_inventory.py).
Source R3 exactly430 CAD volume IDs,2440 native face IDs,
378 original contact witnesses, source88 TEC legs P44/N44,
29/11/4 couples (58/22/8 legs),176 SnSb solders,
98 effective multilayer domains,557 solid/solid,1840 gas/solid,
43 external CAD faces. All430 domain laws and2440 face laws
UNSET/NOT RELEASED. Research analog P/N transport from corrected
Zhang2025 paper 40-300K distinct P and N specimens, NOT as-built
grade, measured coverage above300K ABSENT, quarter-tangent prior
continuation hypothetical. Prior reduced model28/12/4 differs from
physical R3 29/11/4. 430/2440 ledger contains exact source
owner/tag/geometry/required evidence and NULL numeric parameters,
no invented sigma/k/S/contact resistance or boundary conditions.
Selected real first stage0 N/P pair 11 native volume IDs
[1,2,5,6,7,8,9,10,269,270,271] and 11 exact material
interconnect CAD face tags [124,125,140,141,130,135,151,146,8,9,44];
shared cold copper net270 provides native P/N series path.
However whole ceramic0+ceramic1 retained and selection has132
outside cut faces (73 solid-solid,59 gas-solid), and net0/net2
are not independently authorized electric drive terminals.
Therefore subassembly geometric connection PASS but physical
ports/heat coupling STOP; no PDE should be launched. H1 actual
P/N grade and temperature curves; H2 solders/metallization/contact
laws; H3 real electrical port/circuit; H4 hot/cold heat paths,
sink/load/gas/radiation; H5 qualified full current/heat solver.
Future analysis must preserve original P1 GateB FAIL, prospective
P2 STOP, thermal C/D NOT RUN and actual 430 full PDE unqualified.
No new synthetic benchmarks, original source change, physical
coefficient calibration, mesh campaign, or Codex usage. Project
next substantive progress requires source-qualified input/port
evidence, not another FEM diagnostic or invented TEC temperature.

**2026-11-06 Gate B rim-only correction FEASIBILITY SCREEN: NO GO, NO SOLVER.**
Read [counterfactual stop decision](docs/V3_GATE_B_RIM_ONLY_FEASIBILITY_STOP_20261106.md),
[source-hashed signed radial partition](data/v3_physical_blocker_closure_20261106/attempt01/rim_only_feasibility_stop.json),
and [read-only exact replay](scripts/v3_gate_B_rim_only_feasibility.py).
Existing lead9 contact outer-face centroid 0.9<=r/R_CAD<1.05
accounted for78.01% (lead_land face43) and72.47% (lead_pin
face47) of absolute OTHER-side contact-versus-raw mismatch.
But set ALL original RIM-bin errors to zero in saved P2 field,
while freezing INNER signed errors: other-side remaining
1.102884% face43 and1.543405% face47 vs original0.1% GateB
cut threshold (11.03x and15.43x too large), with lead9-side
inner residual3.135939% and1.861681% (31.36x and18.62x).
Therefore isolated RIM-ONLY correction of CURRENT saved flux
would FAIL even if perfect, because inner signed bias persists.
This is a fixed-field conditional calculation, NOT an impossibility
result for a NEW global PDE solve that can redistribute interior
solution. Do NOT authorize rim-only remeshing/solver on these
results; an acceptable future comparator needs a preregistered
FULL-interface correction, all16 raw current cuts, voltage bound,
mesh/physics evidence and original P1/P2 failures preserved.
Priority now source-backed exact430-domain/2440-face physical
material/interface input ledger. GateB original P1 FAIL/STOP,
prospective P2 STOP, thermal C/D NOT RUN. No Codex used.

**2026-11-06 P0 original Gate B lead9 P2 CONTACT-LAW vs RAW-FLUX radial forensic: SOURCE-RECONSTRUCTED; BOTH GATES STOP.**
Read [native face43/47 contact-operator engineering report](docs/V3_GATE_B_LEAD9_CONTACT_OPERATOR_20261106.md),
[318-triangle original source-field JSON](data/v3_physical_blocker_closure_20261106/attempt01/lead9_contact_operator_audit.json)
and [exact read-only reproducer](scripts/v3_gate_B_lead9_contact_operator_audit.py).
No PDE, no new mesh, no property/contact-law change, no Codex.
Compared original P2 raw gradient current on each physical side with
the P2 quadratic finite-contact-law edge-trace current at every
registered TRI3: face43 lead9->lead_land (158), face47 lead9->lead_pin
(160). Unit-voltage mathematical weak contact flux magnitude33.84225A
both. Lead9-side net raw bias -1.14113A (3.3719% unit drive) face43
and+0.64552A(1.9074%) face47; OTHER MATERIAL SIDE raw bias
+2.74099A(8.0993% unit drive) face43 and-2.31918A(6.8529%)
face47. Thus limiting cut is on raw lead_land/pin side.
On native CAD contact radius100um and saved triangle centroid radial
band 0.9<=r/r_CAD<1.05, only20.42% face43 and19.23% face47
meshed face area yields78.01%/72.47% of absolute OTHER-side
raw-vs-weak flux error, but only17.93%/13.30% of lead9-side
absolute error. This REFInes earlier shape analysis: top10% face
gross TWO-SIDED RAW-RAW mismatch 23%/21%, which is NOT the same
observable as rim-binned OTHER-side RAW-vs-CONTACT-law error.
A single uniform raw-vs-weak density scaling explains only
33.31%/30.85% of other-material squared density mismatch;
do not apply such scale to model or fit contact resistance.
Contact-edge/perimeter adjacent material gradients are now a
source-grounded numerical diagnosis target, not a proved mechanism.
Original CAD/saved face area discrepancy -0.102777% does not alone
explain remaining6.85%-8.10% flux error. Original P1 B FAIL/STOP,
prospective P2 STOP, thermal C/D NOT RUN, original0.1% raw current
threshold and negative potential bound remain intact.
Any future solver/perimeter-resolution change requires separate
preregistered methodological decision and cannot reclassify the
original P1 or prospective P2 STOP. Preserve full physical STEP,
Rev3, all 430-volume CAD and historical evidence, issue#2.

**2026-11-06 Original Gate B lead9 P1/P2 interface-shape attribution: NO-SOLVE DIAGNOSTIC PASS, PHYSICAL GATES REMAIN STOP.**
Read [source-grade 318-triangle lead9 shape/flux report](docs/V3_GATE_B_LEAD9_GEOMETRY_ATTRIBUTION_20261106.md),
[pinned source field and shape-quality receipt](data/v3_physical_blocker_closure_20261106/attempt01/lead9_shape_attribution.json),
and [read-only replayable source](scripts/v3_gate_B_lead9_shape_attribution.py).
Same frozen original 28691 TET4 GateB NOM fields and already-stopped
58993-DOF same-mesh P2 correction, no new PDE/mesh/constitutive laws.
Native lead9->lead_land face43 uses158 original TRI3; lead9->lead_pin
face47 uses160. P2 errors8.099302%/6.852908%, both FAIL0.1% limit,
versus original P1 29.17271%/30.01540%. Independent saved-gradient
and contact edge trace integrals reproduce previously archived P1/P2
currents at both interfaces within1e-11 relative to drive current.
Normalized adjacent pairwise minimum mean-ratio q: face43 q_min
0.17530, median0.46344; face47 q_min0.21451, median0.49930.
ZERO source contact area has q<0.1 at EITHER face. Gross absolute
two-sided P2 raw mismatch3.9521A face43 and2.9662A face47;
top10% most mismatched TRI3 carry22.98%/20.89% of gross mismatch,
not a small set of degenerate elements. Actual meshed polygonal
face areas3.13836383e-8m2 vs source CAD circles3.14159265e-8m2,
−0.102777% area difference both, close to0.1% numeric gate but
cannot by itself explain6.85–8.10% raw flux mismatch.
Conclusion: extremely poor tetrahedron SHAPE quality in original
immediately incident cells is not the dominant obvious mechanism;
raw P2 nonconforming interface flux mismatch is distributed.
Do not launch remeshing/solver tests based on global q optimization.
Next only bounded read-only weak-contact-vs-raw interface flux
consistency/area feasibility diagnostic (if genuinely informative).
Original P1 GateB FAIL/STOP, prospective P2 STOP, thermal C/D NOT RUN.
No Codex used; protect all original CAD/mesh fields, laws, Rev3,
histories and open issue#2.

**2026-11-06 original Gate B one-shot P2 raw-gradient comparator: MAJOR NUMERICAL IMPROVEMENT BUT PROSPECTIVE GATE FAIL/STOP; ORIGINAL P1 Gate B STILL FAIL.**
Review [original real coupon P2 correction/stop report](docs/V3_GATE_B_ORIGINAL_P2_CORRECTION_20261106.md),
[pinned preregistration, P2 source/field/16-cut and independent audit receipt](data/v3_gate_B_original_P2_20261106/attempt01/manifest.json),
[producer](scripts/v3_gate_B_p2_coupon_attempt.py), and
[independent saved-field readback](scripts/v3_gate_B_p2_saved_field_audit.py).
Original 28691 TET4 original fine coupon, 105 native CAD face
registry/12 original material regions, original NOM anisotropic
sigma tensors and contact R=1e-11 Ohm*m^2 and actual internal 1/0V
coupon electrodes unchanged. Single prospective P2 TEN-node
scalar field, same linear TET4 geometry, distinct material-trace
vertex and edge DOFs (58993 total/57227 free), preserved 1574
physical interface triangles and all16 original signed raw-current
cut tests. ONE registered bounded4CPU/8GiB/180s attempt ran
8.507 seconds,451.2MiB Python RSS; six ILU-GMRES iterations,
true residual1.09324e-11, independent IV/bulk-contact
power closure6.339e-9. P2 worst raw cut8.099302% at
lead9->lead_land versus original P1 worst85.62550%
at film0->lead_land. Original highest location film0->lead_land
improved85.6255% to1.80522%. Of16 original cuts, P2 improves15
but still FAILS11/16 (>0.1% limit); lead9_mid worsens
0.061289% PASS to0.131997% FAIL. P2 min voltage
-9.14946e-7 V, WORSE than original-7.35136e-7 V and
outside original -1e-8V bound. Source unitV current
33.8422517A (original P1 34.0463045A); NOT device rating.
Separate no-PDE saved-field auditor independently reproduced
both one-sided raw gradient and finite-contact weak integrals
at ALL 1574 native source contact triangles/11 material pairs
and both terminals within3.5861e-13 relative drive current.
Three native interior-plane P2 cut integrals are from original
registered producer (not independently recalculated).
P2 physical mesh refinement NOT RUN. This isolates P1 gradient
approximation order as a significant original numerical failure
contributor, but does NOT qualify P2 B, explain every
remaining mismatch, permit voltage boundedness relaxation
or justify full TEC physics. DO NOT automatically rerun meshes,
tune candidate, or fit arbitrary interface laws. Next only
READ-ONLY remaining lead9-land/pin geometry and local
gradient/shape attribution before any new separately authorised
physical solver gate. No Codex, protected geometry, CAD,
Rev3, original P1 failure or past archives changed.
Gate B FAIL/STOP, C/D NOT RUN, 430 physical laws UNSET.

**P0 Gate B actual face-level current attribution (2026-11-06, no solve).**
Review [face-resolved 11-interface engineering report](docs/V3_GATE_B_FACE_FLUX_DIAGNOSTIC_20261106.md),
[1574-original-interface-triangle receipt](data/v3_physical_blocker_closure_20261106/attempt01/gate_B_face_flux_diagnostic.json),
and [read-only reproducer](scripts/v3_gate_B_face_flux_diagnostic.py).
Rebuilt original 28691-tet fine mesh face adjacency and all 11 original
raw one-sided gradient-current integrals from saved J and exact native
CAD source face/owner IDs, within4e-13 of unit-drive current.
Original worst film0->lead_land: 204 source faces, raw-side
I_A=4.893986A vs weak contact current34.046305A and raw opposite
outward-36.328540A. 35.19% of face area flows reverse relative to
net side-A current; top10% of faces supply45.89% of absolute raw
current and local gross/net flux ratio1.74. But joint6->film2 and
joint4->film0 show 28.9597A and29.4122A signed opposite-side
raw mismatch without any side-A sign reversal, ruling out any
single blanket backflow explanation. Zero-branch high
gross/net cancellation is NOT a physical high circuit current.
This is FACE-LEVEL failure localization, NOT root-cause isolation,
flux-conforming physical qualification, or an original B PASS.
Keep full original16-cut 0.1% gate, voltage boundedness and archived
failure untouched. No Codex, PDE, CAD/mesh/field/material edits.

The 2026-11-06 physical-readiness result is a NO-SOLVE STOP, not
another accepted FEM analysis or material-law release.

**Current R3.17 genuine three-material two-native-contact FEM network (2026-11-06): SYNTHETIC VARIABLE NORMAL-FLUX AND TWO ROBIN CONTACT LAWS PASS; REAL ELECTRICAL/THERMOELECTRIC PDE UNQUALIFIED.**
Read [R3.17 quantitative record](docs/V3_R317_TWO_CONTACT_NETWORK_20261106.md)
and [pinned code, four field solutions and independent receipts](data/v3_r317_two_contact_network_20261106/attempt01/manifest.json).
Original R3.9 TET4 source, actual native CAD material chain
408 p-HgCdTe photoconductor -> native face2336 (6 conformal TRI3)
->410 composite detector8 wedge foot->native face2349 (48 conformal
TRI3)->420 Au detector bond8. Three-region subset26290 tetra,
6998 ORIGINAL geometric nodes, 13766 registered exterior TRI3.
All source mesh ownership, geometry, contact witness records unchanged.
Mathematical-only coefficients k408=2,k410=1,k420=10,
Robin conductances G2336=4,G2349=5 and variable normal-gradient
flux q(x,y)=1+1.8*(x+.35)+2.5*y; both interfaces have distinct
manufactured spatially varying potential jump -q/G and exact normal
flux continuity. Each material has its own field trace (P1 total7055
DOF/free3983; P2 total47334/free35142), positive weak Robin
surface operators, exact non-contact manufactured body/exterior
flux and Dirichlet native face2399.
All four P1/P2 quadratic and quadratic+sinusoidal scalar
benchmarks passed true operator residual<1e-8, ILU-GMRES8/12
iterations. Independent216pt tetra H1_nonpolynomial relative P1
0.110789151 and P2 2.50996255e-5, improvement4413.976x.
P2 nonpolynomial native contact 2336 Robin RMS8.823445e-6
and outward-normal flux imbalance8.818163e-6; contact2349
Robin RMS1.339013e-7 and imbalance2.121760e-7. Both pass
preregistered 1e-5 tolerance, but 2336 is close to threshold
and has only6 original TRI3. Variable q ranges .93483..1.06517
(face2336) and .98157..1.01843 (face2349).
Primary four-point nonpolynomial P2 H1 1.7378267e-5
UNDERSTATED independent216pt 2.5099625e-5 by44.431% relative
to primary; use only independent216pt error for qualification.
Separate full interface face ownership/flux and saved-field 216pt
H1 audit PASS. This is separate FACE-LOCAL contact conservation
not global network current closure: original contact areas differ
and there are manufactured distributed/exterior forcing fluxes.
No physical HgCdTe/Au/composite conductivity, contact resistivity,
thermal/electrical junction/TEC PDE, mesh refinement convergence,
full430-region solve, or measured detector operating point.
Protected original STEP, all R3.3-R3.16 archives/failures,
Rev3 38-page canonical and issue#2 remain unchanged.
Electrical GateB STOP, thermal C/D NOT RUN. No additional compute
or Codex used. Next require physical subassembly constitutive laws
with fully integrated electrical current/reaction closure before
any device-wide electrothermal claims.

**Current R3.16 native finite-contact split-trace scalar P1/P2 (2026-11-05): MATHEMATICAL ROBIN TRANSMISSION, NONPOLYNOMIAL FLUX AND INDEPENDENT H1 PASS; PHYSICAL CONTACT LAWS UNQUALIFIED.**
Read [R3.16 technical report](docs/V3_R316_FINITE_CONTACT_INTERFACE_20261105.md)
and [saved full SHA evidence](data/v3_r316_finite_contact_20261105/attempt02/manifest.json).
Retain original full R3.9 geometric TET4 CAD source; actual shared
CAD face2349 has48 native facets between region410 composite wedge foot
and region420 Au detector bond,26053 total tetrahedra/6908 original
geometric nodes. Introduced distinct per-material scalar field traces:
P1 6957 total DOF/3885 free, P2 46806 total/34614 free, without
changing source mesh/CAD or surface geometry. Artificial k410=1,
k420=10, finite contact G=5, exact potential jump=-0.2 for the
standard diffusive q=-k grad u sign and analytic Q_grad=1.
Robin form G int_interface (u410-u420)(v410-v420) is positive.
Quadratic and nonpolynomial quadratic+sinusoidal manufactured source
f and outer Neumann, native face2399 prescribed Dirichlet.
All four P1/P2 scalar ILU-GMRES cases pass7/11 iterations, independent
true residuals<1e-9, mean interface jump~-0.2. Nonpolynomial P1
vs P2 independent H1_relative 0.0079282100 vs 3.0287548e-5
=261.765x less with P2, P2 relative RMS normal flux imbalance
4.7348e-7 and Robin mismatch2.9610e-7, verified through
independent saved solution coefficients and216pt tetra quadrature.
Important: source P2 four-point quadrature underestimates
nonpolynomial H1 by21.6447% relative to that original estimate:
2.489837e-5 reported initially vs authoritative3.028755e-5.
Preserved registered initial code STOP when same-material face was
counted as material interface, and sign-law FAILED source/run with
opposite initial assumed jump; corrected documented standard diffusive
sign without source mesh edits. No real G,k measurements/contact
resistivity, junction heat or Seebeck/Peltier, full430 material PDE,
mesh spatial convergence, TEC/detector temperature prediction.
All protected original CAD, source R3.3-R3.15/failures, canonical Rev3
and issue#2 remain unchanged. GateB electrical STOP, C/D thermal
NOT RUN. No Codex or resource increase.
Next investigate multi-interface network conservation and nonconstant
normal contact flux with separately measured physical material laws.

**Current R3.15 first native two-region CAD-interface P2 transmission benchmark (2026-11-05): SYNTHETIC TWO-MATERIAL SCALAR CONTINUITY/FLUX PASS; PHYSICAL COEFFICIENTS AND TEC PHYSICS UNQUALIFIED.**
Read [full R3.15 report](docs/V3_R315_TWO_MATERIAL_P2_INTERFACE_20261105.md)
and [replayable geometric, independent flux, H1 and SHA receipts](data/v3_r315_interface_20261105/attempt01/manifest.json).
Identified actual source face2349 between source composite detector
wedge-foot CAD volume410 and Au detector bond CAD volume420.
Independent R3.9 preserved-mesh preflight confirms EXACT 48 native
TRI3 shared by both regions,49 shared vertices,26053 combined
tetrahedra(148 composite/25905 Au),6908 original union nodes,
13586 outer triangles, interface plane z=5.7849mm, source CAD to
saved planar area discrepancy -0.285334% (previous accepted
surface CAD approximation). All original CAD/face/node IDs unchanged.
Artificial mathematical scalar k410=1 and k420=10 (NOT measured
real conductivities), manufactured continuous piecewise quadratic
u=A*((x-x0)^2+(y-y0)^2)+B*(z-z0)^2+Q/k_r*(z-z0),
A=0.025,B=0.05,Q=1. Exact normal flux k_r du/dz=Q across face2349;
analytical body forces and outward natural flux on other surfaces,
true CAD face2399 Dirichlet. Joint multi-domain shared-DOF P1 and
P2 solvers PASS ILU-GMRES8/11 iterations, residual9.35e-11/
4.04e-12. P1 relative H1 gradient error0.006632186 vs P2
1.261908e-8; P1 relative interface RMS normal flux jump0.0358152
versus P2 1.086827e-8. Same preserved TET4 original geometry,
P2 solution DOF46661 total/34469 free; no new geometric nodes
or shared facets. Independent 216pt tetra H1 and separately
reconstructed BOTH-side interface flux checks agree; interface trace
difference <1.7e-18, signed net mismatch P2 ~2.58e-12.
The massive P1/P2 improvement is expected P2 EXACT POLYNOMIAL
REPRESENTATION under a synthetic quadratic manufactured solution,
NOT a realistic real-material accuracy claim or mesh h-convergence.
All preflight implementation failures (same-region internal-face
classification, NumPy face-triplet sort) preserved, corrected without
remeshing or editing sources. No contact resistance, anisotropic
composite/thermoelectric transport, measured properties, global
430-region PDE, GateB physics, thermal C/D or detector temperature.
Next R3.16 separately register finite-interface contact jump laws
or a non-polynomial two-material transmission benchmark.
Protected 824-solid STEP, canonical 38-page Rev3, original
R3.3-R3.14 source/historical receipts, all378 finite contacts
and issue#2 preserved. GateB STOP, thermal C/D NOT RUN.
No Codex usage or resource uplift needed.

**Current R3.14 fixed-geometric P2 FEM regional accuracy milestone (2026-11-05): STRONG P1/P2 MANUFACTURED SCALAR ERROR IMPROVEMENT PASS, FULL PHYSICS UNQUALIFIED.**
Read [complete R3.14 quantitative report](docs/V3_R314_P2_REGIONAL_ACCURACY_20261105.md)
and [all source, replay, independent H1 and hash evidence](data/v3_r314_p2_20261105/attempt01/manifest.json).
Using immutable source R3.9 25905 straight TET4, region420 Au bond8
6884 original mesh vertices and 13540 native source contact/boundary
TRI3, construct global quadratic P2 solution basis on39558 original
unique edges, yielding46442 P2 field DOF (34250 free) vs6884 P1
field DOF (3812 free). Native face2399 prescribed Dirichlet and
analytic Neumann elsewhere, exact manufactured source f=-Delta u;
NO geometric boundary/node/contact/owner modifications.
P2 basis polynomial/interpolation preflight passed. Primary Keast
11-pt degree4 tetra and Dunavant7-pt degree5 face integration
moment-audited all70/56 simplex monomials to <1e-14 absolute.
P2 exact quadratic manufactured solution H1_rel1.65652e-8.
Genuinely non-polynomial quadratic+sinusoidal manufactured field:
P1 H1_rel0.0170792169833553 (1.70792%) vs P2 H1_rel
1.18540703694e-5 (0.001185407%), a confirmed1440.789x
gradient-error reduction ON THE SAME TET4 GEOMETRIC MESH.
ILU-GMRES iterations9 P1 /11 P2, independently computed true
relative residual2.74e-11/1.82e-11. Independently replayed all
P1/P2 solutions and reintegrated grad error with216-point
6x6x6 Duffy quadrature, agreeing with primary64-point within
8.77e-8 relative (P2 nonpoly). Peak Python RAM366.7MiB,
wall11.04s for3 solves; no Codex consumed.
This is a narrow scalar regional approximation accuracy result,
NOT full430-material coupled electrical/thermal model, measured
material laws, physical TEC/detector prediction, CAD curvature
refinement, asymptotic p/h convergence or GateB qualification.
First preflight NumPy structured-array comparison failure before
FEM saved separately; corrected method verifies edge ID uniqueness.
Recommend next R3.15 exact two-material transmission P2 interface
conservation/flux test on native CAD shared region face.
All protected original CAD, R3.3/R3.4 failed receipts, source
meshes and historical R3.8-R3.13 results preserved, Rev3 frozen
issue#2 OPEN, electrical GateB STOP and thermal C/D NOT RUN.

**Current R3.13 non-affine regional refinement gate (2026-11-05): BOUNDARY-EXACT GEOMETRY PASS; MESH/ERROR CONVERGENCE FAIL/STOP.**
Read [full quantitative R3.13 record](docs/V3_R313_NONAFFINE_FIXED_BOUNDARY_REFINEMENT_20261105.md)
and [replayable source + preserved negative results](data/v3_r313_nonaffine_refinement_20261105/attempt01/manifest.json).
Gold detector-bond8 R3.9 region420 unit-scalar non-affine manufactured
quadratic u=sum(((x-o)/s)^2), analytic f=-Delta u and nonzero Neumann
flux on all native region faces except native Dirichlet face2399.
Registered three-level 1->4 interior-centroid tetra refinement:
25905/103620/414480 tets; all13540 original interface/exterior
region TRI3 preserved byte-for-byte as node triplets, all positive
tetra volumes, no nonmanifold face and constant CAD region volume by
independent complete face-complex audit. But minimum normalized q
DETERIORATED1.38495e-4->7.99442e-5->3.26535e-5; q<0.05 fraction
69.13%->71.71%->77.80%. Levels0/1 ILU-GMRES PASS 9/32 iterations,
true relative residual3.40e-11/3.46e-10. EXACT integrated relative
H1 gradient error only1.631253%->1.627525%, 0.2285% relative
improvement despite 4x tets; third level133337 freeDOF SOLVER
STOP after3300 iterations true residual1.8447e-7>1e-8 acceptance.
The failed L2 solve has NO H1 error qualification; do not invent one.
The fixed original boundary facets mean global mesh hmax stays
UNCHANGED, so this mesh sequence is NOT asymptotically refining;
moreover shape quality deteriorates. 125-case independent quadratic
Gaussian quadrature verified H1 exact-moment integration to6.1e-16
relative discrepancy. Peak Python RAM741.3MiB,4CPU/8GiB and total
110.945s; NOT resource blocked. Preserve the negative gate without
rerunning centroid refinement or claiming non-affine convergence.
Potential R3.14: P2 p-enrichment with original planar CAD facets
geometrically intact; new source-face ownership/requalification would
be needed for actual boundary-refining h-mesh. Full430-domain
thermoelectric/electrical PDE remains NOT RUN; GateB STOP,
thermal C/D NOT RUN, canonical Rev3 frozen, issue#2 OPEN,
all protected R3.3-R3.12 sources and failures unchanged.
No Codex usage.

**Current R3.12 solver recovery (2026-11-05): REGIONAL SCALAR ILU-GMRES AND MIXED-BC MANUFACTURED TEST PASS; FULL DEVICE/CONVERGENCE UNQUALIFIED.**
Read [R3.12 measured solver technical report](docs/V3_R312_GOLD_BOND_SOLVER_RECOVERY_20261105.md)
and [source hashes/benchmarks](data/v3_r312_solver_20261105/attempt01/manifest.json).
Preserved unchanged R3.9/R3.10/R3.11 Au detector bond8 regional P1
unit-scalar diffusion on actual native volume420; native CAD face2399
Dirichlet, remaining faces Neumann,3812 free DOF. Previous R3.11
Jacobi-preconditioned CG failures at2500 iterations are REPRODUCED,
relative residuals6.314/6.400/6.720. Sparse-direct residual~1.3e-9.
Without changing source mesh, coefficients, physical boundary constraints
or regularizing the matrix, SciPy spilu(drop_tol1e-3,fill_factor8)+GMRES
converges in88/88/87 iterations, true relative residual<5e-9. Stronger
spilu(drop_tol1e-5,fill_factor16)+GMRES converges10/11/10 iterations
with true ||Au-b||/||b||<1e-8 and relative solution differences from
sparse-direct <3e-10. New independently integrated analytic nonzero
Neumann harmonic affine solution u=x+2y-0.3z: all13540 actual region
boundary TRI3 match registered native facets, exact nodal residual
~1.6e-14, total integrated boundary flux~1.4e-17; strong ILU-GMRES
converges7 iterations R3.9 and R3.11, solution L2 errors<6e-10.
This resolves a REGIONAL scalar linear solver/preconditioner obstacle,
NOT physical gold conductivity, device-level electrothermal PDE,
non-affine interpolation/mesh convergence, global tetra quality or
full430-domain solver readiness. Original mesh/CAD and all historical
failed Jacobi, R3.3/R3.4, original 824 STEP, 378 contacts, Rev3 frozen
and issue#2 unchanged. Electrical GateB STOP, thermal C/D NOT RUN.
No Codex consumed; runtime 4CPU/8GiB, max Python RSS about197MiB.
Next separately authorized R3.13 should examine non-affine analytic
manufactured convergence on boundary-preserving regional refinement
before any physical operator claims.

**Current R3.11 gold-bond actual scalar FEM conditioning benchmark (2026-11-05): GEOMETRIC TARGETED MESH PASS; MIXED-BC NUMERICAL GATE FAIL.**
Read [R3.11 measured report](docs/V3_R311_BOND8_CONDITIONING_20261105.md)
and [full archived code/results](data/v3_r311_bond8_conditioning_20261105/attempt01/manifest.json).
Gold detector bonds7/8 P1 tetrahedral scalar Poisson/Laplace source
operator was assembled and checked against affine manufactured solution
(max absolute error<8e-15) with all boundaries Dirichlet. Such fully
locked-boundary benchmark hides constrained-surface numerical modes:
bond8 free DOF112, unscaled spectral condition R3.9=15.44, R3.10=24.99,
and CG iterations30->33 (worse with smoothing). More revealing mixed-BC
bond8 benchmark (only native face2399 Dirichlet, other faces Neumann)
has3812 free DOF; Jacobi-CG FAIL 2500 max iterations with relative
residual R3.9=6.314, R3.10=6.400. Sparse direct solve gives small
~1.3e-9 algebraic residual, but shift-invert eigen near5.71e-8 shows
weak modes; one geometrically connected tetrahedron region (no proven
geometric disconnection). One target-only bond8 conservative same-material
3-to-2 pass accepted242 flips, R3.9-derived global tets1010119->1009877,
bond8 q<0.05 17908->17623, q<0.01 7369->7248. Full independent
geometry audit PASS exactly320522 facets/2440 face markers,430 material
regions,378 contacts,zero missing/extra/mismatched/nonmanifold faces and
zero nonpositive signed tets. But mixed-BC Jacobi-CG again FAIL 2500
iterations, residual6.720, worse than R3.9 despite q improvement.
This is a scalar benchmark with artificial boundary conditions, not
electrical, thermoelectric or full-package physics. NO real solver
conditioning/convergence qualification; global nonlocal tet-overlap NOT
audited. STOP prioritizing low-q count alone; next focus on robust
preconditioners, boundary-condition rank/scaling and a measured local
mesh-resolution convergence benchmark. Preserve full R3.8-R3.10 meshes,
historical R3.3/R3.4 failures, original824-solid STEP, canonical Rev3
and issue#2. Electrical GateB STOP; thermal C/D NOT RUN.

**Current R3.10 global mesh free-node optimization (2026-11-05): GEOMETRIC PASS, VERY LIMITED QUALITY GAIN; FEM UNQUALIFIED.**
Read [actual R3.10 measurements](docs/V3_R310_INTERIOR_NODE_QUALITY_20261105.md)
and [independent candidate/sha evidence](data/v3_r310_interior_relocation_20261105/attempt01/manifest.json).
Full R3.9 node-incidence census finds only166 movable interior nodes out
of156765; 156599 fixed vertices lie on original registered surface/interface
facets. 13378 of241754 q<0.05 tetrahedra (5.53%) even touch a free node;
228376 (94.47%) do not. One preregistered bounded interior-node relocation
accepted66 moves in3.12s without changing tetrahedral connectivity, fixed
surface or material-interface nodes. Independent FULL saved-mesh audit:
all320522 original TRI3/2440 native owner markers and all430 regions,
378 contact witnesses,0 missing/extra/mismatched facets,0 nonmanifold
faces,0 nonpositive tetrahedral volumes; max CAD region-volume error
remains0.497162% (pin4). Bad q<0.05 count241754->241514 (~0.0993%
relative gain), q<0.01 53490->53420, minimum q0.000138495 unchanged.
THIS IS NOT FEM READY; global nonadjacent tet overlap, solver conditioning,
and physical model convergence unqualified. Do NOT continue generic
interior-node smoothing, since 94.47% bad tetrahedra have no free node.
Investigate strictly same-facet local topology or constrained additional
interior points on a representative difficult region with numerical
conditioning/convergence benchmarks; no PDE or whole-device remeshing
without separately authorized and registered gate. Original R3.9/R3.8
parents, historic R3.3/R3.4 FAIL/STOP records, canonical Rev3, source
824-body STEP and issue#2 remain unchanged. Electrical GateB STOP,
thermal C/D NOT RUN.

**Current R3.9 global tetra quality derivative (2026-11-05): LOCAL MESH QUALITY IMPROVED, GEOMETRIC PASS; FEM STILL NOT QUALIFIED.**
Read [R3.9 measured report](docs/V3_R39_GLOBAL_QUALITY_20261105.md)
and [separately versioned complete candidate evidence](data/v3_r39_quality_20261105/attempt01/manifest.json).
Read-only preflight of the protected R3.8 1043314-tet/156765-node mesh
found 148610 three-cell same-material internal edges; 50418 touched a
bad element (mean-ratio q<0.05). One bounded local 3-to-2 screening admitted
39362 valid candidate topology flips, and a deterministic disjoint batch
accepted33195, yielding 1010119 tets. Bad q<0.05 count280430->241754,
q<0.01 56586->53490, min q2.6566e-5->1.38495e-4. Independently re-audited
the NEW saved tetrahedral face complex: all320522 original constrained
facets/2440 CAD face markers and all430 region owners remain exact, 0
extra/missing interfaces,0 nonmanifold faces,0 inverted tets and unchanged
CAD volume errors (max0.497162%). All378 finite contacts remain preserved.
Initial local-screen code STOPPED on a Python set literal TypeError before
any output; corrected code plus original initial-failure log both archived.
No TetGen remeshing, source node coordinate changes, PDE, convergence or
solver conditioning was run. **Still 241754/1010119 (~23.93%) q<0.05**,
so this is NOT a qualified FEM discretization; global nonlocal tet overlap
NOT independently checked. Original R3.8 source mesh and R3.3/R3.4 failures,
physical824 STEP, old finite contacts, canonical Rev3 and issue#2 unchanged.
Next separately authorized work should prioritize unconstrained interior
nodes, gold detector-bond quality and conservative conditioning assessment,
not silently re-tetrahedralize whole package. Electrical GateB STOP;
thermal C/D NOT RUN.

**Current R3.8 global 430-domain tetrahedral milestone (2026-11-05): GEOMETRIC 3D MESH PASS; ELEMENT QUALITY UNQUALIFIED; NO PDE.**
Read [exact measured record](docs/V3_R38_GLOBAL_TETGEN_20261105.md)
and [full saved mesh provenance/archive](data/v3_r38_global_tetgen_20261105/attempt01/manifest.json).
One and only one registered TetGen -pYYAC -V whole-package attempt (4 CPU,
8GiB, 900s hard wall, output/memory guards) succeeded in25.7496s using the
immutable R3.7 PLC. Saved1043314 positive-volume tetrahedra/156765 nodes
(including166 *interior* added nodes), EXACTLY retained320522 original
registered TRI3 faces/2440 native markers, all430 nonempty source region
attributes, all378 finite contacts, zero unregistered or missing exterior
or material-interface facets, zero tet-face nonmanifold incidences, and
max native CAD material-volume error0.497162% (pin4, <1%). Input original
CAD/mesh/PLC, R3.3 producer FAIL and R3.4 STOP trials remained unchanged.
Original initial saved-mesh independent audit FALSE FAILED because np.sort
result was discarded; corrected + separately cleaned independent full-mesh
audit agree on geometric PASS, and original false-failure code/log preserved.
**Mesh NOT FEM READY:** q_min2.6566e-5, 56586/1043314 q<0.01 and
280430/1043314 q<0.05 (~26.9%), worst gas/lead/pins/Au detector bonds.
TetGen max allocated1580488 tets is NOT saved count. No global
nonadjacent-tet overlap audit or conditioning/convergence, constitutive
law/PDE/TEC performance validation performed. Electrical Gate B STOP,
thermal C/D NOT RUN, 38-page master Rev3 frozen, issue#2 OPEN.
Next authorization should focus on a separately versioned READ-ONLY
global-mesh element-quality localization and candidate quality fixes
while preserving ALL registered source facets/contacts/region volumes.
Do not automatically re-mesh whole package or launch PDE solvers.

**Current R3.7 whole-package PLC preflight (2026-11-05): PASS INPUT/REGION/IDENTITY; FULL 3D NOT RUN.**
Read [R3.7 technical report](docs/V3_R37_FULL_PLC_PREFLIGHT_20261105.md)
and [final PLC evidence](data/v3_r37_plc_preflight_20261105/manifest.json).
The original R3.3 320522 TRI3/156599 node MSH is preserved unchanged; an
independent *input-only* TetGen PLC has 2440 CAD face markers,430 volume
attributes,2397 shared faces,43 exterior faces and all378 finite contact
witnesses. No duplicate triangle triplets, zero bad per-volume edge incidence
and 430 unique OCC inside-volume seeds. 409 cad centroids+1 bbox midpoint+
20 tested inward-offset seeds; six near-boundary seeds subsequently moved
to >=0.0005 mm nearest-CAD-face clearance with no facet changes.
Final PLC SHA256 is recorded in the manifest. The original PLC and FAIL
archives remain untouched. Fixture-ratio extrapolation roughly0.71/1.41/
2.83million tets for 1x/2x/4x but is NOT a bounded 430-domain tet/RAM
forecast; TetGen whole-package recoverability, mesh quality, contact
Jacobian, PDE and solver conditioning NOT TESTED. Do not launch global
TetGen until the next explicit one-run registration with read-only PLC
acceptance and output/kill/resource guards. All R3.3/R3.4 STOPs, R3.5/R3.6
small-fixture evidence, frozen physical CAD/Rev3, issue#2 and electrical
GateB STOP, thermal C/D NOT RUN remain preserved.

**Current R3.6 fixture quality follow-up (2026-11-05): EXECUTED 3-TO-2 CONNECTIVITY IMPROVEMENT, NOT GLOBAL 3D QUALIFICATION.**
Read [measured fixture report](docs/V3_R36_LOCAL_QUALITY_20261105.md)
and [candidate hashes/results](data/v3_r36_quality_20261105/attempt01/manifest.json).
Actual bounded VPS run produced 193 disjoint, locally validated same-region
3-to-2 flips over three passes (113+53+27), reducing tetrahedra 15676->15483
and elements with quality<0.05 377->176, quality<0.01 18->7. Original
7106 external and material-interface facets, node coordinates and per-region
volumes retained; all signed tet volumes positive. Minimum quality 0.008017
UNCHANGED. Global tetrahedron overlap, solver conditioning, full430-domain PLC
seeds/ownership/budget, and any PDE remain NOT QUALIFIED / NOT RUN.
R3.5 source immutable; original R3.3/R3.4 FAILs preserved; original 824-body
STEP, Rev3 PDF and open issue#2 unchanged. Do not infer a global meshing PASS.

**Current R3.5 fixture milestone (2026-11-05): BOUNDARY-PRESERVING TETGEN PLC PASS ON A SMALL CURVED FIXTURE; GLOBAL3D NOT RUN.**
Read [the measured R3.5 report](docs/V3_R35_TETGEN_CONSTRAINED_FIXTURE_20261105.md)
and [immutable fixture inputs/output checksums](data/v3_r35_tetgen_plc_20261105/manifest.json).
TetGen source commit e05aca7 from libigl/tetgen, -pYYA command, yields
15,676 tetrahedra from a conformal0.4mm Cu core/15um polyimide/gas
annular fixture. All7106 input triangles preserved exactly, zero duplicate
or missing faces, zero altered input nodes, zero cross-material face ownership
mismatches, no nonmanifold or nonpositive signed tetrahedra. Actual CAD volume
errors: core-0.5670%,polyimide-0.0546%,gas-0.00295%; strict <1% PASS.
Preserve prior coarse fixture FAIL: core volume error-1.4595% despite
6315 positive tets/facet identity. Element mean-ratio quality is poor at
the lower tail: min0.008017, 377/15676 tets <0.05. This does NOT establish
conditioned FEM, converged fields, 430-region global mesh or solver readiness.
Next priority: evaluate quality-constrained same-facet meshing and prepare
read-only full430-domain PLC provenance/inside-region seed checks. Do NOT
launch global tetrahedralization until scalability/ownership/budget controls
are explicitly registered and all protected mesh/physical source hashes
pass. NO PDE; electrical GateB STOP, thermal C/D NOT RUN, Rev3 frozen.

**Current R3.3/R3.4 outcome (2026-11-05): POSTHOC SURFACE PASS; GLOBAL3D STOP.**
Read [the latest measured record](docs/V3_R33_R34_SURFACE_VOLUME_HANDOFF_20261105.md)
and [machine evidence](data/v3_r34_handoff_review_20261105/summary.json).
Original R3.3 worker FAIL remains immutable. Independent saved-MSH recheck
passes2440/2440 face areas (<1%),2422 ancestors,430 oriented closed skins,
zero corrected mixed-normal signs, completeBVH with98 shared-vertex false
positives rejected using exact rational geometry (zero confirmed interior hits).
The saved320522-triangle surface and source CAD stay frozen. Two independent
global3D Delaunay attempts both STOP: first on missing CAD UV/edge recovery,
second on Gmsh remeshing imported 2D boundaries despite MeshOnlyEmpty=1,
introducing duplicates at copper/polyimide face2360. Parametric restoration
of14747 curve and139111 surface nodes passes exact input-identity comparison,
but does NOT prevent 2D replacement. Discrete planar 15um dielectric fixture
generated1114 tets but FAILS unchanged-boundary gate (632->634 triangles);
curved coaxial fixture STOPPED on unclosed discrete curve loop, zero tets.
NO QUALIFIED GLOBAL3D MESH OR PDE. Recovered image97526dce is NOT identical
to historical a0b22cf. STOP further whole-device meshing until a small curved
thin-feature conformal fixture demonstrates *exactly unchanged* surface facets,
positive tets and material interface ownership. Rev3 master remains frozen,
electrical GateB STOP, thermal C/D NOT RUN, issue#2 OPEN. Preserve every failed
receipt, original physical824-solid STEP,824 source mappings,378 contacts,
R2/R3 CAD, old meshes and untracked archives. Existing sim:0.0 only for
authorized agent work; prefer bounded direct diagnostics to conserve Codex.

**Current R3.2 outcome: GLOBAL SURFACE TRIAL STOP; NO MESH SAVED.**
Read [the measured failure record](docs/V3_R32_GLOBAL_SURFACE_20261103.md),
baseline efd853c, existing sim:0.0, one builder. Exactly ONE worker ended in
5.726s/16.828CPU-s/~227MiB after native2D returned: a tag-sensitive directional
seed guard raised BEFORE serialization. Renumbering is a plausible mechanism,
not proven from retained after-fill data. There is NO actual MSH or measured
global triangle count; all2440 mesh areas/2422 ancestors, quality, normals,
seams/skins/intersections/readback remain NOT MEASURED. Exact ten directional
seed faces were2385–2389 and2397–2401; source430/824/378 identities remain intact.
733 applicable tests/11 runtime skips,18 focused,archive/master/both legacy and
5763 baseline blobs/207 protected inputs/95 preserved trial-file guards PASS.
Evidence commit12faf57 is pushed; exact CI41722977176 PASS. Any receipt-only
successor also needs exact CI before handoff. No further experiment; do NOT rerun
or repair the sealed worker. A serialization-first, renumber-aware surface-only
replay is PROPOSED and requires fresh authorization. No Boolean, geometry/law
change, tet or PDE. Preserve old trials/cache/fields, exact38-page Rev3 and all
failed gates; issue#2 OPEN. Software/integrity PASS does not qualify a mesh.

**Prior R3.1 outcome: LOCAL mesh benchmark PASS; GLOBAL NOT RUN at that checkpoint.**
Read [R3.1 measured methods/results](docs/V3_R31_LOCAL_MESH_BENCHMARK_20261103.md),
baseline b009f36; existing sim:0.0, one execution agent only.54 native faces,
12 actual local workers:8 PASS/4 FAIL or STOP, one permitted correction; original
C leads remains NOT RUN. Corrected exact-boundary directional bonds:27,080 triangles,
13,544 used surface nodes,1.463s end-to-end,maxarea0.285334%;38.26x fewer triangles
than the same14 accepted R2 ancestors. Callback bond timed out180s; native/all
and selective bonds failed4.117/4.142% area gates. No false success or global
speedup: only54/2440 faces benchmarked; the complete600s causal budget is unknown.
715 applicable/11 runtime skips,58 focused,archive/master/both legacy and5636
baseline/93 input/85 preexisting trial-file guards PASS. Study2c47550 is pushed,
exact CI41662900682 PASS; any receipt-only successor also needs exact CI before
handoff. No further experiment. Frozen prospective hybrid plan is NOT EXECUTED; one future bounded
global surface-only trial is PROPOSED and requires new authorization. No Boolean,
global surface/tet mesh,PDE,physical redesign or electrical forensics now.
All430 domains/824 sources/378 contacts,jacket exclusion,pin heterogeneity,laws
UNSET,original STEP/R2/R3/38-page Rev3 and failed gates remain immutable;issue#2 OPEN.

**Prior R3 outcome: SOURCE MIGRATION PASS; GLOBAL MESH STOP (2026-11-03).**
Read [R3 registration/results](docs/V3_ANALYSIS_R3_GLOBAL_MESH_20261103.md),
baseline4955177, existing sim:0.0 only. Saved unimprinted R3 has430 conformal
domains/2440 owned faces, all824 sources/378 contacts, exact6 full/4 partial
jacket regions and0.077162028mm³ polymer excluded from gas; heterogeneous
pin-cap laws remain explicit and UNSET. One meridian imprint STOPPED on unresolved
face lineage; no further CAD retry. The first adaptive surface attempt STOPPED
at600.073s (864.31CPU-s,504.809MiB observed peak RSS) without a completed mesh.
No triangle-reduction/area/3D qualification; full3D and its alternative NOT RUN.
Local QA PASS:687 applicable tests/11 runtime skips,44 focused, archive/master,
both legacy and5548 baseline/84 prior trial-file byte guards. Source/evidence
commit062d643 is pushed with exact CI PASS (run41602077530). Any receipt-only
successor must also pass exact CI before handoff; no further experiment. A native
size-field/periodic-face performance correction is PROPOSED, not authorized here.
Preserve accepted R2, physical824-solid STEP, exact38-page Rev3, all84 preexisting
untracked trial-file identities and every prior FAIL/STOP; issue#2 OPEN.
No PDE, fit, performance, physical redesign or electrical forensics. One builder.

**2026-11-03 prior accepted R2 analysis-only geometry (HISTORICAL):** [R2 derived geometry and meshability release](docs/V3_ANALYSIS_R2_GEOMETRY_AND_MESHABILITY_20261103.md) transforms only separately versioned *computational* solids from baseline5c16da8. Two original 15um annular TEC-lead polyimide jacket volumes become explicit dielectric shell/interface requirements; four 2um Ni+1.5um Au pin-tip finishes become exact source-volume-preserving piecewise-axial effective cap regions, NOT bulk Kovar. The R2 model has428 conformal 3D domains/2422 uniquely owned faces and native one-connected gas (1231.707223196mm³), all824 original source bodies/378 finite contact witnesses mapped with zero area/short errors. Ten inner lead/jacket faces map to 6 full and4 *PARTIAL* shell subfaces; boundary quadrature on partial areas is **NOT QUALIFIED**. A curvature-controlled global 2D mesh has1,416,664 triangles/701,952 nodes, and0/2422 face CAD-area mismatches above1% (max0.509281%); coarse95k/edge185k alternatives FAILED the gate (113/46 faces). A genuine 4-domain local lead/joint/pin 3D mesh has38,496 tets /13,963 nodes and0.321–0.537% source-volume errors. **No qualified whole-device tetrahedral mesh; no PDE or material law fitted**, no electrical STOP reopened. Physical R1 STEP, prior global failures, Rev3 and issue#2 remain untouched. Mandatory next priority: adaptive, face-targeted curvature meshing with achievable global 3D density, and partial dielectric shell operators, preserving all accepted source/contact/insulation gates.

**2026-11-03 prior global V3 meshability STOP (HISTORICAL):** [Bounded global mesh gate](docs/V3_GLOBAL_MESHABILITY_AND_LAW_GATE_20261103.md) on frozen9468b36 registered438 volume /2456 face groups and produced one complete2D candidate (49863triangles/23301nodes), but independent CAD face-area verification FAILS:174/2456 faces >1% area discrepancy, max336.505% relative. Two limited global3D attempts both STOP on overlapping face2395 TEC_lead1/lead1_insulation; 0.01° facet tolerance did not fix even identical boundary triangles. No valid global3D tetra mesh or physics. [Explicit law requirements](data/v3_global_mesh_gate_20261103/physics_law_requirements.json) cover every domain, with all coefficients UNSET, solver_ready=false; no homogeneous bulk Cu/Au/Ni fallback for the98 composites. Physical STEP, Rev3, historical failed gates remain unchanged, issue#2 OPEN. Preserve all original failed attempts; NO additional numerical-forensics or meshing retries without a bounded new geometric representation task.

**2026-11-03 prior derived-geometry milestone (HISTORICAL, GEOMETRY ONLY):**
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

**Current: R3.1 LOCAL benchmark complete and published; no further experiment.**
Read the R3.1 note and preserved R3 source/STOP. Native local sizing and exact
source-boundary UV directional meshing are measured, not global qualification.
A single future global surface-only hybrid trial is PROPOSED, not authorized;
do not restart the campaign, rerun its one correction or enter3D/PDE automatically.
All previous electrical, gas and coupled-thermal STOPs remain constraints.

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
