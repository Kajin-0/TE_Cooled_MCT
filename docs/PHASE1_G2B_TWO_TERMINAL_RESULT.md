# G2b two-terminal coupled stack

Status: engineering in progress, 2026-10-28. No new coupled result claimed yet.
Starting commit: `d763bcc4ad2ed146556c49b3a8855b95fccc0a98`.
G1, G2a and the original six-port geometry are preserved. The existing `sim`
session and pinned Elmer/Gmsh container are reused, with no unrelated project.

First gate: design two internal insulated routing links, Boolean-fragment and
audit the actual mesh for one path through all 88 legs and only two terminals.
Only after that gate will real 3D coupled T/phi cases, positive/zero/negative
drive, actual top-face heat load and a mesh study be attempted. Internal ceramics
remain unconstrained thermal domains. Routing, stage allocation and material
profiles are assumptions; OEM calibration and the complete package are excluded.

Topology gate passed on the first 0.18 mm mesh: 26,120 nodes, 100,463 tetrahedra,
52,240 coupled nodal DOFs and 189 domains. The actual conductor graph has 181
vertices / 180 edges, exactly two degree-one terminals, every internal vertex
degree two and one occurrence of each of the 88 legs. Independent orthogonal CSG
subtracts Cu from alumina and verifies exact volumes/contact areas against OCC
and tetrahedra. No Cu overlap, unwanted conductor face/edge/point contact or
nonmanifold tetra face was found. Minimum SICN = 0.122823, no elements below 0.01.
The two links use buried Cu in explicitly modeled alumina ribs, plate channels
and exit collars; the original six-port geometry remains unchanged. The ribs
introduce real thermal shunts and will participate in the coupled solve.
