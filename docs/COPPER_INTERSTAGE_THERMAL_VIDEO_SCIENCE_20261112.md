# Copper-interconnect thermal bypass: video science register

**Status:** Video production in progress. Original-only V3.27 nominal model. Numerical comparison and independent audits passed; the visual is not measured hardware or a complete cavity thermal solution.

## What the 3D animation represents

The 3D cooler geometry is reconstructed in **Blender 4.3.2** directly from the public source-design registry `data/synthetic_v3_assembly_20261102/source_final/design.json` (824 source bodies). Ceramic plates, P and N elements, source-copper formed tabs (nets 58, 80 and 88), material contacts, and detector have their **source millimeter coordinates and dimensions**, including the 0.50 mm original P/N height.

For animation efficiency the source `boxes` solids are joined into meshes by physical material. The three formed-copper paths are reconstructed from their original line/arc definitions and width/thickness values. This is source-derived 3D geometry, **not a 3D thermal finite-element solution for all materials**. Animated bright points are **schematic flow indicators**, not streamlines or temperature-contour output. Package/cap, pin, and extended detector-bond-wire details are hidden from the source-derived close-up for readability; the source CAD itself is unchanged. This film does not represent an exact photograph or a verified manufacturer device.

The original source synthetic CAD assembly is available as `data/synthetic_v3_assembly_20261102/cad_02/synthetic_v3_mm.step`. The production scene does not claim to import this STEP tessellation directly; it reconstructs the source registry geometries for animation. The registry is the source design from which that STEP assembly was produced.

## Published numerical comparison

Both conditions share:
- nominal original 29/11/4 TEC, 88 nonlinear P/N legs and source FEM ceramics,
- 300 K reservoir, 100 Pa Kr, gas accommodation 0.8,
- imposed 2.0 mW die heat,
- matched **0.59566803496 W** terminal electrical input,
- V3.27 selected source-derived P1 gas paths plus die/window path,
- unselected gas boundaries held adiabatic (incomplete gas-cavity coverage).

| Quantity | Cu conduction ON | Cu conduction OFF diagnostic |
|---|---:|---:|
| Detector temperature | 218.6933026695 K | 211.0588808350 K |
| Detector temperature difference, nominal minus diagnostic | +7.6344218345 K | |
| Copper heat into coldest stage hot ceramic | +0.08741602698 W | +0.00047776043 W |
| Copper internal Joule heat | +0.00205501557 W | +0.00196216930 W |

The thermal-OFF case is **mathematical and physically unrealizable**: it suppresses passive heat conductance in formed copper while retaining the electrical circuit, same temperature-dependent metal resistivity law, and appropriate electrical Joule deposition. Joule power need not be numerically identical because its resistance changes with temperature; what is unchanged is the physical electrical/Joule *law*. The control does not represent removing physical copper or replacing it with zero-thermal-conductivity metal.

At fixed matched **electrical power**, the required drive current self-consistently differs between the two solutions. Therefore do **not** claim the comparison is at matched current.

## Parametric screen (each independently audited)

| One-factor case | Calculated Tdie | Delta vs copper-on nominal |
|---|---:|---:|
| k_Cu ×0.8 | 217.518696 K | -1.174606 K |
| k_Cu ×1.2 | 219.746828 K | +1.053525 K |
| Cu/ceramic R'' ×0.1 | 218.946877 K | +0.253575 K |
| Cu/ceramic R'' ×10 | 216.879923 K | -1.813380 K |
| Effective foil cross-section ×0.8 | 217.550367 K | -1.142936 K |
| Effective foil cross-section ×1.2 | 219.725935 K | +1.032633 K |

Foil cross-section variations alter both Cu electrical resistance and thermal conductance; the contact thermal-resistance and Cu conductivity cases isolate their respective parameters. **These six one-factor cases are not statistical confidence limits or demonstrated fabrication tolerances.** Contact properties and foil material grade are hypothetical.

All six independent audits passed, maximum stage energy closure discrepancy among these cases approximately 1.16e-9 W. The earlier thermal-off diagnostic independently passed maximum stage residual 4.39e-11 W, global 1.93e-11 W.

## Limits required in publication context

- V3.27 represents only about **3.45424%** of registered cavity gas-facing area; others are adiabatic, hence real absolute detector temperatures are **not validated**.
- Source geometry is a synthetic engineering reference, **not a validated commercial assembly**.
- Source-graded P/N transport and Cu/ceramic interfacial resistance remain unmeasured hypotheses.
- A full-source 430-domain native metal electrical PDE has not passed Gate B; reduced conductive foil network is a lower-dimensional conditional model.
- Peltier stage heat-flux impact is inferred from the coupled model, not a measured heat-flow sensor.
- 7.63 K is **not an empirical performance specification**, and cannot be used as a device manufacturer claim.

## Reproducibility files

- Nominal reference: `data/nominal_gas_visibility_v327_20261111/coupled_attempt01/`
- Thermal-off control: `data/copper_ablation_publication_20261112/`
- Six sensitivities: `data/copper_sensitivity_publication_20261112/`
- Blender source: `scripts/render_copper_3d_blender_20261112.py`
- Scene: `media/copper_3d_20261112/source_cad_copper_thermal_study.blend`

No external imagery or nonoriginal music is used. No 3D temperature field is claimed.
