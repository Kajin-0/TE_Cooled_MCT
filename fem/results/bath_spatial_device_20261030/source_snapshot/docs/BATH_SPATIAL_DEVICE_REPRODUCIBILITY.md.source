# Reproduce the bounded coupled spatial-refinement pair

The approved Rev3 PDF and earlier evidence are immutable. Work only here using
the existing pinned4CPU/12GiB `fem/run_g2b.sh`; no install or other session/repo.
The diagnosis archive contains both exact geometry candidates, source snapshots,
independent archived-field audits and manufactured HeatSolver evidence. Verify
with `fem/archive_bath_spatial_diagnosis.py --verify` before reproducing physics.

New geometry follows `data/bath_spatial/refinement_plan.json`: all-bath full
owner-star subdivision, then the fixed8.75mm central-header owner mask. The
resulting784696/1099293-tet meshes retain every cold/TEC/pin cell, source package
volume and contact/exterior area. The geometric construction itself is not a
coupled solution or a qualified model.

Restore geometry from its diagnosis archive into NEW outputs directories with
`fem/restore_cold20.py`; restoration is archival input copying, never a PDE run.
Use `cold20_projection.build` from the genuine archived675496-tet bath case,
then `cold20_refined_lu.run(mesh,new_case,projection=new_transfer,timeout=3000)`.
Both frozen routines are unchanged. Each case has0.1A,2mW volumetric MCT source,
Cu/Au OFF,300K actual Kovar underside only and original stopping/check limits.
Every field requires its own genuine coupled Peltier/Joule/Fourier execution.

Independently audit a completed case with:

```
./fem/run_g2b.sh python -m tecooledmct.bath_spatial_device \
 --mesh outputs/bath-spatial/transverse1_mesh \
 --case outputs/bath-spatial/transverse1_case \
 --out outputs/bath-spatial/NEW_transverse1_audit
```

The auditor first runs the original independent current/cold-contact/bath/heat
checks. It then maps native nodes/tetrahedra and independently reconstructs raw
signed bath flux, bath-node support identity and fixed geometric partitions.
The identity and reaction comparisons are diagnostics, not local true flux or
recovered qualification. The original raw1% remains failed in both cases.

`bath_spatial_modes.py` computes a clearly labeled geometry-only analytic-nodal
P1 interpolant and retained-volume inventory. It never writes a fabricated
device VTU. `bath_spatial_results.py` collects only completed, independently
audited fields and produces the final actual-field maps and plateau comparison.
No combined solve is permitted by these actual failed bath results.

After tests/CLI/demo, `fem/archive_bath_spatial_device.py` seals sources, native
and derived fields, original Elmer inputs, backend/timed source, binary libraries,
initial guesses, audits and the failed raw status. `--verify` checks every source
and artifact plus the entire preceding evidence/report guard chain. Geometry is
referenced by exact hash from the diagnosis archive, rather than regenerated.

Large compressed derived fields are losslessly split into48MiB compressed-byte
parts only when necessary for repository file limits. They are NOT quantized,
downsampled or changed numerically. A manifest records part and concatenated-gzip
hashes; native uncompressed hashes are retained. Restore exact bytes with:

```
python3 fem/restore_bath_spatial.py \
 --case fem/results/bath_spatial_device_20261030/cases/transverse2 \
 --name derived.vtu --out outputs/NEW_spatial_restore/derived.vtu
```

The destination must be a new file under outputs. Restoration checks all parts,
gzip data and exact uncompressed digest, and does not claim a new solver run.
Tests exercise corrupt-part rejection, overwrite refusal and real native/derived
field round trips. During full local tests, `--ignore=outputs` excludes transient
run/cache directories from collection while retaining the complete source suite.
This avoids the already documented temporary-directory collection race.

No new report is generated for this failed pair. Approved Rev3 stays unchanged;
the main technical checkpoint supplies the new matrix, plots and next experiment.
