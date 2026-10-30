# Package geometry and lead discrepancy audit

All numerical temperatures/powers here refer to the **previous assumed geometry**.
The separate [source rebaseline](GEOMETRY_SOURCE_REBASELINE_20261030.md) supplies
the new independent registry; it has no revised coupled solution yet. A VIGO
family housing plus independent TEC Microsystems candidate is not an identified
commercial detector assembly.

| Item | Previous geometry | Source requirement / qualification status |
|---|---|---|
|Flange|31.5×17.5 mm ellipse|Two-ear tangent/circular profile; old ellipse rejected for new geometry|
|Header|1.1 mm|VIGO A-A1.5 mm; source endpoints checked|
|Pins|NineØ0.44 mm, generic instances|VIGO nineØ0.76 mm onØ10.8 PCD, C arrangement|
|Pin functions|Cu generic instances2/3, Au opposite endpoints|Bottom-view TEC1/9, detector7/8, thermistor5/6|
|TEC widths|6.4/2.4 mm|Correct selected independent3MC04-044-05 source values|
|TEC interior|28/12/4 and4.55/3.25 mm plates|Inferred, not OEM measured|
|Case height/window|8.6 mm above header;5.9 mm window|Datums/optical seat and internal carriers unresolved; no matching source claim|
|Supply return|Old body183, stage2 hot pad|Must physically route full series return to module hot side|

Primary sources are the [VIGO drawing](https://vigophotonics.com/app/uploads/2024/07/3TE-TO669p-wW-PVI_PCI-detector-technical-drawing.pdf)
and [TEC Microsystems datasheet](https://www.tec-microsystems.com/Download/Datasheets/Thermoelectric%20Coolers/MC04%20Series/3MC04-044-05_Datasheet_2019.pdf).
Bottom→top mirrors x with page-up y fixed. Old Cu warm endpoints are separated
36°, but specified TEC1/9 are separated72°. Old Au endpoints are180° apart,
but detector7/8 are36° apart. Rigid rotation/mirroring cannot repair these
functional pairs by relabelling; cylinders/endpoints must move.

Independent actual-mesh/raw-VTU face-area averages reproduce the old907-patch
lead powers, with G=0.001602369333 W/K per assumedØ0.202 mm×8 mm Cu lead:

| Lead | Warm tag / T K | TEC tag / T K | Net conduction into TEC |
|---|---|---|---:|
|0|204 /300.118202|103, stage0 /300.242197|−0.198686 mW|
|1|206 /289.486509|104, stage2 /278.307388|+17.913081 mW|

Sum17.714395 mW; each lead's I²R is42.9364 µW and remains a separate source.
The old stage0 terminal centroid is z=0.0325 mm; the return centroid is
z=2.6225 mm. The latter is spatially mid-stack. These are independently measured
endpoints, not names inferred from a schematic.

Lead0's patch-centroid distance is8.111498 mm against assumed8 mm length. This
flags the lumped centroid construction. It **does not prove physical impossibility**:
finite attachment patches have a conservative separation lower bound7.688875 mm
and an actual vertex-pair upper bound7.773085 mm. Actual bond positions and arc
length remain unknown. The initial overstrong centroid interpretation is retained
as unaccepted development; the corrected v2 audit is authoritative for this claim.

The matched actual old fine mesh has204855 nodes/821874 tets. Holding bath,
current, die heat, gray radiation, N2 pressure and Au paths fixed, disabling Cu
conduction and lead Joule gives die266.078136 K versus old lead-on268.798701 K:
**2.720565 K reduction**. V changes0.538259589→0.554844426 V. Its raw bath error
is−0.360846%, while original lead-on remains **FAILED +1.655873%**. This is a
controlled sandbox perturbation, not proof that leads alone explain the raw
gradient defect. The older gas/radiation-off coarse lead-only shift3.064820 K is
a different operating point and must not be substituted for this matched result.

The next corrected full model needs an insulated3D return conductor with its
thermal shunt and two module-hot-side pads. Moving only the thermal endpoint
would omit that internal current/heat path. New pin1/9 hot-side route coordinates
are previews, with no175-cut or physical lead-on claim. Detector bonds must
connect7/8; thermistor paths5/6 remain absent.

Old balanced view factors conserve power but do not validate geometry: raw
reciprocity L1/area≈0.213338 and weighted closure≈0.013627 remain material errors.
New source geometry requires fresh occlusion/rays/patches and ray-count checks.
The fixed-field pressure screen is an algebraic sensitivity diagnostic only,
not a recoupled temperature prediction. High-pressure1D gas-gap extrapolations
are **model-form unqualified**; low Kn requires an appropriate continuum gas
geometry solution and convection assessment. Gray emissivity, accommodation0.8,
gas composition/pressure and the opaque window remain hypotheses. Imposed
optical heat is parametric absorption, not external flux transmitted by that window.

Priority remains geometry/return path→matched lead controls→flux convergence→
contact/wetting→environmental/OEM holdouts. The historical15-page PDF and all
old evidence remain unchanged and are not product-predictive validation.
