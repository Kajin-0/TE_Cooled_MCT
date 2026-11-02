# Physical plausibility gate — independent engineering review

This is an **internal release protocol** for the synthetic TO-66 / three-stage TEC / HgCdTe reference, not an OEM reverse-engineering requirement or a second public scientific report. The authoritative AGENTS.md and append-only engineering chronology remain in force. Review the current code/CAD and source facts independently of the builder. A physically wrong CAD object can pass all software tests, mesh checks and global energy balances.

## 1. Decision gates in order

1. **Physical construction & applicability** — Is there a real, electrically and mechanically realizable way to build the assumed topology? Is each citation applicable to this component/product? Does an analogue support the proposed design, or merely illustrate something different?
2. **Geometry & SI provenance** — Source/drawing → nominal/tolerance/units → code → STEP import → mesh and full circuit topology; include mirror-view pinout checks and area/volume witnesses.
3. **Materials, joints, boundaries** — Sample/grade, orientation, measured temperature domain, solder/barrier process, electrical/thermal interfaces, gas regime and finite sink; quantify omitted consequential paths.
4. **Quantitative sensitivity** — Independent bounds and dimensionless/order-of-magnitude checks before fixing a nominal physical baseline; reject unsupported precision.
5. **Numerics** — Mesh/PDE/energy/regression gates *only after* the physical gates; no numerical success overrides physical failure.
6. **External accuracy** — Comparison to matched real measurements, when available; synthetic design plausibility is not OEM validation.

**STOP** the dependent candidate/claim for an impossible/unsupported current or thermal path, wrong scale/view/pin/product, contradicted construction, missing consequential energy term, or a single high-impact unbounded assumption promoted to an accepted baseline. **CONDITIONAL** permits a physically buildable synthetic hypothesis with analogy evidence, feasible range and explicit closure test. **PASS** certifies only a narrowly named check. **NOT REVIEWED** means no review, not no defect. A new replacement needs a new audit.

No change to existing scientific STOP/FAIL results is implied. The present original 28/12/4 assembly, separate 29/11/4 candidate and any new connector proposal have distinct identities and cannot inherit each other's physical qualification.

## 2. Documentation evidence standard

For each **critical** inferred architecture, search for at least three physically distinct relevant examples where available: matching commercial product-family construction; independently made second vendor device; and a peer-reviewed engineering/patent/standard implementation or independent specimen. Three pictures from one manufacturer are one source family, not independent corroboration. Exact hidden OEM internals may be inaccessible; then classify construction as INFERRED/UNKNOWN, examine more than one mechanically feasible architecture, and seek measured supplier process limits instead of asserting exactness.

Record original source title, URL/DOI, revision/date, exact page/figure/table, product and specimen, described configuration, direct/analog classification, nominal/range/tolerance and SI units, property validity (T, pressure, current, manufacturing), source disagreements, and which claim it actually supports. Inspect original drawing/photo itself; never derive fit/tolerances from a schematic illustration without scale. A product external drawing does not prove its hidden stage wiring.

Evidence labels: DOCUMENTED_EXACT_PRODUCT, DOCUMENTED_FAMILY, INDEPENDENT_ANALOG, PHYSICS_CONSTRAINT, INFERRED_TESTABLE, SCENARIO, UNKNOWN, CONTRADICTED.

## 3. Mandatory subsystem matrix

| Part of reference | Required independent physical review |
| --- | --- |
| TEC pellets/stack | P/N count and polarity, stage ordering (28/12/4 or 29/11/4 remain inferred), hot/intermediate/cold ceramics, leg pitch/area/height, solder and metal stack tolerances, edge pullback, opposing pads, mechanical support, package clearance and assembly feasibility |
| All current-bearing metal | **Whole two-terminal circuit** including interstage bridges and hot-side return; actual contacts and mutually isolated networks; plausible supported patterned conductor, tab, foil or via; real span/width/thickness/bend/landing and fabrication processes; possible CTE/fatigue failure; R(T), current crowding/J, I²R and short/opens; parasitic G and thermal destinations |
| TO-66 housing | VIGO family Rev9 3TE two-ear dimensions, cap/window/focal plane, bottom-view→top-view mirror, 10.8 mm pin circle, nine 0.76 mm shafts; TEC pins 1/9, thermistor 5/6, detector 7/8; housing/TEC joint product identity is **not** established |
| Transport and materials | P/N same-grade S(T), rho(T), k(T), source specimen and temperature domain; Thomson and sigma consistency; source-measured 40–300 K vs assumed 300–390 K; SnSb vs package attach, ceramic/steel/Kovar/Cu/Au/glass/semiconductor/interface choices |
| Boundary/loads | Finite hot-side sink + actual mounting area, Cu/Au leads and their ambient endpoints, die bias and dissipation, radiation and native surface visibility, gas pressure/species/accommodation, Knudsen/Rayleigh validity, actual path vs reduced proxy |
| Output claims | Clear split of real 3D solids, five-node, unqualified cavity proxy and historical studies; matched datasheet operating condition; I,V,Th,Tc,Qload, Qsink, COP, DeltaTmax and the conditional 186K/200K predictions, with failed cases retained |

