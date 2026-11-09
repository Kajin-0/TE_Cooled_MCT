# V3.4 — Interstage copper heat leakage in the three-stage HgCdTe cooler

**8 November 2026 (U.S. Eastern) / 9 November UTC | One accepted conditional model operating point | Hardware-physics assessment, not OEM validation**

## Engineering question and result

How much does heat conduction through the **actual copper foil connections** degrade detector cooling in the existing replacement TEC? The previous V3.3 system models 88 nonlinear P/N legs and 11,791 genuine 3D ceramic tetrahedra but did not include nonlocal thermal bypass through its formed interstage Cu foil.

V3.4 reuses that exact cooler, package, current and 100 Pa krypton case and adds a conservative **three-branch copper electrothermal multiport** coupled to original source CAD ceramic-face heat and temperature maps.

| Quantity | V3.3, without formed Cu coupling | V3.4, with provisional formed Cu coupling | Difference |
|---|---:|---:|---:|
| HgCdTe detector temperature | 210.625214 K | **218.832895 K** | **+8.207681 K** |
| Cooling below 300 K | 89.374786 K | **81.167105 K** | −8.207681 K |
| TEC terminal voltage | 1.522462416 V | **1.489439543 V** | −0.033022873 V |
| Electrical input | 0.608984966 W | **0.595775817 W** | −0.013209149 W |
| Heat rejected to reservoir | 0.594043746 W | **0.579830239 W** | −0.014213507 W |

Both cases: 0.400 A applied TEC current, 300 K reservoir, 2 mW imposed detector load, 100 Pa krypton, matching synthetic thermoelectric and cavity laws.

**Hardware conclusion:** under these uncalibrated contact and material assumptions, the cooler consumes slightly less electrical power but cools the HgCdTe detector approximately **8.2 K less effectively**. The principal mechanism is *nonlocal copper heat bypass*, not the copper's 2.08 mW of additional electrical dissipation. This is an **accepted numerical comparison within a provisional physical model**, not a validated measurement or a temperature accuracy interval.

## Source construction and exact thermal contact mapping

No CAD was modified. The three formed-foil bodies are physically present in the previously qualified synthetic V3 R1 824-solid STEP assembly; V3.4 reads original source arc/line geometry, the 430-domain metal/ceramic face owners, and native ceramic FEM patch temperatures.

| Metal electrical net | Native ceramic thermal face tags | Contacts | Foil length between solder-foot centers |
|---|---|---|---:|
| 58 | 38 → 75 | Ceramic0 → Ceramic1 | 1.660619 mm |
| 80 | 79 → 105 | Ceramic1 → Ceramic2 | 1.670619 mm |
| 88 | 36 → 74 → 104 | Ceramic0 → Ceramic1 → Ceramic2 | 1.660619 + 1.745619 mm |

The full *free-body* centerline lengths 1.960619, 1.970619 and 3.706239 mm are **not** identical to the conduction paths between actual solder-foot centroids. All foil cross sections are 0.300 × 0.030 mm (9.0×10⁻⁹ m²). Every solder-foot overlap is 0.300 × 0.200 mm (0.060 mm²). The intermediate contact on net88 is **a third explicit thermal port**; there is no fictitious direct zero-resistance connection or adiabatic middle support.

## Constitutive assumptions and coupled equations

The provisional foil reference law is

\[
\rho_{\mathrm{Cu}}(T)=1.724\times10^{-8}\,[1+0.0039(T-293.15)]\ \Omega\,\mathrm{m},
\qquad
k_{\mathrm{Cu}}=385\ \mathrm{W/(m\,K)}.
\]

For each foil segment of length L and cross-section A,

\[
R_{ij}^{e}=\rho_{\mathrm{Cu}}((T_i+T_j)/2)L/A,\qquad
G_{ij}^{th}=k_{\mathrm{Cu}}A/L.
\]

Contact areal hypotheses are **not measured**: electrical \(r_e''=10^{-11}\ \Omega\,\mathrm{m^2}\) and thermal \(r_T''=10^{-6}\ \mathrm{m^2\,K/W}\). The nonlinear system solves the three- or two-node foil thermal network with each actual ceramic-pad temperature prescribed by the *iterated source 3D ceramic FEM*:

\[
\sum_jG_{ij}^{th}(T_i^{foil}-T_j^{foil})+
\frac{A_{c,i}}{r_T''}(T_i^{foil}-T_i^{pad})
=P_{J,i}^{foil}.
\]

Axial foil Joule heat is split between its two adjoining thermal nodes, while each electrical-contact Joule term is placed on its source ceramic face. Net heat into the ceramic equals contact conduction plus deposited electrical-contact Joule heat. The model independently verifies \(\sum_i Q_{Cu\to ceramic,i}=I^2R_{Cu,network}\). The V3.3 leg, ceramic, sink and enclosure governing equations are otherwise unchanged.

**Constitutive limits:** the electrical coefficient is a near-room-temperature copper approximation extrapolated below 273 K, and 385 W/mK is not a certificate for this formed-foil grade. The foil has a selected finite contact resistance but is not solved with a full 3D current-crowding/temperature PDE. Native plated metal trace conduction, solder thermo-electric interface/Peltier physics, temperature-dependent foil k, graded/aged contacts, and actual hardware properties remain unqualified.

## Observed copper heat redistribution

**Signs:** heat *into* a ceramic is positive; heat *removed from* a ceramic is negative.

