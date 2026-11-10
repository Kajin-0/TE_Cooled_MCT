# V3.13 — Original-CAD net88 port and local 3D qualification audit

**9 November 2026 | New source-audited port matrix; historical 3D Gate B remains FAIL/STOP | No PDE solves**

## Engineering question

Can the existing source-CAD three-foot formed-Cu return net88 be promoted from the accepted reduced multiport model into a physically trustworthy, local spatial 3D electrical/thermal coupon? **Not yet.** A source-grounded reconstruction of the reduced three-thermal-port response is successful, but the archived original 3D electrical coupon fails its unrelaxed raw one-sided contact-current gate. The necessary thermal coupon C and coupled Joule coupon D are therefore **not run**. This is an evidence-based stop, not a missing confirmation of success.

## Existing net88 three-ceramic-port behavior (reconstructed)

Source original ceramic tags: **36, 74, 104**, for the hot, middle and upper ceramic landings, respectively. At 0.400 A, the original accepted V3.5 plate temperatures are **299.3163, 271.5892, and 247.8891 K**. This thermal port matrix was reconstructed using three one-kelvin unit perturbations around 300 K in the **current source-derived reduced conductor law**, including all three idealized contact surfaces. No 3D PDE, new terminal, or synthetic remeshing was performed. The sign is **heat INTO coupon**:

\[
\mathbf Q_{\rm into\ foil}=\mathbf G\mathbf T,
\qquad\mathbf G=10^{-3}
\begin{bmatrix}
1.952853&-1.892256&-0.060596\\
-1.892256&3.695323&-1.803067\\
-0.060596&-1.803067&1.863663
\end{bmatrix}\ \mathrm{W/K}.
\]

The full-precision matrix in `data/v3_13_native_foil_port_readiness_20261109/port_readiness.json` is symmetric and positive semidefinite (one uniform-temperature zero eigenvalue), with near-zero row and column sums. This is a useful interface *contract* for comparing a future 3D spatial solver. It does **not** prove the reduced law reproduces 3D current crowding or lateral spreading. The original 0.4 A source-accepted foil-foot heat and Joule allocations reconstruct to numerical roundoff.

## A specific electrical-topology discrepancy at the middle foot

The physical CAD `tab_joint5` (Bi57Sn43 family, source `SnBi57_43`) is a **thermally connected middle ceramic landing**, but the historical physical 3D coupon registers its `tab88`→`joint5` contact as an **electrically dead-end branch**. In the archived original P2 source, its expected current fraction is exactly zero, and its weak-form signed terminal-to-contact current under 1 V unit excitation is approximately **−2.93×10⁻⁹ A**.

The current **reduced** net88 source model sums the finite electrical contact resistance at all three landing pads into the copper *series* electrical resistance and deposits (I^2 r''_e/A_c\) Joule heat at each. For the middle foot, at (r''_e=10^{-11}\ \Omega\mathrm{m^2}\), (A_c=0.060\ \mathrm{mm^2}\), and (I=0.400\) A:

\[
R_{c,\mathrm{middle}}=1.66667\times 10^{-4}\ \Omega,\qquad
P_{J,\mathrm{middle}}=26.667\ \mathrm{\mu W}.
\]

If the 3D topology's zero branch current is carried into the full reduced model, that **26.667 µW** is a prospective contact Joule overcount. The nominal net88 reduced resistance **0.00649364 Ω** would become **0.00632697 Ω** under the simple series-contact-count correction. This **does not establish a new fully coupled voltage or detector temperature**, because the correct local current field, physical contact heating distribution and ceramic feedback would need recomputing. It is small in absolute thermal power but exposes a genuine electrical network-ownership mismatch that should be fixed in a *new* candidate solver with complete regression and conservation checks, never by rewriting accepted archived scalar outputs. Do not remove the middle **thermal** landing.

## Historical 3D coupon: strict gates preserved

Original frozen coupon: net88 formed foil, three Bi57Sn43 solder feet, anisotropic multilayer metal films, full lead9 and pin finish plus a SnSb P87 cut, with 12 material regions in the fine mesh and **28,691 original TET4**. Physical electrical ports are **internal P87 solder cut to pin9 head cut**; these are not independent external TEC terminals. Three ceramic underside thermal ports and two other thermal cuts are defined; surrounding omitted domains must not be silently assigned a 300 K wall.

| Electrical numerical metric | Original 3D P1 | Subsequent original-mesh P2 | Required gate |
| --- | ---: | ---: | ---: |
| Worst independent one-sided raw current cut mismatch | **85.6255%** | **8.0993%** | ≤0.1% |
| Registered raw cuts failed | 13 of 16 | 11 of 16 | 0 |
| P2 minimum potential | — | **−9.15×10⁻⁷ V** | ≥−1×10⁻⁸ V |
| P2 IV vs bulk+contact dissipation | — | **6.34×10⁻⁹ relative** | ≤0.5% |

The 3D model is weak-form/current-reaction and power conservative, and P2 improves raw contact gradients, but the primary raw-gradient and boundedness gates still fail. **Good total IV balance does not validate the detailed interfacial current density.** Original source and failures remain unchanged. The electrical B gate is FAIL/STOP and downstream thermal C and coupled Joule D remain NOT RUN.

## Minimal next release path

1. Create a **new** prospective local electrical source-contact formulation that respects the actual dead-end middle electrical branch, all 11 separate material interfaces, and the original P87/pin9 cut-port contract; preserve the source CAD exactly.
2. Audit both one-sided raw current gradients at all contact interfaces under source-registered unit current, plus voltage boundedness, mesh/geometry accuracy, and IV loss closure. **Do not reduce the 0.1% criterion or substitute weak reaction currents for raw gradients.** Use a single preregistered bounded attempt; stop on failure.
3. **Only after electrical B passes**, solve local spatial heat spreading and all five defined thermal ports, including distinct Bi57Sn43 joining feet, 3D films, copper bends and prescribed reservoirs. Compare the resulting symmetric PSD thermal G against the reduced source three-port contract under identical physical port values, with independently audited heat-flux closure and resolution.
4. Only after thermal port release, enable spatial Joule heating/contact sources and compare them against the accepted reduced multiport at fixed original ceramic temperatures. A new entire-TEC detector temperature prediction requires a later fully coupled 88-leg/four-ceramic re-solve and independent energy audit.

**Corrective material provenance:** The original V3.12 publication mistakenly used Sn95Sb5 thermoelectric-leg solder properties for the foil joining feet. That attribution is corrected in the subsequent revised V3.12 source screen: original `tab_joint0...6` are labeled Bi57Sn43. An adjacent Bi58Sn42 thermal conductivity of 19 W/(m K) at 85°C is only a provisional alloy-family analog, not a calibrated 300 K or cryogenic curve. See [Indium's alloy selection chart](https://scp.indium.com/download-files/solder_research_kit_information_97699_r5).

**Reproducer:** `scripts/v3_13_native_foil_port_readiness.py` with sealed `data/v3_13_native_foil_port_readiness_20261109/port_readiness.json`. Original source mesh, P1/P2 failed cases and previous complete reports are preserved.
