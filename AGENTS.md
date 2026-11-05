# CURRENT PROJECT CONTRACT

This is the authoritative continuation contract, updated 2026-11-03. Historical
work orders and milestone instructions describe their own checkpoints; their
"current", "next" and report-freeze language does not override this contract.
Their numerical evidence, original errors and acceptance criteria remain intact.

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
