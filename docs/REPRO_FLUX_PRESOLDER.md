# Reproduce scoped flux/presolder evidence

Use the existing project and pinned4CPU/12GiB runtime. No installs are needed.
Do not overwrite existing raw directories or published archives. Code below
reads the immutable G3b archive and writes only new outputs. Exact ledger/source
versions are authoritative; no solver reuse is counted as a new execution.

```bash
./fem/run_g2b.sh python -m tecooledmct.flux_presolder_diagnosis \
  --out outputs/flux-presolder-diagnosis-v3
./fem/run_g2b.sh python -m tecooledmct.flux_presolder_coupon junction \
  --out outputs/flux-presolder-junction-v3
./fem/run_g2b.sh python fem/run_flux_presolder_scoped.py presolder \
  --out outputs/flux-presolder-metal-coupons
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q \
  > outputs/flux-presolder-full-tests.log 2>&1
./fem/run.sh python -m tecooledmct.cli --quick \
  --out outputs/flux-presolder-quick > outputs/flux-presolder-cli.log 2>&1
./fem/run.sh python -m tecooledmct.geometry_demo \
  --out outputs/flux-presolder-geometry > outputs/flux-presolder-geometry.log 2>&1
./fem/run_g2b.sh python fem/archive_flux_presolder_checkpoint.py
```

For fresh reproduction on this checkout, select unused `--out` names and pass
them to the publisher's `--diagnosis`, `--junction` and `--presolder` arguments,
or re-audit existing raw runs without executing any PDE. The publisher's default is a
one-time additive `fem/results/flux_presolder_checkpoint_20261030` checkpoint;
`--out outputs/flux-presolder-audited-copy` publishes an independent audited copy
from completed raw runs, not additional PDEs. It refuses an existing destination.
It requires all14 coupon verifications, exact actual-field/mesh/material mapping,
SIF/VTU/source hashes and completed full opt-in tests with no skips. It validates
manufactured T, expected raw truncation error and independent archived raw flux.

Archive cases contain compressed actual VTUs with uncompressed hashes, mesh NPZ,
SIFs, source snapshots, ElmerGrid/solver logs and statuses, analytic checks,
interface temperatures and pass scopes. Diagnostics include physical-region
power CSVs, normalized signed differences, actual bath-face arrays/maps and
discrete residual identities. Charts distinguish the original raw gate from
benchmark-only recovery, and full-wetted FEM cases from analytical wetting screens.
Material facts/URLs/retrieval hashes are in `data/flux_presolder`; original vendor
bytes were downloaded to ignored `outputs/flux-presolder-source-downloads`.

Earlier development attempts are retained: the original VTU was correctly
written under the Elmer mesh directory, but the first driver searched its parent;
that postprocessing failed after1 real solve. The next automatic circular mesh
completed4 cases then reached the unchanged300,000-tet cap before refinement.
Their solver fields/logs/source versions are development evidence, never device
acceptance. The final deterministic64-sided ring mesh avoids that cap. No
existing failed directory was removed or overwritten.

Validate all tracked checkpoint data without physics:

```bash
./fem/run.sh python - <<'PY'
from pathlib import Path
import gzip,hashlib,json
from tecooledmct.g2d_data import ROOT,sha
from tecooledmct.flux_presolder_common import guard
p=ROOT/'fem/results/flux_presolder_checkpoint_20261030'
ledger=json.loads((p/'checksums.json').read_text())
for name,digest in ledger['source_sha256'].items():assert sha(ROOT/name)==digest,name
for name,digest in ledger['artifact_sha256'].items():assert sha(p/name)==digest,name
for record in p.glob('cases/*/*/field_provenance.json'):
    r=json.loads(record.read_text())
    with gzip.open(record.parent/'fields.vtu.gz','rb') as f:
        h=hashlib.sha256()
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    assert h.hexdigest()==r['uncompressed_sha256']
guard()
print('Scoped evidence, old G1-G3b chain and Revision2 report verified; full device still unqualified')
PY
```

No change to the full-device1% gate, solver, mount, source registry or standalone
report is part of this checkpoint. Future integration requires new versioned
geometry/physics/evidence; do not edit protected earlier modules to force a pass.
