# V3 geometry-readiness consolidation — physical/analysis split

**Frozen physical reference:** V3 R1 [synthetic assembly specification](SYNTHETIC_V3_ASSEMBLY_CAD_20261102.md), 824-solid STEP `data/synthetic_v3_assembly_20261102/cad_02/synthetic_v3_mm.step`. The original conditional manufacturing-plausibility verdict remains unchanged. This is **not** a new physical redesign, a native gas mesh, a qualification of the failed electrical method, or an experimental validation.

## Objective and action taken

The project had begun to invest disproportionate effort in one failing local electrical flux coupon. This milestone instead organizes the complete V3 geometry for later multiphysics implementation while **preserving the existing physical CAD as authoritative**.

A versioned, strictly derived analysis-preparation packet is now generated from the **actual frozen 824-body source** and its independent STEP/SI import ledger. It contains a machine-readable body/physics registry, physical contact-witness table, initial port definitions, simulation-representation choices, and constrained mechanical/tolerance what-ifs. No CAD STEP regeneration, meshing or PDE solve is performed.

Files:

- [Generator](../scripts/v3_geometry_readiness_registry.py)
- [Machine-readable geometry and port registry](../data/v3_geometry_readiness_20261103/domain_interface_registry.json)
- [824-domain CSV](../data/v3_geometry_readiness_20261103/domains.csv)
- [378 source contact-witness CSV](../data/v3_geometry_readiness_20261103/interfaces.csv)
- [No-solve integrity tests](../tests/test_v3_geometry_readiness_registry.py)

The source is `source_final/design.json` (**824**, not the earlier 822-body intermediate source), the separate imported STEP reader records **824** uniquely identified solids, and every source name is associated with its imported STEP tag and SI volume/bounding-box diagnostics. The 378 explicit source contacts describe only one declared contact class: they are **not** the complete 923 imported face-contact witnesses or all faces needed for future numerical boundary ownership. The prior full contact audit and its 89 TEC-net topology remain separate protected evidence.

## Physics-readiness classification

| Physical group | Bodies | Intended computational representation | Current status |
| --- | ---: | --- | --- |
| Patterned TEC metal | 465 | Sheet/two-sided interface with effective tangential and transverse laws | Proposed; numerical equivalence not qualified for 3D crowding |
| Solder/contact solids | 202 | Resolved 3D on selected joints; interface/contact law for thin layers | Proposed; finite contact law/contact resistance unknown |
| Thermoelectric P/N legs | 88 | Native 3D solids; coupled transport, temperature laws from verified sources | Physical source passed; full V3 coupled transport not run |
| Ceramics | 4 | Full 3D insulating/thermal reservoirs | Physical source passed; port boundaries untagged |
| Formed tabs and TEC lead wires | 5 | Curved 3D conductors, or beam/shell validated by independent comparators | Geometry present; parasitic electrothermal behavior unqualified |
| Pin shafts and coating | 17 | 3D shaft plus finite finish layers | Geometrical only |
| Header/mount/cold coatings | 13 | 3D header + interface/multilayer attachment laws | Thermal contact and stress unqualified |
| Glass, carriers, die, bonds, enclosure and remaining parts | 30 | Mixed solids/optical surfaces/films; gas and radiation boundaries future | Physical source exists, selected properties not qualified |

The machine registry retains each individual element rather than collapsing unlike regions; group counts in this summary are just for orientation. **No combined analysis BREP or analysis mesh has been created.**

### Multiphysics thermal and electrical ports

At minimum the computational model must distinguish **CERAMIC0, CERAMIC1, CERAMIC2, CERAMIC3, HEADER, TEC_PIN1, TEC_PIN9, DET_PIN7, DET_PIN8, CASE, WINDOW, GAS, OPTICAL**.

All ports are **proposed**, not yet uniquely mapped to imported STEP boundary-face IDs. Port-flux sign should be defined globally as heat entering the computational domain positive; electrical pin polarities are pin1/net0, pin9/net88, detector pin7/8, while pins5/6 are intentionally vacant. Some ports may become radiation/source rather than Dirichlet/Neumann heat terminals. No port count may be treated as proof of complete boundary coverage.

**Important missing geometry:** The V3 STEP contains cap and window solids but **no explicit native cavity gas volume or qualified surface-to-surface radiation visibility partition**. Adding gas and view-factor geometry will require a separately specified analysis volume, including impenetrable solids/surface contact, sealed void definition and independent face-ownership checks. No pressure/gas/radiation result exists.

## Physical robustness checks worth addressing

