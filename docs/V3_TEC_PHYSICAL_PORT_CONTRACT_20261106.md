# V3 physical TEC electrical and thermal port contract

**Date:** November 6, 2026. **Baseline:** 0d4ff8b90fa2dac115c3f2716e5b11bd6107c4d4.

**GEOMETRY TOPOLOGY PASS. PHYSICAL PORTS / COEFFICIENTS STOP.** This source-hashed no-solve contract uses only registered solid-to-solid CAD faces. It does not assign conductivity, thermal resistance, thermoelectric material data, electrical voltage, current, heat-load, or calibrated boundary conditions.

[Machine-readable original CAD source circuit and heat path](../data/v3_tec_physical_port_contract_20261106/attempt01/port_and_series_graph.json) and [exact read-only graph reproducer](../scripts/v3_tec_electrical_port_contract.py). The prior [complete 430-domain / 2,440-face law inventory](V3_PHYSICAL_LAW_AND_COUPLE_READINESS_20261106.md) remains STOP.

## TEC electrical boundary topology: real package pins

| Physical port | Exterior face tag | Source volume ID |
| --- | ---: | ---: |
| TEC pin1 | **2414** | 424 |
| TEC pin9 | **2426** | 427 |
| Detector pin7 | **2418** | 425 |
| Detector pin8 | **2422** | 426 |

All **557 solid-solid native faces** were examined. Of 430 source CAD volumes, **407** have candidate electrical-conductor material labels: P/N thermoelectric legs, metal, solder, finite composite-metal traces and metallic lead pins. This is **material-identity connectivity only**, not a conductivity assignment or a physical leakage-current claim.

The conductive graph has **10 components** with sizes 389, 4, 4, 4, 1, 1, 1, 1, 1, 1. The **389-volume TEC component includes both package pins 1 and 9 and all 88 original TEC legs**. The pin7 and pin8 detector branches are separate four-volume components when active HgCdTe is excluded; adding the actual active HgCdTe domain ID408 connects detector pins via native semiconductor/wedge faces 2336 and 2337, but still does not connect detector bias to the TEC branch.

The package terminal paths are:
- pin1 → lead1_pin_joint → TEC_lead1 → lead1_land_joint → net0_plane0.500_Cu
- pin9 → lead9_pin_joint → TEC_lead9 → lead9_land_joint → net88_plane0.500_Cu

**The package port identity question is closed geometrically, not electrically or thermally calibrated.**

## Full 88-leg mandatory series graph — verified

The audit independently removes **each of the 88 distinct P/N leg solids**, then verifies that the original pin1–pin9 conductor graph becomes disconnected. All **88 of 88** are articulation vertices with respect to the actual TEC package terminals: **58 hot-stage legs, 22 middle-stage legs, 8 cold-stage legs**, consistent with the actual **29/11/4 couple** allocation. This excludes a conductive alternate path around any leg in the CAD shared-face graph; it does not prove the values or temperature dependence of their contact resistance.

The native stage transitions are continuous without using other thermoelectric legs:

- Boundary after leg57, net58: net58_plane0.500_Cu (volume327) → tab_joint0 → formed_tab58 → tab_joint1 → net58_plane1.600_Cu (volume328).
- Boundary after leg79, net80: net80_plane1.600_Cu (volume350) → tab_joint2 → formed_tab80 → tab_joint3 → net80_plane2.700_Cu (volume351).

The real stage-0 N/P pair (legs volume5/8 and shared cold net270) remains electrically embedded in this full series path. Its net0 and net2 are **internal metal domains**, not independently accessible external package terminals. The incoming net0 has source CAD physical contact face1531 to lead1_land_joint; net2 has contact face162 to the next leg2 hot solder. The previously selected 11-solid N/P pair plus complete ceramic0/ceramic1 has **132 outside cut faces** (73 solid-solid and 59 gas-solid), which cannot be silently sealed as insulated or adiabatic.

**Decision:** a two-leg physical FEM with invented net0/net2 ideal voltage ports or arbitrary thermal insulation is NOT VALIDATED. A prospective isolated couple is only defensible as an explicitly mathematical substructured network, with separately released current/heat cut-port conditions derived from the other 86 legs and surrounding ceramics.

## Exact original CAD thermal-contact paths

These are geometrically registered heat paths, **not released thermal impedances**.

| Hot header to ceramic0 | Native face ID | Area (mm²) |
| --- | ---: | ---: |
| Header / header Ni finish | 2228 | 37.21 |
| Header finish / In52Sn48 mount solder | 2298 | 36.00 |
| Mount solder / underside Au | 2303 | 36.00 |
| Underside Au / ceramic0 | 6 | 37.21 |

The original header has **12 exterior candidate heat-sink surfaces**: 2222, 2223, 2224, 2225, 2226, 2230, 2231, 2232, 2233, 2234, 2239 and 2243. Their existence does not establish which face physically contacts a sink, the heat-sink temperature, thermal resistance or convective transfer law.

| Cold ceramic3 to HgCdTe | Native face ID | Area (mm²) |
| --- | ---: | ---: |
| ceramic3 / cold Au finish | 119 | 4.41 |
| Cold finish / carrier EP29LPSP | 2314 | 2.56 |
| Carrier adhesive / sapphire | 2319 | 2.56 |
| Sapphire / die attach EP29LPSP | 2325 | 1.00 |
| Die attach / active HgCdTe | 2330 | 1.00 |

The adhesive, Ni/Au composite, solder interfaces, temperature-dependent transport, detector bias heat, native cavity gas and radiative parasitics remain **unreleased**.

## Physical port/solver go-no-go

**Allowed as geometric CAD port identities:** full TEC input/return pins **2414/2426**, detector-bias pins **2418/2422**, native header/stack contact candidate heat-transfer surfaces identified above.

**NOT ASSIGNED:** any V/I value, sink temperature, thermal flux, contact area resistance, gas pressure, radiation law, calibrated P/N S(T), rho(T), k(T), Peltier/Thomson law, or pair-level cut-port condition.

**Before any PDE:** obtain matched P/N grade transport data, as-built solder/contact properties, confirmed thermal sink mounting condition, measured detector heat load/bias and a physically coupled current/heat acceptance contract. Preserve original electrical Gate B and the stopped P2 candidate unchanged. The frozen 824-solid source STEP, 430-domain derived geometry, Rev3, all archived failures and issue #2 are untouched.

**Verdict: native 88-leg network topology and terminal identity PASS; electrically and thermally qualified full-device model STOP; Gate B FAIL/STOP; thermal C/D NOT RUN. No PDE, remesh or Codex use.**
