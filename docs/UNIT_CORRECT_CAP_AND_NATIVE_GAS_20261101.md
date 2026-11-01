# Unit-correct cap derivative and bounded native gas experiment

## Registration before construction or comparative field access

Preserve the original STEP/MSH, source registry, prior fields/failures and Rev3.
The seven-port solid studies remain stopped. One attempt at each conditional
phase; no geometry changes to match transport output, retries or refinement.

**A — derivative.** Construct the exact registered shell/roof/window in Gmsh's
millimetre CAD convention, using SI registry lengths converted numerically to mm.
Export a separate STEP with explicit millimetre context; never overwrite or
patch the archived bad STEP. Independently parse length/radius declarations,
then import with target unit M. A separately authored 1 mm cube must import as
1e-9 m³. Require three unique solids, physical radii 7.6/7.1/2.95 mm, z datums
1.5/9.65/10.1 mm, volumes within 1e-8 relative of analytic/source values and
bboxes within 2.1e-7 m (kernel padding). Confirm shared cap interfaces and no
positive-volume header penetration. Keep original/derivative hashes.

**B — native void.** Import the corrected source package and new cap in metres.
Map every solid uniquely to its registered bbox and volume (2.1e-7 m / 2e-7
relative). Explicitly select **external hybrid Cu/Au wires OFF**, matching the
archived wire-off geometry; do not invent volumetric wires. All 216 resolved
package bodies and three cap solids remain, including 88 legs and nine seals/pins.
One Boolean partition with the exact inner-cap cylinder defines gas as envelope
fragments owned by no solid. Require source-volume preservation, no multi-solid
ownership, positive bounded gas volume, one connected gas region, complete
gas/solid face ownership, oriented manifold closure and outward normals. Audit
cap/header and roof/window sealing areas and original solid contact pairs.
Assume exact nominal contacts impermeable; this is a hypothetical construction.
Stop on any ambiguity/failure or >180 s CAD; no tolerance tuning or discarded slivers.

**C — one deliberately conduction-only N2 control, only after B passes.**
No archived solved temperatures are needed: impose a compatible analytic wall
control. Reservoir surfaces (header, seals/pins, cap/window) are 300 K. All
stack surfaces share `T(z)=300-50 u²(3-2u)`,
`u=(z-1.5 mm)/(highest stack top-1.5 mm)`; stack endpoints are 300/250 K.
The common smooth profile is continuous at every solid junction, including
P174 and its hot foot. It is prescribed wall data, not a solved device field.
Freeze that definition with geometry before any result comparison.

Use constant k=0.0259 W/(m K), the registered N2 value at 300 K, with all
temperatures inside the sourced 200–400 K interval. Pressure 101325 Pa passes
the 150 µm gap Kn screen (~0.000452); 100 Pa fails (~0.458). Nominal cavity
Ra~2501 flags possible buoyancy. Suppress flow deliberately: this is a gas
diffusion baseline, not full steady gas behavior or a gas-selection result.

One gas-only P1 mesh: core size 180 µm, outer 600 µm, minimum 30 µm, curvature
16; intended <=300k tets, hard stop at 500k, no refinement. CAD/mesh each <=180 s;
PDE <=120 s, <=4 CPUs/8 GiB, pinned tools, no installation or full TEC solve.
Require positive cells and exact boundary incidence. Independent analytic slab
and uniform controls validate the P1 operator; check interior nodal reactions
and global heat below 1 nW, plus independent raw-gradient global flux <1%.
Report raw surface flux separately from conservative nodal reactions partitioned
by incident face area at shared nodes. The latter is a declared allocation,
not a replacement for raw flux. Flag any failed gate and stop without remeshing.
Save actual stage/body gas surfaces and heat budgets; never use all-Cu volume
integrals as gas port power. No new detector temperature, convection, ranking,
OEM validation or retrospective numerical release is implied.

Produce one concise internal record and an actual geometry/field diagram if
computed. Null stages remain NOT RUN. Run focused/opt-in regression, archive,
master and legacy checks; commit/push verified scoped work and check exact CI.

## Results

**Phase A FAILED; Phases B and C NOT RUN.** The single export attempt did not
produce a unit-correct derivative. This was an implementation error in the new
exporter, not a demonstrated contradiction in the intended physical assembly.
The attempt and failure are preserved; no second export or geometry retry was
made under the registered one-attempt stop.

