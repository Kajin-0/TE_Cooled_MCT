# Flux localization and explicit presolder — verified scoped checkpoint

**Neither full G3b nor a full-stack metallic-presolder device is qualified.**
The original1% raw bath-gradient gate is unchanged. All G1–G3b accepted/rejected
source, fields, checks and the15-page Revision2 PDF remain unchanged. Work uses
the existing pinned Elmer26.2.1 image,4CPUs and at most12GiB, without host installs,
other sessions/repositories, or LSDDTS work.

## Results actually obtained

- Independent archived-field reconstruction reproduces coarse0.42015% and failed
  fine1.65587%/1.51412%/1.58383% raw bath errors. Partitioned maps/CSV and exact
  discrete integration-by-parts checks expose broad Kovar, seal-adjacent and mount
  contributions, dominated by weighted internal P1 gradient jumps on fine meshes.
  See [bath qualification](PHASE1_BATH_FLUX_QUALIFICATION.md).
- Six genuine independent3D Elmer junction executions verify forward/reverse
  source-free conduction, manufactured source balance and raw axial convergence.
  Raw manufactured errors decrease4.167%→0.521%; coarse benchmark raw failures
  remain explicitly distinct from the experiment's analytic-verification PASS.
  Limited quadratic temperature recovery is not a device recovery method.
- Eight genuine isolated3D Elmer Kovar/interlayer/alumina coupons verify explicit
  material volumes, contact-resistance films, zero-contact and equal-material
  limits, thickness/proxy sensitivity and refinement. Actual fields, SIFs, solver
  logs, sources, mappings and independent analytic checks are retained.
- No new coupled88-leg package solve, original-gate correction, actual presolder
  chemistry identification, device calibration or reader-facing report change
  is claimed.

## Physical presolder and data provenance

The owner confirms presolder physically exists between Kovar and bottom Al2O3.
The old full-device50µm/k2W/(m K) mount remains unchanged and is not relabeled a
metal. New coupons explicitly mesh Kovar, an **unidentified metallic presolder
hypothesis**, and alumina. Coupon area is1mm², with full wetting and adiabatic
sides,300/310K end temperatures and no TEC conductors. HeatSolver verifies thermal
conduction only; no electrical-transport or full-device shorting claim is made.
Alumina is a separate resolved layer. Real package electrical isolation still
requires a new topology/current audit before integration.

New vendor reference values are35W/(m K),sigma9.5e6S/m for a95Sn5Sb example
([Array Solders](https://arraysolders.com/wp-content/uploads/2023/06/TDS-for-95sn5sb.pdf)),
and57W/(m K),rho160nΩm for anAuSn example
([Knowles](https://www.knowlescapacitors.com/Products/Thin-Film-and-Substrates/Build-To-Print/Pre-deposited-Solders)).
They are not identified package alloys. Transport reference temperatures are
not stated in these tables. Frozen coefficients over300..310K are explicit
numerical hypotheses, **not measured k(T)/rho(T)**. Electrical values are recorded
but not used by the thermal coupon. Original source bytes are retained locally;
curated facts, URLs and retrieval hashes are revision controlled.

These candidates do not establish process compatibility. Their240–250/284°C
melting references can exceed the inherited TEC internal solder reference near
230°C. Metallization, solder hierarchy, reflow, wetting, stress and manufacturer
process approval are unresolved. The vendor AuSn guidance describes metallized
pads, not direct wetting of bare alumina. No solder chemistry is recommended.
The different old Indalloy reference remains intact; new vendor values are not
silently substituted into earlier evidence.

Sensitivity bounds20–100µm,k10–80W/(m K),each R''0..1e-5m²K/W and wetted fraction
0.5..1 are unmeasured hypotheses. Nonzero contacts use separate2µm films with
k=tfilm/R'', conserving heat and reproducing finite series resistance. They
are not identified intermetallics or zero-thickness jump conditions. The
wetted-fraction table is analytical only and omits void geometry/spreading.

## Coupon verification, not device predictions

For full area A, `R=sum(t_i/(k_i*A))`, including contact-film contributions
`R''1/A+R''2/A`. End temperatures are prescribed only at the external coupon ends;
internal interface temperatures are solved and checked against analytic drops.

| Coupon | Analytic R (K/W), A1mm² |
|---|---:|
| 25µm,k35 | 71.631434 |
| 50µm,k35 | 72.345720 |
| Same50µm, twice all layer divisions | 72.345720 |
| 100µm,k35 | 73.774291 |
| 50µm,k57 AuSn example | 71.794341 |
| 50µm,k35,contact R''2e-6/3e-6 | 77.345720 |
| All materials k17.3 continuum regression | 79.190751 |
| Old50µm/k2 mount control | 95.917148 |

Integrated raw flux agrees with analytic series power within2.4e-13 relative;
interface temperatures, free residual and reaction balance are independently
checked. The50µm layer has2 elements through thickness, doubled to4 in the
refinement case (other layers doubled too). This exact1D-like limit does not
establish convergence of realistic lateral spreading or partially wetted joints.
At the real6.4mm-square footprint, the isolated layer resistance would change
from0.61035K/W (oldk2) to0.03488K/W (50µm/k35), before contact/spreading. **No device
temperature shift follows from this conditional1D calculation.**

The8-case coupon driver completed in2.005s, with child-process high-water RSS
122,392KiB and container charged-memory high-water93,171,712bytes. These are
separate Linux accounting measures, not interchangeable per-solver RSS. Junction
RSS was not measured; its hard container cap and per-solver wall times are kept.
All coupon solvers are bounded at120s,100,000nodes/300,000tets; the final junction
uses12,545nodes/61,440tets. Earlier rejected development meshes remain retained.

## Remaining qualification gaps

1. Resolve the independent raw device bath-flux error; implement and independently
   qualify general equilibrated recovery if pursued, retaining the original gate.
2. Benchmark true3D curved/protruding-junction transverse flow and nonuniform
   boundary-normal device refinement; the axial benchmark does not cover it.
3. Identify actual alloy, metallization, thickness, contacts, wetting/voids and
   temperature-dependent transport before physical presolder/device claims.
4. Integrate the explicit layer in a new coupled88-leg case at300K/.1A/2mW and
   reverify all175current cuts, energy, bath flux, mesh sensitivity and geometry.
5. Keep the original report unchanged until such device physics is qualified.

The machine archive and reproduction notes give exact execution counts, failed
attempts, test result, hashes and commands. Only14 completed coupon executions
are classified as the scoped benchmark/coupon evidence;5 earlier genuine driver
executions remain development evidence, and a cap rejection involved no new PDE.
Full opt-in regression solvers are additional tests, not new device predictions.

## Regression and publication

`./fem/run.sh env TE_FEM_SMOKE=1 pytest -q` passes **99 tests with no skips**
(254.45s). These include genuine baseline Elmer/Gmsh regressions and the new
isolated3D layered Elmer smoke. Existing CLI quick and geometry-demo checks pass.
A separate audit reopens actual VTUs, verifies actual tetrahedron/body IDs,
recomputes raw bath flux and manufactured fields, and rejects stale source/SIF/
mesh/field hashes before publishing the additive checkpoint. Failed development
fields/statuses and original1% fine failures remain explicit. No old proof is
rewritten and no full-device pass is claimed.
