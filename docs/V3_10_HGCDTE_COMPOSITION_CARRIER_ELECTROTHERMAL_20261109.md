# V3.10 — Composition-aware HgCdTe photoconductor electrically coupled to a three-stage TEC and TO package

**9 November 2026 | Seven accepted whole-device electrothermal simulations | Conditionally realistic carrier model, no measured detector-grade calibration**

## Executive engineering result

The model no longer needs to impose an arbitrary constant 500 Ω or invented effective dark-resistance activation slope to calculate HgCdTe bias Joule heating. A separate **source-backed composition/temperature-dependent nondegenerate carrier calculation** computes intrinsic carrier concentration and bulk dark conductivity, then couples detector current and resistive heating back to the existing full TEC/ceramic/metal/package thermal solution. The published bandgap and intrinsic-concentration formulas are real semiconductor-material relationships. **The selected alloy composition, fully ionized net acceptor concentration, 400 × 100 × 10 µm detector channel, carrier mobilities and electron/hole mobility ratios remain explicitly unmeasured hypotheses.** No hardware calibration is claimed.

At fixed 0.400 A TEC current, 300 K mount, 100 Pa Kr, 0.500 mW assumed *absorbed* optical heating and 0.35 V separate detector bias:

| Alloy Cd fraction | Idealized Eg-derived threshold (µm) | Dark channel resistance (Ω) | Bias Joule (mW) | HgCdTe temperature (K) |
|---:|---:|---:|---:|---:|
| x=0.20 | **9.645** | **68.812** | **1.780** | **218.987** |
| x=0.22 | 7.859 | 178.061 | 0.688 | 218.648 |
| x=0.24 | 6.636 | 596.601 | 0.205 | 218.498 |
| x=0.29 | 4.788 | 8506.234 | 0.0144 | 218.439 |

The four cases deliberately also use different *hypothesized* hole mobilities, respectively 450, 450, 400, and 220 cm²/(V·s). They **are not a controlled x-only experiment**, and the wavelength values are **hc/Eg estimates, NOT measured 50%-response spectral cutoffs**. The model does not yet calculate quantum efficiency, photoresponse or detectivity, so lower bias power at larger x cannot be interpreted as better IR-detector performance.

**Controlled operating checks** at x=0.20, 10¹⁶ cm⁻³ acceptors and 450 cm²/(V·s) hole mobility:
- 0 V bias (0.5 mW absorbed optical heat alone): **218.434031 K**, zero bias Joule, 69.657 Ω.
- 0.35 V bias: **218.987142 K**, 1.780 mW bias Joule, 68.812 Ω.
- 0.65 V bias: **220.404357 K**, 6.333 mW bias Joule, 66.713 Ω.
- At 0.35 V and net acceptors reduced from 10¹⁶ to 10¹⁵ cm⁻³: **219.226893 K**, 2.551 mW Joule, 48.016 Ω.

This is a meaningful whole-device bias/temperature tradeoff: at x=0.20, increasing detector bias from 0.35 to 0.65 V raises the predicted chip temperature by **1.417 K** under this hypothetical conduction law. The detector and TEC electrical supplies remain distinct; the reported TEC terminal input near **0.595 W** excludes the external detector-bias supply. A power-budget total must count TEC electrical input **plus** detector bias power (and any real driver losses).

## Physical material relations and published provenance

The composition and temperature-dependent Hansen–Schmit–Casselman bandgap relation, Eg in electronvolts, is

\[
E_g(x,T)=-0.302+1.930x-0.810x^2+0.832x^3
+5.35\times10^{-4}(1-2x)T.
\]

