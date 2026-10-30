# Reproduce the completed assumed-geometry checkpoint

Use the existing pinned Docker image and sim session in TE_Cooled_MCT. These
commands reproduce historical sandbox physics, **not** the new source geometry.
The user-priority source/return rebaseline now precedes further full-stack
parameter campaigns. Never overwrite old output labels or archives.

```bash
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q
./fem/run.sh python -m tecooledmct.cli --quick --out outputs/repro-full-cli
./fem/run.sh python -m tecooledmct.geometry_demo --out outputs/repro-full-pellet
./fem/run.sh python -m tecooledmct.full_presolder_benchmark oblique --out outputs/repro-oblique
./fem/run.sh python -m tecooledmct.full_presolder_benchmark curved --out outputs/repro-curved
./fem/run_g2b.sh python -m tecooledmct.full_presolder_geometry --legacy --k 2 --out outputs/repro-control-operator
./fem/run_g2b.sh python -m tecooledmct.full_presolder_geometry --k 35 --out outputs/repro-zero-operator
./fem/run_g2b.sh python - <<'PY'
from pathlib import Path
from tecooledmct.full_presolder_geometry import build_split
build_split(Path('outputs/repro-contact-operator').resolve(),contact=True)
PY
./fem/run_g2b.sh python -m tecooledmct.full_presolder_run \
 --operator outputs/repro-control-operator --case outputs/repro-control --timeout 900
./fem/run_g2b.sh python -m tecooledmct.full_presolder_run \
 --operator outputs/repro-zero-operator --case outputs/repro-zero --timeout 900
./fem/run_g2b.sh python -m tecooledmct.full_presolder_run \
 --operator outputs/repro-contact-operator --case outputs/repro-contact --timeout 900
./fem/run_g2b.sh python -m tecooledmct.full_presolder_joint_audit \
 --operator outputs/repro-zero-operator --case outputs/repro-zero
./fem/run_g2b.sh python -m tecooledmct.full_presolder_joint_audit \
 --operator outputs/repro-contact-operator --case outputs/repro-contact
./fem/run_g2b.sh python -m tecooledmct.full_presolder_lead_control --case outputs/repro-fine-lead-off --timeout 1800
./fem/run.sh python fem/archive_full_presolder_checkpoint.py --verify
```

ElmerSolver is invoked genuinely by the runners. Fresh cases warm-start only
from hashed actual archived T/phi, with exact old-node identity and P1 edge
prolongation for the contact mesh. The fine control uses the exact old fine mesh
in outputs/fem-g3b/operator_h1 and a hashed converged-but-bath-unaccepted field
only as an initial guess. Reconstruct the protected fine operator via the old
G3b reproduction guide if its ignored raw directory is absent. It must match the
protected mesh/operator hashes. A zero solver exit and nonlinear convergence
do not themselves qualify the raw bath or added interface gates.

The publication verifier checks source/SIF/field/mesh/manifest digests, actual
VTU node/tet counts and finite T/phi,175 cut records, per-case checks, independent
geometry reaudits and benchmark sources/fields/local balances. The control must
reproduce the old907-patch die within1e−5 K and voltage within1e−7 V. It explicitly
requires retention of old fine failures, unqualified recovery, failed zero-contact
interface diagnostic and unrun second-resolution status. The archive's raw
T/phi VTUs contain actual3D cells; `derived.vtu` in each raw run contains q/J/Joule.
Recompute those derived fields with the frozen postprocessor rather than treating
their absence from the compressed tracked archive as a missing solver execution.

Archive .gz files use deterministic compression and retain original uncompressed
digests. Unpack field/payload/initial-data files into a new replay directory,
restore the small generated Fortran sources, and use the corresponding new
operator with full_presolder_post.postprocess for field verification. The coarse
and fine unchanged meshes and cavity matrices are referenced by protected paths
and digests to avoid duplicating old archives. New contact/refined meshes and
weights are included. `protected_references.json` identifies what to copy into
each reconstructed operator. Actual Elmer meshes can be re-encoded from those
arrays with meshio/Gmsh22 and ElmerGrid; they must preserve all body/boundary IDs.

The contact/refined generation digest differs from the final independent reaudit
by exactly three added exterior-skin checks. The exact earlier version is restored
as split_generation.py.source and its recorded digest verified. The first legacy
generator snapshot is retained. The zero-contact original generator digest was
not captured; its exact protected parent mesh plus current independent reaudit
is recorded honestly. No physical PDE sources changed while solves were active.

Full106 opt-in tests passed for the presolder/flux implementation; the later
source-geometry addition passed110. CLI and geometry_demo passed. Logs include
the early invalid Elmer keyword, invalid zero-bath relative comparison, corrected
benchmark cases, and an interface-audit JSON serialization failure followed by
successful diagnostic replay. None is silently promoted to qualification.

The immutable15-page PDF and earlier G1–G3b/flux checkpoint guards are mandatory.
No permission flow, reinstall, new session, LSDDTS integration, recovered-flux
gate substitution or OEM-device claim is part of this reproduction.
