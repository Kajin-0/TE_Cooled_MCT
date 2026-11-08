# V3.3 working source-CAD TEC with first explicit krypton and gray-radiation package feedback

**Date:** 8 November 2026 UTC / 7 November 2026 US Central. **Canonical previous integrated V3.2:** commit \`15d5746\`. **Engineering goal:** a progressively more realistic *synthetic* HgCdTe/three-stage TEC reference design, not an OEM product clone. **Numerical verdict:** one coupled 0.400 A operating point completed. Source original 430-domain E/T spatial gates remain historically unrun.

## A self-contained independent-engineer reproduction document

**Historical V3.3 physics record:** the latest architecture-specific assessment is [the current engineering report](../reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf). Historical Revision 3 is now restored unchanged.

**READ FIRST:** [11-page standalone reproduction PDF](../reports/generated/TEC_HgCdTe_Reference_V3_3_Standalone_Method_20261108.pdf), with [equivalent complete source Markdown](../reports/generated/TEC_HgCdTe_Reference_V3_3_Standalone_Method_20261108.md). These are complete technical documents without a reader needing access to this codebase or prior conversation. They contain a numerical model specification, governing equations and sign conventions, all six temperature-dependent 14-node P/N property tables (**84 numbers**), 29/11/4 stage topology, ceramic/die/material/joint dimensions, actual Cu/Au wire metrics, source-specific hot-side resistance, declared gas/gray-radiation coefficients and equations, **all 88 source leg-centre coordinates**, **all 95 original ceramic pad face areas/centroids/solved heat fluxes**, registered stopping rules, side-by-side V3.2/V3.3 results, independent references and limitations.

**Historical Rev3 is unchanged:** [38-page Rev3 technical assessment](../reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf), SHA-256 \`882209b09796acdc5e7d3aafc376f1722fce2843230233c7a76542ebcb273248\`. Its primary 216-domain geometry and historical 28/12/4 reduced calculation are **not identical** to the new **430-domain, 29/11/4** original-source reference construction. Section 13 of Rev3 documents separate cavity radiation and chord-jump gas methods and limitations, not this integrated V3.3 result. The standalone companion explicitly distinguishes the model generations rather than appending a current result to an old CAD model description.

## Implementation and source integrity

[Working exact V3.2-derived V3.3 source](../scripts/v3_3_cavity_package_feedback.py), [one immutable registered original-source 0.4 A case](../data/v3_3_cavity_package_feedback_20261108/attempt02/registration.json), [full new 88-leg and four original 3D ceramic electrothermal numerical result](../data/v3_3_cavity_package_feedback_20261108/attempt02/result.json), [saved original mesh 3D ceramic nodal temperatures](../data/v3_3_cavity_package_feedback_20261108/attempt02/source_native_ceramics_V3_3.npz), [independent no-solve reconstruction of gas, radiation, 88-leg electrical/heat and stage balances](../data/v3_3_cavity_package_feedback_20261108/attempt02/independent_read_only_acceptance.json), [PDF and Markdown document generator](../scripts/v3_3_standalone_report.py), [PDF rendering script](../scripts/v3_3_standalone_pdf.py), [SHA manifest](../data/v3_3_cavity_package_feedback_20261108/manifest.json).

The new model keeps identical 0.4 A/300 K/2 mW die inputs, same 88 source P/N legs and nonlinear 32-interval conservation, exact original ceramic1–4 11,791 source tetrahedra and spatial nonuniform per-pad heat, 176 SnSb hypothetical solder bulk losses, 352 electrical interface losses, original Cu/Au leads, die attach, and full external 4.83338696 K/W header/TIM/radiator path. The material analogs remain source-backed *hypotheses*; no actual OEM grade data are needed to work on this design.

**Added physics:** cold ceramic1, ceramic2, ceramic3 and detector now each receive gas and/or gray-radiation power from a 300 K effective cap/window reservoir. Exposed area proxy (ceramic1 shell / ceramic2 shell / ceramic3 shell / die): **[12.60, 8.68, 4.76, 1.00] mm²** from original ceramic footprint differences. Gas **Kr 100 Pa**, **3 mm effective gap**, accommodation **0.8**, actual NIST tabulated k(200/300/400 K) **[0.0064,0.0095,0.0122] W/(m K)**, Eucken viscosity and rarefied temperature jump used as in Rev3. Gray ε_cap=0.20, ε_ceramic=0.80, ε_window=0.10, F_ceramic=0.50, F_die=0.70, Stefan–Boltzmann constant standard. Actual source cavity **is not meshed**; the reduced gas/radiative heat on the cold ceramics is spread via **area-weighted upper metal-pad original TRI3 Neumann bases**, a declared engineering proxy. No gas-fluid CFD, true bare ceramic exposed surface flux, real spectral window or detailed 14-surface radiosity is claimed.

**Conservation:** Positive external load per cold ceramic subtracts from its individual stage-to-stage power balance. Die gas/radiation enters the 2 mW die/Au/attach balance. Global electric+die+Au+Cu+all enclosure heat minus bath heat must vanish. Cavity reservoir receives exactly the negative of the reported total gas and radiation powers.

## One complete original-source 0.4 A comparison

| Quantity | Working V3.2, cavity OFF | Working V3.3, 100 Pa Kr + gray radiation | Delta |
| --- | ---: | ---: | ---: |
| HgCdTe die T (K) | 209.987981 | **210.625214** | **+0.637233** |
| TEC terminal V (V) | 1.524070832 | **1.522462416** | **−0.001608416** |
| TEC electrical input (W) | 0.609628333 | **0.608984966** | **−0.000643367** |
| Bath/sink heat rejected (W) | 0.590322603 | **0.594043746** | **+0.003721143** |
| Original 3D ceramic tetrahedra | 11,791 | **11,791** | none |
| Source TEC P/N legs | 88 | **88** | none |

| Heat input to colder surfaces (mW) | Kr gas | Gray thermal radiation |
| --- | ---: | ---: |
| Ceramic1 | 1.159010 | 0.208742 |
| Ceramic2 | 1.445333 | 0.233892 |
| Ceramic3 | 1.064693 | 0.157697 |
| Detector | 0.223517 | 0.023746 |
| **Total** | **3.892553** | **0.624077** |

All new enclosure thermal input totals **4.516629 mW**. Not all this heat appears one-for-one as extra electrical input because the staged TE transport and hot-side heat simultaneously respond to changing temperatures.

The registered prototype converged in **five fixed-point spatial iterations** with maximum last upper-pad/plate temperature change **1.65345×10⁻⁵ K** against its declared coarse **2×10⁻⁵ K** threshold; the old V3.2 initial-condition temperature fields were used as the V3.3 warm start. Whole-device electrical/thermal energy residual **8.8674×10⁻⁹ W**, maximum stage/node heat imbalance **4.9061×10⁻⁹ W**, four original ceramic exact net pad flux max **5.50×10⁻¹⁵ W** and worst individual P/N leg heat balance **1.2364×10⁻¹³ W**. This is a **coarse successful numerical prototype, not a numerical error-bound or h-converged physical prediction**. An independent no-PDE calculation reconstructs gas and radiation fluxes from stated SI properties, all 88 P/N currents and three interstage equations, and finds a **finite 2.535×10⁻⁸ W** final native pad heat/leg update discrepancy, which is explicitly preserved rather than declared zero. See [saved acceptance](../data/v3_3_cavity_package_feedback_20261108/attempt02/independent_read_only_acceptance.json).

## Failed trial, no-churn treatment and next development direction

The first prospective V3.3 run inherited an older V3 starting field and the unnecessarily tight \(2\times10^{-7}\) K spatial threshold. The code progressively converged through three updates but was deliberately stopped early before accepting any result. Its registration and stop evidence remain in [attempt01](../data/v3_3_cavity_package_feedback_20261108/attempt01/early_iteration_timeout.json). The second preregistered case **only** changed the initial guess to the already-converged V3.2 physical state and used the explicit coarse-prototype \(2\times10^{-5}\) K threshold, while holding all source material laws, pressure/gas/radiation/die/sink and current inputs fixed. It accepted after five iterations. There was no post-hoc material-coefficient fitting.

**Next fidelity increment:** preserve V3.3 as the running package model; validate a small pressure/current/load sweep at the same explicit physics fidelity (likely vacuum and one nonzero backfill at different currents). Add actual exposed cold-surface Neumann mapping and improved source gas geometry only if a bounded complete-system comparison finds it materially changes T_die, IV, P or global stability. Avoid another standalone micromesh audit and avoid OEM identity as a development gate.

**Original Gate B FAIL/STOP, first source pair P1 raw flux FAIL 8/8, prospective P2 STOP and full original source 430-domain C/D NOT RUN all remain unchanged.** No source Rev3 edits, no manufacturer outreach, no Codex.
