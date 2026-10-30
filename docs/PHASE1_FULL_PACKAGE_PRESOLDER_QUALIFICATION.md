# Full-package presolder and bath-flux checkpoint

**Scoped numerical evidence only. General bath-flux recovery and physical device
qualification are NOT PASSED.** The completed full88-leg runs below use the
previous assumed package geometry. They do not use the new VIGO source geometry.
At the user-directed safe checkpoint, further old-geometry presolder campaigns
stopped and the independent [source geometry rebaseline](GEOMETRY_SOURCE_REBASELINE_20261030.md)
was committed first. No previous result or15-page report has been rewritten.

## Genuine coupled sandbox executions

All four new executions use actual Elmer26.2.1 ThermoElectricSolver, with solved
3D temperature/potential in the88-leg stack and passive package. The bath is
300 K on the external header underside, I=0.1 A, detector bias1.5 mW plus
parametric absorbed optical heat0.5 mW, N2 at100 Pa, existing gray radiosity and
hybrid Au/Cu exchange. No TEC internal temperature is prescribed. All original
per-case current/work/stage/energy checks pass, including175 interior cuts.
This does not override the additional failures below.

| New case | Nodes / tets | Die K | Cold ceramic K | TEC V | Raw bath error |
|---|---:|---:|---:|---:|---:|
| Same-physics old k2 control |109771 /429100|268.806887687|268.395968725|0.537982492|+0.420150%|
|50 µm explicit presolder, k35, zero added contact|109771 /429100|268.762810818|268.351631966|0.537757218|+0.425606%|
|46 µm presolder plus two2 µm contact films|119613 /483866|268.771520683|268.360393116|0.537808997|+0.421964%|
|Matched old fine mesh, Cu thermal links off|204855 /821874|266.078136247|265.635983842|0.554844426|−0.360846%|

The new control reproduces the archived907-patch case within0.000000368 K in
die mean and4.57 nV in voltage. Replacing the old joint law lowers die mean by
0.044077 K; the contact hypothesis raises it0.008710 K relative to zero contact.
These are sandbox sensitivities, not predictions for manufactured solder.
Cold temperatures do not approach an independent OEM validation claim.

The new versioned geometry replaces the existing resolved50 µm joint envelope
with a separately named Presolder material domain191; old Mount material and
old sources are preserved. The contact case divides the same envelope into
46 µm/k35 bulk,2 µm/k1 lower film (R''=2e−6 m²K/W), and2 µm/k(2/3) upper film
(R''=3e−6). No geometric thickness or cavity volume is added. Body216/217 are
distinct films. Complete shared-face and exterior-skin checks prove conformity,
volume/contact agreement, body connectivity,181-vertex/180-edge conductor path
and separation of joint from P/N/Cu. No solder electrical short is created.

The alloy, wetting and measured k(T) are unknown. k35 is a frozen hypothesis with
a fail-closed290..320 K numerical interval, **not** a traceable measured trajectory.
The work-order k10..80 W/m/K,t20..100 µm,R''0..1e−5 ranges remain unrun full-device
sensitivities. Passive package sigma1e−12 S/m and S=0 are numerical thermal-solid
extensions, not metallic electrical transport. Side-patch optical coating retains
the old emissivity assumption. Actual wetting voids and partial-area shorts are
not simulated. No metallurgical qualification is claimed.

An independent raw affine-gradient interface audit adds a5% diagnostic without
changing any prior gate. Zero-contact Kovar/presolder mismatch is **5.73220%:
FAILED** (upper interface0.57988%). All four contact-case interfaces are below
5%, maximum2.84385%. Area-mean contact-case temperature drops are0.00403913 K
(lower film),0.00265461 K (bulk),0.00606018 K (upper film). Shared nodal temperature
does not prove raw interface flux accuracy. A second mid-joint-refined mesh
(114694 nodes/455544 tets) was generated and audited but **not solved** after the
geometry-priority instruction. Two-resolution presolder physics is not qualified.

