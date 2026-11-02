# Gated candidate Cu, transport calibration and sink study

Internal registered record, baseline `7d7e9be162a334ee252c4214e7751f903c99b562`.
New prospective user authorization covers only this separate candidate. Preserve
the original28/12/4 model, prior29/11/4 STEP/results, old STOP/FAILs, material
laws and exact38-page Rev3. Geometric feasibility is not manufacturing or OEM
validation. RMT2008/current, TEC Microsystems2019 and VIGO housing are distinct
sources; candidate ordering/construction is inferred. Calibration is not blind.

## Preregistration — before fixture or reduced runs

### Stage A: electrical operator and explicit thermal coverage

Import the frozen361-solid STEP into a fresh metre-target Gmsh process and
independently match all volume/bbox signatures. Keep89 Cu bodies, two Cu tails,
176 solder tools and4 ceramics as needed for **contact-face imprinting only**;
remove P/N and detector solids. Fuse each tail into its own Cu endpoint, retaining
89 disconnected Cu conductors. No changed physical geometry/export. Audit
176 exact Cu/solder footprints, two true tail-end terminals, exclusive owners,
areas/normals,89 connected components and both ports per component. Interface
electrical resistance is explicitly ideal zero; actual solder/contact R unknown.

Solve actual3D `div(sigma grad V)=0`, sigma=1/(1.72e-8ohm m), isothermal300K,
using independently assembled linear tetrahedral FEM and sparse direct solve.
Each disconnected conductor has1/0V on its actual incoming/outgoing footprints,
insulated remaining faces. Normalize each field to1A; series R is the sum of
89 measured operator resistances, not the old .314365ohm centerline estimate.
No P/N3D field or whole-device current-localization claim follows.
Pre-run inspection of the frozen `path_boxes` shows horizontal ribbons have
.1×.03mm sections but vertical pillars have **.1×.1mm** sections. The previous
uniform-area estimate did not capture this distinction; preserve it as old
unqualified evidence. Registered vertical sections use the actual square area,
without changing geometry or selecting dimensions from electrical results.

Fixed two mesh sizes **60µm and40µm**,32 minimum circle points, P1 tets only.
Target coarse<=120k /fine<=250k; **hard250k tets each**, positive volumes,
per-body volume agreement<1%, no omitted faces/ports/components. One geometry
imprint, at most two meshes, no adaptive/repeated attempts. **600s total fixture**,
CAD<=120s, each mesh<=150s, sparse analysis<=90s per level;4CPU/8GiB wrapper
(within12GiB user cap), external hard timeout600s. Stop on budget/invalid topology.

Before interpreting candidate fields, exact analytic3D uniform-bar and affine/
zero controls must reproduce R=rhoL/A, I=VA/(rhoL), integralJ·E=IV, with1e-9
relative/1e-12 absolute errors. Negative topology/unit/material controls reject.
For each actual conductor require: free-node residual relativeL1<1e-8, signed
terminal reaction closure<1e-8, work/independent volume-Joule discrepancy<1e-8,
symmetry/terminal-swap reciprocity and sign reversal<1e-8. Independently solve
swapped and negative BC right-hand sides, not replayed scaling only.

Raw current is additionally integrated on **one interior geometric section per
conductor**: ordinary pair-link midpoint between its two leg centers; node0 x=0,
node58 z=1.2mm, node80 z=2.4mm, node88 z=2.0mm. Intersect actual saved tets with
the plane and integrate their constant J·n over true polygons. Required fine
section-current error **<2% for all89**, absolute comparison to1A. Require
coarse-to-fine change in each R and total R **<2%**. Raw terminal gradients are
reported separately from reactions; neither is relabeled as the other. These
new electrical criteria do not waive old raw bath1%/cold5% or gas1% gates.
This comparator is limited numerical evidence, not general mesh independence.

**Thermal/Joule partition must not be invented.** If electrical gates pass and
time permits, use the same fine Cu mesh for an independently solved constant
kCu=400W/(m K) thermal response. Thermal ports are actual imprinted Cu/ceramic
contact faces plus Cu/solder footprints grouped by the four **assumed isothermal
ceramics**, and the two tail ends grouped as one ambient reservoir. Perfect
thermal contact is an explicit reduced closure, not measured solder/ceramic
accuracy. Check conflicting shared-node traces and exact source-face ownership;
STOP thermal qualification on ambiguity, never add arbitrary conditions.

Five harmonic-temperature basis solves plus one actual Poisson solve with the
computed3D1A Joule load produce a passive thermal conductance matrix L and source
vector p. Derive `qCu=-L*T+I²*p` by static condensation/adjoint integration,
including Joule loads on Dirichlet nodes. Require reciprocity/row closure/energy
relative<1e-8, positive semidefinite L, nonnegative p and sum(p)=R within1e-8;
uniform-temperature zero-current heat exactly zero to1e-10W. Independently
compare basis allocation against the actual Poisson reactions<1e-8 relative.
No assumed half-split. Record full Cu temperatures and thermal destinations.
All faces not contacting these registered bodies are adiabatic; gas/radiation,
real ceramic spreading and unknown contact impedances remain unqualified.

