# Current V3 project status and reviewer guide

**As of 2026-11-03; documentation-only snapshot.** The authoritative contract
is [AGENTS.md](../AGENTS.md). This guide distinguishes current geometry from
historical physical and numerical failures. It does not grant new numerical,
manufacturing or physical qualification.

## Current configuration

| Layer | Published milestone | What is actually established |
| --- | --- | --- |
| **Physical** | [V3 R1 824-solid assembly](SYNTHETIC_V3_ASSEMBLY_CAD_20261102.md); [conditional independent design review](SYNTHETIC_V3_CORRECTIVE_INDEPENDENT_REVIEW_20261102.md) | 88 thermoelectric legs (29/11/4 couples; 58/22/8 legs), 176 leg contacts, 89 internal TEC nets, real formed tabs and joints, TEC leads pins 1/9, detector bonds pins 7/8. Frozen STEP. Physical/manufacturing acceptance **CONDITIONAL**, not supplier or OEM qualified |
| **Prior accepted analysis geometry** | [R2 derived BREP and surface-mesh record](V3_ANALYSIS_R2_GEOMETRY_AND_MESHABILITY_20261103.md) | 428 conformal volumes, 2,422 registered faces, one connected gas volume, 824/824 sources and 378 declared finite contacts preserved |
| **R2 global surface mesh** | [R2 surface evidence](../data/v3_analysis_r2_release_20261103/) | 1,416,664 triangles / 701,952 nodes; **0 / 2,422** CAD-face areas fail the 1% gate (maximum 0.509281%); surface fidelity only |
| **Newest R3 derived geometry** | [R3 source migration/mesh STOP](V3_ANALYSIS_R3_GLOBAL_MESH_20261103.md) | 430 conformal volumes, 2,440 owned faces, 824/824 source mappings, 378/378 declared contact witnesses, original jackets represented as volume, six full/four partial dielectric regions, **0.077162028 mm³** polymer excluded from cavity gas |
| **R3 global mesh** | Same R3 record | One adaptive surface attempt **STOPPED at 600.073 seconds**, without a completed mesh; no R3 surface-area PASS or 3D volume mesh |
| **Local geometric meshability** | R2 lead/pin fixture | 38,496 tetrahedra, four domains; source-volume differences 0.321–0.537%; not global convergence |
| **Electrical physics** | [V3 Gate B](V3_INTERCONNECT_ELECTROTHERMAL_20261102.md), [conservative-flux study](V3_CONSERVATIVE_FLUX_20261102.md) | Numerical **STOP**: P1 cut mismatch 81.241662%, recovered loss discrepancy 0.769154%, mixed-potential undershoot, lost mixed-flux export; not a full TEC rating or heat partition |
| **Thermal/coupled physics** | [R3](V3_ANALYSIS_R3_GLOBAL_MESH_20261103.md) and Gate B dependency | V3 thermal Gates C/D **NOT RUN**. New geometry's material/interface laws **UNSET**; no qualified V3 temperature, voltage, heat budget or cooling prediction |

The original 824-solid physical STEP and canonical 38-page
[Rev3 engineering report](../reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf)
remain byte-identical. [Issue #2](https://github.com/Kajin-0/TE_Cooled_MCT/issues/2)
remains open; its original V2 STOP is retained as historical evidence.

## What changed since the older reviews

1. **V2 STOP is historical.** Earlier models with physically unsupported Cu
   interstage routing and absent connections are not the present physical V3 R1
   design. V3 has conditional physical-design acceptance, not unconditional
   manufacturability or measured performance.
2. **The physical-to-analysis interface now exists.** Source names, volumes,
   finite contacts, ownership and cavity topology are explicitly mapped.
   A contact *witness* count of 378 is not the number of all material faces.
3. **R2 passed only a high-cost 2D geometric area gate.** Its 1.417-million
   surface triangles were too costly to accept automatically for full 3D meshing.
4. **R3 fixed gas/jacket representation geometrically.** Reinstating the two
   original 15 µm dielectric jacket volumes prevents gas occupying the
   removed-polymer region. Material laws, finite-contact coupling, and global
   mesh quality remain unqualified. The R3 surface attempt ended at its time
   limit without a mesh, so do not claim surface fidelity or tetrahedral success.
5. **Reduced physics is not V3 device physics.** Earlier reduced TEC studies
   commonly used 28/12/4 couples, versus V3's 29/11/4. Some reduced scenarios
   predict 186–200 K; neither the geometry nor the numerical results make
   those V3 coupled multiphysics predictions.

## Known physical and constitutive limits

The design retains a tight **6 µm** upper height reserve and nominal
**20%** simple outer-fiber strain proxy for 30 µm copper foil / 75 µm bend
radius. These are risk screens, not accepted physical redesigns.

The corrected Zhang P/N analog source covers **40–300 K** as experimental
data from research specimens. Reduced-model behavior above 300 K relies on
an explicitly assumed continuation within a selected numerical range; it is
not measured hot-side transport. Thin-film, dielectric, gas, radiation,
contact and detector laws remain to be qualified for R3. No current rating,
sealed-package hermeticity, manufacturing yield or OEM fit is established.

## Next action and guardrails

The R3 report proposes an independently scoped check of **local periodic-wire
surface sizing and its execution cost**, distinguishing surface-size-field
implementation overhead from unavoidable curvature resolution. This is a
**proposal**, not authorization to repeat the failed global surface attempt.

After a bounded, preregistered surface strategy passes all CAD-face/contact/
dielectric and source-provenance gates at affordable density, evaluate one
global conformal tetrahedral mesh under the declared resource budget. Preserve
the original physical STEP, accepted R2, all failed R3 trials, full numerical
STOP history and the 38-page Rev3. Do not initiate PDE calculations based on
this documentation update.

## Reviewer reading order

For present geometry: [R3 milestone](V3_ANALYSIS_R3_GLOBAL_MESH_20261103.md)
→ [R2 predecessor](V3_ANALYSIS_R2_GEOMETRY_AND_MESHABILITY_20261103.md)
→ [V3 physical CAD](SYNTHETIC_V3_ASSEMBLY_CAD_20261102.md)
→ [independent conditional physical review](SYNTHETIC_V3_CORRECTIVE_INDEPENDENT_REVIEW_20261102.md).

For numerical limitations: [V3 Gate B](V3_INTERCONNECT_ELECTROTHERMAL_20261102.md)
→ [conservative-flux experiment](V3_CONSERVATIVE_FLUX_20261102.md)
→ [typed archive protocol](V3_FLUX_ARCHIVE_INTEGRITY_20261103.md).

For historical reduced-model claims:
[material plausibility](TEC_MATERIAL_PLAUSIBILITY_20261101.md),
[identifiability](TEC_GEOMETRY_MATERIAL_IDENTIFIABILITY_20261101.md),
[finite sink](FINITE_SINK_MATCHED_TARGET_20261101.md),
and the preserved [Rev3 master](../reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf).

**Read current date-scoped status before older documents labelled CURRENT or
STOP. Their original wording is evidence of historical checkpoints, not a
replacement for the newest geometry state.**
