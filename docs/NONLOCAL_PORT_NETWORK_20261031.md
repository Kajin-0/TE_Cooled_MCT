# Internal Milestone 2: geometry-derived nonlocal solid paths

This is an opt-in diagnostic, not a replacement for the original five-node
model or the single Rev3 master. Milestone 1 and all original numerical gates
remain intact. No whole-device FEM or gas calculation is authorized here.

## Registration before comparative calculations

Fix the model using only the corrected manifest, actual mesh geometry and SIF
material constants. Do not load solved fields, measured heat flows or Milestone 1
comparison outputs until all three geometry operators are written and fingerprinted.

- Model Cu 184/185/190/191 and alumina 186/187/188/189/192 as an orthogonal,
  positive-conductance local finite-volume/resistor network. Raw support boxes
  are cut by Cu before assignment; reject overlapping material ownership.
  Use exact box-coordinate planes, shared-face areas and half-cell series
  resistances: G=A/(di/ki+dj/kj). This is a local reduced conduction fixture,
  not a solved full-device 3D thermoelectric field.
- Audit every retained body volume and contact area against the manifest and
  actual native tetrahedra. Face neighbors alone connect cells; no edge/point
  contacts. Outside faces are adiabatic. Reject any unmapped solid contact.
- Thermal ports: source ceramics 1/2/3 and adjacent original Cu pads are
  isothermal at their corresponding reduced node temperatures. This omits
  finite plate/pad spreading and is an explicit closure, not a fitted contact R.
  All declared contact areas come from geometry, including the distributed
  Cu/alumina interfaces. No FEM heat-flow-derived K is permitted.
- The 192/174 side contact gets its own thermal port at its geometric area
  centroid. Split P leg 174 into two conduction segments there, keeping its
  original length, area, k, electrical R and total Joule heat. Retain the full
  stage Seebeck/Peltier terms; distribute segment Joule conservatively. The
  rest of the P/N stages retain the original alpha/R/K without rescaling.
- Solve the four disconnected Cu routes electrically using their geometry and
  rho=1.72e-8 ohm m, with equipotential contact ports, prescribed series 0.1 A
  and no current in alumina. Derive route R and spatial Joule from this operator;
  conserve IV=sum(Joule), including boundary half-cell elements. Original Cu
  bridges/pads outside the retained domain remain omitted, not silently fitted.
  Split intercell element heat equally; split a material-boundary element
  between cell/thermal port, while external adiabatic-terminal heat stays in Cu.
- Condense internal thermal nodes to a multiport response and Joule source.
  Keep nonlocal off-diagonal terms; never replace them with stage-local K values.

Fixed numerical levels: maximum coordinate spacing 160/80/40 micrometres,
at most 60,000 active cells / 200,000 edges per level, 180 seconds per build,
4 CPUs / 8 GiB runtime. No target-driven mesh adjustment or parameter search.
All three operators must be fixed before comparative data are opened.

Baseline and controls: fixed hot ceramic 300.1148977882757 K, I=0.1 A, uniform
die source 2 mW, external Cu/Au OFF, gas/radiation OFF. OFF must recover the
original matched five-node result within 2 microK / 20 nV. ON is solved once
per registered level; no additional operating sweep. Passive unit-temperature,
uniform-temperature, zero-current/load, analytic layered-bar, invalid-input and
sign-reversal tests verify the network independently.

Reject geometry mismatches above 1e-8 relative (absolute tolerances 1e-20 m3 /
1e-18 m2). Require positive face G, reciprocal/symmetric reduced operators,
nonpositive off-diagonals and nonnegative eigenvalues within 1e-10 relative
roundoff, row closure <1e-10 W/K, and port/electrical/thermal work balances <1 nW.
Reject temperatures outside 180–390 K and singular/disconnected port problems;
never clip a result. A coarse-to-fine difference >0.1 K cold temperature or >5%
path heat flags unresolved numerical sensitivity, not an invitation to tune.

Report before/after ceramic temperatures, stage lifts, isothermal die and a
separate source-law finite-die readout estimate, module voltage, per-route Joule,
node budgets and remaining discrepancies. Compare sharp horizontal path fluxes
at the same geometry-derived leg-midplanes; do not subtract Milestone 1 P1
indicator powers from sharp-plane predictions. Archive gradients remain unqualified.