If thermal coverage fails or is not completed, retain electrical-only result,
report conservative0–100% Joule-destination bounds and **STOP B/C qualification**.
Constant Cu rho/k are declared engineering laws referenced at300K, not measured
180–390K properties; no electromigration/fatigue/reliability claim. Their reuse
in later reduced studies requires actual Cu field extrema within180–390K and
explicit assumption labeling; the isothermal solve alone proves no safe1A use.

### Stage B: conditional isolated three-factor study

Only after A electrical AND thermal gates pass: create a new isolated five-node
candidate solver using original nonlinear32 P/N stages and the qualified Cu
operator, never patch original/reference solvers. Cu89+tails are included once:
`Vterminal=sum(V_TE)+I*Rcu`; thermalqCu supplies four ceramic nodes and ambient.
No extra old Cu wire resistance/Joule or post-fit correction is added. Verify
global `Qsink+qCu_ambient-QAu=I*Vterminal+Qdie` and stageQh−Qc=I*V_TE.
Stage/node/global gates1e-9/1e-8/1e-8W; hotspot/domain/residual failures reject.

Module-alone vacuum surrogate, hot300.15K, actual20 chart I/Qc conditions,
AuOFF, auxiliary attach30µm/1mm², gas/radiationOFF. Nominal sourceS/rho/k=1/1/1
and external **UNVERIFIED** triple1.01/1.19/1.15 are evaluated separately, with
CuOFF and qualified CuON contexts explicitly separated. Original two-factor
failure remains archived. Measured P/N40–300K, active180–390K, >300K quarter
tangent ASSUMED, sigma=1/rho and tau=T*dS/dT retain one-sided semantics.

New calibrationS[.9,1.1],rho[.8,1.2],k[.8,1.2], common factors with unchanged
source shape/geometry, start nominal, bounded least-squares max12 function
evaluations, fractional Jacobian step.001. Only four conditions(.2A,0),(.2A,.1W),
(.6A,0),(.6A,.1W); objective residuals(lift/5K,V/.1V), engineering weights,
not likelihood. Remaining16 are previously viewed evaluation, not blind data.
Rejects retain diagnostics; a rejected calibration trial stops refinement, no
penalty observations, restarts, enlarged bounds or extra knobs. **350 outer
reduced calls /600s /8s each**, no repeated launch. All20 admission, liftMAE<=8K,
maxabs<=15K, VrelativeRMS<=15%, maxrelative<=25% and all physical/numerical gates
must pass. Report signed residuals and load dependence; no ACR=DC V/I inference.
Dry-N2 higher-Th panels NOT COMPARABLE; Qmax/DeltaTmax NOT RUN.

### Stage C: conditional matched-target sink performance

Only if B fully passes: selected candidate law, ambient300K, die2mW, Au thermal
wires ON using coincident original detector/warm-end route hypotheses, Cu operator
tails at ambient. No old Cu lead branch (already included); no gas/radiation or
failed nonlocal inputs. Rtheta=0/2/5/10K/W, I=0/.1/.15/.2/.25/.3/.35/.4/.5/.6/
.8/1A. At most48 grid cases plus10 actual midpoint solves per Rtheta in the
first adjacent admitted falling200K bracket; tolerance.005K on cold-side solve,
no rejected gaps or nonmonotone branch crossing. **100 calls /300s /8s each**.
Enforce Th=300+Rtheta*Qsink; do not equate Qsink with IV. Report die/hot/Cu/P/N
extrema, terminalV/P, sinkheat, COP, rejected counts and assumed continuation.
No continuous optimum, actual-device feasibility or external ~3W/10K/W claim.

### Preservation, verification and report policy

Freeze source/preregistration/old hashes before runs. Save every attempted
geometry/mesh/solver result including STOPs. No million-tet production FEM or CFD,
new agents/sessions or other repositories. Test analytic/negative/conservative
controls, actual operator fields, source domains and qualified stage transitions;
full applicable regression excludes existing12 runtime cases (this bounded
fixture itself is explicitly authorized), archive/master and both legacy checks.
Append actual UTC material events. Reassess the SAME Rev3 only for substantively
verified physics, with predecessor preservation/determinism/every-page QA if
changed. Otherwise preserve its bytes and explain why. Stop after these gates.

## Results

**STOP: Stage A execution unavailable; no physical qualification result.**
The pinned `tecooledmct-fem:26.2.1` image was absent. The initial wrapper never
started the fixture; there are **zero CAD imports, meshes, PDE solutions or new
reduced cases**. Only `dolfinx/dolfinx:stable` is present; it was not substituted.
Host Python3.13.7 lacks NumPy, SciPy and Gmsh; no host packages were installed.
Stage B (including the external triple) and Stage C are **NOT RUN**.

