# R3.2 one global hybrid surface-only trial

Baseline `efd853cbd33a85acba5012b0b70521389ea31e0b`, existing sim:0.0 only.
The complete user work order is retained under `data/v3_r32_global_surface_20261103`.
No original geometry, field, accepted mesh, material law or38-page Rev3 changes.
Issue#2 and all historical failed release gates remain OPEN/unchanged.

## Registration before the single worker

Exactly **one** global2D mesh worker, including import, constraints,1D generation,
directional construction, native2D filling, serialization and validation, must
finish within600.0s. The parent kills at599.5s to reserve scheduling/cleanup margin;
no second worker, retry, pilot mesh, adaptive run or rerun after any failure.
Docker enforces4CPU/8GiB/offline; a parent monitors the child and stops at7.5GiB
observed RSS before the container cap when possible. Kernel OOM/timeout and phase
progress remain durable evidence. Accepted size is<=800,000 triangles. A larger
completed mesh still gets all2440 face-area checks if wall budget remains.

Frozen source:430 volumes/2440 uniquely owned native faces,824 physical source
bodies,378 finite contacts,88 essential series legs and isolated detector. Real
polymer jackets displace0.077162027868mm³ gas; six full/four partial Cu/polymer
patches and actual bare complements remain real CAD faces. Four effective pin
domains retain explicit axial Kovar/Ni/Au regions. All constitutive values UNSET.
Only source metadata and existing local MSH were read in preparation; no new mesh.

Directional faces are **exactly2385–2389 and2397–2401**, no pin or other wire face.
Use the unmodified R3.1 `seed_periodic` correction: exact source-boundary node IDs
and source UV coordinates,48 interior circumferential divisions,80µm axial target
and source turning-angle constraintsπ/24. Shared curves are discretized once.
Other2430 faces use the cached R3 h values with native MathEval/Restrict/Min,
IncludeBoundary=1, curved/quad-required constraints,20 previously registered
curved four-corner faces. Directional boundary counts override only their30
shared curves; no private seam nodes, no CAD Boolean/imprint or geometry change.
`MeshOnlyEmpty` fills native faces after the ten directional patches exist.
No `generate(3)`, PDE, material fit, detector-temperature or OEM claim.

Before meshing, verify every actual source face owner/area and volume mass against
the frozen registry; seal complete executed sources and inputs. Native surface
groups cover every2440 face and all430 volume IDs as metadata only. One globally
scheduled `generate(2)` call is allowed, preceded by one shared `generate(1)`.

## Measured gates and conventions

- Strict individual native face and all2422 complete R2 ancestor area errors
  `abs(A_mesh/A_CAD-1)<0.01`; no mean or selected-subset substitute.
- Actual positive TRI3 elements, every face/owner/physical group present, zero
  tetrahedra, no duplicate element tags or node triplets, <=800k triangles.
- Exact native curve-node incidence including repeated periodic seams. Triangle
  winding is normalized **only to the existing oriented CAD boundary**: a uniform
  opposite face is reversed, mixed/incompatible winding fails. Read-only old-MSH
  controls found28/4 positive/opposite lead faces and12/2 bond faces; source
  orientation is not inferred from desired heat/current results. All430 volume
  skins must be closed, manifold and consistently oriented with original owner
  signs. Every shared native face has opposite source-volume signs.
- Per-face and global edge lengths, longest/shortest edge aspect and shape quality
  `4*sqrt(3)*A/sum(edge²)` at min/1/5/50/95/99/max percentiles; positive values.
- At most8 deterministically spaced triangles per native face: chord centroid
  projected onto the underlying source CAD surface, unsigned normal-angle error
  `acos(abs(n_triangle·n_CAD))` and centroid distance. Signed-normal consistency
  is recorded per face. This is a **sampled underlying-surface measure**, not an
  exhaustive normal/Hausdorff bound or trim-aware distance certificate.
- Minimum edge/curvature and radial jacket-end metrics are reported; effective
  Ni/Au axial regions are law requirements, not separately meshed film volumes.
  Report actual nearest node z offsets to their datums; do not claim film-field
  resolution or3D through-thickness qualification from a surface mesh.
- Duplicate geometric triplets use1e-10mm coordinate quantization. If primary
  area/topology gates pass and time remains, attempt an exhaustive bounding-box
  hierarchy (16 triangles/leaf) for linear facet intersections. Narrow phase tests
  segment/triangle interior piercing plus coplanar positive-area overlap, with
  relative tolerance1e-10 and coplanar distance1e-9mm. Boundary-only touching is
  excluded; first measured improper intersection FAILS with native-face witnesses.
  A complete zero traversal is required for an intersection PASS; a time stop,
  skipped test or partial traversal is explicitly NOT MEASURED/NOT COMPLETE,
  never inferred intersection-free. If prior gates fail, this expensive check
  may be NOT RUN because the candidate is already rejected.

Actual MSH is saved before validation, alongside immediate counts and phase
receipts, so a failed criterion never erases the candidate. Independent fresh-file
read-back recomputes cross-product areas (worker Gram determinants), owner/group
and shared-edge/skin incidence without meshing; it is an independent arithmetic
implementation by this execution agent, not external physical certification.
Every unmeasured criterion is named. No global-surface success grants volume
meshing or physics authorization; unknown material/process/physical accuracy stays
separate. Failed candidate/gates are immutable, with no second global attempt.

## Provenance, verification and release

Pinned image `tecooledmct-fem:26.2.1`, identity
`sha256:a0b22cf70bbecaea2cbc8e1cf40aaef1bd620c187b73e251aee37a4fb9d28688`:
Gmsh4.13.1,NumPy2.1.3,SciPy1.14.1. No installation, rebuild or substitution.
Before edits,207 parent inputs and95 existing untracked/ledger files were hashed.
Original R2/R3/R3.1 artifacts/producer sources and canonical PDF remain unchanged.
Registration includes source hashes, metadata, one run slot and strict bounds.
Positive/negative nonmeshing tests precede the worker; final no-new-PDE regression,
archive/master and byte guards precede scoped publication and exact-commit CI.
Actual saved geometry/mesh figures are required if a mesh completes. This internal
technical note is not a second public report; Rev3 remains byte-identical.

## Result

PENDING. No global worker has run at registration time.
