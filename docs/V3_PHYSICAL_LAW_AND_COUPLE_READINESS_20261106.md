# V3 physical-law readiness and first real N/P couple — November 6, 2026

**Baseline:** 9829b399834be53f16caf04b11349f97571fe7d4.
**Decision: source CAD connectivity PASS; physical property release STOP; electrothermal subassembly NOT RUN.**

This is an evidence-backed, **no-solve** inventory. The [complete source-ID ledger](../data/v3_physical_law_readiness_20261106/attempt01/law_and_subassembly_inventory.json) and [deterministic builder](../scripts/v3_physical_law_inventory.py) identify every actual 430-domain/2,440-face accepted R3 CAD record without inserting unverified material constants, extrapolating thermal curves or assigning an electrical or thermal port.

## 1. Physical geometry scope

| Source count | Value |
| --- | ---: |
| Accepted CAD volumes | **430** |
| Actual P/N TEC leg solids | **44 P + 44 N** |
| Stage hot-to-cold leg population | **58 / 22 / 8** |
| Stage couple count | **29 / 11 / 4** |
| SnSb solder solids | **176** |
| Effective multilayer solids | **98** |
| Native CAD solid-solid interfaces | **557** |
| Native CAD gas-solid interfaces | **1,840** |
| Native exterior faces | **43** |
| Source finite-contact witnesses | **378** |
| Active solver-ready domain laws | **0 of 430** |
| Active solver-ready face laws | **0 of 2,440** |

Each ledger row preserves exact CAD identity, owner IDs, face area where applicable, original constitutive readiness, temperature/anisotropy/uncertainty requirements, and explicit NULL values for released transport and interface coefficients. The **historical 438-domain/2,456-face requirements record is not the live R3 law registry** and cannot be used without an independently verified source-mapping transformation.

## 2. What transport data already exist, and why they are insufficient

