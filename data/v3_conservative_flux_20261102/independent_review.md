**A. Target and inspected scope**

Independent read-only numerical audit of clean `main` at **b2be51921d323ef5b049e087e1e37afc78860f15**, limited to the separately registered local electrical conservative-discretization attempt.

I inspected the current contract, chronology, technical record, preregistration, sealed sources, RT0/control/geometry/study/audit implementations, saved results, failure log and both figures. I independently calculated geometry, face coverage, field reconstruction and losses from saved arrays without solving anything.

All **65 review-packet hashes and 132 preregistered hashes matched before and after**. HEAD/status remained unchanged and clean through **2026-11-02T23:49:58Z**. These checks include the protected original STEP, coupon inputs/fields and Rev3. I inspected the recorded 5,401-blob guard result; I did not rerun that guard.

No tests, controls, meshing, PDEs, writes, sessions, issues or PR changes occurred. `sim:0.0` was left untouched. Complete assembly physics, vendor diagrams and hardware were not re-reviewed.

**B. Verdict**

**STOP local electrical qualification.**

| Scope | Verdict |
|---|---|
| Prospective source/input sealing | **PASS**, recorded timing and exact identities |
| RT0 basis, mass and finite-contact equations | **Consistent on inspection**, limited by shared implementation |
| Saved analytic-control criteria | **PASS**, source/formula and summary checks |
| L1 geometric fidelity and face coverage | **PASS**, independently recalculated |
| Raw P1 current/voltage qualification | **FAIL** |
| Recovered-field irreversible-loss criterion | **FAIL** |
| Retained mixed cell-potential boundedness | **FAIL**, additional quantitative witness |
| Direct-mixed coupon flux/current/loss comparison | **NOT QUALIFIED: flux export lost** |
| L2 and refinement | **NOT RUN** |
| Thermal C/D | **NOT RUN / NOT AUTHORIZED** |