| Copper connection | Hot ceramic0 | Middle ceramic1 | Upper ceramic2 | Copper + contact Joule |
|---|---:|---:|---:|---:|
| Net58 | −54.594 mW | +55.141 mW | 0 | 0.547 mW |
| Net80 | 0 | −40.619 mW | +41.115 mW | 0.496 mW |
| Net88 | −53.881 mW | +9.044 mW | +45.875 mW | 1.038 mW |
| **Total** | **−108.475 mW** | **+23.566 mW** | **+86.989 mW** | **2.080 mW** |

The network **transfers** large amounts of heat; it does not create 108 mW of extra external power. It generates 2.080 mW of Joule heat and redistributes the remaining internal heat among ceramics. The upper stage hot ceramic increases from 236.157 K to 247.269 K. The third stage cold-side heat pumping remains 4.910 mW in V3.4, but with a much warmer hot boundary the HgCdTe settles to 218.833 K.

## Convergence and independent acceptance

- **First attempt:** 12-iteration STOP. Maximum pad-temperature change 1.02134×10⁻⁴ K exceeded prescribed 2×10⁻⁵ K. The nonconverged output was rejected, and source/registration/log preserved.
- **Second attempt:** 14-iteration STOP. Pad change 1.55261×10⁻⁵ K passed the preliminary threshold, but independent recomputed stage heat imbalance 8.83096×10⁻⁸ W exceeded 1×10⁻⁸ W. Source and rejection record preserved.
- **Accepted third attempt:** only a stricter pad update gate and larger cap changed (tolerance **3×10⁻⁷ K**, maximum **22 iterations**). It converged in **19 iterations** without changing geometry, material laws, copper contact properties, current, ambient or detector load.

| Independently checked acceptance | Numerical value |
|---|---:|
| Last local ceramic pad-temperature change | 1.39917×10⁻⁷ K |
| Reconstructed largest stage heat residual | 7.95874×10⁻¹⁰ W |
| Global electrothermal residual | 6.77452×10⁻¹⁰ W |
| Native ceramic FEM net heat imbalance | 1.75554×10⁻¹⁵ W |
| Reconstructed copper heat minus Cu electrical work | −8.40474×10⁻¹⁶ W |
| Independent copper-network face-flux recomputation difference | 0 in saved floating-point representation |

Two independent no-solve checks were completed. The first verifies stage, pad and global energy from saved results. A **second independent algebraic implementation** recomputes each Cu branch from the archived lengths, material equations, actual face temperatures and contact area without importing the V3.4 Cu solver code, then reconstructs its heat and stage balances. Both pass; neither reruns a PDE. Six focused physical/network tests also pass. The old V3.3 result remains unmodified (SHA-256: a7679d0c69b1d53f9fc7b289eb8596af4bac856fa3f3d9ade83b263f998bbd58).

**Accepted V3.4 result SHA-256:** 2aa84432098907c3ac37d276fa3b430652ac77ce53a5fbac1174828b9e5d63bb.

## Source evidence and reproduction files

- [Accepted V3.4 full numerical result](../data/v3_4_copper_multiport_20261108/attempt03/result.json)
- [Registered inputs and strict gate](../data/v3_4_copper_multiport_20261108/attempt03/registration.json)
- [Independent read-only acceptance](../data/v3_4_copper_multiport_20261108/attempt03/independent_read_only_acceptance.json)
- [Actual four-ceramic 3D nodal fields](../data/v3_4_copper_multiport_20261108/attempt03/source_native_ceramics_V3_4.npz)
- [Copper CAD-foot multiport implementation](../scripts/v3_4_source_copper_multiport.py)
- [Coupled nonlinear 88-leg / original 3D ceramic / package implementation](../scripts/v3_4_source_copper_feedback.py)
- [Independent no-solve audit source](../scripts/v3_4_copper_read_only_audit.py)
- [Independent separate-equation copper reconstruction](../scripts/v3_4_independent_multiport_reconstruction.py) and [archived PASS result](../data/v3_4_copper_multiport_20261108/attempt03/independent_physics_reconstruction.json)
- [Six focused verification tests](../tests/test_v3_4_copper_multiport.py)
- [Attempt01 STOP evidence](../data/v3_4_copper_multiport_20261108/attempt01/nonconvergence_receipt.json) and [attempt02 STOP evidence](../data/v3_4_copper_multiport_20261108/attempt02/independent_stop_receipt.json)
- [Previous immutable V3.3 source result](../data/v3_3_cavity_package_feedback_20261108/attempt02/result.json)

Original global 430-domain Gate B remains **FAIL/STOP**, source first-couple raw gradient 8/8 **FAIL**, prospective P2 **STOP**, and whole-device full-source electrical/thermal C/D **NOT RUN**. This is **not** a new complete 430-domain FEM or measured detector-performance claim.

## Next engineering priority

The source-derived copper bypass is no longer wholly missing, but its **magnitude remains uncertain**. Next bound the foil's k(T), rho(T) and actual grade/purity, 0.03 mm formed-section tolerances, plated-face spreading, electrical/thermal solder interface impedances, middle-return thermal landing, and stage-dependent heat-load response. Use fast *fixed-temperature* copper-network perturbations to rank possible impact; only expensive full-system recomputations should receive the highest-impact credible cases. Do not substitute arbitrarily small FEM residuals for calibrated device accuracy.

For material source follow-up, see NIST [OFHC copper thermal conductivity versus RRR](https://trc.nist.gov/cryogenics/materials/OFHC%20Copper/OFHC_Copper_rev1.htm), [Properties of Selected Materials at Cryogenic Temperatures](https://www.nist.gov/publications/properties-selected-materials-cryogenic-temperatures), and the NBS/NIST [Copper wire resistance coefficient near room temperature](https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook100.pdf). None measures the properties of this specific formed foil.
