# V3 original 88-leg TEC: source-contact transport scale and coupled-model prerequisites

**Date:** November 7, 2026. **Baseline:** d627ebfe2584eb9725d63b7aa2bf91454a83c73a.

**Scientific result:** Native 352 solder-side interface CAD identities verified; exactly reproducible resistance and contact-specific measurement-sensitivity calculations. **NO constitutive parameter released, no 3D coupled PDE run, no as-built product grade identified.**

[Reproducible no-solve source-CAD audit](../scripts/v3_tec_contact_scale_gate.py) and [source-hashed numerical receipt](../data/v3_tec_contact_scale_20261107/attempt01/conditional_contact_scale.json). Reuses [actual R3 physical-law readiness](V3_PHYSICAL_LAW_AND_COUPLE_READINESS_20261106.md), [source circuit and port topology](V3_TEC_PHYSICAL_PORT_CONTRACT_20261106.md), and [separate 3D header/TIM boundary](V3_R3_HEADER_TIM_ROBIN_REFERENCE_20261107.md) without changing their original source data, scopes or numerical qualification.

## 1. Physical source topology

The accepted source 430-domain CAD has **88 actual thermoelectric P/N legs** (44 P and 44 N) in the source-verified single series electrical path, across a 29/11/4 three-stage network. Every individual leg has **two original solder bodies**, one hot and one cold. The source therefore contains **176 SnSb solder solids** (0.4 × 0.4 × 0.035 mm) and exactly **352 original registered solder interfaces**: 88 N-leg/SnSb, 88 P-leg/SnSb, and 176 SnSb/composite-metal-pad interfaces. Every interface's source area is **0.16 mm²**. No interfaces were introduced, omitted or reclassified.

Source terminal electric pins are **pin1 CAD face2414** and **pin9 face2426**, with independent detector contacts pin7/pin8; the first stage0 N/P test pair has native electrical cut edges **1531 and 162** against the rest of the circuit. Its ceramic thermal connections to the rest of the full model cannot be assumed insulated by default. This is already documented in the original port-contract audit.

## 2. Analytical, conditional resistance scale at a single 300 K reference point

Only the already recorded **different-specimen Zhang P-HE/N-HE-1 300 K research analog**, and the older Gate B bulk solder-property hypotheses, are used. Neither is an identified as-built TEC grade.

| Quantity | Formula and assumption | Result |
| --- | --- | ---: |
| Native leg section | \(A = 0.16\) mm², \(L=0.500\) mm | Verified |
| Nominal 300 K P/N research analog \(\rho\) | \(\rho_P=12.08061,\;\rho_N=7.54328\) µΩ·m | Unmatched specimens |
| **All 88 ideal P/N leg electrical series resistance** | \(44(\rho_P+\rho_N)L/A\) | **2.698285 Ω** |
| SnSb bulk assumed \(\rho\) | \(1.7\times10^{-7}\,\Omega\mathrm m\), prior Gate B engineering model | Hypothesis |
| **All 176 solder solids in electrical series** | \(176\rho_s L_s/A\) | **0.006545 Ω**, **0.2426%** of leg-only R |
| Nominal interface specific \(\rho_c\), hypothetical | \(1\times10^{-11}\,\Omega\mathrm m^2\) at all 352 faces | **0.022 Ω** series R |
| High interface specific \(\rho_c\), hypothetical | \(1\times10^{-10}\,\Omega\mathrm m^2\) at all 352 faces | **0.220 Ω** series R |

The same source-algebraic model gives a **one-percent interface-to-P/N-leg resistance threshold** when every contact is assigned identical \(\rho_c\):

\[
  \rho_{c,1\%} = \frac{0.01R_{\mathrm{PN,88}} A}{352}
   = 1.22649\times10^{-11}\ \Omega\,\mathrm m^2.
\]

This is a **measurement planning sensitivity target**, NOT a physical quality criterion or evidence that actual contact resistivity lies near this value. The former lead9 Gate B coupon's contact coefficients are explicitly *not* identified as those of the TEC leg joints.

At current **0.40 A**, the hypothetical aggregate interface Joule heat is **0.352 mW**, **3.520 mW**, or **35.20 mW** for \(\rho_c=10^{-12}\), \(10^{-11}\), or \(10^{-10}\,\Omega\mathrm m^2\), respectively. Associated contact voltage drops are \(0.00088\), \(0.00880\), or \(0.0880\) V. The solder bulk hypothesis contributes \(I^2R_s=1.0472\) mW at 0.40 A. **These are whole-circuit electric-loss arithmetic, not predictions of the temperature rise, localized contact heating or real full-device voltage.**

