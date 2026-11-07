# R3 manufacturer-guided heat-sink boundary and remaining physical interface gap

**Date:** November 7, 2026. **Baseline:** a08ab283d90c80af7581f08ff580c7f67e98e02c.
**New evidence:** VIGO Photonics offers direct manufacturer **design guidance**, not a measured mounting resistance for this source-constrained hybrid CAD. **Physical installed header-to-radiator boundary remains STOP**; no new FEM solution, no coefficient fitting, no Codex.

## Primary manufacturer source

[VIGO Photonics, *Thermoelectric Cooling, Heat Sinking*, revision V3.0 dated 11 September 2025, p.1](https://vigophotonics.com/app/uploads/2024/07/Thermoelectric-cooling-heat-sinking.pdf). The original PDF and schematic were inspected directly.

- For 1TE, 2TE and 3TE packages, a **heat sink of approximately 2 K/W** is typically recommended; for 4TE, approximately 1 K/W. This is the heat sink/radiator *to its surrounding environment* design capability, **NOT the detector header–sink interface resistance**, not the source-CAD hot ceramic-to-air resistance, and not a claim that the user's unknown fixture has this rating.
- Firm attachment of the detector **header base** to the sink is required, with a thin layer of conductive epoxy or silicone thermal grease to improve contact. The cap or screw alone is insufficient.
- The illustration shows the physical heat-sink placement concept but **does not provide the installed thermal contact area, surface flatness, force, contact resistance, TIM conductivity, bondline thickness, exact sink base temperature or air-flow conditions**. No source-backed numerical interface conductance can be released from this document.

The existing [R3 source-identity audit](V3_TEC_SOURCE_IDENTITY_AND_PHYSICAL_EVIDENCE_20261107.md) demonstrates that the VIGO reference package and TEC Microsystems source TEC are **not established as the same built product**. The OEM design guideline is therefore a reasonable *reference-design criterion*, never an as-built calibration point.

## Source-linked thermal budget (illustrative only)

[Reproducible exact original-CAD budget](../scripts/v3_oem_sink_boundary_evidence.py), [source-hashed input/result receipt](../data/v3_oem_sink_boundary_20261107/attempt01/boundary_evidence.json). The named terms are **sequential only under a simplified equivalent thermal circuit**, combining a previously archived single-boundary 3D header calculation with two simplified 1D layers and an OEM radiator design recommendation:

| Named term | Thermal resistance (K/W) | Evidence class |
| --- | ---: | --- |
| Ceramic0 500 µm / 37.21 mm² | **0.44791** | Generic AD995 alumina k=30 W/(m·K), 1D uniform-flux approximation |
| In52Sn48 80 µm / 36 mm² | **0.07407** | Prior engineering hypothesis k=30 W/(m·K), 1D uniform-flux approximation |
| Original source Kovar header, 47,702 TET4 | **1.57704** | [Numerical 3D original CAD](V3_R3_HEADER_ONE_CONDITION_3D_SPREADING_20261107.md), 17.3 W/(m·K) Kovar proxy; ideal full-underside 300 K BC, source face2228 |
| Radiator to surrounding environment | **2.00000** | VIGO *typical design recommendation*, not a measured installed sink |
| **Sum of four named reference terms** | **4.09902** | **Not a physically validated total resistance** |

The original Kovar 3D result uses face2228 at the **header to Ni composite** interface, whereas the solder/ceramic path includes Ni/Au composite metallization and its additional interfaces. Those are **unknown**, and the full ceramic has 3D spreading not represented by a single 1D thickness. Accordingly, this series sum is **illustrative**, not a strict upper or lower bound on the real whole assembly.

At the *previously archived conditional* heat rejection \(Q=0.5870297615\) W (nominal P/N research analog, 0.4 A, 5 K/W reduced sink, CAD wires ON), simple multiplication gives:

| Contribution | \(\Delta T=Q R\) |
| --- | ---: |
| Ceramic analog | 0.263 K |
| Solder hypothesis | 0.0435 K |
| Single-boundary header 3D | 0.926 K |
| OEM radiator design target | 1.174 K |
| **Illustrative sum** | **2.406 K** |

This **does not** create a new coupled solution at a hypothetical hot-side \(302.406\) K. The original reduced case used **5 K/W as its entire effective hot-side sink**, with a different thermal boundary contract and heat flow; the present parts **must not be added to that 5 K/W parameter**. A self-consistent updated reduced-model coupling would require a distinct registered complete thermal path, actual radiative/wire boundary changes and the material properties valid above 300 K. No such solve is authorized or claimed.

## Thermal boundary readiness decision

**Source-confirmed:** For a source-constrained 3TE detector reference, a **~2 K/W radiator-to-ambient design criterion**, base-mounted header and a thin conducting interface are OEM-recommended. The CAD original header-to-TEC and exterior area tags are known, and the existing one-condition header P1 FEM is independently reproducible.

**Still missing:** *Installed* sink thermal resistance at actual heat load, sink mounting footprint, thermal interface material brand and bondline thickness, contact pressure and Kovar surface finish, thermal contact resistance and temperature-dependent conductivity, proper multilayer thermal tensors, detector/package heat load and real full-assembly wiring. Without them, the CAD original full 430-volume coupled thermal C/D model remains **NOT RUN** and a physically released 430/2440 law table remains STOP.

**High-value next decision:** Acquire the actual fixture/sink specification or a measured \(T_\mathrm{header\ base}-T_\mathrm{ambient}\) at known sink heat flow \(Q\) and mounting conditions. Alternatively, for a clearly labeled **reference design**, explicitly adopt an OEM-guided radiator model with a declared unknown TIM/interface resistance and uncertainty, and derive a *new* coupled system boundary before solving. Avoid more arbitrary heat-sink sweeps or silently equating an OEM guide with laboratory calibration.

**Preservation:** Original P1 electrical Gate B FAIL/STOP, prospective P2 STOP, full coupled C/D NOT RUN, source CAD/mesh/Rev3 unchanged, no Codex and no physical-as-built detector temperature claim.
