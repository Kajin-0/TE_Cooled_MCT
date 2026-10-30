# Independent bath-flux localization — scoped numerical result, 2026-10-30

**Full G3b remains NOT QUALIFIED.** The unchanged original raw-gradient criterion
is `abs((Qdirect - Pexternal)/Pexternal) < 0.01`. No recovered flux, reaction,
reference benchmark or temperature insensitivity replaces that gate.

`flux_presolder_diagnosis` reads immutable actual archived mesh/VTU pairs for the
accepted 907-patch coarse case and all three rejected converged fine cases. It
checks the entire older source/evidence chain and the unchanged Revision 2 PDF,
compressed/uncompressed field hashes, bijective node mapping and unordered actual
tetrahedra. No original postprocessor is invoked and no baseline file is written.

Gradients are reconstructed by inversion of each tetrahedron's affine coordinate
matrix, independently of the baseline cofactor routine. Actual one-sided cell
owners determine triangle normals; every bath normal points in -z. The bath is
planar, and every bath-adjacent body is Kovar. Its constant k17.3 and S0 make the
raw total heat flux exactly Fourier flux there, with exact triangle quadrature.
The bath nodal star also includes glass; its conductivity jump is retained.
Tiny computational electrical work is included. The star contains no TEC,
detector source or nonlocal endpoint/surface source support. The nonlocal sparse
weights are explicitly checked to have zero columns at bath nodes.

The external input is independently reconstructed from the actual terminal
potential difference, imposed current, detector load and two Cu lead I²R terms.
Both raw flux and the FE nodal reaction reproduce the earlier archived estimates
to below 1 nW. No sign, orientation, face-owner, material coefficient or omitted
bath-source defect is found in these checks. This does not prove the complete
Fortran/device model is physically accurate.

| Mesh/case | Raw error (%) | Direct minus reaction (mW) | Reaction minus input (nW) |
|---|---:|---:|---:|
| Accepted coarse | +0.420149927 | +0.234796770 | +0.329230 |
| Global fine, rejected | +1.655872526 | +0.925827222 | +1.438377 |
| Bath-refined, rejected | +1.514121595 | +0.846572438 | +1.466900 |
| Feedthrough-refined, rejected | +1.583834511 | +0.885551109 | +1.295928 |

## Physical partition and interpretation

Bath triangles are partitioned disjointly into: the mount footprint (|x|,|y| <=
3.2mm), Kovar within 1.1mm of each of nine seal centres, 0.6mm neighborhoods of
mount-hole edges, the outer flange (elliptical radial coordinate >0.9), and
remaining Kovar. Seal neighborhoods have precedence, then the footprint, hole
edges and outer edge. The curved flange has no geometric corners to invent.
Glass annuli and metal pin roots are explicit **zero-bath-area regions**, because
those surfaces are not Dirichlet bath faces. They can still affect bath nodal
reactions through their shared mesh.

For a descriptive local comparison, each bath node's FE reaction is distributed
to incident bath triangles in proportion to area/3. This is a conservative nodal
allocation, not an exact or uniquely defined local continuum heat flux. Region
boundaries affect its attribution. CSV records retain area, direct power,
allocated reaction, signed difference in W and normalization by external input.

For the last rejected fine case, the largest signed contributions are:

| Region | Direct minus allocated reaction (mW) | Fraction of external input (%) |
|---|---:|---:|
| Kovar away from listed neighborhoods | +0.458964 | +0.820869 |
| Seal-adjacent Kovar, instance3 | +0.307425 | +0.549839 |
| Mount footprint | +0.112362 | +0.200963 |
| Outer flange edge | +0.013425 | +0.024012 |

The error is not restricted to one feedthrough annulus. The coarse distant-Kovar
contribution is negative (-0.459164mW), whereas it is positive on fine meshes.
Cancellation in the coarse integrated flux therefore does not establish local
flux convergence.

## Exact discrete residual identity

Let w be the continuous P1 nodal indicator equal to one at bath nodes and zero
elsewhere. In the passive bath star, q=-k grad(T), each element has constant q,
and work density is sigma|grad(phi)|². Elementwise integration by parts gives

`Qreaction = Qbath,raw + Qother-exterior,weighted + Qinternal-jump,weighted + integral(work*w)`.

Face traces use the exact linear mean of w. Every internal face has both owner
contributions; artificial star-cut faces have zero trace. Other exterior terms
include raw gradients on nominally insulated surfaces and are not presumed zero.
No detector/nonlocal source acts on w in these particular archived cases.

| Case | Other exterior term (mW) | Internal jump term (mW) |
|---|---:|---:|
| Coarse | -0.085276550 | -0.149520220 |
| Global fine | -0.069657192 | -0.856170030 |
| Bath refinement | -0.070746104 | -0.775826334 |
| Feedthrough refinement | -0.059660149 | -0.825890960 |

Volume electrical terms are about1e-17W, and identity closure is <=1.4e-17W.
Thus weighted P1 internal flux jumps dominate the fine raw/reaction discrepancy.
This is a discrete consistency/localization identity, **not an independent error
reference, proof of root cause, or recovered-flux qualification**.

## Independent manufactured 3D junction benchmark

A separate three-material column has a 1.1mm height, pin radius0.22mm, glass outer
radius0.55mm and outer Kovar radius1.3mm. Interfaces are conformal64-sided
polygons; their common area defect versus the circular geometry is -0.160561% and
is reported separately. The fixed triangular base is radially nonuniform; axial
layers are refined independently. A fixed global prism diagonal prevents hanging
faces. The finest coupon has12,545 nodes and61,440 tetrahedra.

The analytic solution is `T=300 + delta*z/L + a*(z/L)*(1-z/L)` with body source
`2*k*a/L²`, prescribed end temperatures and insulated sides. It has continuous T
and zero normal heat flux across vertical material interfaces. Linear delta=+10K
and reverse delta=-10K source-free checks verify signs to about2.4e-13 relative.
For delta10K,a5K, exact bottom heat is `(delta+a)*sum(k_i*A_i)/L` on the actual
polygonal geometry. Raw P1 flux errors are -4.166667%,-2.083333%,-1.041667% and
-0.520833% at8/16/32/64 layers: only the last passes the original1% raw criterion.
The experiment's benchmark PASS describes agreement with the analytic truncation
law and conservation; it does not relabel the three coarser raw errors as passes.

A separate three-plane, temperature-only one-sided quadratic derivative recovers
the analytic boundary flux within2.5e-12 relative. It uses no FE reaction or input
power renormalization. **It is valid here for the aligned quadratic family, not
an equilibrated RT0 reconstruction or a qualified arbitrary package flux.**
Normal heat flow through planar material jumps is independently exercised by the
presolder slab coupons. Combined tests do not resolve a general3D curved,
protruding-pin corner with transverse and axial flow. General conservative patch
recovery and systematic bath-normal device refinement remain pending.

Two initial driver attempts are retained: an output-VTU-location postprocessing
failure after a genuine solve, and a curved automatic mesh that hit the declared
300,000-tet coupon cap before another solve. A deterministic structured radial
mesh enabled the bounded benchmark without raising that cap. See the combined
result and reproduction notes for execution/status provenance.
