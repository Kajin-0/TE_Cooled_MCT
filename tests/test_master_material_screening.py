"""Report-only extraction, observable definitions and rejection gaps."""
import json
import numpy as np
import matplotlib.pyplot as plt

from reports.master.material_screening import evidence,generate
from reports.master.history import ROOT,sha,verify_historical


def test_frozen_screening_report_keeps_domain_and_no_run_contract():
    d=evidence();s=d['summary'];a=d['analysis']
    assert (s['cases'],s['accepted'],s['rejected'],s['not_run'])==(181,141,40,0)
    assert a['source_domain_counts']=={'accepted_nonlinear':130,'measured_domain_only':56,'assumed_continuation':74}
    assert all(d['summary']['targets'][h+'_wires_ON']['minimum_accepted_sample']['all_legs_within_measured_domain'] for h in ('nominal','higher'))
    assert s['targets']['lower_wires_ON']['minimum_accepted_sample']['assumed_continuation_used']
    for name,digest in d['registration']['input_sha256'].items():
        assert sha(ROOT/name)==digest
    assert verify_historical()


def test_report_projection_preserves_failures_and_terminal_module_distinction(tmp_path):
    panels={}
    def capture(fig,name):
        panels[name]=[[(line.get_label(),line.get_xdata().copy(),line.get_ydata().copy())
                      for line in ax.lines] for ax in fig.axes]
        plt.close(fig)
    generate(tmp_path,capture)
    d=evidence();c=d['summary']['targets']['nominal_wires_ON']['minimum_accepted_sample']
    tex=(tmp_path/'screening_numerics.tex').read_text()
    assert f"\\newcommand{{\\ScreenVoltage}}{{{c['terminal_voltage_V']:.6f}}}" in tex
    assert c['terminal_voltage_V']!=c['module_voltage_V']
    assert f"{c['Qc_cold_W']*1000:.6f}" in tex and c['Qc_cold_W']>.002
    line=next(row for row in panels['material_operating_grid'][0] if row[0]=='Nominal / OFF')
    for current in (.5,.6,.8):assert np.isnan(line[2][list(line[1]).index(current)])
    assert np.isfinite(line[2][-1])  # Disconnected warm branch retained.
    volts=next(row for row in panels['material_operating_grid'][1] if row[0]=='Nominal / ON')
    assert volts[2][list(volts[1]).index(.4)]==c['module_voltage_V']
    # Manufacturer table must use module-only zero-load 0.2 A, not package Tdie.
    for r in d['oem_comparison']['rows']:
        if (r['hypothesis']=='nominal' and r['current_A']==.2 and r['Qc_W']==0
                and r['status']=='CONDITIONAL BOUNDARY-MATCHED PLAUSIBILITY'):
            assert f"{r['source_value']:.6f}" in tex and f"{r['signed_difference']:+.6f}" in tex
    record=json.loads((tmp_path/'material_screening.json').read_text())
    assert record['new_physics_runs']==0 and record['no_parameter_fit']
    assert record['actual_device_feasibility']=='unresolved'


def test_prior_28_page_report_is_explicit_historical_evidence():
    p=ROOT/'reports/historical/rev3_pre_material_20261101'
    d=json.loads((p/'historical_identity.json').read_text())
    assert d['pages']==28 and 'HISTORICAL' in d['kind']
    assert d['prior_source_commit']=='6098ce1986e2e4a9d9536488e57c2aca2d14c864'
    assert 'source_snapshot/reports/master/report.tex.source' in d['snapshot_sha256']