### Exact runtime blocker and bounded recovery attempt

Read-only inventory found cached descriptions of all pinned Dockerfile steps,
but both historical image IDs and the required tag were absent. There is no
local image archive: the prior10kB context tar is build input, not an image.
One **cache-only** reconstruction of the unchanged Dockerfile was attempted
with `--network=none --pull=false`. The first apt step was uncached; the guard
aborted after **1.509s**, before package installation. The captured output shows
the attempted network-disabled apt update was canceled. No full dependency
rebuild, version change, pruning, host install or second recovery was attempted.

[Cache registration/result/log](../data/gated_candidate_cu_20261102/verification/cache_restore_result.json)
and [runtime inventory](../data/gated_candidate_cu_20261102/verification/runtime_inventory.txt)
are preserved. Dockerfile SHA remains
`1dd10a8f2684011a5c8fde55f4debe510d628d2a68e5e5e4b8cdad9c6975795c`.
Availability and version/source verification of that exact pinned runtime is
the prerequisite to resume the already registered Stage A; cached descriptions
alone did not establish a usable scientific environment.

### Source-only result, explicitly not a3D operator

The independent standard-library [source audit](../fem/gated_cu_source_audit.py)
matches every registered route segment to its frozen box primitive. The source's
vertical path construction uses square0.1×0.1mm pillars, rather than a uniform
0.1×0.03mm ribbon. Total vertical centerline length is **4.4mm**. With the same
old rhoCu=1.72e-8ohm m proxy:

| Conditional centerline estimate | R, ohm |
| --- | ---: |
| Earlier uniform-area estimate, retained unchanged | .314364540 |
| Direction-aware estimate using frozen primitive cross sections | .296705873 |
| Analytic difference from the vertical-area assumption | .017658667 |

The difference is independently `rho*Lvertical*(1/Ahorizontal−1/Avertical)`.
Neither estimate includes exact spreading/corners/stubs/contact changes; neither
is measured or independently3D-qualified resistance. Do not replace the old
estimate's historical record or insert either value as ground-truth device heat.
Nominal1A section-average J is3.33e8A/m² in horizontal ribbons and1e8A/m² in
vertical pillars, **not calculated hot-spot current density or reliability**.
Joule fractions remain UNKNOWN (each0–100%, sum100% of the unknown I²Rcu);
no half-split or physical thermal destination is assigned.

Raw source-only algebra and its explicit NOT RUN fields are in
[source_only_audit.json](../data/gated_candidate_cu_20261102/source_audit/source_only_audit.json).
No chart residual, temperature, Cu source law or prior accepted/rejected case
was recomputed or changed. The gated3D implementation is an **unexecuted draft**,
not a verified electrical/thermal operator; do not infer success from code alone.

### Available checks and outstanding checks

- **4 standard-library source tests PASS**: exact uniform-bar scalar resistance,
  true vertical section, invalid geometry/material rejection and independent
  direction-correction identity. These are not the registered3D analytic FEM
  controls, which remain NOT RUN with the fixture.
- Current master validation **PASS**, exact38-page PDF unchanged. A separate
  streaming Git-blob guard checks **4,941 baseline files /2,896,428,811 bytes**
  (excluding only three mutable continuation documents): zero mismatches.
  This is strong byte integrity, not a semantic/numerical archive rerun.
- The standard semantic archive verifier cannot import NumPy; its failure log
  is preserved. Full applicable regression, legacy demos and exact-commit CI
  are **NOT RUN**, not reported as passed. Draft Python syntax parses only.
- Original39 registered inputs still match their frozen hashes; old scientific
  FAIL/STOPs and previous STEP/results remain intact. No candidate heat-current
  result, manufacturer calibration or finite-sink conclusion is released.

Checks and environmental scope are in
[status.json](../data/gated_candidate_cu_20261102/status.json).
All work remains **uncommitted**, because the independent fixture and required
runtime regressions cannot be executed. Preserve the pending source/data and
read current status before resuming; do not discard to obtain a clean tree.

### Resume order and report disposition

First make the exact pinned runtime available and verify its versions/source;
do not substitute the dolfinx image or install host scientific packages. Then
run the registered fixture once with its original budgets (it has not yet
executed), inspect every A gate, and only then consider B/C. The executable
entry point, after prerequisite verification, is:

```bash
./fem/run.sh env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=4 timeout 600 \
  python -m tecooledmct.candidate_cu_fixture \
  --out data/gated_candidate_cu_20261102/fixture
```

For the source-only checks use new output paths:

```bash
python3 -B fem/gated_cu_source_audit.py --out outputs/new-cu-source-audit
python3 -B -m unittest discover -s tests -p test_gated_cu_source_audit.py -v
python3 -B -m reports.master.validate --current
```

Rev3 remains byte-identical: an environmental STOP/source-only finding does not
justify public-report clutter or an unqualified new field. No alternative PDF,
subsequent experiment, new fit or sink campaign has been launched.