Original: G. L. Hansen, J. L. Schmit and T. N. Casselman, *Journal of Applied Physics* **53**, 7099 (1982), [DOI: 10.1063/1.330018](https://doi.org/10.1063/1.330018).

Hansen and Schmit's empirical nondegenerate intrinsic carrier formula (n_i in cm⁻³) is

\[
n_i(x,T)=
(5.585-3.820x+0.001753T-0.001364xT)
\times10^{14}\,E_g^{3/4}T^{3/2}
\exp\left[-\frac{E_g}{2k_BT}\right].
\]

Original: G. L. Hansen and J. L. Schmit, *Journal of Applied Physics* (1983), [DOI: 10.1063/1.332153](https://doi.org/10.1063/1.332153). The source expression is restricted here to **0.16 ≤ x ≤ 0.40 and 50 K < T ≤ 300 K**, and strictly positive Eg, so the numerical code refuses unsupported inputs instead of extrapolating. This limited domain is compatible with the computed 218–221 K semiconductor states.

For uniform **p-type, nondegenerate, fully ionized** channel net acceptors N = N_A−N_D with thermal equilibrium carrier product \(np=n_i^2\),

\[
p=\frac{N+\sqrt{N^2+4n_i^2}}{2},\qquad
n=\frac{n_i^2}{p}.
\]

With assumed hole/electron mobilities \(\mu_h,\mu_e\) and a rectangular, uniform, contact-free Ohmic resistor,

\[
\sigma_d=q(p\mu_h+n\mu_e),\qquad
R_d(T)=\frac{L}{W\,t\,\sigma_d(T)},\qquad
P_{\rm Joule}(T)=\frac{V_d^2}{R_d(T)}.
\]

The charge-neutrality and channel-conductivity form is also explicitly described in [Pan et al., *Advanced Materials Interfaces* (2022/2023), DOI 10.1002/admi.202201932](https://doi.org/10.1002/admi.202201932). Representative independent p-type HgCdTe samples have reported x≈0.22 hole mobility 400–580 cm²/(V·s), x≈0.30–0.38 200–220 cm²/(V·s), from [*Thin Solid Films*, S0040609013018300](https://www.sciencedirect.com/science/article/abs/pii/S0040609013018300). These mobilities are **not from a matched specimen set or our simulated package**. We have assumed \(\mu_e/\mu_h=100\), held mobility independent of temperature and dopant density, without enforcing minority carrier scattering, high electric-field effects or degeneracy corrections.

The model evaluates the exact analytical conductivity logarithmic-temperature derivative under these stated hypotheses and feeds \(\partial P_{\rm Joule}/\partial T\) consistently into its electrothermal consistency checks. It additionally reports **ideal equilibrium Johnson noise spectral densities** \(\sqrt{4k_BTR}\) V/√Hz and \(\sqrt{4k_BT/R}\) A/√Hz, which must **not** be confused with complete HgCdTe measured noise: generation–recombination, 1/f, shot, amplifier, contact and illuminated noise remain unmodeled. There is no responsivity, quantum efficiency, or D* prediction.

## Coupled model hardware and numerical verification

The existing **29/11/4-couple three-stage TEC** source geometry is unchanged. Every accepted full-device operating point retains:
- All **88** P/N nonlinear 32-interval axial transport elements with original research-source temperature-dependent laws.
- **Four actual source-coordinate three-dimensional ceramic FEM temperature fields**, totaling **11,791 tetrahedral elements**.
- The previously integrated source CAD copper-foil interstage nets 58, 80, and three-landing net 88 return, source-placed terminal leads and separate detector Au bonds; source-constrained TO package header thermal reservoir.
- Effective 100 Pa Kr gas and gray-radiation cavity models, plus finite external mounting resistance **4.833 K/W**. These are existing engineering proxies, not fully resolved 430-volume current/thermal fields.

For each of the seven scenarios, a **second, separate no-FEM-solve verifier** reconstructs HSC Eg(x,T), intrinsic n_i, p and n via charge neutrality, absolute channel resistance and detector Joule power, its analytic derivative and Johnson amplitudes *without importing the main detector transport function*. It separately reconstructs the source Cu and lead resistor/conductor network, all three stage balances, package sink boundary and global heat conservation. Saved original FEM nodal arrays are retained.

Independent energy closure **does not establish physical validity of unmeasured mobility, channel thickness, surface contact law, lifetime or optical absorption**. The original 430-domain global bulk metal/semiconductor 3D PDE and source interface raw-gradient release gates remain unsatisfied/unchanged.

## Scientific significance and next productive work

The new material law predicts strong **composition-dependent thermal/electrical bias coupling**, and reveals an important missing measurement requirement: actual dark resistance cannot be responsibly inferred from bandgap alone. It depends on geometry, doping, both mobilities, nondegenerate vs degenerate statistics, surfaces, contacts and temperature, **and** the real photoconductor bias regime. The selected 400 × 100 × 10 µm channel lives *within* a 1-mm die but is hypothetical; the specific die's actual electrode spacing and active cross-section are unknown.

**Do not claim a highly accurate LWIR detector model merely because x=0.20 gives ~9.6 µm Eg threshold at 219 K.** Detector wavelength performance requires finite absorption, composition/active layer, carrier lifetime, gain, noise, Johnson and non-Johnson sources and signal amplification. Real Pb/Hg/Cd composition and 3D thermal transport may also alter source die heat conduction/attach compared with fixed thermal proxy assumptions.

The next practical model milestone is to introduce optical photon energy relative to the calculated gap, temperature-dependent absorption **with explicit thickness, window transmission and carrier lifetime**, photoconductive excess-carrier signal at the given bias, and physically bounded G–R/1/f noise. It should be **source-backed and opt-in**, not fitted to undocumented hypothetical measurements. Only then can the TEC’s operating point be evaluated against **actual signal-to-noise or detector figure-of-merit** rather than temperature alone. A second independent check should evaluate photoresponse limiting behavior and thermal/optical power energy conservation.

## Source and reproduction

- [Main new equilibrium carrier transport equations](../tecooledmct/hgcdte_carrier_transport_v310.py)
- [Full source-geometry TEC + HgCdTe nonlinear coupled solver](../scripts/v3_10_hgcdte_carrier_coupled.py)
- [Independent semiconductor and whole-TEC energy verification](../scripts/v3_10_independent_hgcdte_carrier_audit.py)
- [Scientific regression tests](../tests/test_v3_10_hgcdte_carrier.py)
- [Complete 7-case registered input, original 3D ceramic, nonlinear and independent audit evidence](../data/v3_10_hgcdte_carrier_20261109/)
- [Composition-dependent dark resistance and Joule heat figure](../reports/current/figures/v310_composition_resistance_and_joule.pdf)
- [Actual coupled detector temperature figure](../reports/current/figures/v310_coupled_detector_temperature.pdf)
- [Prior V3.9 high-T TEC material source audit](V3_9_MATERIAL_SOURCE_HIGH_T_QUALIFICATION_20261109.md)
- [Stable cumulative 30-page engineering assessment](../reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf), **unchanged**

Neither source 38-page Rev3 nor its geometry, nor previous source-based model results have been modified. V3.10 is a distinct engineering-physics increment documented standalone so the current cumulative report can be professionally revised later rather than churned.
