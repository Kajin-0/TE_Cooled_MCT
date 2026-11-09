# V3.5: TEC terminal wires, package-pin heat paths and interstage contact sensitivity

**8 November 2026 U.S. Eastern / 9 November UTC | Three independently audited full-device cases, plus a separate fixed-field material screen | Synthetic engineering reference**

## Question and primary design finding

Commercial multistage thermoelectric coolers can arrive with long lead wires that are trimmed to the actual installed length and soldered to the TO header pins. The physical heat leak depends on the **installed length from each TEC terminal landing to the soldered package pin**, not on how much surplus factory wire existed before trimming or remains disconnected outside the assembly. Lead material and thermal connection to the package are also relevant, and must not be guessed from a wire's appearance.

The prior V3.4 end-to-end cooler treated both terminal power leads as nominal copper, combined their heat-transfer effect at a single source ceramic face (36), and evaluated conduction against a single averaged stage-hot temperature. **That approximation has now been replaced.** The source CAD resolves pin 1 through native ceramic metal face **8** and pin 9 through native ceramic metal face **36**, separated by 5.55 K in the archived spatial V3.4 ceramic field. At that operating point the lead at face8 can cool the warm ceramic toward the 300 K pin, whereas the lead at face36 carries heat in the reverse direction.

**Nominal whole-device conditions** remain 0.400 A TEC current, 300 K package/ambient thermal reservoir, 2.00 mW imposed detector heat, 100 Pa krypton, four original spatial ceramic FEMs (11,791 TET4), 88 axial nonlinear thermoelectric legs, three formed-Cu interstage links with true native contact geometry, and unchanged detector/package/optical-cavity effective thermal laws.

| Model / assumed installation | T(detector) (K) | TEC V (V) | Input (mW) | Sink heat (mW) | Full-system status |
|---|---:|---:|---:|---:|---|
| V3.4, former combined power-lead approximation | 218.832895 | 1.489440 | 595.776 | 579.830 | Previous accepted comparator |
| **V3.5, individual native Cu leads, nominal Cu foil contacts** | **218.900024** | **1.489170** | **595.668** | **592.331** | Accepted, independently audited |
| V3.5, pure-nickel-like power leads instead | 218.915286 | 1.495249 | 598.100 | 601.285 | Accepted, independently audited |
| V3.5, copper leads with much higher **interstage Cu-to-ceramic** contact resistance | **212.623582** | 1.518772 | 607.509 | 602.003 | Accepted, independently audited, **extreme hypothetical interface** |

Compared with corrected copper leads, the selected nickel-like power-lead material raises detector temperature by **0.015262 K**, while increasing terminal electrical input by **2.432 mW**. Correcting the lead landing map itself changes detector temperature from V3.4 by **+0.067129 K**. By contrast, increasing the assumed interstage copper thermal-contact areal resistance from \(10^{-6}\) to \(10^{-4}\ {\rm m^2 K/W}\) lowers the computed detector temperature by **6.276442 K**. **This large thermal improvement is an extreme contact-isolation sensitivity, not an engineering recommendation to make a solder joint defective or resistive.** A real interface must independently satisfy electrical continuity, process reliability, current density, fatigue and assembly feasibility.

The full-system comparison demonstrates that, for this construction, **interstage heat bypass dominates the short pin-to-TEC power-lead conduction**. The result is conditional on the assumed material and contact laws and does not establish the true as-manufactured accuracy.

## Source geometry and the significance of lead trimming

| Actual synthetic CAD wire | TEC-to-package connection | Internal centerline length | Radius / diameter | Native source metal-pad face |
|---|---|---:|---:|---|
| TEC_lead1 | TEC first terminal to header pin1 | 3.451062 mm | 0.100 / 0.200 mm | 8 |
| TEC_lead9 | TEC return to header pin9 | 4.964887 mm | 0.100 / 0.200 mm | 36 |

The source join surfaces directly connect the lead wires to their respective internal terminal metal lands and then to package pin-side solder joints. This is an engineered synthetic layout and is not evidence of any specific OEM cooler's wire material or amount of trimming.

Factory-supplied uninstalled wire is outside this thermal network. If the final TO attachment leaves the internal lead route unchanged, cutting away an *external surplus* **does not change the conductor's ceramic-to-pin thermal length**. If installation actually changes the span or routing between the TEC land and package solder point, that revised length and position must be propagated into the model. If the header temperature is not approximately 300 K, it must be separately solved, not held to 300 K by assumption.

Manufacturer evidence is relevant to alloy identification. TEC Microsystems explicitly states that a three-stage miniature TEC is normally supplied with **blank tinned single-core copper terminal wire**, and the wire type, diameter and length are selectable. RMT also lists tinned copper as its standard. These do not establish the material of the user's previously observed individual coolers. Kanthal FeCrAl is retained solely as a resistive-alloy *hypothetical* because the user was uncertain of the alloy. Kanthal A-1's own datasheet gives \(\rho_{20^\circ C}\approx1.45\times10^{-6}\ \Omega{\rm m}\); it is substantially more resistive than ordinary copper.

