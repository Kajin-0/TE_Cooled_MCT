#!/usr/bin/env python3
"""Seal this screen's report, source, tests and results; never mutate source evidence."""
from pathlib import Path
from hashlib import sha256
import json, datetime
root = Path(__file__).resolve().parents[1]
base = root / 'data/tec_pellet_screen_20261110'
def digest(p):
    h = sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''): h.update(chunk)
    return h.hexdigest()
reg = json.loads((base / 'registration.json').read_text())
seal = json.loads((base / 'source_seal.json').read_text())
for name, expected in reg['source_sha256'].items():
    assert digest(root / name) == expected, f'Changed prior source: {name}'
for name, expected in seal['sources_sha256'].items():
    assert digest(root / name) == expected, f'Changed executed source: {name}'
assert digest(base/'registration.json') == seal['registration_sha256']
summary = json.loads((base/'summary.json').read_text())
assert (summary['accepted_case_count'],summary['independently_audited_count'],summary['accepted_states'],summary['full_system_solves']) == (5,5,10,0)
visual = json.loads((base/'report_visual_reproducibility.json').read_text())
assert visual['all_page_contact_sheets_inspected'] and visual['new_section_pages_33_34_inspected_individually']
assert visual['independent_build_pdfs_identical'] and visual['rendered_pages_identical']
paths = [p for p in base.rglob('*') if p.is_file() and p.name != 'manifest.json']
paths += [root / p for p in [
    'scripts/tec_pellet_transport_screen_20261110.py',
    'scripts/tec_pellet_independent_audit_20261110.py',
    'scripts/tec_pellet_screen_report_20261110.py',
    'scripts/tec_pellet_report_build_20261110.py',
    'scripts/tec_pellet_manifest_20261110.py',
    'tests/test_tec_pellet_screen_20261110.py',
    'docs/TEC_PELLET_TRANSPORT_SCREEN_20261110.md',
    'reports/current/reader_first_pellet_20261110.tex',
    'reports/current/v317_pellet_transport_section.tex',
    'reports/current/figures/v317_pellet_fixed_boundary.pdf',
    'reports/current/figures/v317_pellet_fixed_boundary.png',
    'reports/current/figures/v317_pellet_stage_budgets.pdf',
    'reports/current/figures/v317_pellet_stage_budgets.png',
    'reports/current/TEC_TO_Reader_First_Assessment_20261110_V317.pdf',
]]
manifest = {'observed_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'scope':'88-leg fixed-boundary transport only; no new package or temperature solution',
 'accepted_cases':5,'independent_audits':5,'fixed_and_matched_power_states':10,
 'full_system_solves':0,'geometry_variants_qualified':0,
 'source_sha256':reg['source_sha256'], 'files_sha256':{str(p.relative_to(root)):digest(p) for p in sorted(paths)},
 'report_pages':44,'report_visual_and_reproducibility':'PASS; see report_visual_reproducibility.json',
 'historical_failures':'unchanged; not reclassified or retested as passing'}
out=base/'manifest.json';out.write_text(json.dumps(manifest,indent=2)+'\n')
print(f'PASS prior source seals and {len(paths)} current artifact hashes: {out.relative_to(root)}')