Independent SI witnesses are mandatory: length/area/volume consistency (a 1,000× STEP length error is 10^9× volume); pin coordinates and mirrored bottom-view; min/max component envelope; circuit reachability and contact geometry; R = integral rho/A ds [ohm]; J = I/A [A/m2]; P_J = I²R [W]; electrical work from integral J·E dV and IV; conditional G = (integral ds/[k A])^-1 [W/K] only when a 1D branch is justified; independent full 3D or bounded contact/spreading paths otherwise. Reducing conductor R using larger cross-section tends to increase conductive heat leakage: audit both.

Do not substitute conserved reactions for failed raw flux, or inferred datasheet ACR for measured DC resistance. Do not use parameter fitting to establish physical dimensions/material identity. Report where material law is used outside measured range, including *interior leg temperatures*. Establish datasheet-vs-synthetic comparison on identical hot-side T, ambient/vacuum/gas conditions, cold-side load, I/V and control volume; otherwise NOT COMPARABLE.

## 4. What the audit delivers

Each independent review packet records:

- **Target:** exact commit/ref, paths/changed assumptions and any uncommitted or stopped work excluded.
- **Source matrix:** URL+page/figure, exact/analog status, SI value/range/domain, contradictory records and direct linkage to source/parameter/CAD/material/result.
- **Findings:** unique IDs, severity, quantitative mechanism, affected scientific conclusions, evidence gaps, proposed minimal real-world-feasible architecture and an independently testable closure criterion.
- **Verdict:** PASS, CONDITIONAL, STOP or NOT REVIEWED separately for topology, geometry, materials, interfaces, boundaries and claims; overall worst critical status.
- **Release decision:** specifically which dependent claims stop, and which exploratory independent hypotheses may continue; required experiment/source acquisition versus code-only verification.

The independent reviewer is NOT the physical model builder. A reviewer must not edit its subject, clear failed archived evidence or certify its own suggested replacement. A hardware engineer or project owner should explicitly accept any consequential replacement, after inspecting evidence and the blocked claims. The role and skill may be invoked on a **finished checkpoint**, sequentially, without interrupting sim:0.0.

There is **no automatic GitHub branch-protection or mandatory autonomous review** established by these documentation files alone. A project-scoped Codex reviewer and discovery skill have been supplied; their actual runtime invocation, thorough review, and any subsequent branch-protection policy are separate activities.

## 5. Initial primary sources and scope

- [TEC Microsystems 3MC04-044-05 (2019) datasheet](https://www.tec-microsystems.com/Download/Datasheets/Thermoelectric%20Coolers/MC04%20Series/3MC04-044-05_Datasheet_2019.pdf), pp.1–2: external hot/cold ceramic plates 6.4/2.4 mm, assembly 3.8 mm, nominal 27 C vacuum performance. Exact internal routing dimensions are **not** given.
- [VIGO ZTM-TO66-Z030 Rev9 (2024)](https://vigophotonics.com/app/uploads/2024/07/3TE-TO669p-wW-PVI_PCI-detector-technical-drawing.pdf), p.1: 3TE 9-pin package, bottom-view electrical pinout, 0.76 mm pins, physical materials and geometry. It does **not** identify the TEC Microsystems internal cooler as its installed device.
- [TEC Microsystems MC04 family 3MC04-076-05 (2019)](https://www.tec-microsystems.com/Download/Datasheets/Thermoelectric%20Coolers/MC04%20Series/3MC04-076-05_Datasheet_2019.pdf), overview drawing: **interstage connectors**, BiTe posts and metallization; same family but different model.
- [TEC Microsystems MC06 three-stage construction](https://www.tec-microsystems.com/products/thermoelectric-coolers/3mc06-series-thermoelectric-coolers.html): an additional vendor physical illustration, **not** dimensioned MC04 details.
- [TEC Microsystems metallization options](https://www.tec-microsystems.com/services/customized-au-patterns.html): substrate-supported metal pattern and via technologies, not a demonstrated rated cross-stage connection for this candidate.
- [RMT 3MC04 series](https://www.rmt-tec.com/products/thermoelectric-modules/multistage-modules/three-stage-modules/series-3mc04/): independent supplier dimensions, pellet cross-section and operating comparisons; different generation/grade/source conditions.
- [Ferrotec multistage modeling reference](https://thermal.ferrotec.com/technology/thermoelectric-reference-guide/thermalref12/): independent thermal/electrical stage-transport model and energy-accounting precedent; *not* a CAD specification.

Unspecified solder joint, bridge thickness, internal pad mapping, current density rating and alloy composition remain UNKNOWN until source- or process-backed.
