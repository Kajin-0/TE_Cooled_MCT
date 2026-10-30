"""Reproducible transport accuracy/cost evidence, without OEM fitting."""
import argparse
import json
from pathlib import Path
import time

from . import graded_tec
from .graded_tec_checks import POINTS
from .integrated_reference import geometry,Scenario,solve,OperatingPointFailure
from .nonlinear_tec import Transport
from .oem_phase_a import bounded_leg


class ActiveProfile:
    interval=(180.,390.)
    def properties(self,polarity,t):
        return graded_tec.props(polarity,t)


def compare():
    g=geometry();rows=[]
    points=(*POINTS,(0,230.,210.,.9),(1,260.,235.,.7),
            (0,330.,260.,.2),(2,380.,350.,.2))
    for i,hot,cold,current in points:
        geom=g['stages'][i];a=geom['leg_area_m2'];n=geom['couples']
        measured=max(hot,cold)<300
        profile=graded_tec.source() if measured else ActiveProfile()
        start=time.perf_counter()
        try:
            reference={pol:bounded_leg(profile,pol,hot,cold,current/a*(1 if pol=='N' else -1),
                geom['leg_length_m'],intervals=64) for pol in ('P','N')}
        except ValueError as error:
            rows.append({'stage_index':i,'hot_k':hot,'cold_k':cold,'current_a':current,
                         'status':'REFERENCE FAILED CLOSED','reason':str(error)})
            continue
        reference_seconds=time.perf_counter()-start
        ref={'qc_w':-n*a*sum(v['q_cold_w_m2'] for v in reference.values()),
             'voltage_v':n*(reference['N']['electric_integral_v']-reference['P']['electric_integral_v'])}
        if measured and not all(40<v['min_k']<=v['max_k']<300 for v in reference.values()):
            raise ValueError('Measured comparison left strict source interior')
        levels=[]
        for intervals in (16,32,64):
            tr=Transport(intervals);start=time.perf_counter()
            result=tr.stage(geom,hot,cold,current)
            errors={key:{'absolute':abs(result[key]-ref[key]),
                         'relative_abs':abs((result[key]-ref[key])/ref[key]) if ref[key]!=0 else None}
                    for key in ref}
            levels.append({'intervals':intervals,'result':result,'errors_against_reference64':errors,
                           'seconds':time.perf_counter()-start})
        affine=graded_tec.stage(geom,hot,cold,current)
        rows.append({'stage_index':i,'hot_k':hot,'cold_k':cold,'current_a':current,
            'comparison_scope':'measured-domain numerical check' if measured else 'assumed continuation cross-implementation check ONLY',
            'reference64':ref,'reference_seconds':reference_seconds,'newton_levels':levels,
            'affine_errors':{key:abs(affine[key]-ref[key]) for key in ref}})
    return {'scope':'Independent numerical comparison, no experimental/OEM validation',
            'source':graded_tec.source_evidence(),'rows':rows}


def package_convergence():
    rows=[]
    for current in (.15,.4,.9):
        for intervals in (16,32,64):
            start=time.perf_counter()
            try:
                r=solve(Scenario(current_a=current,material_model='zhang2025_nonlinear'),
                        transport_intervals=intervals)
                rows.append({'current_a':current,'intervals':intervals,'seconds':time.perf_counter()-start,
                    'die_k':r['MCT_die_k'],'terminal_voltage_v':r['terminal_voltage_v'],
                    'max_node_balance_residual_w':r['max_node_balance_residual_w'],
                    'transport_computation':r['transport_computation']})
            except OperatingPointFailure as error:
                rows.append({'current_a':current,'intervals':intervals,'status':'FAILED CLOSED',
                             'reason':str(error),'diagnostics':error.diagnostics})
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    if args.out.exists():raise ValueError('Choose a new output directory')
    result=compare();result['package_convergence']=package_convergence()
    args.out.mkdir(parents=True)
    (args.out/'comparison.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print('Comparison rows',len(result['rows']),'package points',len(result['package_convergence']))
