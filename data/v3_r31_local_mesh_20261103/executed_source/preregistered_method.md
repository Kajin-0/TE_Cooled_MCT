# R3.1 local native-surface meshing benchmark

Baseline `b009f36ba8ba4f90de5e19e1aadb93327e8b4f6e`; implementation in the
existing sim:0.0 only. This is a separately versioned local numerical geometry
experiment, not a new global mesh or physical model. Original R3/R2 artifacts,
824-solid physical STEP,38-page Rev3 and historical failures remain immutable;
issue#2 remains OPEN. The full user work order is retained with the data.

## Prospective registration — before meshing

The read-only inventory selects54 actual R3 native faces in three fixed fixtures:
32 Cu-lead/jacket faces,14 detector-bond faces,8 pin/ceramic/contact faces. The
first fixture contains all four partial Cu/polymer patches and their real bare
Cu/gas complements; all outer polymer surfaces and annular ends are included.
The bond fixture includes the9µm-radius, approximately5mm long straight wire
surfaces and toroidal elbows. The final fixture includes pin1's three native
cylindrical sections and terminal, two perforated ceramic planes, a0.16mm²
P/solder contact and a0.06mm² finite tab joint. Exact tags, owners, R2 ancestors,
areas, boundary multiplicities, curve lengths and curvature are in `inventory.json`.
Selection precedes all new mesh outcomes; no synthetic replacement geometry.

Each strategy/fixture runs once, sequentially, <=180s including setup/validation,
4CPU/8GiB in the unchanged pinned image. Maximum12 normal runs plus **one total**
targeted corrective replay (<=180s) for a demonstrated implementation defect,
never geometry/size/accuracy tuning. An external parent kills a worker at180s and
preserves censored progress/resource evidence. No uncontrolled retries. Total
normal worker budget2160s, replay180s. The following fixed comparisons apply:

| Strategy | Sizing | Explicit curve constraints | Purpose |
| --- | --- | --- | --- |
| A_callback_all | Original R3 Python callback, instrumented | All4521 R3 shared-edge counts /20 curved quad constraints | Reproduce local behavior and count callback cost |
| B_native_all | Constant MathEval + native Restrict/Min fields, identical face sizes | Same4521 counts/quad constraints | Isolate callback versus native field at matched sizing/edges |
| B_native_selective | Same native face fields | Quad-required edges plus selected curved edges; other edges native | Assess broad transfinite constraints; counts may differ |
| C_directional | Native source UV grid on supported periodic Cylinder/Torus; native mesher on other faces | Shared source-curve grid;48 full-circle segments, axial<=80µm for wires /300µm for pins, arc<=π/24 | Separate circumferential and axial resolution without CAD imprint |

A/B_all preserve the original R3 settings and per-face sizes exactly; native
Restrict fields exclude boundaries for this controlled comparison. Selective
fields include boundaries and apply common counts on curved/quad-required edges;
differences in boundary density are reported, not called a callback-only effect.
All mesh generation is restricted to explicitly visible selected faces and their
CAD boundaries. No other native face may acquire2D elements; no3D elements may
exist. Original CAD volume/face tags and actual owners must match before every run.

For C, periodicity is determined from the saved face's UV bounds and repeated
seam edge; no OCC Boolean/imprint or fabricated descendant mapping. Shared1D
curve nodes are generated once. Source UV grid boundary points must match unique
nodes on their **explicit native boundary curves** within1e-8mm; otherwise STOP
that directional fixture without guessing. Only genuine rectangular periodic
Cylinder/Torus surfaces are seeded; ordinary planes and other faces use native
meshing. Full circumferential seam closure uses shared node IDs, not duplicate
coincident nodes. Thin finite contacts remain distinct source faces.

Acceptance requires an actual native MSH, every selected face area error strictly
<1%, nonzero positive geometric triangles, complete selected-face ownership and
exact1D/2D shared-edge incidence (including repeated seam multiplicity). Every R2
ancestor with all local descendants present receives a separately aggregated area
comparison; new outer polymer faces have no R2 analogue. The previously accepted
R2 high-density mesh is read only as a quantitative reference, never relabeled R3.
No average error may hide one failed face. No global speedup/volume claim follows.

Profiles separate import/source validation, parametrization/curvature API calls,
sizing constraints,1D meshing, source-grid construction, native2D meshing, native
artifact write and independent area/topology validation. Report wall/CPU, peak
RSS, callback counts/body time by dimension/face, triangle/node counts, edge
length/aspect distributions, feature resolution and local conformality. Native
meshing time includes callback bridge/GIL overhead; callback-body time alone does
not measure that crossing. Timed-out ratios are lower bounds, not point estimates.

The run order is A and B variants on leads, bonds, pin/planes/contacts, followed
by C on pin/planes/contacts, bonds, then leads/jackets. A method/area failure is
retained; a source-identity failure stops the campaign. C topology incompatibility
stops C rather than remapping by inference. At most the one preregistered replay
may fix a provable coding defect; failed evidence is never overwritten.

## Preservation and publication gates

Before edits, verified original R3 source/artifact SHA seals and snapshotted93
protected inputs and85 preexisting untracked files, including the R2 mesh cache.
All824 source/378 contact identities,430 source volumes, gas1231.630061168mm³,
polymer0.077162028mm³ and explicit Kovar/Ni/Au axial cap requirements are unchanged.
All laws remain UNSET; no parallel polymer shell/gas path is introduced.

New benchmark/operator sources and exact case list are sealed before execution.
Focused positive/negative geometry/lineage/area/conformity tests, applicable
no-new-PDE regression, archive/master and original frozen hash guards precede
commit/push and exact-commit CI. Actual saved meshes and measured comparison
figures are required; no fictitious fields. Rev3 stays unchanged because local
meshing performance is an internal methods result, not new device physics.

Gmsh native Restrict/MathEval fields follow the
[primary reference manual](https://gmsh.info/doc/texinfo/gmsh.html#Specifying-mesh-element-sizes).
The inspected public manual is newer than pinned4.13.1; options are exercised
in the actual pinned runtime, with no version substitution.

## Results

PENDING; accepted and rejected/censored results will be reported separately.