The repo includes corrected digitized research-specimen P-HE and N-HE-1 properties from [Zhang et al. (2025), DOI 10.1088/0256-307X/42/5/056304](https://doi.org/10.1088/0256-307X/42/5/056304), recorded in [TEC material plausibility](TEC_MATERIAL_PLAUSIBILITY_20261101.md). Digitized measured-domain coverage is **40–300 K**, with an assumed quarter-slope continuation above 300 K in previous reduced studies. These two polarities are **different research specimens, not a certified matched grade from the actual device manufacturer**.

Descriptive values from the existing *nominal research analog* at 300 K:

| Property | Research P | Research N |
| --- | ---: | ---: |
| Seebeck coefficient, µV/K | +212.463 | −189.575 |
| Resistivity, µΩ·m | 12.0806 | 7.54328 |
| Thermal conductivity, W/(m·K) | 1.09901 | 1.39923 |

**These values have not been assigned to the real 88 leg volumes.** The prior reduced TEC study used **28/12/4**, unlike the actual R3 geometry **29/11/4**. Its conditional temperature estimates, including approximately 186.5 K, cannot be represented as accepted R3 detector temperatures. Even exact numerical conservation in a reduced study cannot identify manufacturing grade, solder interfaces, hot sink or real contact resistivity.

## 3. Selected real CAD N/P subassembly: connected, but not physically isolated

A real stage-0 series N/P pair is identifiable:

| Physical component | CAD volume |
| --- | ---: |
| Hot ceramic0 / cold ceramic1 | **1 / 2** |
| N leg0 and solders0 hot/cold | **5 / 6 / 7** |
| P leg1 and solders1 hot/cold | **8 / 9 / 10** |
| N hot metal net0 | **269** |
| Shared N/P cold metal net1 | **270** |
| P hot metal net2 | **271** |

The source-registered contact sequence is: N leg/solders **face 124 and 125**; P leg/solders **140 and 141**; N hot solder/net0 **130**; N cold solder/net1 **135**; P cold solder/net1 **151**; P hot solder/net2 **146**; net0/ceramic0 **8**; net2/ceramic0 **9**; net1/ceramic1 **44**. All eleven are original nonzero-area CAD solid-solid faces, not fabricated fixture interfaces. The leg-to-solder and solder-to-net contact areas are each **0.16 mm²**.

The 11-source-volume selection includes **the entire original ceramic0 and ceramic1 plates**. It has **132 external-to-selection cut faces: 73 solid-solid and 59 gas-solid**. Other TEC legs attach to the same whole ceramics, and net0/net2 are original metal network segments rather than certified independent source and return terminals.

Thus a two-leg PDE without a defined cut-port reduction would make up an electrical circuit and heat boundary. This gate is explicitly **STOP**. We have a genuine *geometry candidate*, not a physically valid isolated couple calculation.

## 4. Five blocking evidence classes

| Priority | Missing independently qualified information | What would release it |
| --- | --- | --- |
| **H1: P/N transport** | Actual paired leg grades, S(T), rho(T), k(T), Thomson derivatives, anisotropy and uncertainty over the full operating temperature range | Manufacturer grade-specific measurements or separate same-grade experiments, not a mismatched research analog |
| **H2: metallization and contacts** | Actual SnSb solder, copper/metallization conductivity and thermal conductivity, electrical and thermal contact area resistances, joining/process identity | Evidence-backed material and contact measurements with temperature ranges; explicit heat/Peltier partition |
| **H3: real electrical ports** | How this N/P pair is driven relative to the full 29/11/4 series/bridge network; valid external terminals and voltage/current signs | Source circuit topology, port cuts, conservation boundaries and measured drive |
| **H4: real thermal boundaries** | Hot-side/cold-side condition, ceramic thermal spreading, TEC adjacent-leg interactions and gas/radiation loads | Measured sink and heat-load conditions, or a rigorously defined, externally coupled stage reduction |
| **H5: full FEM qualification** | Original Gate B and separate prospective P2 current gates remain stopped; global current and energy closure and mesh convergence unqualified | A prospective conservative full-physics acceptance framework with independent current/energy results and appropriate numerical observables |

No H1–H4 physical release is granted here. All 430/2,440 current source statuses remain unchanged.

## 5. Coupled equations to implement only after evidence and ports are resolved

For one consistent potential/Seebeck sign convention, use for example

\[
\mathbf J=-\sigma(T)[\nabla V+S(T)\nabla T],\qquad
\mathbf q=S(T)T\,\mathbf J-k(T)\nabla T.
\]

The charge and energy weak forms must be derived consistently from these definitions; in particular, bulk Joule/Thomson transport, interfacial Peltier effects, finite thermal/electrical contacts, boundary heat exchange and signed external electrical power all need independent balance. These equations are **not an executed or qualified R3 model**.

Before physical subassembly calculation, require separately preregistered electrical port conservation, full electrical-plus-thermal energy closure, full field temperature validity, material-law uncertainty, and a meaningful mesh independence check. The historical original P1 Gate B failure cannot be reclassified by replacing raw bulk-gradient current with weak contact reaction.

## 6. Anti-churn decision

**No further synthetic scalar FEM benchmarks, unspecific mesh optimization or repetitive Gate B field diagnostics.** The next required progress is identifiable physical evidence: actual grade-matched thermoelectric curves, solder/contact laws, source circuit/port definitions, and ceramic/sink heat-flow conditions. The existing 40–300 K research data are useful as *candidate analogs*, not physically released inputs.

A scenario-only feasibility model could be separately labeled if actual material evidence remains unavailable; it must not be presented as the as-built detector temperature or an OEM-validated TEC. No new P1/P2 PDE, original geometry edit, material fit, mesh generation or Codex use occurred in this milestone.

**Original P1 electrical Gate B FAIL/STOP; prospective P2 STOP; thermal C/D NOT RUN; full 430-domain physical electrothermal prediction UNQUALIFIED.** All protected 824-solid STEP, canonical Rev3, original R3 geometry, failure archives and issue #2 remain intact.
