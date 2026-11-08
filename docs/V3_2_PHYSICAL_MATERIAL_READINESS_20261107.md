# V3.2 — Physical-material evidence gate for the working TEC model

**Date:** November 7, 2026. **Parent working checkpoint:** commit \`1fe7cbe\`. **Decision:** preserve the already running, increasingly detailed V1–V3.2 29/11/4 TEC/detector solvers; prioritize **evidence for the actual P/N material** before more FEM refinement.

**Result:** the current transport law is *source-traceable as a conditional research analog*, but **FAIL-CLOSED as a qualified material model for the actual installed TEC**. The source is not a physically calibrated commercial P/N pair, and the first-stage hot boundaries exceed the research curve's published 300 K upper bound.

## Physically sourced evidence and executable contract

- [Existing active source table, unmodified](../data/g2c/zhang2025_he_40_300_v2.json), provenance DOI [10.1088/0256-307X/42/5/056304](https://doi.org/10.1088/0256-307X/42/5/056304)
- [Active numerical model's source interpolation / extension, unmodified](../tecooledmct/graded_tec.py) and [unmodified nonlinear 32-slice transport](../tecooledmct/nonlinear_tec.py)
- [Saved V3.2 88-leg original geometry, actual solved leg end temperatures and full I/V/Tdie/E](../data/v3_2_joint_loss_feedback_20261107/attempt01/result.json)
- [One-run read-only complete material-source physical readiness audit](../data/v3_2_material_readiness_20261107/attempt01/material_contract.json)
- [Source hash and engineering gate audit implementation](../scripts/v3_2_material_readiness_contract.py)
- [Structured manufacturer/experimental P/N candidate input template](../data/v3_2_material_readiness_20261107/attempt01/candidate_INGEST_TEMPLATE.json)
- [Evidence-gated candidate intake validator](../scripts/v3_2_material_candidate_validator.py)
- [Intentional rejection of the empty candidate template (11 specific missing evidence items)](../data/v3_2_material_readiness_20261107/attempt01/candidate_template_rejection.json)
- [Source-hashed, immutable evidence manifest](../data/v3_2_material_readiness_20261107/attempt01/manifest.json)

## What exactly is published vs assumed?

The active source is the existing Zhang et al. (2025) publication digitization. Its **two research specimens** are:

| Transport specimen | Composition | Processing | Source-matched to TEC |
| --- | --- | --- | --- |
| N-HE-1 | Bi₂(Te,Se)₃ | Hot extrusion | **Not established** |
| P-HE | (Bi,Sb)₂Te₃ | Hot extrusion | **Not established** |

Each source specimen has published **\(S(T)\), \(\rho(T)\), and \(k(T)\)** markers converted to SI units. The six source curves contain **14 markers each, 84 markers total** over **40–300 K**. The table uses piecewise-linear interpolation between digitized markers. These are **digitized published figure-marker positions**, **not directly measured raw instrument data**. Attached source values include figure-axis/marker-reading bounds (e.g., temperature-axis reading uncertainty \(\sim1.3\) K), which **do not** quantify original instrument errors, sample-to-sample variation, batch-level manufacturing variation, aging or mismatched specimens. Do **not** interpret digitization error as physical confidence in the actual module.

There is **no record establishing that either research specimen is the exact installed TEC grade or batch**, or that these two specimens were ever paired as a manufactured device. Existing OEM identification is a *proprietary high-grade hot-extruded Bi–Te* family description, not a verified full six-curve grade match.

### Source temperature coverage versus actual working V3.2

The original saved 88 source leg temperatures have the following boundary ranges:

| Original stage | Individual P/N legs | Hot contact range (K) | Cold contact range (K) | Legs with hot boundary above 300 K |
| --- | ---: | ---: | ---: | ---: |
| 0 | 58 | **302.213–304.615** | 265.195–266.261 | **58** |
| 1 | 22 | 265.706–266.524 | 235.551–235.688 | 0 |
| 2 | 8 | 235.676–235.830 | 209.901–209.902 | 0 |
| **Total** | **88** | | | **58** |

Source plot coverage ends at 300 K. For \(T>300\) K, the current code uses

\[
f(T)=f(300\,\mathrm K)+(T-300\,\mathrm K)\,
0.25\,f'_{\mathrm{last\ plotted\ segment}}(300\,\mathrm K),
\quad f\in\{S,\rho,k\}.
\]

**The 25% terminal tangent extension is a modelling assumption, not an extrapolation supported by the paper.** The highest hot source pad is **304.615 K**, so the active solver requires up to **4.615 K** of extension beyond the source curves. Exactly **58/88** leg hot boundaries are above 300 K. Individual nonlinear axial 33-point temperature profiles are **not re-solved in this audit**, so any *reported linear-interpolation* fraction of leg length above 300 K is **only a boundary-temperature proxy**, not an exact local thermoelectric temperature-field measurement.

The active solver accepts model temperatures 180–390 K, but only the subset through 300 K is supported by the published research-curve digitization. The 300–390 K extension is a code-domain provision, **not validated material coverage**.

## Next source evidence needed before physical model release

A proper material source should provide, **for both P and N legs**, the installed TEC manufacturer/module identification, grade or lot IDs, consistent hot/cold current and thermopower sign conventions, and six *temperature-dependent* \(S(T)\), \(\rho(T)\), \(k(T)\) curves with measurement provenance across at least the **actual 209.901–304.615 K working temperature interval**. Prefer full practical margin 200–305 K. The curves must include verified SI units, ordered temperature nodes, uncertainty of source measurements (not only graph reading bounds), source/citation IDs and actual module grade-pair evidence.

The new candidate validator requires at least three ordered, traceable points per curve and complete current temperature coverage before it can even return **SCHEMA_COMPLETE_PENDING_INDEPENDENT_GRADE_AND_MEASUREMENT_REVIEW**. It **never** automatically approves the device grade or mutates V3.2, even if all six data schemas pass. Actual source/grade authenticity, measurement conditions, fit quality, constitutive-law compatibility and module I/V vs temperature/load still require separate engineering checks.

The supplied template intentionally has no invented material data. When passed through the validator it is correctly **REJECTED** with 11 evidence/curve deficiencies. This demonstrates strict input handling without creating a fictitious OEM material specification.

## Decision and priority

Previous fast end-to-end **V1 reduced** screening (not full spatial V3.2 response) found \(+\!10\%\) Seebeck coefficient changed detector temperature by **−6.60 K**, \(+\!20\%\) P/N thermal conductivity by **+10.22 K**, and \(+\!20\%\) resistivity by **+2.43 K** at the same 0.4 A operating point; coherent research analog transport hypotheses changed predicted temperature by approximately **±20 K**. Because grades are unmatched, these are sensitivity scenarios, not calibration/error bars. They make sourcing material evidence the rational next physics step, not refining mesh shape factors.

**No new 3D PDE, no parameter refit, no hidden external measurement and no original CAD, V1–V3.2 solver or source table modifications** were made for this material gate. V3.2 remains a complete *conditional* electrothermal/3D-ceramic hybrid, not an OEM-qualified physical device prediction. Historical original P1 electrical Gate B **FAIL/STOP**, first source-pair raw P1 contact current **FAIL 8/8**, prospective P2 **STOP**, full original 430-domain coupled C/D **NOT RUN** remain open and unchanged.

**Concrete next model revision trigger:** obtain a real source-grade/lot material table, run the fail-closed intake and independent physical plausibility/unit checks; only then swap the six curves in a *separately versioned* V3.2 material law and compare complete I/V/P/Tdie/energy at the existing 0.4 A point. Do not overwrite research analogs or claim predictive validity before source-specific I/V and temperature data agree.
