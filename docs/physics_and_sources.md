# Governing equations and provenance

## Effective three-stage thermoelectric network

Ordered from bottom/hot to top/cold, with **the same series current** I through the effective stages:

- Qc_i = alpha_i I Tc_i - 0.5 I² Ri - Ki(Th_i-Tc_i)
- Qh_i = alpha_i I Th_i + 0.5 I² Ri - Ki(Th_i-Tc_i)
- Vi = I Ri + alpha_i (Th_i-Tc_i)
- Qh_i - Qc_i = I Vi (energy conservation check)

Four simultaneous balances: Qc1=Qh2+parasitic1; Qc2=Qh3+parasitic2; Qc3=detector+parasitic3; Th=Tamb+R_sink Qh1. scipy.optimize.least_squares solves for three junction temperatures and one hot-side temperature. Unconverged states are rejected.

**Caveat:** This constant-effective-coefficient network omits temperature-dependent Seebeck, Thomson heating, full transport PDE, true interstage topology, local gradient and thermal contacts. Intermediate nodes are nominal effective thermoelectric junction temperatures, not calibrated ceramic thermistor measurements.

## Verified vs inferred material and geometry

**OEM source:** TEC Microsystems 2019 datasheet for 3MC04-044-05. Footprints 6.4×6.4 and 2.4×2.4 mm, height 3.8 ± 0.15 mm, 44 couples, AC electrical resistance about 2.9 Ω; 300 K vacuum reference ΔTmax ~113 K and Qmax ~0.5 W at their distinct test limits.

**Inferred:** Stage split 28/12/4 couples; leg lengths [1.07, 0.82, 0.64] mm; area 0.4×0.4 mm each; initial differential Seebeck ~420 µV/K/couple; resistivity ~5.5 µΩ·m; k ~1.45 W/m/K. Electrical resistances normalized to OEM nominal 2.89 Ω; effective Seebeck and thermal conductance multipliers are adjusted to two manufacturer limiting points. Those multipliers should NOT be mistaken for measured bulk Bi2Te3 coefficients.

**Package priors:** 3 mm effective gas gap; hot-side thermal resistance 2 K/W; nominal four bonds 18 µm diameter × 7 mm length; k_wire ~315 W/m/K; emissivities 0.7 (cap), 0.5 (cold), and view factor 0.7; a constant 100 Ω MCT resistor biased at 0.5 V. All illustrative.

## Gas conduction and noncontinuum caveats

Approximate reference k at 300 K (W/m/K): N2 0.02583; Ar 0.01772; Kr 0.00943. Effective k(T,p) = k300*(T/300)^0.75/[1+a*lambda(T,p)/gap]. Mean free path scales T/p. This is a *first-order model*, not a pressure/gas accommodation validated fluid calculation. Mixtures currently have linearly mole-fraction-weighted properties: **not a precision mixing law**.

An indicative Rayleigh number and a heuristic Nusselt correction are reported, not resolved CFD. Sealed sub-centimeter cavities generally have low natural convection but orientation/geometry/pressure require verification. Pressure-dependent, temperature-dependent real mixture transport data and gas-surface accommodation values are needed for accuracy. At sufficiently low pressure, rarefied gas physics replaces continuum conduction.

## Radiation / aperture

Greybody effective-emissivity model: Qrad = epsilon_eff sigma F A (Tcap^4 - Tstage^4), epsilon_eff=1/(1/epsilon_cap+1/epsilon_stage-1). The additional warm-aperture function adds radiation from a surface at a specified temperature. It **does not** simulate the beneficial warm-surface masking effect of a cold shield. Future model requires view-factor/radiosity matrix, angular acceptance, baffle temperature and support conductance.

## Detector

Nominal self-heating P=V_bias²/R_detector plus absorbed optical power and thermistor dissipation. No MCT R(T), photoconductive response or spectral absorption model is yet provided. A 0.5 V bias over 100 Ω gives 2.5 mW; this value is a chosen example, not a device measurement.

## Transient and uncertainty

The 4-node transient uses assumed heat capacities and a stiff ODE integrator. Do **not** infer cooldown time of a real unit.

Uncertainty varies analyst-chosen ranges in gap multiplier, wire diameter, emissivity, sink resistance and detector resistance. Reported P05/P95 are prior-driven sensitivity intervals, **not statistically calibrated predictive intervals**. Important uncertain terms omitted include materials, interstage couple allocation, internal electrical contacts and package view factors.

## Primary sources

- TEC: https://www.tec-microsystems.com/Download/Datasheets/Thermoelectric%20Coolers/MC04%20Series/3MC04-044-05_Datasheet_2019.pdf
- TEC family: https://tec-microsystems.com/products/thermoelectric-coolers/3mc04-series-thermoelectric-coolers.html
- TO66 detector: https://vigophotonics.com/app/uploads/2024/07/3TE-TO669p-wW-PVI_PCI-detector-technical-drawing.pdf
- Thermoelectric governing physics: https://doc.comsol.com/6.4/doc/com.comsol.help.heat/heat_ug_theory.07.087.html
- Gas reference sources to check: https://webbook.nist.gov/chemistry/ and https://www.nist.gov/srd/refprop

Vendor materials remain copyright their respective owners; no external datasheet has been reproduced.