Even an improved match cannot establish a unique physical mapping from ceramic
volume means to contact temperatures. If that closure or discretization prevents
attribution, retain the residual and specify ONE bounded passive port/spreading
experiment. Do not add fitted bypasses, unregistered closures or new production
FEM. Rev3 changes require a verified predictive conclusion worth presenting;
otherwise preserve its exact current bytes and publish this internal note only.

## Results

**Conditional mechanism identified; mean-to-contact closure and side-port
convergence remain unqualified.** The geometry-only network predicts 8.412629 K
warming, overshooting the archived cold ceramic by 0.782163 K. Absolute mismatch
falls 89.75%, without fitting. This is neither a physical accuracy bound nor a
unique causal allocation of kelvins to individual paths. The three registered
levels are complete; the side-contact sensitivity stops further refinement here.

### Geometry, equations and fixed coefficients

Inputs are the corrected `geometry_complete_checkpoint_20261030` manifest/native
mesh and `corrected_coupled_thermal_20261030/cases/cu_off/case.sif`. All nine retained
volumes and 29 contact areas agree with source CSG/native faces to the registered
tolerances. This is the hypothetical internal construction already in that mesh,
not an independently measured assembly. Known source contact areas do not establish
actual manufactured contact resistances. No thermal contact resistance is added.

| Gap path | Axial cross-section at the comparison planes | Actual connectivity |
| --- | --- | --- |
| Cu 184 | 60 × 60 µm; 0.0036 mm² | Pad 117 → buried plate-2 route → pad 165; T0–T1 |
| Alumina 186 | 135 × 200 minus 60 × 60 µm; 0.0234 mm² | Hot plate/pad → plate 2, distributed contact to 184 |
| Cu 185 | 60 × 60 µm; 0.0036 mm² | Pad 166 → buried plate-3 route → pad 182; T1–T2 |
| Alumina 188 | 200 × 185 minus 60 × 60 µm; 0.0334 mm² | Plate 2/pad → plate 3, distributed contact to 185 |
| Cu 191 | 100 × 80 µm; 0.0080 mm² | External hot pad → pad 183; spans both gaps, bypasses T1 |
| Alumina 192 | 300 × 220 minus 100 × 80 µm; 0.0580 mm² | T0 → T2/pad 183 plus P174 side contact; bypasses T1 |

The full source box unions determine bends, lengths and lateral Cu/alumina
coupling, rather than A/L for a stage-local bar. For example, vertical Cu boxes
184/185/191 are 1.3275/1.0775/2.630 mm long. Exit collars 187/189 and hot input
190 are retained too. The 192/174 contact has area 0.0121 mm² and centroid
27.5 µm above P174's hot end, within its 640 µm leg; replacing it by T2 would
erase a real thermal connection. All box coordinates remain in the source manifest.

With SI units, each cell face uses `Gij=A/(di/ki+dj/kj)` in W/K. The local
rectilinear diffusion fixture resolves conduction inside these routes/supports;
the rest of the device is reduced. Schur condensation gives
`Qout=Kport Tport − jport I²`, with `Tport=(T0,T1,T2,TX)`. Kport is symmetric,
has zero row sums, nonpositive off-diagonals and nonnegative eigenvalues within
roundoff. At 40 µm its equivalent *nonlocal* positive edge conductances are:

| Edge | T0–T1 | T0–T2 | T0–X | T1–T2 | T2–X |
| --- | ---: | ---: | ---: | ---: | ---: |
| G (mW/K) | 1.752610 | 0.871918 | 0.000341 | 2.511605 | 7.184197 |

Cu uses k=400 W/(m K), rho=1.72e-8 ohm m, S=0; alumina k=30 W/(m K).
The original P/N counts 28/12/4, alpha/R/K and constant verification laws are
unchanged. Each stage obeys `Qc=alpha I Tc−K ΔT−I²R/2`,
`Qh=alpha I Th−K ΔT+I²R/2`, `V=IR+alpha ΔT`, except that stage 3's split P174
segments explicitly retain side heat: `Qh−Qc=IV+Qside`. The side is thermal
only, with no electrical branch. Joule source partition is conservative.

