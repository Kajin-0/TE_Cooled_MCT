# V3 R3.16 — Native CAD contact with finite interfacial resistance: P1/P2 transmission and nonlinear field audit

**Local milestone date:** November 5, 2026. **Baseline:** `040b6a36e0b207ed361171527c2f225f83a45750` (R3.15).  
**Verdict:** **PASS** on a deliberately synthetic, mathematically specified finite-contact scalar diffusion problem, with independent contact-law/flux and high-order H¹-error verification. **No real physical contact resistivity, transport constitutive law, full-device electrothermal PDE, or mesh convergence has been qualified.**

## Experiment and immutable CAD/mesh source

The geometric source is the existing conforming R3.9 full-package mesh, narrowed without remeshing to **native CAD face 2349** joining **region 410** (`COMPOSITE_MULTILAYER`, source `det8_wedge_foot`) to **region 420** (`Au`, source `detector_bond8`). There are **26,053 source TET4 elements** and **6,908 unique source geometric vertices** across both regions, and the interface comprises **48 exact registered native TRI3 facets** with **49 source vertices**. The entire physical original face geometry, 430-domain CAD material ownership, original node coordinates, and 378 contact witnesses remain unchanged.

The R3.15 ideal transmission experiment used *one continuous field* shared across both source volumes. R3.16 deliberately uses **separate field degrees of freedom on either side of the same geometric contact**: P1 has **6,957 scalar DOFs** (including 49 additional interface-side vertex values) and P2 has **46,806 scalar DOFs** (region-specific edge DOFs are also separated at face 2349). No physical gap, interface volume, duplicate geometric tetrahedron or displacement of any original source face was introduced. The contact is represented by a positive-semidefinite surface bilinear form rather than forced pointwise continuity.

## Registered artificial contact law and sign convention

In the *mathematical unit scalar diffusion problem*, set

\[
k_{410}=1,\quad k_{420}=10,\quad G_c=5,\quad Q=1
\]

in mutually consistent arbitrary units. **These numbers are synthetic test coefficients and must not be used as gold conductivity, wedge-foot conductivity, or actual contact conductance.**

Let the outward normal of region 410 on native face 2349 be \(\mathbf n_{410}=+\hat z\), with \(\mathbf n_{420}=-\hat z\), and let \(\mathbf q_r=-k_r\nabla u_r\). The contact law is

\[
\mathbf q_{410}\cdot\mathbf n_{410}
=G_c(u_{410}-u_{420}),
\qquad
\mathbf q_{410}\cdot\mathbf n_{410}
+\mathbf q_{420}\cdot\mathbf n_{420}=0.
\]

The positive interface stiffness term is \(G_c\int_\Gamma(u_{410}-u_{420})(v_{410}-v_{420})\,dA\), assembled over the original **48 conformal triangles** using their geometrically identical two-sided but separately numbered field traces.

The exact piecewise manufactured solution is

\[
u_r=A[(x-x_0)^2+(y-y_0)^2]+B(z-z_0)^2
+\frac{Q}{k_r}(z-z_0)
-\mathbb{1}_{r=410}\frac{Q}{G_c}
+\beta\sin(\omega(y-y_{\min})).
\]

For the polynomial case \(\beta=0\); for the non-polynomial case \(\beta=0.25\). The other registered parameters are \(A=0.025\), \(B=0.05\), \(x_0=-0.35\,{\rm mm}\), \(z_0=5.7849\,{\rm mm}\), and \(\omega=\pi/\max(\Delta y,0.05\,{\rm mm})\). Each region has analytic forcing \(f_r=-\nabla\cdot(k_r\nabla u_r)\). Source CAD face 2399 retains exact manufactured Dirichlet values, and every other *external* regional facet receives analytically computed Neumann flux. The internal face 2349 is **not** assigned an exterior Neumann load.

The exact interface properties are:

\[
u_{410}-u_{420}=-Q/G_c=-0.2,\quad
k_{410}\partial_z u_{410}
=k_{420}\partial_z u_{420}=Q,
\quad
\mathbf q_{410}\cdot\mathbf n_{410}=-Q.
\]

Thus a **nonzero potential jump is required**, not a continuity error. The test explicitly verifies both Robin and two-sided normal-flux conditions.

## Measured numerical results

All four registered P1/P2 cases use the same original geometric TET4 elements. They pass the unpreconditioned true relative residual criterion \(\|Au-b\|_2/\|b\|_2<10^{-8}\) under SciPy ILU-GMRES with no artificial contact anchoring or source-mesh modifications.