**Sources:** TEC Microsystems, [2023 3MC06-050-12/1 datasheet](https://www.tec-microsystems.com/Download/Datasheets/Thermoelectric%20Coolers/MC06%20Series/3MC06-050-12_1_Datasheet_Standard_2023.pdf); [RMT terminal manufacturing options](https://www.rmtltd.ru/support/thermoelectric-module-options/); [Kanthal A-1 technical material data](https://www.kanthal.com/en/products/datasheets/material-datasheets/wire/resistance-heating-wire-and-resistance-wire/kanthal-a-1/).

## Two separate electrical/thermal terminal boundary conditions

For each of the two **original** wire segments \(i\), with internal length \(L_i\), radius \(r_i\), metal resistivity \(\rho_i\) and conductivity \(k_i\), the conservative reduced lead model uses

\[
A_i=\pi r_i^2,\quad R_i=\rho_i L_i/A_i,\quad G_i=k_i A_i/L_i,
\]
\[
Q_{i\to{\rm ceramic}} =
G_i(T_{\rm pin}-T_{{\rm face},i})+\frac12 I^2 R_i,
\qquad
P_{J,i}=I^2R_i .
\]

Each wire's **ceramic end receives half its uniformly generated Joule heat**; the other half is allocated to the warm pin/reservoir. This symmetric heating partition is an explicit approximation, not a solved axial conductor with a spatially varying source. The full electrical resistance of both wires is included in the TEC terminal voltage. For energy bookkeeping,

\[
\sum Q_{{\rm wire}\to{\rm ceramic}} =
\sum G_i(T_{\rm pin}-T_{{\rm face},i})+
\frac12 I^2\sum R_i.
\]

The thermal face temperature is taken from the **local native TRI3 source ceramic temperature average** and updated at each coupled spatial iteration, rather than set equal to the mean hot-ceramic temperature.

Selected illustrative, near-room-temperature constant-property wire scenarios:

| Lead hypothesis | Selected \(k\) (W/mK) | Selected \(\rho\) (Ωm) | 2-lead source resistance at original lengths | Joule at 0.4 A |
|---|---:|---:|---:|---:|
| Nominal copper | 400 | 1.72×10⁻⁸ | 0.004608 Ω | 0.737 mW |
| Nickel-like | 90 | 7.00×10⁻⁸ | 0.018752 Ω | 3.000 mW |
| FeCrAl Kanthal-like *fixed-field-only screen* | 11 | 1.45×10⁻⁶ | 0.388438 Ω | 62.150 mW |

The selected FeCrAl thermal conductivity is a screening proxy. Its manufacturability, solder wettability, oxidation/thermal cycling and actual terminal length and source alloy were not verified. The **62.15 mW** of hypothetical Joule heating is a reason **not** to presume that a low-thermal-conductivity alloy automatically improves TEC operation.

At the original saved V3.4 pad temperatures, face8 = **303.943145 K** and face36 = **298.390621 K**, the two-source-pad fixed-temperature lead heat totals are copper **−9.916 mW**, nickel **−0.814 mW** and FeCrAl **+30.792 mW**. These *fixed-field* fluxes are not complete new detector-temperature predictions. The **fully converged** copper and nickel models recalculate the pad temperatures and redistribute heat to each source ceramic FEM node.

## Dominant contact-physics uncertainty

The formed stage-to-stage copper foil is not the same as the two terminal supply wires. The existing bridge model still uses original CAD foil routes 58 (faces38→75), 80 (79→105), and stepped return 88 (36→74→104), with \(\rho_{\rm Cu}(T)\) and \(k_{\rm Cu}\) as declared in the preceding V3.4 assessment. Its source joining feet are each 0.060 mm². At one joint,

\[
G_{c,i}=\frac{A_{{\rm joint},i}}{r_{T,c}''}.
\]

Holding the **frozen V3.4** ceramic temperatures fixed while changing only the Cu/ceramic contact areal thermal resistance changes copper heat entering the upper source ceramic:

| Hypothetical \(r_{T,c}''\) (m²K/W) | Fixed-field upper copper heat (mW) |
|---|---:|
| 0 (ideal thermal connection) | 91.033 |
| 1×10⁻⁷ | 90.611 |
| **1×10⁻⁶ (nominal)** | **86.989** |
| 1×10⁻⁵ | 62.664 |
| **1×10⁻⁴ (severe isolation)** | **17.493** |

Those five values are *not* five nonlinear device results. To verify system response, V3.5 fully re-solved the **nominal** \(10^{-6}\) and severe \(10^{-4}\) cases, producing **218.900 K** and **212.624 K**, respectively. In the actual full severe-contact scenario the upper Cu heat load is **21.697 mW** (because the entire detector/stage temperature field responds), versus **87.173 mW** in the fully coupled nominal case. The upper-stage hot-side temperature falls from **247.359 K** to **238.856 K**.

This makes the Cu joint interface a high-leverage **design and validation** variable. An intentionally resistive thermal bridge may conflict with the purpose of a continuous electrically low-resistance conductor; specifying separate electrical and thermal requirements is essential. A physically manufacturable reduced heat path, such as patterned foil geometry with sufficient electrical cross-section, should be evaluated before assuming an unusually poorly conducting solder interface.

## Numerical acceptance and evidence

All three scenarios use the frozen V3.4 model and exact unchanged 88-leg nonlinear transport, the original four 3D ceramic meshes, optical cavity and package heat paths. The only new modifications are **which native ceramic faces receive terminal-lead heat** and the declared lead/contact scenario. The original synthetic 824-solid CAD source is unchanged. There are **zero** new full 430-domain electrothermal FEM claims.

| Full solve | Outer iterations | Final pad update (K) | Independent maximum stage balance residual (W) | Global balance residual magnitude (W) |
|---|---:|---:|---:|---:|
| Corrected copper | 18 | 1.7670×10⁻⁷ | 1.0825×10⁻⁹ | 9.3764×10⁻¹⁰ |
| Nickel-like power leads | 16 | 2.4410×10⁻⁷ | 1.4098×10⁻⁹ | 1.2049×10⁻⁹ |
| Severe interstage thermal contact R | 14 | 1.4563×10⁻⁷ | 5.6330×10⁻¹¹ | 4.5766×10⁻¹¹ |

All satisfy the registered pad temperature update threshold **3×10⁻⁷ K**, 1×10⁻⁸ W stage and global balance bounds, 5×10⁻⁸ W ceramic native face-balance condition, and individual-leg heat transport checks. **Independent audit source** re-derives from original saved source CAD each power wire's \(R,G,Q_i,P_J\), the three-branch Cu foil equations with their explicit intermediate return landing, every stage heat balance, source terminal voltage, global electrical power, and the external pin-side half-Joule allocation, without importing the V3.5 or V3.4 nonlinear solvers.

The initial copper case had two quick **preflight STOP** conditions because the first start used a V3.4 solution without reconstructing all frozen V3.4 Cu and cavity fluxes at the source pad. Those preflight logs were preserved; the correct seed explicitly includes all original signed source Cu and external cavity heat terms. No source physics was weakened to pass a gate.

The correct benchmark is not a single detector temperature. It is the complete operating state including \(I,V,P,T_i,Q_h,Q_c,Q_{\rm sink}\) and consistent signed boundary and Joule heat accounting under clearly stated material assumptions.

## Primary reproduction artifacts

- [Revised power lead source geometry and selected material laws](../scripts/v3_5_supply_lead_boundary.py)
- [Complete source-integrated coupled V3.5 nonlinear model](../scripts/v3_5_power_lead_and_copper_sensitivity.py)
- [Independent no-PDE physical energy audit](../scripts/v3_5_independent_energy_audit.py)
- [Six lead geometry and physical checks](../tests/test_v3_5_source_tec_leads.py)
- [Frozen original-face scenario screen](../data/v3_5_power_lead_and_copper_sensitivity_20261108/fixed_source_field_screen.json)
- [Nominal copper accepted result and spatial field](../data/v3_5_power_lead_and_copper_sensitivity_20261108/copper_native_pad/)
- [Nickel-like lead accepted result and spatial field](../data/v3_5_power_lead_and_copper_sensitivity_20261108/nickel_native_pad/)
- [Severe interstage contact accepted result and spatial field](../data/v3_5_power_lead_and_copper_sensitivity_20261108/high_interstage_contact_R/)
- [All three report figures and source hashes](../reports/current/v35_figure_provenance.json)
- [Original historical Rev3 methods](../reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf), unrelated old 216/28/12/4 design, frozen byte-identically.

## Next physically meaningful step

The large V3.5 change associated with the hypothesized \(r_{T,c}''\) should not be interpreted as measured uncertainty. The next step is an **intermediate realistic thermal-resistance and actual plating-layer heat-path study**, not claiming the extreme thermal resistance is desirable. Evaluate physically credible 20–35 µm Sn-based solder conductivity and effective joint geometry; include metal-sheet spreading/foil bends and coupled electrical current crowding in small source-based components. Run a short matched-current operating sweep once those component laws are bounded, continuing to distinguish global numerical convergence, material-property plausibility, geometric qualification and empirical validation. The very long leads shipped by the vendor should be modeled **only according to their final installed ceramic-to-pin route**.