For the contact case the actual conservative stage-control-volume budgets are:

| Band | Hot out W | Cold out downward W | Electrical work W | Other net source W | Residual W |
|---|---:|---:|---:|---:|---:|
|0|0.055866773|0.039526082|0.038324602|−0.021983911|−6.81e−10|
|1|0.039526082|0.024499024|0.011996487|0.003030571|−1.79e−11|
|2|0.024499024|0|0.003459811|0.021039213|4.58e−10|

These are P1 control-volume transfers through plates/routing, not independently
resolved sharp-interface heat fluxes. Actual raw bath output is0.056102510 W
against external input0.055866773 W. The worst driven cut error is0.24893%.
Full per-band source components, lead endpoint powers, actual raw T/phi fields,
source snapshots and solver/resource logs are archived for reproduction.

## Independent3D bath-flux recovery: NOT QUALIFIED

The new recovery solves a full-mass RT0 H(div) constrained least-squares problem
against raw P1 q. Shared face powers enforce normal continuity and each cell's
divergence balance. No FE weak reaction is input. Consequently its integrated
global balance is **enforced, not an independent validation check**. Independent
analytic fields and separately assembled conforming P2 references test accuracy.

Six genuine Elmer HeatSolver runs cover a nonuniform rotated three-material
box with transverse flow and a rotated32-sided chordal glass/pin junction.
Each has three refinement levels; source/flux/material jumps, actual meshes,
P2 solutions and recovered face fields are retained. Fixed chordal geometry
isolates field discretization from true-circle geometry error.

Predeclared targets remain boundary face-mean L2<5%, integrated bath<1%,
reference Cauchy<1%, local balance<1e−9 W. Finest results:

| Benchmark | Raw / recovered boundary L2 | Recovered bath error | Independent reference | Decision |
|---|---:|---:|---|---|
|Oblique,10368 tets|5.62356 /3.08901%|**−1.08018%**|P2 manufactured nodal error8.36e−12 K|**FAIL bath1%**|
|Curved chordal,30720 tets|15.33879 /4.37114%|+0.0006244%|**P2 bottom Cauchy7.24799%**|**FAIL reference1%**|

Maximum cell residuals are1.76e−17 and5.34e−18 W. Oblique volume flux error
decreases18.1169→9.19146→4.61361%; this is convergence, not a pass at the finest
available resolution. The curved P2 reference remains insufficiently resolved
despite a small integrated bottom error. A40,000-tet bounded recovery/reference
cap prevents an unaudited full429k–1.2M-tet application. **No full-device recovered
bath result is published or substituted for the raw gate.**

Earlier development evidence remains explicitly unaccepted: an Elmer keyword
failure and a zero-net-bath analytic choice with meaningless relative bath
normalization. The final nonzero-bath manufactured case supersedes neither raw
logs nor the need to report these failures.

## Geometry/lead findings and unchanged failed gate

The [independent discrepancy audit](GEOMETRY_PINOUT_LEAD_DISCREPANCY_AUDIT_20261030.md)
confirms that the old supply return heats a mid-stack endpoint. Actual907-patch
raw temperatures give17.714395 mW net Cu conduction into TEC endpoints. A new
matched fine-mesh lead-off run lowers die mean **2.720565 K** relative to the old
lead-on result. This identifies an influential assumed path; it does not prove
a corrected hot-side routing or actual device parasitic load.

Original fine raw bath failures remain **1.655872526%,1.514121595%,1.583834511%**.
The passing new coarse cases and fine lead-off case are different hypotheses;
they cannot retroactively accept those executions. Full numerical qualification,
corrected geometry physics and OEM/device validation remain incomplete.

The unchanged15-page PDF SHA256 is
751284cabaffa34f7f338f85ffa05cd88c59e157831f3dc9f1837d7758f3ac1c.
The protected G1–G3b and previous flux/presolder checkpoint ledgers pass.
No LSDDTS or other repository was accessed or changed.
