# Native interleg gas conduction: geometry and regime gate

## Registration before comparative field access

Use only the corrected C-layout package and standalone corrected cap/window
sources. The stopped seven-port solid experiment stays closed. Preserve all
original sources, fields, failures and the single Rev3 master.

Source inspection has identified a possible STEP unit inconsistency: both files
declare millimetres while cap cylinder values resemble SI metre coordinates.
This is an unblinded source-format observation, not a transport comparison.
Verify it independently before choosing a gas domain or reading solved fields.

1. Check protected package/cap STEP, mesh, registry and hypothesis hashes.
   Parse STEP length declarations independently of Gmsh; compare source cylinder
   radii, frames and native cap tetrahedral volumes with SI registry dimensions.
2. ONE bounded Gmsh/OpenCASCADE import session, explicitly targeting metres:
   verify a separate analytic 1 mm cube STEP round-trip, then import the actual
   216-body package and three cap/roof/window solids without scaling/healing.
   Compare package/header and cap volume/frame identities. At most 120 s,
   4 CPUs / 8 GiB; no retry, tool install, source edit or silent unit correction.
3. **STOP before Boolean/meshing/PDE** on inconsistent units, missing bodies,
   solid penetration, unassigned/open boundary or unverifiable sealing/access.
   Provide the exact defect and one minimum next fix; do not report gas regions,
   normals, stage heat budgets or conservation as checked when not extracted.
   Hybrid wire centre-lines are not native volumetric solids; their treatment
   would need an explicit wire-off scenario or registered 3D construction.
4. Only after this gate: a single native gas Boolean difference using all
   resolved solids (88 legs, Cu, supports, ceramics, joints/die, header/pins,
   cap/window). Nominal cap/header and window contacts are assumed impermeable.
   Verify positive bounded void volumes, connectivity, watertight/manifold
   interfaces, exclusive solid ownership, outward normals/areas, no overlap/leak
   and no filled-core substitute. Bound CAD work to 180 s; one mesh <=300,000
   tets (hard stop at 500,000), <=180 s meshing, one <=120 s constant-k gas solve.
   No retries, refinement, full thermoelectric production solve or CFD.
5. Gas starts with N2 only. Screen actual same-stage interleg gap and nominal
   cavity height at 100 Pa and 101325 Pa, T=300 K and a declared 50 K contrast.
   Reuse only registered conductivity/kinetic formulas, never G3b geometry or
   visibility/chords. The NIST table domain is 200–400 K; Eucken viscosity is
   an engineering closure. Choose continuum only when the relevant Kn<0.01
   conservative screening gate passes; Ra/orientation must qualify neglect of
   buoyancy or explicitly restrict the result to a conduction-only control.
   A stopped geometry permits conditional scale screens, not a selected case.
6. An admitted gas calculation must use complete continuous prescribed wall
   temperatures from a declared archived field or analytic control, conserve
   mapped heat to 1 nW reactions and <=1% raw global flux discrepancy, pass
   analytic slab/zero controls, positive tetrahedra and surface ownership checks.
   Freeze geometry and boundary definitions before comparative fields. It is
   one-way gas diffusion, not a new device temperature or gas-selection result.

Save actual reader/source identities and targeted negative/analytic tests. If
stopped, use null heat budgets, zero gas cells/solves and no invented gas field.
Run focused regression, archive/master integrity and relevant legacy checks;
commit only verified scoped evidence and check exact CI. Rev3 remains unchanged
unless genuinely verified predictive physics warrants an in-place update.

## Results

**STOP at the source-unit gate.** The two current STEP exports do not share a
consistent physical scale. No Boolean void extraction, gas mesh, PDE, fitted
transport coefficient or new device temperature was produced. The stopped
solid studies and their unqualified residual remain unchanged.

### Reproducible defect: cap STEP is 1,000 times too small

Both package and cap STEP files explicitly declare `SI_UNIT(.MILLI.,.METRE.)`.
The package uses millimetre coordinates consistently. The cap export instead
writes SI-sized numbers into that millimetre context. Independent raw STEP
parsing and an actual OpenCASCADE import targeting **metres** agree:

| Quantity | Intended SI registry / native cap mesh | Unit-aware cap STEP |
| --- | ---: | ---: |
| Outer radius | 7.6 mm | 0.0076 mm = 7.6 µm |
| Header-foot datum | 1.5 mm | 0.0015 mm = 1.5 µm |
| Roof top | 10.1 mm | 0.0101 mm = 10.1 µm |
| Each of three cap solid volumes | Reference | 1e-9 × reference |