| Result | P1 polynomial | P2 polynomial | P1 non-polynomial | P2 non-polynomial |
| --- | ---: | ---: | ---: | ---: |
| Free field DOF | 3,885 | 34,614 | 3,885 | 34,614 |
| ILU-GMRES iterations | 7 | 11 | 7 | 11 |
| True relative algebraic residual | 7.69×10⁻¹⁰ | 1.02×10⁻¹¹ | 6.93×10⁻¹⁰ | 8.33×10⁻¹² |
| Mean contact jump \(u_{410}-u_{420}\) | −0.2000000 | −0.2000000 | −0.2000000 | −0.2000000 |
| Interface normal-flux imbalance, relative RMS | 0.0359276 | **3.70×10⁻⁹** | 0.0359269 | **4.73×10⁻⁷** |
| Robin-law mismatch, relative RMS | 2.327×10⁻⁴ | **2.11×10⁻⁹** | 2.317×10⁻⁴ | **2.96×10⁻⁷** |
| Relative H¹ gradient error, independently checked | 0.00663209 | **1.38989×10⁻⁸** | 0.00792821 | **3.02875×10⁻⁵** |

For the **non-polynomial** field, independent H¹ error falls by **261.76×** when switching from P1 to P2. The interface Robin mismatch and normal-flux error are below \(10^{-6}\) relative for P2. This is a substantive accuracy improvement beyond pure quadratic polynomial representability, although still measured on only one fixed geometric mesh and one smooth manufactured field.

The complete four-solve benchmark took **7.679 seconds**, with **362.4 MiB** peak Python RSS, within a 4-CPU/8-GiB recovered FEM Docker runtime and its 300-second hard limit. No Codex usage or additional compute capacity was required.

## Independent audit and two preserved failures

The original registered preflight encountered a **code-level face-incidence classification error**, incorrectly counting interior faces of the same region as cross-material interface faces. This stopped before any FEM result. The corrected test counts only faces incident to *two different source material regions*.

The next solver run obtained algebraically convergent solutions but failed the independent physical sign convention: a positive-definite interface contact matrix produced a **negative contact-potential jump**, while the initially specified manufactured field had prescribed the opposite sign. This is a real manufactured-law **FAIL** and is archived unchanged. The corrected source uses the standard diffusive flux \(\mathbf q=-k\nabla u\) and the exact jump \(-0.2\). There is no physical remeshing or material-law substitution.

A separate [independent audit](../data/v3_r316_finite_contact_20261105/attempt02/independent_contact_audit.json) reads all four saved scalar field coefficient vectors, reconstructs both interface faces from the original tetrahedral regions, and independently recomputes the one-sided normal-gradient flux, Robin residual, interface potential jump and volume H¹ gradient errors. It uses **216 tetrahedral integration points per cell** (6×6×6 Duffy Gauss–Legendre) instead of the primary four-point tetrahedral rule.

The independent verification found an additional numerical issue: the original **four-point H¹ rule underestimates the non-polynomial P2 error by 21.64% relative to the primary estimate**. It reported \(2.48984\times10^{-5}\) where the independent 216-point integration reports \(3.02875\times10^{-5}\). This discrepancy is preserved, and **the high-order value is authoritative**. All contact-potential and flux metrics agree across the primary and independent implementations; the quadratic cases' H¹ results agree at the expected numerical precision.

R3.16 evidence is preserved under [the SHA-256 source-and-result manifest](../data/v3_r316_finite_contact_20261105/attempt02/manifest.json), including the failed sign case, first classification error, separately preserved corrected source, coefficient vectors, audit sources and logs. The older R3.15 ideal-contact benchmark and all earlier failures remain untouched.

## Scientific interpretation and next gate

**Qualified:** the real native two-region interface and its preserved conformal TRI3 facets can support **separate scalar field traces**, a positive finite-conductance Robin coupling, a nonzero intended potential jump, a normal-flux conservation check and independently measured non-polynomial P1/P2 approximation error. This is a mathematical scalar benchmark and establishes useful software infrastructure for finite contact laws.

**Not qualified:** actual contact resistivity, gold/composite conductivity or anisotropy, thermoelectric Seebeck/Peltier effects, Joule heat, mechanical/thermal interface conductance, full 430-domain conservative PDE, mesh spatial convergence, real TEC temperature or detector performance. Actual contact coefficients and physical interface model must be specified and independently verified before extrapolating this result.

**Recommended next gate:** a *network conservation* exercise across more than one actual contact interface, plus a non-polynomial manufactured solution with **spatially varying normal contact flux**. This would test conservation beyond a constant-\(Q\) local interface and a single source material pairing. A physically parameterized multi-material electrical/thermal model remains separately gated.

The original 824-solid physical STEP, canonical 38-page Rev3, source R3.8–R3.15 meshes, all 320,522 original surface facets, 378 finite-contact witnesses, historical R3.3/R3.4 failures and issue #2 remain preserved. **Electrical Gate B stays STOP; thermal gates C/D remain NOT RUN.**