[Exact-commit CI run 41548045677](https://github.com/Kajin-0/TE_Cooled_MCT/actions/runs/41548045677) independently reports **completed / success** for the audited SHA. That software result does not qualify the stopped numerical experiment.

**C. Severity-ranked findings**

**CF-01 — Critical numerical qualification failure: accurate geometry and conserved recovered current do not establish electrical accuracy.**

Witnesses: [raw result](/home/User/TE_Cooled_MCT/data/v3_conservative_flux_20261102/geometry/L1_field/P1_raw.json), [retained alternatives](/home/User/TE_Cooled_MCT/data/v3_conservative_flux_20261102/geometry/L1_field/alternative.json), [flux evaluation](/home/User/TE_Cooled_MCT/tecooledmct/v3_flux_rt0.py:135).

The saved raw result has **81.241662%** worst cut mismatch versus **0.1%**. Its minimum potential, independently read from the saved field, is **−4.282997e−7 V**, below **−1e−8 V**.

Using an independent tetrahedral-moment integral rather than the producer’s four-point loss quadrature, I obtain:

\[
I=34.005243342578\ {\rm A},
\]

\[
P_{\rm bulk}=32.136426110056\ {\rm W},\qquad
P_{\rm contact}=2.130369796692\ {\rm W}.
\]

At unit excitation:

\[
\frac{P_{\rm bulk}+P_{\rm contact}}{IV}-1
=0.007691536318.
\]

Thus the retained recovery fails the **0.5%** loss criterion with **0.769154%** mismatch. Its cell balance is approximately **3.876e−14 relative**, and terminal closure is near roundoff. Those constraints do not establish constitutive accuracy.

**Minimum closure, proposed only:** a separately authorized numerical successor must meet the unchanged raw, loss, voltage and refinement gates. Neither fitting coefficients nor substituting conservative flux for the raw gate closes this finding.

**CF-02 — High: method-label overwrite destroys the paired direct-mixed export.**

Locations: [outer method loop](/home/User/TE_Cooled_MCT/tecooledmct/v3_flux_study.py:43), [name overwrite](/home/User/TE_Cooled_MCT/tecooledmct/v3_flux_study.py:68), [exports](/home/User/TE_Cooled_MCT/tecooledmct/v3_flux_study.py:76), [failed return](/home/User/TE_Cooled_MCT/tecooledmct/v3_flux_study.py:88).

The interior-cut loop replaces `name` with `lead9`. Both methods consequently write the same keys/file. Recovery runs last and overwrites the mixed flux, current field and result dictionary. The subsequent `results['mixed']` access raises the recorded `KeyError`.

This is an implementation/data-retention defect. It is not evidence that the missing mixed flux numerically failed or passed. The surviving `lead9_q`, `lead9_J` and VTU cover the **whole recovered coupon**.

**Minimum closure, proposed only:** a separately versioned producer needs distinct method identifiers and output-schema checks before another authorized attempt. Preserve this producer and its artifacts unchanged; do not reconstruct the missing field with another solve.

**CF-03 — High: surviving mixed cell potentials independently fail boundedness.**

The first iteration’s cell potentials survive as `lead9_cell_V`: the recovery iteration has `pressure=None` and does not overwrite that array. Its 207,396 entries have:

\[
V_{\min}=-2.65228085795\times10^{-5}\ {\rm V},\qquad
V_{\max}=0.999982465557\ {\rm V}.
\]

The minimum violates the frozen **−1e−8 V** floor. Missing mixed flux prevents its current/loss assessment, but does **not** erase this independently observable voltage failure.

**Minimum correction:** explicitly record this additional retained failure in a successor receipt while preserving the original record. Any numerical remedy requires separate authorization and qualification.

**D. Evidence and limitations**

The RT0 basis \(\phi_i=(x-v_i)/(3|K|)\) has unit outward integrated face flux. The tetrahedral covariance factor \(1/20\), resistivity-weighted mass and contact diagonal \(r_e''/A_f\) are consistent with their stated equations and SI units. Shared oriented face currents enforce normal continuity; cell incidence enforces divergence balance. This agrees with the relevant [RT element definition](https://defelement.org/elements/raviart-thomas.html) and [mixed-Poisson framework](https://docs.fenicsproject.org/dolfinx/main/python/demos/demo_mixed-poisson.html).

The mixed solve uses terminal potentials independently of P1 current. Recovery explicitly constrains that current. Both paths share RT0 basis/mass code, so their agreement is not independent software certification.

Control fields were not archived—only case summaries and gates remain. I checked their source formulas and numerical gate arithmetic, but could not independently reconstruct their reported L2 integrals from saved control fields. No controls were rerun.

Material/contact values remain the original selected hypotheses. This numerical audit adds no measured plated-film transport, interface characterization or physical assembly acceptance.

**E. Independent quantitative checks**

The saved L1 mesh contains **65,004 nodes and 207,396 positive tetrahedra**, minimum volume **3.09842e−18 m³**. I independently obtain:

- Total volume error: **−0.0848746531%**, passing 0.25%.
- Largest domain error, lead9: **−0.1183480573%**, passing 0.5%.
- Complete unique physical-face coverage; maximum incidence two.
- Recovered field reconstruction difference: **5.9043e−15 relative**.
- Raw P1 reconstruction difference: **1.1781e−13 relative**.

All sixteen saved control cases satisfy their recorded criteria. Maximum uniform flux error is **3.4330e−10**. Finest harmonic L2 errors are P1 **1.94038%**, recovery **2.13415%**, mixed **2.11167%**, with reductions **2.0000**, **1.9794**, **1.9358**. Recovery does not outperform P1 in this benchmark.

The **23:32:22.040577Z** registration precedes the control execution recorded at **23:32:50.231016Z** after 2.925 seconds. Sources/snapshots remain exact, and the controller checks seals before numerical phases. This prospectively addresses sealing for this attempt; historical V3ET-04 remains unchanged.

**F. Disposition**

The external controller correctly stopped after the first coupon exception. L2, resistance/interface-loss refinement and thermal C/D remain unexecuted. The documentation candidly preserves the output defect and numerical STOP; it should additionally disclose CF-03’s surviving mixed-potential failure.

No current rating, independent recovered resistance, full TEC resistance, thermal partition, temperature or device-performance claim follows. No new campaign is authorized by this review.

[Issue #2](https://github.com/Kajin-0/TE_Cooled_MCT/issues/2) was independently confirmed **OPEN** and must remain open. Preserve all earlier verdicts, failures and immutable artifacts.
