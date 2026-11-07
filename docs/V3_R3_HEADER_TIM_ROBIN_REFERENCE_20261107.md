# R3 source-CAD 3D Kovar header with explicit TIM Robin interface and separate radiator node

**Date:** November 7, 2026. **Baseline:** f8523fa42cc4d465fb8a296501c43570636390bf.

**Qualification:** ONE 3D header-only P1 source-mesh numerical PASS for an explicitly assumed, non-isothermal TIM boundary. NOT an as-built product measurement, not a mesh-converged thermal resistance, not a full 430-domain thermal or electrical coupled calculation.

The [pre-registered run](../data/v3_header_tim_robin_20261107/attempt01/registration.json), [saved original-mesh FEM result](../data/v3_header_tim_robin_20261107/attempt01/result.json), [source/mesh SHA-256 manifest](../data/v3_header_tim_robin_20261107/attempt01/manifest.json), [exact executable source](../scripts/v3_header_tim_robin_reference.py) and [single-run log](../data/v3_header_tim_robin_20261107/attempt01/run.log) are preserved. The baseline reference is the previously completed [isothermal-underside 3D header study](V3_R3_HEADER_ONE_CONDITION_3D_SPREADING_20261107.md), whose original inputs and numerical result remain immutable.

## 1. Manufacturer evidence and explicit source separation

VIGO's [general 2025 thermoelectric detector heat-sink guidance](V3_R3_OEM_SINK_BOUNDARY_EVIDENCE_20261107.md) recommends a heat sink around **2 K/W to ambient** for one to three TEC stages and a thermally conductive header-base interface, rather than mounting by the cap or screw alone. That guidance does **not** specify a measured mounting interface for the source reference model.

