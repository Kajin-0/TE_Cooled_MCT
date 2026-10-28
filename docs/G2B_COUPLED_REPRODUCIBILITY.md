# Reproduce the inferred two-terminal 88-leg coupled FEM

This is an assumed construction for numerical verification, not OEM artwork.
It is separate from the preserved six-port geometry and the unchanged G1/G2a.
Use the existing pinned headless image. No new host packages or reinstall:

```bash
./fem/run_g2b.sh python -m tecooledmct.fem_g2b_run --out outputs/fem-g2b-two-terminal
./fem/run_g2b.sh python -m tecooledmct.fem_g2b_connectivity --run outputs/fem-g2b-two-terminal
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q
./fem/run.sh python -m tecooledmct.cli --quick --out outputs/check-g2b-coupled
./fem/run.sh python -m tecooledmct.geometry_demo --out outputs/pellet-g2b-coupled
```

The new runtime wrapper uses the same image, user UID/GID and project-only mount,
disables network, caps CPU at four and RAM at **12 GiB**. G1's original wrapper
and image/bootstrap files are untouched. Full solver children have a 900 s
timeout. `wait4` records each actual solver's CPU time, elapsed time and peak RSS.

For a functional real-solver smoke use `--quick`. It uses a coarse 0.18 mm mesh,
actual ±0.05/0 A loaded cases and a +0.1 A convergence point. It does not establish
mesh convergence or the fine Cu-bridge accuracy gate. The full study uses a
0.18 mm coarse mesh and two 0.12 mm global meshes, with 0.04 and then 0.025 mm
Cu-gap targets. The final background-field policy prevents the tiny gap target
from propagating unnecessarily over all leg sidewalls. The intermediate grid
is retained, including its bridge errors just above the acceptance threshold.
Small routing features are also geometrically resolved; these are maximum target
sizes, not a uniform-grid spacing. Netgen optimization is applied and minimum
tetrahedron SICN/sliver counts are audited.

Already generated inputs can be reused with explicit actual-mesh re-auditing:

```bash
./fem/run_g2b.sh python -m tecooledmct.fem_g2b_run \
  --out outputs/fem-g2b-two-terminal \
  --mesh-root outputs/fem-g2b-connected --reuse-mesh
```

This rereads the actual Gmsh tetrahedron qualities and compressed node/material/
face arrays, independently recomputes contact/volume/circuit checks, verifies
requested mesh sizes and runs ElmerGrid again. It does **not** reuse old PDE
solutions by default. `--resume` separately allows previously completed cases
only after matching actual BCs, zero exit status and SIF/VTU hashes, followed by
fresh independent field verification. The loaded-positive sweep label explicitly
uses the identical fine convergence execution; it does not claim another solve.
Nearby new cases load a hashed real `solution.result` as an Elmer restart initial
guess, and still execute the full coupled PDE and all balance/current checks.

## Why this routing construction

The original three stage-local paths end on hot-side pads at different heights.
A planar trace alone cannot reach the next stage. A free external Cu jumper
would violate the modeling contract. A through-ceramic via by itself spans only
the plate thickness, leaving the stage-height gap unsupported. The selected
assumed construction combines a supported buried vertical Cu insert, a buried
plate trace, an exit via and an insulated pad-side collar. It fits inside the
nominal stack footprint, with an explicit ceramic structure around the route.
Manufacturing/bonding/process compatibility and real contact resistance still
require independent validation.

The 28/12/4 split, stage-local artwork, 0.4 mm legs, stage heights, shared plates
and nominal 3.8 mm envelope come from the earlier inferred feasibility model.
Two new Cu domains connect stage 0 out → stage 1 in and stage 1 out → stage 2 in.
Each consists of six face-connected rectangular segments fused into one physical
conductor. Vertical Cu sections are 0.06 × 0.06 mm; buried horizontal trace/tab
sections are 0.06 × 0.04 mm. They do not intersect each other or any unintended
leg/pad. The main vertical cores are laterally separated from lower-stage legs
by at least 45/75 micrometres, with explicit dielectric walls and air clearance.
Buried plate traces have roughly 80–100 micrometres of alumina separation from
adjacent stage Cu. Exact dimensions, rather than prose approximations, are in
each mesh's `manifest.json`.

