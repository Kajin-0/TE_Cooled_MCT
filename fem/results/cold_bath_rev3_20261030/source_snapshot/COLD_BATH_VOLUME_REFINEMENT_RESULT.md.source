# Independent cold-contact and bath-volume refinement

This is a scoped numerical investigation of the unchanged corrected216-domain,
88-leg solid-only model. The VIGO source housing plus independent TEC reference
is an unverified synthetic composite. No OEM validation or enclosure physics is
added. All old failures and the old15-page PDF remain unchanged.

## Fixed physics and independent region locks

All cases retain0.1A,2mW uniform MCT heat (1.5mW bias-like plus0.5mW imposed
optical-like),300K Kovar underside only, Cu/Au OFF, identical bulk material laws
and the original raw5% cold/raw1% bath limits. The normal-edge algorithm bisects
complete incident tetrahedral/physical-face stars. It adds free normal-direction
nodes while retaining each target interface triangle exactly. Original points
and material volumes are unchanged. Actual material adjacency,216 solids,
88leg series connectivity, terminal locations, exterior faces and Elmer mapping
are audited after each refinement.

The independent cold track changes only domains4/302/303, retaining every bath,
pin, glass and TEC-conductor cell byte-for-byte. The independent bath tracks
change only Kovar domain300, retaining all cold/TEC cells byte-for-byte.
The actual face-owner normal height, not merely surface triangle count, measures
refinement. No weak reaction or recovered flux substitutes for a raw gate.

## Actually completed cases

| Case | Tets | Die mean K | Module V | Ceramic/attach raw | Attach/MCT raw | Bath raw |
|---|---:|---:|---:|---:|---:|---:|
| Archived fine baseline |647657|265.616093085|0.551926633|+6.476539% FAIL|-4.608512% PASS|-1.496257% FAIL|
| Cold normal1 |821078|265.616118028|0.551926634|+4.795425% PASS|-2.305670% PASS|-1.496257% FAIL|
| Bath normal1 |744713|265.616580391|0.551930113|+6.476541% FAIL|-4.608512% PASS|-1.068632% FAIL|
| Bath normal2 |821458|265.616592661|0.551930210|+6.476541% FAIL|-4.608512% PASS|-1.092875% FAIL|

Cold normal1 genuinely completed in1269.532s,2 nonlinear iterations, last change
4.2283e-11 and8626872KiB peak RSS. It passes177 current cuts and all nonraw
energy/free-residual gates. Its Tc shift is+24.943 microkelvin and voltage shift
+0.583nanovolt relative to the archived fine replay. Passing cold5% is
independent of the remaining bath failure; the preferred4.5% cold margin is
not met and is not treated as a replacement gate.

Bath normal1 genuinely completed in1221.444s,4 nonlinear iterations, last
change2.1718e-11 and5553288KiB RSS. It passes all nonraw conservation/current
checks. Median bath-owner height falls from295.961 to147.981 micrometers
relative to its actual archived parent; cold interface owner heights and every
cold cell remain identical. Relative to that parent, Tc changes+66.476
microkelvin and voltage+0.534451microvolt. Raw1% remains FAILED.

A second strict bath-normal halving is preregistered and bounded to2400s and
less than1million tetrahedra. Its geometry passes at821458tets, minimum
SICN0.026579 and only Kovar cells changed. The real coupled solve completed in903.693s,3 nonlinear iterations, last
change2.68175e-10 and5707624KiB peak RSS. All177 cuts and every nonraw
heat/current check pass. Median bath-owner normal height halves again to
73.990micrometers; every cold/TEC cell remains exactly fixed. Tc shifts
+12.270microkelvin and voltage+0.096409microvolt from the preceding level.

The raw bath error WORSENS from1.068632% to1.092875% despite exact normal
refinement. This is nonmonotone local sensitivity, not demonstrated raw-flux
convergence and not an extrapolation/GCI. Further transverse/volume resolution
and signed spatial cancellation need controlled investigation; normal depth alone
has not qualified the boundary integral. A combined solve was NOT RUN because
the preregistered independent bath1% condition remains unmet. No separate-mesh
pass is substituted for a combined case.

## Release status

Full numerical release is NOT achieved by separate passing meshes. Both original
raw thresholds must pass on the same production mesh AND at least one
systematically refined comparator, with all177cuts, global/stage/free thermal
residuals below1microW, free current below1microA, nonlinear below1e-9,
homogeneous/reproducibility checks and quantified Tc/V sensitivity. No qualified
whole-device GCI or OEM assembly validation is inferred.

The new13-page Rev3 review draft is already published independently of these
remaining gates. Its initial immutable edition explicitly freezes the earlier
solved-field evidence and marks these new runs pending. The updated review supplement is rebuilt only from this immutable numerical
archive, with its own source/figure/PDF ledger and honest nonmonotone failed bath
results. The initial review edition remains unchanged.
