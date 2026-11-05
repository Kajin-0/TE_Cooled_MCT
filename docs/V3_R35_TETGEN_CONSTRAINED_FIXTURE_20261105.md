# V3 R3.5 — Facet-preserving constrained tetrahedralization fixture

**2026-11-05 • Baseline:** `c40cb394ac2be5bff72e1f1a6e20bfb3f07a55ec`  
**Result: PASS for the refined three-material curved fixture; whole-package 3D remains NOT RUN / NOT QUALIFIED.**

This is the bounded successor to the [R3.3–R3.4 surface/volume handoff investigation](V3_R33_R34_SURFACE_VOLUME_HANDOFF_20261105.md). No physical 824-solid CAD STEP, 430-domain R3 BREP, 320,522-triangle saved R3.3 surface, source-to-material map, prior failed mesh, issue #2, solver field, or canonical Rev3 report has been changed. The goal is to demonstrate a *genuine constrained PLC tetrahedralizer*, without implicit Gmsh surface remeshing.

## Method and reproducibility

A separate locally compiled TetGen executable was built from the publicly available libigl/tetgen source, pinned to Git commit `e05aca7df74e3f531bc35733ed87d36d437266c5`. Compilation is recorded in the [evidence manifest](../data/v3_r35_tetgen_plc_20261105/manifest.json), including executable SHA-256. No system installation or modification of the existing FEM Docker image was required.

The representative native Gmsh CAD fixture is a **0.400 mm-long coaxial copper core (radius 0.100 mm), 15 µm radial polyimide shell (outer radius 0.115 mm), and gas annulus (outer radius 0.220 mm)**. The volumes are fragmented to share conformal CAD faces. A *single* set of triangulated surfaces with distinct native-face identifiers is exported as a TetGen PLC; material-region seed points and attributes 1/2/3 identify copper, polyimide and gas.

The key TetGen invocation is `tetgen -pYYA -V coaxial_15um.poly`. `-p` reads the PLC, `-YY` requests preservation of the original boundary facets (including internal facets), and `-A` assigns material-region attributes. We **independently compare the output** rather than taking the flag as proof. Output tetrahedra are analyzed from the saved `.1.node`, `.1.ele`, and `.1.face` tables using the saved Python validator. Gmsh is used only to generate this fixture's input surface, not to regenerate its faces during TetGen volume meshing.

## Experiment outcomes

Two strictly separate fixture runs were retained. The coarse trial **failed the registered volume gate**, even though facet identity, region assignments and positive Jacobians held. One finer-curvature fixture was then attempted with smaller surface sizing (Gmsh minimum 0.007 mm, maximum 0.022 mm versus initial 0.012–0.035 mm).

| Measure | Coarse fixture | Refined fixture |
| --- | ---: | ---: |
| Input/output facet count | 2,960 / 2,960 | **7,106 / 7,106** |
| Tetrahedra | 6,315 | **15,676** |
| Copper-domain tetrahedra | 1,248 | 3,367 |
| Polyimide-domain tetrahedra | 1,722 | 4,357 |
| Gas-domain tetrahedra | 3,345 | 7,952 |
| Copper CAD-volume error | **−1.4595% — FAIL** | **−0.5670% — PASS** |
| Polyimide CAD-volume error | +0.1654% | **−0.0546%** |
| Gas CAD-volume error | −0.01572% | **−0.00295%** |
| Lost/added input facets | 0 / 0 | **0 / 0** |
| Moved original nodes | 0 | **0** |
| Incorrect interface material owners | 0 | **0** |
| Duplicate output facets | 0 | **0** |
| Nonmanifold tetrahedral face incidence | 0 | **0** |
| Nonpositive signed tetrahedra | 0 | **0** |
| **Overall strict fixture gate** | **FAIL (core volume)** | **PASS** |

Surface-facet equality is established by comparing the original and output *sorted node-triplet multisets*, with per-face markers; internal material boundaries are checked against tetrahedron-side material attributes, not merely exterior surface counts. The refined output has 518 input triangles on the copper/polyimide interface and 608 on polyimide/gas; every input facet corresponds to the expected tetrahedral external or two-region interface facet. Three nonempty material attributes are verified.

### Tetrahedron shape quality: positive but poorly conditioned elements

Mean-ratio normalized shape quality was computed on each saved tetrahedron:
\[
q = \frac{12(3V)^{2/3}}{\sum_{e=1}^{6}\ell_e^2},\quad q_{\mathrm{regular}}=1.
\]

| Shape metric | Refined fixture |
| --- | ---: |
| Minimum | **0.008017** |
| 1st percentile | 0.021237 |
| 5th percentile | 0.108752 |
| Median | 0.306244 |
| 95th percentile | 0.957785 |
| q < 0.01 | 18 tets |
| q < 0.05 | 377 tets |
| q < 0.10 | 676 tets |

The positive-volume/shape gate passes, but the poor low-end element quality **does not** establish adequate solver conditioning, convergence or practical meshing of the complete package. More rigorous pre-3D qualification should impose or justify a quantitative quality floor. Do not infer that the 430-domain model can be meshed within the 3-million-tet / 8-GiB / finite wall-time constraints.

## Archive and next gate

The evidence package at [`data/v3_r35_tetgen_plc_20261105/`](../data/v3_r35_tetgen_plc_20261105/manifest.json) includes both inputs and exact validator source; the refined case additionally contains the four native TetGen output tables and independent quality distribution. Its [manifest](../data/v3_r35_tetgen_plc_20261105/manifest.json) includes per-file SHA-256, pinned TetGen source commit and build binary hash. Historical R3.3/R3.4 STOP files remain untouched.

**Next engineering gate:** investigate *quality-constrained* tetrahedralization of the same curved three-material fixture without changing any of the 7,106 registered surface facets; explicitly test interface ownership, element Jacobians, solver conditioning proxies and material-volume accuracy. If quality remains marginal, evaluate a controlled anisotropic/tetrahedral strategy with explicit limitations rather than discarding thin polymer or metal domains.

Before another global run: construct and read-only audit a 430-region PLC from the protected R3.3 mesh, including an unambiguous region seed inside each actual CAD volume, exact 2D facet markers, complete internal face ownership, all 378 finite contacts, no duplicate facets, and a credible estimated memory/tetrahedron budget. **No whole-device 3D mesher, PDE, electrical Gate B retest, or thermal C/D solve was launched in this milestone.** The frozen canonical Rev3 and open issue #2 remain unchanged.