The registered source audit completed in 5.12 s; the import session ran once.
A separately exported 1 mm cube imports as
1e-9 m³, independently checking reader scale. The corrected package imports
as 216 volumes with correct aggregate/header volumes. The cap imports as three
volumes, each at 1e-9 of its SI registry volume. Its original 8,143-tet native
MSH remains positive and consistent with the intended SI volumes; this defect
is in the exported STEP's physical-unit context, not a rescaled historical field.

As imported, the entire cap lies inside the Kovar header: its z range is near
1.5–10.1 µm while header thickness is 1,500 µm. Its radial extent is far inside
the central header disk and every feedthrough/mounting bore. The source-only
containment witness is saved numerically; this is a solid-penetration failure,
not a candidate sealed cavity. The cap-defined interior minus the actual header
would be empty. No gas topology or ownership is claimed from that contradiction.
CAD bounding boxes include kernel tolerance padding; exact dimensions above
come from independently parsed STEP entities and their declared units.

### Conditional molecular/buoyancy scales, not an admitted operating point

Source counts are 88 legs (56/24/8), nine pins, nine glass seals and three
cap/roof/window solids. Four external wire routes remain 1D hybrid centre-lines,
not native 3D solids. A subsequent domain must explicitly select the archived
wire-off configuration or construct and audit their volumes; they are not
silently replaced with a filled core or generic pin layout.

The actual same-stage P/N box gaps are 150 µm. The nominal SI cavity height is
8.15 mm. The following conditional screens use N2 at 300 K, 50 K contrast,
k=0.0259 W/(m K), registered ideal-gas/Eucken formulas and +z vertical:

| Pressure | Mean free path | Kn at 150 µm | Ra at 150 µm | Ra at nominal cavity height |
| --- | ---: | ---: | ---: | ---: |
| 100 Pa | 68.706 µm | 0.4580 | 1.52e-8 | 0.00244 |
| 101325 Pa | 0.067807 µm | 0.000452 | 0.0156 | 2501.5 |

Thus bulk continuum conduction at 100 Pa fails the conservative interleg
Kn<0.01 screen. Atmospheric N2 passes that gap screen, but its nominal cavity
Ra flags potential buoyancy; 1708 is an ideal heated-below slab indicator, not
a universal threshold for this geometry. No orientation-independent no-convection
claim follows. Source k is bounded to 200–400 K; Eucken viscosity is an estimate,
not measured viscosity or a validated rarefied law. These scales do not qualify
the missing gas domain or select an operating pressure. No N2/Ar/Kr comparison,
slip/jump model, ray-chord diffusion substitute or CFD was run.

### One minimum next fix and checks

**Publish one separate unit-correct cap/window STEP derivative**, with explicit
physical units and an export/import round-trip checking SI bounding boxes,
volumes and datum against the existing registry and native MSH. Preserve the
original archived STEP bytes and expose its unit defect. This is a geometry
interchange correction, not a change to cap dimensions or a fit to temperatures.
Then resume the registered native-void subtraction and sealing/ownership gates.
No broad geometry redesign or solid-model reopening is indicated by this audit.

Connectivity, manifold closure, gas/solid normals and areas, void mesh quality,
analytic slab/PDE balances, stage-resolved gas heat and flux fields are all
**NOT RUN**. Their saved values are null, not zero heat or successful checks.
Rev3 is unchanged: no qualified predictive gas calculation warrants a report update.

Evidence: `data/native_gas_domain_audit_20261101/audit.json` records raw unit
declarations, actual CAD imports, cube control, source counts, containment,
conditional regime screens and hashes. The cube STEP is a reader control,
not a package/gas CAD replacement. No gas figure is fabricated. Reproduce:

```bash
./fem/run.sh timeout --kill-after=5s 120s python -m tecooledmct.native_gas_audit --out outputs/new-native-gas-audit
./fem/run.sh pytest -q tests/test_native_gas_audit.py tests/test_passive_plate_audit.py tests/test_nonlocal_solid_network.py tests/test_corrected_enclosure.py
```

Use an absent directory. This command reproduces the expected explicit scientific
STOP; it does not silently normalize geometry or run transport. Verification
results and original archive/master identities are recorded alongside the audit.