Four additional alumina support/collar domains encapsulate the routes. Cu is
actually cut out of the relevant ceramic/support volumes before fragmentation;
overlapping Cu and alumina are never assigned to the same tetrahedron. These
supports and Cu links create real thermal shunts and participate in the solve.
They must not be dismissed as purely electrical wiring.

The actual model has 189 physical domains and 181 conductor vertices. Its unique
path has 180 edges, exactly two degree-one terminals and degree two at every
internal conductor. It traverses all 88 legs once. The old six pad locations are
retained as stage-local interface descriptors; four now join Cu links.
`external_ports`, `terminal_planes`, the actual physical
boundary names and actual mesh graph identify exactly two external terminals.
The six-port generator and its published evidence retain their original meaning.
Current manifests label those historical IDs as `original_six_port_boundary_ids`
and `original_stage_pad_count`; earlier topology snapshots used the legacy names.

## Independent geometric and actual-mesh audits

An orthogonal-cell CSG calculation uses every box boundary to compute exact
material volumes and interface areas, independently of OpenCascade. Conductor
overlaps are rejected. Dielectric cells occupied by the intended Cu links are
removed explicitly. Face, edge and point contacts of distinct conductors must
match the intended single path. OCC masses are compared with these independent
volumes before meshing. After Boolean fragmentation, tetrahedron face adjacency,
all interface areas and body volumes must match the independent CSG. Shared-node
checks reject zero-area mesh shorts; tagged faces must have correct incidence.

The supplemental `fem_g2b_connectivity` command also unions actual tetrahedron
faces within each of the 189 domains, then across all conducting solids and all
thermal solids. Each domain must have one face-connected component; the complete
conductor and thermal assemblies must each have one component. A common material
tag cannot hide disconnected fragments, and point/edge-only joins cannot pass.
Its three actual-mesh proofs and source hashes extend the full result to 30 gates.

Only these exposed faces carry imposed conditions:

| Physical BC | Condition |
|---|---|
| 101 | Bottom ceramic bath, T = 300 K |
| 102 | Outer top ceramic, uniform specified inward total load (0 or 2 mW) |
| 103 | Stage-0 input pad, specified inward total current |
| 104 | Last-stage return pad, phi = 0 |
| 105 | Other exposed surfaces, natural zero total heat/electric flux |
| 1001 onward | Material interfaces, shared conforming nodes; no extra source/BC |

The intermediate plate temperatures are **unknowns**. A 300 K initial guess is
not an intermediate fixed-temperature condition. Radiation and gas are omitted
deliberately at this conduction-only gate. Contacts/bonds are ideal; no hidden
solder gap or fitted resistance is included.

## Genuine PDE and material scope

The pinned Elmer ThermoElectricSolver solves T and phi together on the complete
mesh, with J = sigma(−grad(phi) − S grad(T)), q = −k grad(T) + TSJ,
div(J) = 0, div(q) = J·E. These are not 88 independent lumped coolers or a field
painted from cascade algebra. Discontinuous S and continuous total flux include
Peltier junction conversion; Joule and Seebeck are present in the same solve.

The mixed G1/G2a room-temperature Bi-Te constants, Cu assumption and alumina proxy
are unchanged. Alumina uses sigma = 1e-12 S/m to retain a well-posed potential
field in the coupled solver. A 100-fold conductivity reduction is explicitly
tested and a conservative leakage bound is reported. Material references and
temperature limits remain those in FEM_G1_REPRODUCIBILITY.md; no physical curves,
cryogenic validity, OEM ΔTmax/Qmax match or production accuracy are claimed.

