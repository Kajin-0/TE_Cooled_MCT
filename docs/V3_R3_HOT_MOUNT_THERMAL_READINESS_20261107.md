# V3 R3 hot-side mounting path: CAD-area, bulk-layer and sink-readiness audit

**Date:** November 7, 2026. **Baseline:** `17518f5254f14a1cdb614fdc68c7858a7f328018`.
**Result:** SOURCE GEOMETRY PASS; **PHYSICAL SINK BOUNDARY STOP**. No FEM, property fitting, remesh, new synthetic current/temperature scenario, or alteration of the original Gate B acceptance requirements.

[Exact source and thermal calculation](../scripts/v3_hot_mount_thermal_path_readiness.py) and [deterministic source-hashed quantitative results](../data/v3_hot_mount_readiness_20261107/attempt01/thermal_path_audit.json). The input is the existing accepted 430-domain, 2,440-face CAD and original hot-side interface registry, not the older 28/12/4 reduced stack.

## Source-native hot-side thermal pathway

The original interface face tags are **2228** (Kovar header / Ni composite finish, 37.21 mm²), **2298** (Ni composite / In52Sn48 mounting solder, 36.00 mm²), **2303** (In52Sn48 solder / Au composite underside, 36.00 mm²) and **6** (Au composite underside / ceramic0, 37.21 mm²). The original CAD material identities and IDs are unchanged: header volume386, finish401, solder402, underside403, ceramic0 volume1.

The header's true **exterior underside** is original CAD face **2225**, area **333.9607 mm²** at z=0, compared with the **36.00 mm²** solder footprint. The mounting area is only **10.78%** of the exposed header underside. In particular, the header's other exterior faces and its upper exterior face **2226** must not be summed and described as a single clamped heat sink. The actual footprint in thermal contact with a fixture, contact pressure, external conductor temperature and heat transfer law are not recorded.

## Purely illustrative one-dimensional bulk-layer calculations

For an assumed uniform axial heat path at the CAD interface area,
\[
 R_{1D}=\frac{L}{kA}.
\]

| Layer | CAD thickness | Thermal conductivity assumption | CAD area used | \(R_{1D}\) |
| --- | ---: | --- | ---: | ---: |
| In52Sn48 solder (volume402) | 80 µm | **30 W/(m·K), explicit historical engineering hypothesis**, not measured as-built | 36.00 mm² | **0.07407 K/W** |
| Alumina ceramic0 (volume1) | 500 µm | **30 W/(m·K), CoorsTek AD995 99.5% analog**, not identified actual grade | 37.21 mm² | **0.44791 K/W** |
| Alternative ceramic AD96 analog | 500 µm | **24.7 W/(m·K)**, alternate supplier grade | 37.21 mm² | **0.54402 K/W** |
| Nominal solder + AD995 analog | | | | **0.52198 K/W** |

Neither the Ni composite finish (2 µm), Au composite underside (0.25 µm), nor the finite contact resistances is assigned a k value. The CAD classifies both finishes as **effective multilayers** that require tensor/interfacial laws, not pure independent bulk Ni/Au slabs. Solder grade, void fraction and temperature dependence are not qualified. The full ceramic conducts heat nonuniformly from many TEC pad islands, so uniform axial flow is only a comparison assumption.

The bulk Kovar header thickness is **1.5 mm**; using historical 17.3 W/(m·K) Kovar bulk proxy, *two incompatible, idealized constant-cross-section columns* give approximately:
- **2.408 K/W** assuming that the *entire thickness* carries the heat only through 36 mm².
- **0.260 K/W** assuming that the *entire thickness* carries heat uniformly through the full 333.96 mm² exposed underside.

**Neither figure is a rigorous lower/upper bound on the actual 3D spreading resistance.** The true heat source covers a small central pad, and the heat sink's footprint and local boundary law are unknown. The two idealized columns cannot be used to bracket real Kovar spreading or define a released `R_sink`.

## Relation to the preceding nonlinear reduced case

The existing [R3 finite-sink and CAD-wire sensitivity study](V3_R3_FINITE_SINK_AND_CAD_WIRE_SENSITIVITY_20261107.md) gives **0.58703 W** to its hypothetical sink for the nominal 0.4 A, wires-on, 5 K/W case. Applying that **previously computed model** heat flow to the assumed one-dimensional layers yields ~**0.0435 K** over In52Sn48 and **0.2629 K** over AD995 alumina, ~**0.3064 K total**.

These numbers illustrate the magnitude of **bulk conduction under uniform flux**; they do not constitute a new coupled electrothermal solution or the true temperature partition at these real interfaces. The previous 5 K/W `R_sink` is a total **effective hot-ceramic-to-300 K reservoir** parameter and **already contains whatever bulk/contact/spreading path it represents**. Adding 0.522 K/W or any header term on top would double count parts of that thermal path. The 5 K/W case used an *assumed* >300 K extension of the research P/N transport curve, not directly measured property data.

## Stop/go for thermal boundary release

**PASS:** Real header-to-hot-ceramic interface identities, actual CAD face areas, the 36 mm² solder thermal footprint, exterior header underside face2225 and footprint contrast; reproducible, source-hashed formula checks.

**STOP:** Actual Kovar header lateral spreading, clamped contact-footprint and pressure, external sink T and conductance, composite Ni/Au effective thermal tensors, solder composition and voids, real ceramic grade k(T), all native interface thermal resistances, and real device heat rejection. The project has **zero released** 430-domain material or 2,440-face transport laws.

**Proposed next physical milestone:** qualify the external heat-sink contact boundary (actual fixture contact footprint, mounting pressure/T, and measured or sourced interface heat transfer), and perform a **one-condition source-CAD header spreading solve** only once those conditions are registered. This 3D heat conduction task is distinct from and cannot bypass the blocked fully coupled electrical Gate B. If those data cannot be obtained, the previous 0–5 K/W reduced sink scenarios remain plainly labeled hypothetical; do not launch a sequence of arbitrary sink guesses.

**Original P1 Gate B FAIL/STOP; prospective P2 STOP; thermal C/D NOT RUN; as-built detector-temperature prediction UNQUALIFIED.** No Codex, 3D PDE, geometry modification, parameter fitting or revision of the 38-page Rev3 report.