### Prediction versus reference, after operator freeze

All cases: I=0.1 A, die heat=2 mW, hot ceramic=300.114897788 K; external Cu/Au,
gas and radiation OFF. Temperatures below are K. Archived values are volume
means, while reduced values are node temperatures; this distinction remains.

| Observable | Original / OFF | Network ON, 40 µm | Archived 3D |
| --- | ---: | ---: | ---: |
| Plate 2 | 281.877130 | 285.217805 | 284.998212 |
| Plate 3 | 268.118227 | 276.875459 | 276.087269 |
| Cold ceramic | 257.793580 | 266.206209 | 265.424046 |
| Isothermal die node | 257.853580 | 266.266209 | — |
| Separate finite-die 1D mean | — | 266.386605 | 265.592524 |
| Stage lifts, hot to cold | 18.237768 / 13.758903 / 10.324647 | 14.897093 / 8.342346 / 10.669250 | 15.116685 / 8.910943 / 10.663223 |
| Module V (V) | 0.585707694 | 0.544129405 | 0.551939871 |
| FEM minus cold prediction | +7.630466 | −0.782163 | — |
| FEM minus voltage prediction (mV) | −33.767823 | +7.810466 | — |

The original model's isothermal die must not be equated to the 3D volume mean.
The extra 1D readout solves `−d(k(T)dT/dz)/dz=qvol`, uniform heating and an
adiabatic top, by a Kirchhoff transform of the actual MCT source law. It does
not feed back into the constant-load solution. Its remaining die error is
−0.794081 K (FEM minus prediction), rather than the isothermal node's −0.673685 K.

| Path at exact common plane | Predicted upward mW | Archived raw upward mW |
| --- | ---: | ---: |
| Gap 1, z=2.370 mm: Cu 184 / Al 186 | 17.552114 / 8.556683 | 14.929813 / 7.281411 |
| Gap 1: Cu 191 / Al 192 | 13.099551 / 7.123867 | 12.426563 / 6.757248 |
| Gap 2, z=3.665 mm: Cu 185 / Al 188 | 12.354731 / 8.598117 | 10.070515 / 7.005126 |
| Gap 2: Cu 191 / Al 192 | 13.118110 / 7.133153 | 12.444860 / 6.767184 |
| Total gap 1 / gap 2 | 46.332214 / 41.204111 | 41.395036 / 36.287684 |

Same planes, material ownership and cross-sectional areas are independently
verified. S=0 on these paths, so the archived comparison is raw `−k grad(T)`.
Positive is upward, toward the cold end. There is no retained path through the
third-stage midplane. These sharp powers are **not** the earlier P1-indicator
41.392/36.293 mW; numerical flux release failures remain explicit.

| Cu route | Geometry R (ohm) | Predicted Joule (mW) | Archived Joule (mW) |
| --- | ---: | ---: | ---: |
| 184 | 0.052539 | 0.525387 | 0.510245 |
| 185 | 0.018427 | 0.184269 | 0.171039 |
| 190 | 0.007277 | 0.072766 | 0.072048 |
| 191 | 0.024600 | 0.246002 | 0.243634 |

These four routes add 10.284237 mV and 1.028424 mW. Other original Cu bridges/
pads remain outside this network; the archived *all-Cu* loss is 12.369902 mV.
The remaining 7.810466 mV terminal gap also contains changed stage lifts and
unresolved current-weighted thermopower; it is not purely a missing resistor.
Using Milestone 1's independent volume-work identity, that gap separates into
+4.272727 mV from ceramic-mean drops, +2.085665 mV from all-Cu loss minus the
four modeled routes, +1.441007 mV current-weighted reversible correction,
+0.011073 mV P/N localization loss and −0.0000055 mV terminal/work remainder.
Their sum closes to 2e-16 V; this is post-freeze accounting, not a voltage correction.

