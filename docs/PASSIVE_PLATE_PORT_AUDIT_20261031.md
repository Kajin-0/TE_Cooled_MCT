# Internal passive plate/pad experiment: seven-port admissibility

## Registered plan before native audit or reference temperature access

Question: can the proposed finite-plate passive fixture distinguish spreading
from the previous nonlocal fixture's excess gap heat? Preserve the previous
fixed operators, 7.277% side-port failure, original 3D/legacy models and Rev3.

Retain exactly four original ceramics, all original stage Cu bridges/terminals,
and Cu/alumina routing bodies 184–192. Exclude P/N solids, presolder, attach,
die, header and enclosure. Use source manifest/native mesh/SIF only. Map six
stage hot/cold P/N attachment-footprint groups and dedicated 174/192 side patch.
Verify positive body volumes, actual two-sided face ownership, face areas,
footprint orientation/coverage and material k. Check independent port trace
compatibility on native shared nodes/edges, and the rank of grouping footprint
constants into seven scalars. Do not infer heat from surface area or body labels.
Audit the previous side-closure patch adjacency for the same continuity defect,
without rebuilding that operator or evaluating its fields.

**Stop before discretization/solves** if a physical cut interface is unmapped,
or independent port Dirichlet data conflict along a shared positive-length edge.
Do not silently make a cut interface adiabatic, add a reservoir/port, merge the
side port, average incompatible boundary values or regularize an edge. A
seven-scalar grouping cannot be assumed to represent arbitrary nonisothermal
footprint temperatures; distinguish this limitation from internal plate spreading.

Only if admissible: ONE maximum-80-µm fixture, at most 60,000 active cells,
200,000 edges and 180 s build plus seven unit-temperature solves, 4 CPUs / 8 GiB.
Freeze a positive-conductance symmetric Schur response before reading archived
temperatures. Require row closure and port balances <1 nW for 1 K controls,
relative reciprocity/positivity tolerance 1e-10, zero/uniform and analytic
conduction controls, positive-temperature nonnegative entropy production.
Compare old versus finite-plate closures under identical complete boundaries;
never fit coefficients or attribute kelvins without a matched coupled solve.

For an inadmissible boundary, record null comparisons and zero actual fixture
solves; operator reciprocity/entropy and reference-field comparisons are NOT RUN.
Test the gate with analytic/synthetic positive and negative controls. Save a
source-geometry diagram, quantitative interface table/plot and identities.
No reference fields/temperatures will be read on this stop branch.

After this one experiment or its admissibility stop, the next scientific
priority is independent **native interleg gas conduction**, not further solid
grids, extra fitted conditions or another plate fixture. No gas work is run here.

## Results

**STOP: the seven independent constant-temperature ports are not admissible.**
No 80 µm grid, Schur operator or unit-temperature solve was built. No archived
temperature field was read by the fixture experiment. Subsequent independent
regression/archive gates retain their usual checks of historical evidence.
This is a verified boundary/identifiability finding,
not a passive transport prediction or a physical/numerical convergence pass.

### Native geometry and interface mapping

The source-only audit took 4.45 s. It retains 104 actual bodies: four ceramics,
85 original Cu bridges, six original Cu terminals and nine routes/supports
(184–192). Native volumes total 19.647370 mm³; every volume matches its source
CSG value. These are the hypothetical reference's registered construction
dimensions. Cu k=400 and alumina k=30 W/(m K) match the actual constant-k SIF.
The read-only 366,156-tet native mesh supplies ownership and geometry only.
All 22,846 audited contact triangles have positive area, two correct material
owners and source-matching areas; 119 contact pairs are internal to the fixture.

| Proposed port / actual cut | Native patches | Area (mm²) | Mapping |
| --- | ---: | ---: | --- |
| Stage 1 hot / cold | 56 / 56 | 8.96 / 8.96 | Grouped P/N end footprints |
| Stage 2 hot / cold | 24 / 24 | 3.84 / 3.84 | Grouped P/N end footprints |
| Stage 3 hot / cold | 8 / 8 | 1.28 / 1.28 | Grouped P/N end footprints |
| 174/192 side | 1 | 0.0121 | Dedicated side patch |
| 1/301 hot ceramic–presolder | 1 | 40.96 | **Unmapped physical interface** |
| 4/302 cold ceramic–die attach | 1 | 1.00 | **Unmapped physical interface** |

The seven ports cover 28.1721 mm², while 41.96 mm² of physical cut interfaces
have no registered condition. Areas describe coverage, **not heat-flow shares**.
The omitted hot and cold reservoir/load couplings cannot be erased when claiming
matched boundaries with the archived active device. No extra port, imposed flux
or adiabatic cut condition was introduced.