| Issue | Frozen configuration | Arithmetic-only proposal | Engineering action |
| --- | --- | --- | --- |
| Height clearance | 3.664–3.944 mm; 6 µm upper reserve against 3.950 mm | Reduce selected worst-case assembly growth or tighten manufacturing stack by 10–20 µm; upper reserve would arithmetically become 16–26 µm | Check true source tolerances and inspectability; do not alter supplier's ±0.15 mm envelope or pretend the tighter budget is achieved |
| Formed copper tabs | 30 µm foil; 75 µm neutral radius; `t/(2R)=0.20` outer-fiber screening proxy | 100 µm radius gives 15%; 150 µm gives 10%; 200 µm gives 7.5% | Rebuild/profile tabs only after proving horizontal span, 50 µm tab/ceramic clearance and formed-foot geometry still fit; fatigue and Cu temper compatibility remain untested |
| Joint thermal sequence | Initial selected solder stack has approximately 6 °C melting separation | Localized joining, fixture-controlled intentional remelt, or an appropriate different process family | Test with real thermal-profile/metallurgical coupons; don't assume temperature hierarchy protects joints |
| Detector and enclosure | Synthetic top-contact photoconductor, wire bonds, steel cap, candidate window | Add explicit optical, radiative and gas-exchange analysis surfaces | Do not invent cavity temperature, seal leak rate, optical absorption or device responsivity |

The radius suggestions are not new qualified designs or new manufactured dimensions; they are **analytical pre-screening candidates**. A larger radius may consume substantially more lateral and vertical clearance; the registry deliberately labels all actual geometry rebuild and fit checks **NOT RUN**. The 6 µm reserve is the actual worst-case selected interval outcome, not a nominal-assembly fit failure.

## Required independent model verification — computational representation

1. **Layer equivalence controls:** For a homogeneous metal sheet with in-plane length L, width w, thickness t, verify `R_sheet = ρ L/(w t)`. For a stack of layers, derive parallel in-plane sheet conductance and series through-thickness electrical/thermal resistance; explicitly preserve interfacial `r''/A`. Test a bulk-layer reference against surface operators on at least two independent resolutions before using them near contact edges.
2. **Resolved joints:** Maintain both sides of actual contact and independent area/normal owner mapping; ensure current and heat continuity, finite contact jumps, and no twice-counted solder/barrier resistance.
3. **Curved wire or tab reduction:** Compare 3D lead against 1D/shell effective `R = ∫ρ/A ds` and `G = (∫ ds/(kA))⁻¹`, then separately test current crowding, bends and bond/contact terminal spreading. 1D results **do not** qualify 3D edge currents.
4. **Thermal port operator:** Require every exposure/bonded boundary to be covered once, no duplicate metal/ceramic heat-port tags, and a complete multiport conservation/reciprocity/PSD validation for a passive fixed-property conduction model.
5. **Gas and radiation:** Create actual enclosed void and distinguish gas conduction across pressure/Knudsen regimes from surface-to-surface radiative exchange; prohibit a fabricated gas port without geometric ownership.
6. **Parametric CAD stability:** Rebuild separate *analysis-derived* versions at representative leg size, tab radius, ceramic size, header/material and detector/carrier dimensions; verify source contact graph, unlike-net clearance, stage/pin assignments and SI scale for each. **No such rebuild is claimed in this milestone.**

The three distinct readiness gates are **(i)** frozen physical STEP/source integrity, **(ii)** complete analysis mapping/representation and geometry-tolerance checks, and **(iii)** independent PDE/field qualification. Passing (i) does not pass (ii) or (iii).

## Stop conditions, completed scope and downstream division of labor

The physical architecture is considered a legitimate **conditionally plausible synthetic reference**, not an exact manufacturer replica. Protect its 824-solid original, 88 legs, 176 contacts, 89 TEC nets, Rev3 and all historic STOP gates. Physical changes are permitted only under a new version and a specific demonstrated buildability/clearance improvement.

**Verified now:** Source-to-STEP body identity and SI names; source contact-witness extraction; preliminary per-domain physics tags; declared 13 candidate external/source ports; analytical tab and height variants; no-solve tests. **Not verified now:** Unique STEP-face tagging for all physics domains, native gas geometry, parameterized CAD rebuilds, geometrically validated reduced analysis BREP, real analysis meshes, finite-contact material laws or any coupled field. These require further scoped milestones; do not label the packet 'multiphysics-ready' until implemented.

The local electrical Gate B **remains STOP** (81.241662% raw P1 cut, 0.769154% recovered/P1 loss discrepancy). Thermal Gate C and coupled D remain NOT RUN. They should be pursued as an independent numerical-method workstream rather than repeatedly invalidating the physical geometry program.

The existing 38-page Rev3 is unchanged. Issue #2 remains OPEN. The Codex `sim:0.0` session was usage-limited and not interrupted; a separate model-assisted engineering reviewer is **NOT RUN** for this new registry.