An independent ideal constant-property cascade solves stagewise heat balances
with no intermediate bath: Qc0=Qh1, Qc1=Qh2, Qc2=load. It includes estimated local
Cu resistance but omits routing/support shunts, spreading and contact losses.
Its T/V differences are a sanity comparison, not an accuracy acceptance test or
a fitted correction. The FEM support/routing losses can legitimately reduce lift.

## Field verification and stage budgets

The independent postprocessor maps actual VTU values to original mesh nodes,
reconstructs gradients, E/J/q/Joule and the original nonlinear weak form. For
constant properties J and J·E are cellwise constant and q is affine, allowing
exact weak-form and planar polygon integration. Every one of the 88 legs, 85
local bridges and two buried links has an independent current/heat cut. Leg
volume Joule powers and all body electrical-work contributions are retained.

Global checks compare reconstructed ground/bath reactions, direct constitutive
bath flux, terminal I times area-mean voltage and integrated J·E. Free-node
residual norms prevent internal imbalance being hidden by global cancellation.
No-drive errors use absolute current, because relative error to zero is undefined.
Negative-current input must have consistent voltage sign and independently
verified positive electrical work, rather than an unexplained generator output.

Four original plate domains have actual volume-weighted mean, minimum and maximum
temperature. Additional routing supports are not averaged into those plate means.
Stage heat budgets use conservative **nodal plane control volumes** divided in
the lower portions of the shared intermediate plates. A P1 indicator w(z) gives
the independently integrated upward transfer −∫q·grad(w), and ∫w J·E gives the
electrical work below the cut. These regions include the relevant ceramic and
routing portions, unlike a leg-only textbook stage. Each resulting Qhot−Qcold
is checked against that region's actual electrical work. Direct sharp geometric
plane fluxes are recorded separately. Neither conservative transfer nor global
balance is a claim that raw contact-corner P1 flux peaks are resolved.

Full acceptance includes <0.5% every driven leg/bridge/link current error,
<1% direct bath energy mismatch on the fine mesh, <1% of lift in cold mean/max
mesh change, <1% voltage mesh change, global work/current/weak residual checks,
coherent polarity/load behavior and <1 mK response to ceramic sigma reduction.
The functional coarse smoke omits the fine bridge/bath/convergence gates.

Elmer's final nonlinear stopping tolerance is 1e-9, matching the independently
declared convergence gate. Earlier runs requested 1e-10 and are retained at their
stronger tolerance. The sigma=1e-14 sensitivity attempt reached a roundoff plateau
around 1e-10; that incomplete attempt was retained separately and rerun with the
consistent 1e-9 setting. No current, energy, mesh or material gate was relaxed.

## Outputs and provenance

`summary.json` records protected G1/G2a/six-port hashes, current source hashes,
solver version, actual per-case logs/exit code/nonlinear residual, elapsed/CPU/
peak RSS, SIF/VTU hashes and all acceptance checks. Each mesh records original
Gmsh input, node/domain/face arrays, graph/volume/contact/quality audits and
ElmerGrid conversion. Selected actual fields include E, J, q, Joule and T/phi
and temperature isosurfaces. Stage temperatures, heat budgets, component cuts,
current sweep and mesh convergence are CSV/JSON/PNG/SVG. Full raw experiments
remain in ignored `outputs/`. Only accepted coupled evidence is archived under
`fem/results/g2b_two_terminal_20261028`. Final actual results and limitations are
in PHASE1_G2B_TWO_TERMINAL_RESULT.md.

The early convergence runs precede scheduler/restart and stopping-setting improvements.
Their original source snapshots are retained with `.source` suffixes and hashes;
their actual fields are reverified, not recomputed or attributed to a nonexistent
new solve. Archived SIFs keep their original paths and restart references. Use
the generator/runner to reconstruct local paths and actual restart states in a
fresh checkout. Each actual SIF records its original tolerance and restart input;
both pre-restart and pre-tolerance-change source snapshots are retained. The
resource CSV counts unique successful executions, not repeated labels or aborted
experiments. Incomplete plateau/duplicate attempts are not accepted results.
