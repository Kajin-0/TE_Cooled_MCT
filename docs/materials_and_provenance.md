# Source-backed materials — Phase 1b (first-pass bulk material registry)

## Material facts vs measurements and uncertain proxies

All values have units, source URL and provenance in tecooledmct/materials.py. Unless explicitly specified, listed properties are near 293–300 K and are not valid over the entire 190–300 K cooler temperature span without calibration.

- **TEC Microsystems 3MC04-044-05 (2019)**: high-grade hot-extruded Bi-Te P/N legs, 100% alumina plates (manufacturer nomenclature), internal Sn-Sb solder, gold-plated hot/cold surfaces (0.2–0.3 µm), and standard AWG-32 terminal leads. No proprietary dopant chemistry, P/N thermal conductivity k(T), S(T), or resistivity rho(T) supplied.
  https://www.tec-microsystems.com/Download/Datasheets/Thermoelectric%20Coolers/MC04%20Series/3MC04-044-05_Datasheet_2019.pdf
- **P/N Bi2Te3 literature *examples***: S_p=+160, S_n=-170 µV/K and σ_p=1.4×10^5, σ_n=1.655×10^5 S/m at 300 K from the same literature example (Goldsmid, 2014). k~1.5 W/m/K for each leg is a separate **generic** BiTe benchmark from Ferrotec Appendix B, not measured on those P/N samples or the specific TEC. Thus the literature profile is internally mixed and illustrative, not experimentally grade-calibrated.
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5453363/
  https://ferrotec.com.sg/product/thermo/technical_reference_guide/14/
- **Alumina**: TEC says 100%; CoorsTek AD-995 99.5% is a defensible but imperfect grade proxy: k=30 W/m/K at 20 C, density 3900 kg/m3, cp 880 J/kg K at 100 C. CoorsTek AD-96 k=24.7 W/mK is an alternate grade. In particular the manufacturer's 100% label is NOT a CoorsTek grade assignment.
  https://www.coorstek.com/en/materials/alumina/
- **Kovar**: Fe-Ni-Co alloy representative header (composition and actual header plating not OEM-verified). Coining/AMETEK: k=17.3 W/mK, density=8360 kg/m3, CTE~5.5 ppm/K at 30–200 C, cp~439 J/kg/K at 0 C.
  https://www.ametekinterconnect.com/-/media/ametek-ecp/v2/files/cw_datasheets_sds_cfsi/datasheets/kovar.pdf?la=en
- **Gold bonding wire**: Inseto / AMETEK Au ≥99.99% with small Be dopant, k=315 W/mK at 20 C, density=19340 kg/m3, resistivity=2.3×10^-8 Ωm. The 315 W/mK number in Phase 0 was realistic but previously unattributed. **Gold + indium** is not identified as the bond wire composition; Au/In may refer to a separate die attach or bonding interface, requiring assembly-specific confirmation.
  https://www.inseto.com/wp-content/uploads/2022/08/Gold-Wire-Data-Sheet.pdf
- **Sn-Sb solder**: manufacturer's chemistry only "Sn-Sb"; 95Sn/5Sb Indalloy 133 is a *proxy*, k=64.7 W/mK, density=7250 kg/m3, CTE=31 ppm/K, liquidus 240 C. The TEC vendor states melting point ~230 C for its own internal Sn-Sb. Do NOT equate its unspecified alloy with the nominal Sn95Sb5 datasheet without checking.
  https://documents.indium.com/qdynamo/download.php?docid=4064

## What is now computed

The material registry is directly used by the **optional** literature P/N profile in \`material_transport.py\`. It derives per-stage Seebeck (N*(S_p-S_n)), electrical resistance (N*(rho_p+rho_n)*L/A), and heat conduction (N*(k_p+k_n)*A/L) from literature reference values and the same nominal 28/12/4 couples. Use:

    from tecooledmct.material_transport import literature_stage_coefficients
    from tecooledmct.geometry_sweep import solve_geometry, TECGeometry
    from tecooledmct.model import Scenario
    print(solve_geometry(Scenario(), TECGeometry(),
                         coefficients=literature_stage_coefficients(TECGeometry())))

**Default Phase 0 remains OEM-limits fitted.** No false claim that 2014 specimen values are the actual hot-extruded production BiTe formulation. Compare with \`compare_coefficients()\`.

\`materials.layer_temperature_drop\` calculates an independent **simple 1-D analytical** thermal resistance for ceramic, solder, header or wire where valid. Example 0.22 mm 99.5% alumina across a hypothetical 2.4×2.4 mm full contact area: R≈1.27 K/W, so at 15 mW the temperature drop is ~0.019 K. This is not the local spreading/contact thermal resistance, and does NOT couple into the 4-node package solver.

## What still is not represented physically

Al2O3 3D plates, Kovar/steel cap, 9 glass-to-metal seals, nickel plating, real Sn-Sb bridges, die attach, gold bond-wire paths, TEC leads, optical window, cavity gas flow, radiation and inter-material contact resistances are not yet meshed and solved as connected domains. Bulk material properties alone do not make this a 3D multiphysics digital twin.

**Recommended next:** temperature-dependent P/N property tables from 190–350 K (grade matched where possible); a material-tagged CAD mesh; calibrated heat/contact resistances and boundary conditions; independent measured I-V-lift curves; temperature-dependent coupled FEM with explicit source/sink geometry.

## Why the model profiles disagree

The OEM-fitted effective coefficients are **module-level** values reflecting other effects (contact R, stage geometry, unknown grade, unmodeled real flux). The literature coefficients are from different samples; do not force the literature profile to match the OEM without independently identifying the material and contact parameters. Refit only with adequate independent data and holdout validation.