At the fine level, network heat into (T0,T1,T2,X) is
(−46.119203, +5.677239, +39.686376, +1.784012) mW, summing to Cu Joule.
Stage (Qc,Qh,IV,Qside) in mW is (64.078031,102.532144,38.454113,0),
(46.988353,58.400791,11.412438,0), (2,7.301978,3.517966,1.784012).
Thus `Qc1=Qh2+Qnetwork,T1`, `Qc2=Qh3+Qnetwork,T2`; the cold node accepts 2 mW.
Bath rejection is 56.412941 mW = load + module electrical work. Node, stage,
internal-cell and global residuals are below 1 nW; no heat is counted twice.

### Numerical limits and identifiability stop

| Maximum spacing (µm) | Active cells | Cold K | V (V) | Side heat (mW) |
| --- | ---: | ---: | ---: | ---: |
| 160 | 1,136 | 266.115439 | 0.544837898 | 1.654198 |
| 80 | 2,238 | 266.164844 | 0.544484182 | 1.654651 |
| 40 | 11,051 | 266.206209 | 0.544129405 | 1.784012 |

Cold coarse-to-fine change is 0.090770 K and the eight sharp-path changes are
at most 1.504%; their narrow screen is quiet. **The P174 side port changes
7.277%, exceeding the registered 5% heat-path threshold.** The independent
`all_port_review.json` is the overall sensitivity decision; the initial
`diagnostic.json` sharp-cut flag excludes this port and is not an overall pass.
No numerical convergence or physical closure is claimed. No extra grid is run.

Observed archived contact means differ from ceramic means: plate-2/rib-186
+2.047159 K, plate-3/rib-188 +1.486589 K, hot/support-192 −0.837715 K;
the buried 184/plate-2 interface itself ranges 284.430–287.240 K. These actual
nonisothermal interfaces invalidate a unique volume-mean-to-contact-temperature
mapping. They were read only after coefficient freeze, not fed into predictions.
Finite ceramic/pad spreading, the centroid side-port approximation, unretained
Cu and local P/N current/temperature structure remain confounded. No fitted
contact or observed heat flow is used to explain away the residual.

**One bounded next experiment:** a passive, constant-k local fixture retaining
the routes/supports **and four original ceramic plates plus adjacent Cu pads**.
Use six grouped hot/cold P/N attachment-footprint ports plus the P174 side patch,
one unit-temperature basis per port; compare reactions and plate mean-to-face
offsets with this isothermal closure. Proposed registration: one 80 µm maximum
spacing fixture, at most 60,000 active cells / 200,000 edges, 180 seconds for
build plus seven passive solves, 4 CPUs / 8 GiB; stop if exceeded. No P/N solid,
Peltier/Joule, whole-device rerun, target calibration or adaptive grid search.
That experiment is specified, not executed here. Native exchange remains later;
reuse G3b conservative source logic only, never its geometry/view-factor mapping.

Rev3 is unchanged: these conditional predictions and the failed side-port
sensitivity do not yet substantiate a physical causal reconciliation for the
professional master. All original 1% bath / 5% cold failures and historical
PDF/field bytes remain preserved.

### Evidence and reproduction

`data/nonlocal_solid_network_20261031` contains frozen operator JSON/NPZ, reduced
temperature arrays, post-freeze reference/contact/cut observations, the independent
all-port review and two figures (geometry/ports and temperatures/sharp powers).
`frozen_operators.json` stores the registration verbatim, input/source identities
and all three coefficient hashes before target access. `checksums.json` guards
the study outputs; the later review separately fingerprints its inputs/source.
The exact native field/cell mapping is inherited read-only from Milestone 1.
These saved local cell temperatures are reduced-fixture results, not new Elmer fields.

```bash
./fem/run.sh python -m tecooledmct.nonlocal_solid_study --out outputs/new-nonlocal-study
./fem/run.sh python -m tecooledmct.nonlocal_solid_review --data outputs/new-nonlocal-study
./fem/run.sh pytest -q tests/test_nonlocal_solid_network.py tests/test_solid_model_diagnostic.py tests/test_integrated_reference.py tests/test_engineering_report.py
```

Choose an absent output directory. Reproduction recomputes only the three small
geometry operators and fixed affine solves; no Elmer, Gmsh or optimization is invoked.
Focused/full regression, archive/master checks and legacy-demo results are recorded
in the accompanying verification record; numerical conservation is separate from
the unresolved discretization, physical closure and original release failures.
