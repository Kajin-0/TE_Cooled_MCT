# V3 physical source-identity hard gate — no as-built TEC/detector equivalence

**Audit date:** November 7, 2026. **Baseline commit:** bc8468e8a3a8232d3878e309a47735346caa9b23.

**NO-GO for a product-validated electrothermal operating temperature.** The existing 430-solid derived simulation assembly is a scientifically useful **source-constrained reference design**. It is **not verified to be a real commercially assembled detector containing the particular cooler used as a performance reference**.

[Machine-readable source identity gate](../data/v3_tec_source_identity_20261107/attempt01/source_identity_gate.json) and [deterministic no-solve verification script](../scripts/v3_tec_source_identity_hard_gate.py). The script reuses local source CAD, source provenance, complete 430/2440 physical-input ledger and the independently established actual CAD electrical/thermal connectivity receipt.

## 1. Two sources must never be treated as one as-built assembly

| Evidence | TEC reference | Separately selected detector-package reference |
| --- | --- | --- |
| Manufacturer and identity | **TEC Microsystems** 3MC04-044-05 (2019) | **VIGO Photonics**, 3TE-TO66 package drawing and PCI-12 detector series (May 2026) |
| OEM source | [TEC 2019 datasheet, p.1](https://www.tec-microsystems.com/Download/Datasheets/Thermoelectric%20Coolers/MC04%20Series/3MC04-044-05_Datasheet_2019.pdf) | [VIGO 3TE-TO66 9-pin drawing, Rev9](https://vigophotonics.com/app/uploads/2024/07/3TE-TO669p-wW-PVI_PCI-detector-technical-drawing.pdf), [PCI-12 series datasheet](https://vigophotonics.com/app/uploads/2024/07/PCI-12-detector-series-datasheet.pdf) |
| Technology or package | Three-stage **44-couple** high-grade hot-extruded Bi-Te TEC, alumina, Sn-Sb assembly and Au exterior plating | Three-stage detector package with HgCdTe photoconductor, pins1/9 TEC, pins7/8 detector, pins5/6 thermistor |
| Temperature datum | **ΔTmax 113 K**, at Qc=0, nominal hot side 300 K and vacuum | **Typical chip temperature ~210 K** at ambient 293 K for PCI-12 series |
| Current datum | **Imax 1.0 A** under 300 K vacuum and held hot side | **0.45 A TEC absolute maximum** for PCI-12, NOT a recommended operating current |
| Voltage datum | Umax **3.5 V** at 300 K reference | **3.6 V TEC absolute maximum** |
| Independent material-grade laws S(T), rho(T), k(T) | **Not disclosed** | **Not disclosed** |
| Assembled together? | **UNPROVEN** | **UNPROVEN** |

**Critical:** A standalone TEC reference-module 1.0 A performance-current maximum and a separately published *packaged detector's 0.45 A absolute maximum* are **not interchangeable**. Different OEM/product/condition definitions may explain the distinction; **do not invent a physical contradiction or select one limit as a rating for the other hardware**. The current CAD is explicitly a hybrid reference construction; no physical actual device is verified to combine those exact internals. Similarly, 300 K - 113 K = 187 K is an ideal **TEC-only zero-load reference limit**, not a predicted detector temperature. VIGO's 210 K is a typical value for a different detector family and cannot serve as a same-product validation point for this hybrid CAD.

The original, previously written [geometry source of truth](../GEOMETRY_SOURCE_OF_TRUTH_SPEC.md) already warned about different OEMs. This new gate prevents that warning from being lost while promoting R3 meshes, contact FEM tests or 29/11/4 electrical graph success.

## 2. The 29/11/4 topology is a chosen source-constrained hypothesis

The accepted CAD contains 44 P/N couples across 29/11/4 stages, with each of all 88 legs geometrically necessary for the current path between TEC pins1/9. Those are genuine [CAD network checks](V3_TEC_PHYSICAL_PORT_CONTRACT_20261106.md).

However, the original TEC Microsystems selected data sheet specifies **44 total couples**, NOT the actual split 29/11/4 or the unpublished internal interstage metal dimensions. The original project [physical geometry evidence index](TEC_GEOMETRY_EVIDENCE_LIBRARY_20261102.md) classifies 29/11/4 as **INFERRED**. Other published three-stage layouts establish manufacturing plausibility only.

Therefore **CAD topology PASS must not be described as an OEM-confirmed wiring/revision**. The project's internals are fully specified mathematically but not verified as fabricated.

## 3. Missing thermistor in the nominal detector-package model

VIGO's 3TE-TO66 drawing specifies **pins5 and6 for a thermistor**. The accepted R3 source CAD instead has only metallic pin5 volume394 and pin6 volume396, each connected geometrically to its own glass seal; there is **no modeled thermistor volume, resistance-temperature law R(T), or conductive connection between the thermistor pins**.

This is an as-built completeness/measurement-interface gap. A thermal prediction without the thermistor can still be treated as a **standalone reference sensitivity study**, provided that limitation is explicit. No sensor geometry, lead wiring or R(T) calibration can be invented in the frozen original source model. An eventual as-built variant requires actual thermistor installation and measurement details.

## 4. Physical model readiness

The [complete R3 law inventory](V3_PHYSICAL_LAW_AND_COUPLE_READINESS_20261106.md) contains **430/430 source volume laws and 2,440/2,440 face laws currently UNSET**. Research-specific P/N transport curves are available as analogs in the literature, but those are neither matched actual 44-couple production-grade measurements nor a qualified above-300 K continuation. Ceramic/metal/solder material identity, finite electrical and thermal joining coefficients, hot-side sink mounting, optical heating, gas, radiation and real operating states remain unreleased.

**Release order:**
1. Establish whether the target is **(A)** a *reference-design virtual device* with explicit uncertainties or **(B)** one *actual OEM-identified detector product*. Do not silently switch.
2. For **A**, explicitly tag each unknown as hypothesis with bounded sensitivity ranges and model-form restrictions; report conditional predictions **only**, not validated detector temperature or an actual VIGO datasheet match.
3. For **B**, obtain the actual detector/cooler assembly part/revision and available internal TEC documentation or X-ray/cross-section, the grade-matched S/rho/k curves, contact/assembly properties, actual TEC electrical limits, measured sink/thermal loads, detector power and R(T) of any thermistor.
4. Independent holdout measurement of I-V/current, cold-side T and heat-lift across multiple operating states is required for empirical validation, separately from any calibration data.

No source CAD/mesh, material coefficient, P1/P2 historical failure, Rev3 report or issue #2 was altered. No PDE was run, and Codex was not used.

**Verdict: exact reference-source identity remains unresolved; material-law and thermistor qualification STOP; original electrical Gate B FAIL/STOP; prospective P2 STOP; thermal C/D NOT RUN.**
