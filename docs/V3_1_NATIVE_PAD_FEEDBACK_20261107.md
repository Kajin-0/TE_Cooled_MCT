# V3.1 — Actual native-pad nonuniform heat-feedback closure on the complete working 29/11/4 TEC

**Date:** November 7, 2026. **Previous runnable baseline:** V3 \`e404b141d500550f041cad51f2fbbd636b3d83f8\`.

**Status:** **Numerical PASS within prospectively registered fixed-point, 3D ceramic FEM and complete-system heat/electrical balance tolerances**. Conditional 88-leg axial thermoelectric / original 3D four-ceramic spatial hybrid, **not** full 430-domain 3D electrical/thermal FEM, not material-validated, and not an OEM detector temperature prediction.

## Outputs and reproducibility

- [One source-preserving fully coupled nonlinear driver](../scripts/v3_1_native_pad_feedback.py)
- [Registered complete original operating case](../data/v3_1_native_pad_feedback_20261107/attempt02/registration.json)
- [88 source leg results, actual original-face heat allocations, full I/V/P/T and convergence record](../data/v3_1_native_pad_feedback_20261107/attempt02/result.json)
- [Four actual-source 3D ceramic nodal temperature fields](../data/v3_1_native_pad_feedback_20261107/attempt02/source_native_ceramics_V3_1.npz)
- [Independent read-only source CAD flux and energy check](../data/v3_1_native_pad_feedback_20261107/attempt02/read_only_acceptance.json)
- [Source SHA-256 and failed-attempt evidence manifest](../data/v3_1_native_pad_feedback_20261107/manifest.json)

## Model modification from working V3

V3 calculated the source-specific temperature and heat response of each of the original 88 P/N thermoelectric legs, but each ceramic temperature field still assumed **area-uniform heat deposition**. The source-specific leg heat allocations differed by up to **44.8% in normalized absolute pad-flux distribution on ceramic2's upper face**. V3.1 directly addresses this detected integrated-model limitation.

Preserve all source bodies, accepted 430 CAD domains, saved R3.9 mesh, real 29/11/4 series chain, material assumptions, existing nonlinear 32-cell P/N axial solver, 300 K ambient, 0.40 A drive and 2 mW detector heat. The ceramic solves still use exactly **11,791 native original tetrahedra**, in four real ceramic domains, with assumed constant \(k_{\mathrm{Al_2O_3}}=30\) W/(m·K).

**New two-way local coupling:**

1. Associate every P/N leg to its source **solder → metal network → ceramic–metal CAD pad face**, as in V3. Calculate each leg's hot and cold heat \(Q_h,Q_c\) at its actual 3D pad-average temperatures.
2. On the original ceramic surface triangles, apply **that leg's actual \(Q_h\)** to its hot-pad face and **\(-Q_c\)** to its cold-pad face. Multiple legs sharing one original metal net have their heat contributions summed on its native face.
3. Apply the **Cu-wire heat and half-Joule correction** separately to **ceramic0 original net88 face36**; remove total sink heat through **original underside face6**. The original ceramic1 intermediate net88 contact face74 receives **zero independent source heat** in this simplified model, as no non-leg metal Joule path is spatially modeled. Deposit detector carrier heat on **original ceramic3 upper Au-finish face119**.
4. Assemble **balanced original 3D P1 Neumann FEM heat equations** on each ceramic. To avoid repeated unnecessary 3D matrix assembly/factorization, factorize each source P1 stiffness matrix once and precompute native-face unit-flux influence vectors. At every nonlinear iteration, superpose each real source-face heat load, obtaining local 3D field, every native pad-average temperature, and the plate-average through-temperature response.
5. Feed those local temperatures into all **88 independent nonlinear 32-interval axial P/N solves** and enforce the same complete-stage, interstage, detector and sink equations. Iterate until maximum pad/plate thermal-field update is below **\(2\times10^{-7}\) K** and all stage and total-energy balances satisfy their independently registered numerical gates.

**Limits:** Cu and extra interconnect face heating remain assumed lumped, and other solder/metal junction Joule and Peltier heat are not independently modeled. Each 88-leg P/N transport path is **axial**, not spatially solved 3D current. Only the **four ceramics** have full original-geometry source P1 FEM temperature fields. There is still only **one native global mesh**, no spatial h-convergence, no measured source material grade or contact resistance, no gas/radiation and no as-built temperature validation.

## Results at identical 0.400 A point

| Observable | V3 | V3.1 | Difference |
| --- | ---: | ---: | ---: |
| HgCdTe detector die temperature | 209.688407 K | **209.803293 K** | **+0.114887 K** |
| Terminal voltage | 1.511733 V | **1.513297 V** | **+1.56392 mV** |
| Electrical input | 0.604693 W | **0.605319 W** | **+0.626 mW** |
| Heat rejected to ambient | 0.586082 W | **0.586174 W** | **+0.0919 mW** |

V3.1's eight mean physical-equivalent temperatures, solved with the nonuniform native source-pad distributions, are:

| Location | Calculated V3.1 T |
| --- | ---: |
| Stage0 hot | 303.60807 K |
| Stage0 cold | 265.61594 K |
| Stage1 hot | 266.04086 K |
| Stage1 cold | 235.42711 K |
| Stage2 hot | 235.56837 K |
| Stage2 cold | 209.71717 K |
| Detector carrier | 209.73341 K |
| **HgCdTe detector** | **209.80329 K** |

Actual-source ceramic spatial nodal ranges:

| Original ceramic | Nodal T range | Mean top–bottom temperature difference |
| --- | --- | ---: |
| ceramic0 | 300.841–304.638 K | **0.774865 K** |
| ceramic1 | 265.043–266.438 K | **0.424911 K** |
| ceramic2 | 235.341–235.687 K | **0.141265 K** |
| ceramic3 | 209.714–209.738 K | **0.016244 K** |

The stage0 original power-lead correction is **−21.9017 mW** into original net88 face36, balancing the TEC0 hot-side heat against the radiator heat path; the detector carrier heat enters original face119, and radiator heat exits face6. The selected metal pad and source current mapping is not arbitrary.

## Numerical convergence and scope

The first registered iteration used a loose \(2\times10^{-5}\) K thermal step tolerance and **failed the final stage energy-balance acceptance criterion** after the update. Its failure log and original preregistration are preserved. A separate preflight invocation of attempt02 was rejected by the exact-registration check while synchronizing the tighter source script, before a numerical run. Attempt02 retains exactly the same materials, source faces, case and governing equations, changes the fixed-point stopping condition to **\(2\times10^{-7}\) K** (18 steps maximum) and adds iteration telemetry.

One complete attempt02 nonlinear/spatial coupled solve converged in **11 outer iterations**, with these final gates:

| Check | Recorded |
| --- | ---: |
| Last maximum local pad/plate temperature update | **\(1.3181\times10^{-7}\) K** |
| Maximum plate integrated top/bottom heat imbalance | **\(2.22\times10^{-15}\) W** |
| Maximum original source ceramic free-node P1 weak residual | **\(7.72\times10^{-15}\) W** |
| Maximum full-stage heat balance mismatch | **\(1.32\times10^{-10}\) W** |
| Maximum mean ceramic temperature closure residual | **\(5.09\times10^{-10}\) K** |
| Maximum individual leg energy residual | **\(1.18\times10^{-13}\) W** |
| Global terminal/detector/heat-sink energy residual | **\(1.36\times10^{-10}\) W** |

The read-only acceptance confirms that original source leg-level heat and voltage sum to stage values, all original source-face loads balance at each plate, and initial source mesh and script SHA-256 hashes agree. At finite tolerance the saved last 3D field and the recomputed final bath heat differ by about **\(1.05\times10^{-10}\) W**, within the preregistered hybrid-model limit. Neither weak-form or integrated energy closure establishes h-convergence or the physical validity of the model's assumed coefficients.

**No fresh global mesh and no Codex.** V1, V2, V3 remain runnable separate baselines. The source-Gate B historical P1 **FAIL/STOP**, prospective P2 **STOP**, first P1 actual-couple raw current **FAIL 8/8**, full original 430-domain thermal C/D **NOT RUN**, source real P/N/contact law UNSET, and no as-built detector temperature release remain unchanged.

## Next decision: maintain working-system iteration priority

V3.1 achieves the next identified full-system improvement: **local native-pad thermal feedback now iterates against all actual 88 leg heat flows**. Its effect on the calculated die temperature is only **+0.115 K** under the present conditional material set, after the +0.030 K V2→V3 location-only change.

This does not mean the spatial electrical P/N model is accurate. The next increase in fidelity should be chosen based on a **whole-system output**, ideally a coarse spatial thermoelectric model of the actual 88 legs connected to the current four ceramic fields (preserving one 0.4 A I/V/P/Tdie case), or a targeted exploration of material transport uncertainty if real component data become available. Avoid repeating isolated high-resolution contact diagnostics and do not retroactively pass the original failed raw-gradient criteria.
