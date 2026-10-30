# NEXT IMPLEMENTATION WORK ORDER — 2026-10-30 (bounded phase COMPLETED)

**Execution outcome:** The bounded reduced-order alternative was implemented as
`tecooledmct/integrated_reference.py`, with `tests/test_integrated_reference.py`,
scenario evidence under `data/integrated_reference_20261030/`, and comprehensive
scope/limitations in `docs/INTEGRATED_REFERENCE_THERMAL_20261030.md`. The
corrected-geometry cap/window 3D operator remains a separate NEXT milestone.
Do not rerun this work order as though it were unstarted.

Read AGENTS.md and docs/PLAUSIBLE_REFERENCE_MODEL_POLICY_20261030.md FIRST. The user has authorized work in Kajin-0/TE_Cooled_MCT. The goal is a plausible physically defensible reference device, NOT OEM validation and NOT a Kovar raw-bath refinement campaign.

Focus next deliverable: a **practical integrated thermal-budget scenario model** for the CORRECTED 3D geometry, bridging the existing genuine Elmer coupled solid model to the cap/window/gas/radiation and hot-side heat sinking without misleading 3D-completeness claims.

Conduct independent source/code review and make best defensible engineering choices:
1. Identify what is and isn't currently modeled: actual corrected geometry 216 domains, the original hypothetical G3b operator based on older geometry, material laws and G2d / bounded-screen transport.
2. Construct *additive* auditable reduced-order thermal-package coupling, or preferably corrected-geometry 3D boundary operators if feasible within bounded resources. Reuse actual corrected body/endpoint sizes and source declarations. Never silently reuse old G3b geometry or claim unexecuted 3D fields.
3. Physics minimum: three-stage thermoelectric cascade (not necessarily OEM-matched), configurable heat-sink hot-side resistance, source-backed/analog N2/Kr/Xe/Ar cavity gas heat leak with pressure/free molecular transition, gray diffuse radiative heat load from hypothesized cap/window (do not claim actual optical window transmission), Au/Cu wire conduction+Joule heat from corrected 1D routes, MCT bias and parametric absorbed heating. Separate cap assumption and thermal BC: any fictive cap is a defined boundary reservoir, NOT a validated meshed 3D cap. For relative scenarios select nominal+low/high meaningful ranges. Any range is an engineering hypothesis not a statistical confidence interval.
4. Heat path budgets and stage conservation to 1e-6 W; thermo-electric electrical balance; temperature and power outputs over current and pressure. Guard pressure 0, I=0, invalid temperatures and material-table domains. Verify convergence; independent limiting-case analytic tests; cross-check with existing package model but do not fit OEM.
5. Produce reproducible machine-readable scenario output, small plots if simple, docs explaining actual implementation limitations and tradeoffs, clear tests, and latest AGENTS entry. No changes to accepted evidence or Rev3 PDF or frozen scripts. Existing data/g3b old geometry must not be imported as geometry source.
6. Execute targeted and full opt-in regression if practical, CLI/demo and archive verifier; fix failures. Commit and push to main, clean worktree. Do not alter other repos or add tmux sessions. Respect 4 CPUs 12GiB docker, space 64GiB. No expensive million-tet runs unless essential.

If scope becomes too ambitious, implement a *well-tested, truthful reduced-order prototype* as a necessary building block, not a falsely complete 3D result. Own the work through completion with a final summary of results and remaining gaps; do NOT stop just to ask for approval.

The previously discussed numerical bath failure remains unchanged and NOT a release claim. Use source references and measured-vs-assumed categories. No need for OEM model fit.