### Actual unit-aware observations

The author created a 1 mm cube and exported it in a fresh process. Its subsequent
metre-target import correctly gave 1e-9 m³. The cap was then authored with
numerical millimetre dimensions after that SI import. Clearing the import target
option did not restore the assumed writer context in this run: the cap writer
applied another factor 1,000 to coordinate values in its millimetre STEP context.

| Physical quantity | Intended registry | Original archived STEP | New unaccepted attempt |
| --- | ---: | ---: | ---: |
| Outer radius | 7.6 mm | 7.6 µm | 7.6 m |
| Foot datum | 1.5 mm | 1.5 µm | 1.5 m |
| Roof top | 10.1 mm | 10.1 µm | 10.1 m |
| Each cap solid volume / intended volume | 1 | 1e-9 | 1e9 |

An independent read-only validation in the pinned Gmsh 4.13.1 runtime imported
the already-written cube and attempted cap into metres. All three attempted cap
volumes have the same 1e9 volume error; the independent raw STEP parser also
finds 7600 mm = 7.6 m outer radius. The cube still passes. No additional geometry
was authored during this validation. The radius/volume gate therefore rejects
the attempt explicitly; the failed file is **not an approved assembly input**.

`Geometry.OCCTargetUnit` is documented as an import conversion option, not a
promise to reset export/model state when cleared
([official Gmsh manual](https://gmsh.info/doc/texinfo/gmsh.html#index-Geometry_002eOCCTargetUnit)).
That current manual is version 4.15.2; the numerical evidence here is from pinned
4.13.1. Retained writer-unit context is the interpretation of the observed
sequence, not a claim that every OpenCASCADE internal setting was inspected.

The original cap remains unchanged and too small as declared. The new attempt
is too large and its foot is about 1.4985 m above the 1.5 mm header top; it cannot
close the intended cavity. No cap/header seal or void was accepted from it.
The original native SI cap mesh and all source registry dimensions are unchanged.

### Disposition and exact next implementation

The failed producer is kept as `unaccepted_phase_A_attempt/author.py.snapshot`,
with its exact log, cube and attempted STEP. It is not installed as a current
export command. `cap_export_validation.py` only reads and rejects those artifacts.
The candidate's legacy basename is retained for forensic identity; the enclosing
**unaccepted** directory and validation flags govern its status.

The minimum implementation correction is to **isolate writer and reader
processes**: in a fresh author process, export the millimetre cube and cap before
any metre-target import; independently import both in a separate SI reader
process and repeat the registered radius, datum, volume and mating checks.
That additional export is specified, not performed under this stop. No source
geometry, model law, material coefficient or temperature target should change.

| Gate | Actual result |
| --- | --- |
| Independent 1 mm cube / SI import | PASS |
| Attempted cap physical radius, datum and volume | FAIL, uniformly 1,000× length / 1e9 volume |
| Valid derivative published | No |
| Phase B native gas CSG / normals / ownership / closure | NOT RUN |
| Phase C gas mesh / PDE / raw flux / stage heat | NOT RUN; null, not zero heat |
| New detector temperature or resolution of old residual | None |

The original bad STEP, native meshes, solid fields, seven-port stop, raw bath/cold
failures and Rev3 exact bytes are preserved. No gas image or transport field is
invented. The [physical-scale diagram](../data/unit_correct_cap_native_gas_20261101/physical_scale_failure.png)
uses actual parsed/imported dimensions on a logarithmic axis; it is not a mesh
or thermal prediction. No public report change is justified by this failed attempt.

Evidence is in `data/unit_correct_cap_native_gas_20261101`. The read-only check:

```bash
./fem/run.sh timeout --kill-after=5s 120s python -m tecooledmct.cap_export_validation --attempt outputs/copied-unaccepted-attempt
./fem/run.sh pytest -q tests/test_cap_export_validation.py tests/test_native_gas_audit.py tests/test_corrected_enclosure.py
```

Copy the quarantined attempt to an absent output parent first; the validator
refuses to overwrite its result. Reproduction rejects the physical scale and
performs no new export. Software/old-evidence regression results are recorded
separately; passing them cannot turn this failed Phase A into a qualified export.
