"""Frozen-result projection and primary-source audit; contains no solver calls."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from .physical_input_qualification import ROOT, FACTORS, TOL, implicit
from .tec_material_plausibility import read, write, sha

LABELS=('Seebeck S','Resistivity rho','Conductivity k','Au effective G','Attach effective k')


def sources():
    specs=[
        ('Zhang2025','outputs/g2c-sources/zhang2025.pdf',
         '53dc665aea32e4eabb2c9d191af78ba458472054abded37461b6c0fe04f0ec3b',
         'https://cpl.iphy.ac.cn/en/article/pdf/preview/10.1088/0256-307X/42/5/056304.pdf',
         '10.1088/0256-307X/42/5/056304',
         'Title/abstract; sections 3/4; Figures 2/3; active v2r1 digitization panels and units',
         'Same-sample S/rho/k within each polarity; distinct N-HE-1 and P-HE specimens, not a matched cooler. Paper 10-300 K; ingested 40-300 K. Published measurement uncertainty is not model/digitization error.'),
        ('TEC2019','outputs/g2c-sources/oem2019.pdf',
         '1cc1075ed76a959b6a21cd24bde1704f72ab22529e77695a00e9b1af86a55492',
         'https://www.tec-microsystems.com/Download/Datasheets/Thermoelectric%20Coolers/MC04%20Series/3MC04-044-05_Datasheet_2019.pdf',None,
         'Pages 1-5: dimensional/performance tables, chart conditions, terminal options and extrema definitions',
         '3MC04-044-05; literal chart 27 C vacuum, higher-temperature dry N2 panels distinct. ACR 2.9 ohm is not DC R or thermoelectric V/I. Actual pellet grade/count/contact dimensions not given; not identified VIGO assembly.'),
        ('VIGO2024','outputs/full-presolder-source-review/vigo.pdf',
         '1f17637e02eb9ca0c340be6d936a485ae632ef7b12d9d7ea26e7664b42d6fc01',
         'https://vigophotonics.com/app/uploads/2024/07/3TE-TO669p-wW-PVI_PCI-detector-technical-drawing.pdf',None,
         'Page 1: ZTM-TO66-Z030 Rev9, 2024-03-01, external dimensions, materials and pinout',
         'Family drawing supports 31.5/17.5 mm flange, 0.76 mm pins and TEC1/9, detector7/8. No identification of independent candidate cooler, internal routes, seals or actual header alloy grade.'),
        ('Huber2019','outputs/g3b-sources/nist-gas-2019.pdf',
         'f8c8ac745e3aa73dd623c77a0f5a40373a3913eb3df7958cb26d82e00b2aedc4',
         'https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=926438',None,
         'Opening domain/units paragraph and N2/Ar/Kr rows at 200,300,400 K',
         'Thermal Conductivity of Gases, Marcia L. Huber. Table mW/(m K) converted by .001; N2/Ar/Kr low-pressure-limit rows. Typically <1% difference from 100 kPa; generally <3% source uncertainty, not rarefied-gap or convection qualification.')]
    records=[]
    for id,path,digest,url,doi,where,scope in specs:
        if sha(ROOT/path)!=digest:raise AssertionError('Cached primary bytes changed: '+id)
        records.append(dict(id=id,local_cache=path,sha256=digest,url=url,doi=doi,
                            inspected_locations=where,scope=scope,network_retrieval_this_milestone=False))
    return records


def project(out):
    out=Path(out)
    cases=read(out/'cases.json');targets=read(out/'targets.json');d=read(out/'derivatives.json')
    controls=read(out/'controls.json');cp=controls['current_partial']
    ref=cases[targets['nominal']['cold_side_case']];P=ref['audit']['terminal_W']
    result=[]
    for f,label in zip(FACTORS,LABELS):
        a=d[f]
        if a['status']!='PASS':
            result.append({'factor':f,'label':label,'status':a['status']});continue
        v=implicit(a['h005']['Tdie_K'],a['h005']['terminal_W'],cp['Tdie_K'],cp['terminal_W'],P)
        row=dict(factor=f,label=label,status='PASS',fixed_current_K_per_log_factor=a['h005']['Tdie_K'],**v)
        rminus,rplus=[targets[f'{f}_{s:+d}'] for s in (-1,1)]
        if rminus['status']==rplus['status']=='PASS':
            minus,plus=[cases[r['cold_side_case']] for r in (rminus,rplus)]
            actual=(plus['audit']['terminal_W']-minus['audit']['terminal_W'])/.02
            temp_error=sum(abs(200-r['audit']['Tdie_K']) for r in (minus,plus))
            propagation=abs(cp['terminal_W']/cp['Tdie_K'])*temp_error/.02
            tolerance=.02*max(abs(v['power_W_per_log_factor']),1e-4)+propagation
            discrepancy=abs(actual-v['power_W_per_log_factor'])
            row.update(actual_target_W_per_log_factor=actual,actual_target_elasticity=actual/P,
                actual_power_derivative_error_W_per_log_factor=discrepancy,
                actual_derivative_tolerance_W_per_log_factor=tolerance,
                target_temperature_propagation_W_per_log_factor=propagation,
                chain_rule_agrees=bool(discrepancy<=tolerance),
                signal_resolution='RESOLVED' if abs(plus['audit']['terminal_W']-minus['audit']['terminal_W'])>
                    10*abs(cp['terminal_W']/cp['Tdie_K'])*2*TOL else 'RESOLUTION LIMITED',
                target_minus_case=minus['case']['id'],target_plus_case=plus['case']['id'])
            if not row['chain_rule_agrees']:row['status']='FAIL: local derivative/target comparison'
        else:row['status']='STOP: actual target pair incomplete'
        budgets=[.01]
        if row['fixed_current_K_per_log_factor']!=0:budgets.append(1/abs(row['fixed_current_K_per_log_factor']))
        if v['power_elasticity']!=0:budgets.append(.05/abs(v['power_elasticity']))
        row['conditional_fractional_measurement_TARGET']=min(budgets)
        row['TARGET_scope']='At most verified 1%; fixed geometry/other factors. Not a measured tolerance or statistical CI.'
        result.append(row)
    summary={'nominal_target_case':ref['case']['id'],'nominal_target':ref['audit'],
        'nominal_current_A':ref['case']['current_A'],'sensitivities':result,
        'all_actual_target_chain_rules_pass':all(r['status']=='PASS' for r in result),
        'planning_budgets':{'fixed_current_temperature_K':1.,'target_power_fraction':.05,
                            'maximum_local_fraction':.01},
        'physical_validation':False,'native_gas_nonlocal_contact_matched_target_sensitivity':'NOT RUN',
        'next_affine_gas_control':'proposed only; NOT RUN; cannot qualify original field'}
    by={r['factor']:r for r in result}
    summary['gauge_derived_common_A_over_L_partial']={
        'fixed_current_K_per_log_g':by[FACTORS[2]]['fixed_current_K_per_log_factor']-by[FACTORS[1]]['fixed_current_K_per_log_factor'],
        'target_power_elasticity':by[FACTORS[2]]['power_elasticity']-by[FACTORS[1]]['power_elasticity'],
        'definition':'Analytic tangent only: d/dln(g) = d/dln(k scale) - d/dln(rho scale). No geometry scenario executed; no pad compatibility claim.'}
    write(out/'evidence_analysis.json',summary);write(out/'source_audit.json',sources())
    fig,ax=plt.subplots(1,2,figsize=(10,4.4),layout='constrained')
    y=np.arange(len(result))
    ax[0].barh(y,[r['fixed_current_K_per_log_factor']*.01 for r in result],color='#365f85')
    ax[0].set(xlabel='Local die shift for +1% input (K)\nFixed current; other inputs fixed',yticks=y,yticklabels=LABELS)
    ax[1].barh(y,[r['power_elasticity'] for r in result],color='#815c31',alpha=.7,label='Implicit derivative')
    ax[1].plot([r.get('actual_target_elasticity',np.nan) for r in result],y,'ko',ms=4,label='Actual ±1% target pair')
    ax[1].set(xlabel='Target power change for +1% input (%)\nTdie = 200 K; current changes',yticks=y,yticklabels=[])
    for a in ax:
        a.axvline(0,color='black',lw=.6);a.grid(axis='x',alpha=.2);a.invert_yaxis()
    ax[1].legend(fontsize=8)
    fig.suptitle('Conditional reduced sensitivity: 300 K ambient, 2 K/W sink, 2 mW die\nOriginal geometry / wires ON / exchange OFF; assumed >300 K continuation',fontsize=10)
    fig.savefig(out/'conditional_sensitivity.png',dpi=220);plt.close(fig)
    print(summary['all_actual_target_chain_rules_pass'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    project(p.parse_args().out)