## 3. Thermal resistance scale and why junction energy is still essential

The same older SnSb model assumed \(k_s=45\) W/(m·K); the reference 300 K unmatched P/N \(k\) are 1.0990 and 1.3992 W/(m·K). Each 35-µm solder slab, if axial and uniform, contributes **4.8611 K/W** in its own leg heat path. One 0.5-mm P-type leg has **2843.48 K/W**, one N-type **2233.38 K/W**. In each leg's path, two SnSb bodies plus four native electrical/thermal interfaces carry heat, but real contact quality and interfacial spreading are unknown.

| **Hypothetical** common area-specific thermal contact resistance \(r_t\) | Four interfaces, per-leg series \(4r_t/A\) | Two SnSb slabs plus interfaces, per leg |
| --- | ---: | ---: |
| \(10^{-8}\,\mathrm{m^2K/W}\) | 0.25 K/W | 9.972 K/W |
| \(10^{-7}\,\mathrm{m^2K/W}\) | 2.50 K/W | 12.222 K/W |
| \(10^{-6}\,\mathrm{m^2K/W}\) | 25.0 K/W | 34.722 K/W |

Under just this simple axial-resistance definition, equal area-specific interface contact resistance must reach **\(1.1374\times10^{-6}\,\mathrm{m^2K/W}\)** for four contacts to contribute 1% of a P leg's axial thermal resistance, or **\(8.9335\times10^{-7}\,\mathrm{m^2K/W}\)** for an N leg. **This does not justify deleting contact terms in the physics solver**.

At a P/N/metal or solder/leg junction, thermoelectric Peltier heat depends on the local Seebeck discontinuity and current. Additionally, electrical contact resistance dissipates localized Joule heat, and thermal conduction into the original complex copper/composite metal pads is not a one-dimensional series network. Bulk contact \(r_t\) alone cannot replace energy-conserving interface constitutive conditions. The 88 leg heat paths are also **not** one thermal series circuit: within every stage legs carry heat in parallel between shared ceramics, with interstage spreading and bypasses.

## 4. Consequence for first physically meaningful 3D thermoelectric couple

The authentic stage0 candidate has **9 conducting solids**: N/P legs IDs5 and8; solder IDs6,7,9,10; original metal nets269,270,271. It has native original electrical terminals as **mathematical cut faces 1531 and162**, not external package pins. The original copper/ceramic interfaces to retained plates lie on **CAD faces8,9,44** and require separately justified thermal conditions; surrounding gas and remaining 86 thermoelectric legs require a declared reduction.

A valid prospective 3D coupled solve would require at least:

1. **Explicit current port contract:** prescribed source/return direction and total current on native face1531/162, no invented physical pins, and a conservative treatment of interface current across all source solder/leg/pad faces. Original P1 Gate B failure remains a separate historical validation issue.
2. **Temperature-dependent transport:** source-identifiable P and N \(S(T),\rho(T),k(T)\) with correct signs, temperature validity, Thomson derivative and declared manufacturing-grade uncertainty. The old research curves may support an explicitly **conditional feasibility** model, never an as-built release.
3. **Finite thermal/electrical interface laws:** independently supported \(r_e(T)\), \(r_t(T)\) and thermoelectric junction energy terms, no arbitrary fitted values or silent use of old lead9 coupon coefficients.
4. **Defined hot and cold thermal cut ports:** temperature/flux on native ceramic-pad faces8,9,44 must be derived from a source-registered full ceramic coupling or independently specified *hypothetical* ideal bath; do not call an insulated surrounding ceramic physically correct.
5. **Prospective numerical acceptance:** independently reconstructed charge balance and electrical power, interface Joule and Peltier terms, heat flux and full electric/thermal energy closure, mesh convergence, as well as the original 0.1% raw-gradient Gate B threshold retained in its own historical record. It is not appropriate to declare an alternate weak-reaction gate equivalent without an independent contract.

**Stop/no-churn:** With no measured matched P/N material, no specific solder/interface contact resistivity, and no physical cut-port thermal state, no physically accepted 3D coupled detector prediction is possible. This inventory DOES give quantitative **contact-specific data targets** and a nine-domain real CAD path for a **separately labeled conditional coupled feasibility experiment** once the coupling terms and boundaries are preregistered. Do not launch unlimited synthetic contact sweeps or claim a manufactured temperature from the old 5-node outputs.

**Preservation:** Original 824-solid STEP and Rev3, R3.8–R3.9 saved meshes, old raw P1 Gate B **FAIL/STOP**, prospective P2 **STOP**, full thermal C/D **NOT RUN**, source material and 2,440 face release UNSET, issue #2 unchanged. No new PDE or Codex.