### Independent side-port constants violate interface continuity

The native stage-3 hot P174 footprint (Cu183/P174) and side patch (192/P174)
meet along the **same 0.220 mm edge**, represented by two native segments and
three nodes. Its exact coordinates are x=−1.025 mm, z=4.425 mm,
y=0.175–0.395 mm. Thus a side-only unit basis asks those three conforming nodes
to have both zero and one temperature increment. Adding finite plates and pads
does not remove this incompatible boundary trace.

The same native edge joins the **previous** fixture's 183/192 and 174/192
constant-temperature cut patches. This identifies a structural defect in the
centroid side-temperature closure that is relevant to its unresolved 7.277%
refinement sensitivity. It does not determine what fraction of that change or
the gap heat error comes from this defect.

An independent analytic control illustrates why positive discrete conductance
alone would not fix it. In an extruded homogeneous wedge with meeting boundary
temperatures separated by ΔT, the harmonic angular solution gives

`D = integral k |grad(T)|² dV = k L (ΔT)² / theta * ln(R/epsilon)` [W K].

For nonzero ΔT, D depends logarithmically on the edge cutoff and diverges as
epsilon tends to zero. For positive absolute temperatures,
`D/Tmax² <= entropy production <= D/Tmin²` [W/K]. A composite Cu/alumina wedge
has different coefficients, but positive bounded k does not remove the
incompatible edge jump. This analytic example is **not** a fitted device
conductance or a quantitative explanation of the measured refinement change.

There is a second, distinct information limit: 177 patch-constant values map to
seven group scalars, leaving 170 zero-group-mean patch modes unrepresented.
This is an algebraic patch-mean rank statement, not a claim that seven independent
constants possess a continuous native nodal extension. General nonisothermal
P/N footprint data and a side profile continuous into the hot foot are absent.
Their actual archived temperature variations were not examined on this stop branch.
The obstruction applies to these registered constant-patch ports. A compatible
continuous spatial basis would require additional profile assumptions absent
from this experiment; seven amplitudes alone do not specify that basis.

### Scientific disposition and next priority

| Requested comparison | Actual result |
| --- | --- |
| New passive reciprocity / port balance / entropy | **NOT RUN**: no admissible operator |
| Old versus finite-plate flux under matched boundaries | **NOT RUN**: boundary closure fails |
| Archived plate mean-to-face differences / side reactions | **NOT RUN**: no operator frozen, no reference field read |
| Spreading contribution to prior +4.937178 / +4.916427 mW gap excess | **Unidentifiable**, not zero and not attributed |
| Causal kelvin reconciliation | **Not established**; prior −0.782163 K residual remains a conditional result |

The registered stop is complete. No extra port/profile, contact law, fit, grid,
passive rerun or coupled reduced solve is substituted. Original five-node/3D
models, frozen nonlocal evidence, the side 5% failure and original raw bath/cold
failures remain intact. Rev3 is unchanged because no new predictive physical
reconciliation was established. The next scientific priority is **independent
native interleg gas conduction**, with physically appropriate regime checks;
this checkpoint does not implement gas/CFD or authorize more solid-side churn.

### Evidence and checks

`data/passive_plate_port_audit_20261031/boundary_audit.json` contains exact body,
face, port and edge witnesses, the registration verbatim, hashes and explicit
null comparisons. `native_boundary_geometry.npz` preserves native node IDs and
actual interface triangles; the two PNGs show the native edge and interface
areas. In the geometry view, translucent red planes mark unmapped cuts; opaque
colored patches mark stage ports. They depict geometry, **not solved temperatures**. No all-Cu body integral
is treated as a port reaction. The source/field archives are untouched.

[Native geometry and shared edge](../data/passive_plate_port_audit_20261031/native_port_geometry.png)
and [quantitative cut-area plot](../data/passive_plate_port_audit_20261031/native_port_coverage.png).

```bash
./fem/run.sh python -m tecooledmct.passive_plate_audit --out outputs/new-passive-port-audit
./fem/run.sh pytest -q tests/test_passive_plate_audit.py tests/test_nonlocal_solid_network.py tests/test_solid_model_diagnostic.py tests/test_engineering_report.py
```

Use an absent output directory. Reproduction performs the geometry gate only;
the expected result is an explicit scientific STOP with zero fixture solves.
Verification results, original-PDF identity and full archive/legacy checks are
recorded in the accompanying verification record. Passing software tests does
not change the experiment's inadmissibility or any historical numerical failure.