A separate VIGO primary document, [*AMS3140-01 / AMS6140-01 Preliminary Datasheet*, V11.0 (14 November 2023), thermal design p.8](https://vigophotonics.com/app/uploads/2023/11/AMS3140-01-AMS6140-01-Preliminary-datasheet.pdf), gives a worked **different-module** TIM example: grease thickness **0.1 mm**, conductivity **1 W/(m·K)**, and a lumped correction factor \(K_f\approx2\) to account for nonuniform thermal transfer through *that module's* heat-transfer surface. Its documented 450 mm² cooling area and 0.44 K/W example are NOT geometry or contact data from our CAD.

**Only the hypothetical 0.1 mm and 1 W/(m·K) values were adopted.** The reference TIM is applied uniformly to the model's **entire original Kovar underside CAD face2225**, at its actual triangulated area **334.00611 mm²**. That full-area contact is an *explicit unverified idealization*; it is not VIGO's 450 mm² module area and is not an experimentally measured TO66 bondline.

The original source header is material volume386 and uses existing R3.9 tetrahedra, with source TEC-side face2228 carrying the previously archived *conditional* 0.5870297615 W heat input. The header Kovar conductivity **17.3 W/(m·K)** remains an unqualified generic room-temperature bulk reference.

## 2. Two distinct external thermal elements

**Local, spatially distributed TIM boundary** on face2225:

\[
-k\nabla T\cdot\mathbf n=h_\mathrm{TIM}(T-T_\mathrm{rad}),\quad
h_\mathrm{TIM}=\frac{k_\mathrm{TIM}}{t_\mathrm{TIM}}
=\frac{1}{10^{-4}}=10^4\,\mathrm{W/(m^2\,K)}.
\]

In the finite element system, exact P1 surface mass integration adds the symmetric Robin matrix \(H_f=(h A_f/12)\begin{bmatrix}2&1&1\\1&2&1\\1&1&2\end{bmatrix}\) on each native original 2225 triangle. A fixed total **inward 0.5870297615 W**, uniformly distributed over the source upper face2228, produces a spatially resolved steady conduction field. All other header boundaries are insulated.

**Separate lumped radiator-to-ambient element**:

\[
T_\mathrm{rad}=T_\mathrm{amb}+Q\,R_\mathrm{rad},
\qquad T_\mathrm{amb}=300\,\mathrm K,\ R_\mathrm{rad}=2\,\mathrm{K/W}.
\]

Because the total heat input is fixed and all of it passes through the TIM, the linear header/TIM problem is shift invariant: first solve for \(T-T_\mathrm{rad}\) with a zero-reference Robin boundary, then add \(T_\mathrm{rad}=301.1740595\,\mathrm K\) to every node. Thus the radiator is a *series global* heat-sink condition, **not** an additional local \(h\) wrongly combined in parallel with TIM.

The AMS data sheet's empirical nonuniform correction factor \(K_f=2\) is **not multiplied into the TIM boundary or added as a lumped correction**: it approximates nonuniformity in a lumped TIM calculation, while the original header temperature field is spatially solved here. It is not established that \(K_f=2\) for this CAD or that all its transfer effects are captured by header spreading; applying it anyway would create an arbitrary, potentially double-counted penalty.

## 3. One actual source mesh and computed fields

| Numerical observable | Result |
| --- | ---: |
| Original source TET4 for Kovar header volume386 | **47,702** |
| Original mesh header nodes | **16,277** |
| Heat source, original CAD face2228 | **0.5870297615 W** |
| Finite TIM boundary, original face2225 | **9,617 source TRI3** |
| TIM \(t\), \(k\), \(h\) | 0.1 mm, 1 W/(m·K), **10,000 W/(m²·K)** |
| Radiator to 300 K ambient | **2.000 K/W** (OEM design recommendation) |
| Radiator temperature node | **301.17406 K** |
| Mean TEC-side original header temperature | **302.79386 K** |
| Minimum/maximum source face2228 nodal temperature | **301.96084 / 303.26784 K** |
| **Header + explicit TIM effective resistance**, TEC-side mean relative to radiator | **2.75931 K/W** |
| **Radiator + header + TIM** mean TEC-facing temperature rise / Q | **4.75931 K/W** |
| Original full-underside fixed-temperature header-only result | **1.57704 K/W** |
| Finite TIM condition's effective incremental penalty | **1.18228 K/W** |
| Uniform 1D TIM comparison \(t/(k A)\) | **0.29940 K/W** |
| Robin surface heat rejection | **0.587029761502 W** |
| Source/sink relative conservation error | **8.380×10⁻¹²** |
| Discrete Robin + bulk gradient energy-work error | **2.335×10⁻¹⁶** |
| Maximum nodal weak residual | **4.627×10⁻¹³ W** |

The **1.182 K/W** change relative to the fixed-temperature-header problem is not merely one-dimensional TIM thickness resistance. Replacing a perfectly isothermal entire underside by finite local heat transfer changes the *spatial thermal spreading throughout the Kovar header*. Here the mean underside temperature is **0.17575 K above the radiator**, corresponding to approximately **0.2994 K/W** for mean underside/TIM flux. The remaining effective difference arises from changed nonuniform header transport. The actual source face2228 is itself nonisothermal, with a roughly **1.307 K** range across its nodal temperatures. Neither the scalar TIM-only uniform result nor the old all-Dirichlet 1.577 K/W alone represents this solution.

This is a **single-mesh, one-condition solution**. A small source/sink residual and an exact discrete energy identity establish that the specified finite-element equations were solved consistently, not that the field is h-converged or that the TIM is actually installed at the assumed thickness and conductivity.

## 4. Full TEC interpretation, remaining STOP and anti-churn

**Do not reuse the previous 5 K/W as an additional term.** The previous reduced TEC assumed 5 K/W for the **whole effective hot-ceramic-to-ambient path**. The 4.7593 K/W here is a different **radiator + header + TIM** reference path that starts at the TEC-side of the *header*, not the TEC hot ceramic. It also excludes actual Ni/Au composite metallization, In52Sn48 solder, alumina, joints, finite contact resistances and ceramic thermal spreading. Adding the previously estimated 0.522 K/W uniform bulk layers would be a *simple illustrative sum* only, not a self-consistent full 3D coupled temperature solve; it would retain unknown contacts and mismatch in applied heat distribution.

Consequently **the earlier conditional 208.985 K HgCdTe die result is unchanged**, and no as-built detector temperature is derived by offsetting it with the present header reference. External radiator resistance and TIM thickness/area are not confirmed for an assembled commercial product; the source 29/11/4 TEC internals themselves are an inferred reference design, not proven OEM construction.

The next high-value engineering work requires *actual* header-to-radiator TIM/contact area, bondline thickness and mounted sink performance, matched P/N transport, and finite solder/interconnect contacts before a physically validated coupled TEC/detector calculation. Further arbitrary TIM-sweep combinations or repeated header-only solves would be churn.

**Preservation:** Original 824-solid STEP, accepted 430-domain source geometry, R3.8/R3.9 original mesh archives, historical electrical P1 Gate B **FAIL/STOP**, P2 prospective **STOP**, thermal coupled C/D **NOT RUN**, canonical Rev3 and issue #2 unchanged. No Codex use, new mesh, material-law release, or OEM calibration in this milestone.
