"""Independent bounded 1D checks of the affine analog, not experimental validation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .graded_tec import source, source_evidence, stage
from .integrated_reference import geometry
from .oem_phase_a import bounded_leg

# Every boundary and accepted BVP interior must lie STRICTLY inside 40..300 K.
# Stage indices are hot-to-cold. Include back-conduction, cooling, and large I.
POINTS=((0,295.,250.,.1), (0,295.,285.,.15), (1,280.,250.,.15),
        (2,250.,230.,.15), (2,230.,190.,.5), (0,260.,240.,.7))


def compare():
    g=geometry();profile=source();rows=[]
    for idx,hot,cold,current in POINTS:
        geom=g['stages'][idx];area=geom['leg_area_m2'];count=geom['couples']
        approximate=stage(geom,hot,cold,current)
        levels=[]
        for intervals in (16,32):
            n=bounded_leg(profile,'N',hot,cold,current/area,geom['leg_length_m'],intervals=intervals)
            p=bounded_leg(profile,'P',hot,cold,-current/area,geom['leg_length_m'],intervals=intervals)
            if not (40<min(n['min_k'],p['min_k']) and max(n['max_k'],p['max_k'])<300):
                raise ValueError('BVP reference left strict measured-temperature interior')
            levels.append({'intervals':intervals,
                'qc_w':-count*area*(n['q_cold_w_m2']+p['q_cold_w_m2']),
                'voltage_v':count*(n['electric_integral_v']-p['electric_integral_v']),
                'temperature_min_k':min(n['min_k'],p['min_k']),
                'temperature_max_k':max(n['max_k'],p['max_k']),
                'max_leg_balance_residual_w':count*area*max(n['max_balance_residual_w_m2'],p['max_balance_residual_w_m2']),
                'max_leg_energy_error_w':count*area*max(abs(n['energy_error_w_m2']),abs(p['energy_error_w_m2']))})
        reference=levels[-1];errors={}
        for key in ('qc_w','voltage_v'):
            difference=approximate[key]-reference[key]
            errors[key]={'signed_error':difference,'absolute_error':abs(difference),
                'relative_error_abs':abs(difference/reference[key]) if reference[key]!=0 else None,
                'reference_16_to_32_abs_change':abs(levels[0][key]-reference[key])}
        rows.append({'stage_index':idx,'hot_k':hot,'cold_k':cold,'current_a':current,
            'geometry':geom,'affine':{key:approximate[key] for key in ('qc_w','voltage_v')},
            'bvp_levels':levels,'errors':errors,
            'caution':'Relative Qc errors grow near zero cooling; high-current Joule/Thomson curvature is absent from affine T.'})
    return {'scope':'Numerical approximation comparison for a synthetic reference; NOT OEM or measured-device validation.',
        'source':source_evidence(),'boundary_and_interior_temperature_requirement':'strictly 40<T<300 K',
        'assumed_300_390K_continuation_validated':False,
        'relative_error_definition':'abs(affine-BVP32)/abs(BVP32); null only if reference is exactly zero',
        'discretization_warning':'16/32 differences are diagnostics, not a rigorous continuum error bound.',
        'rows':rows}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    result=compare()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    for row in result['rows']:
        print(row['stage_index'],row['hot_k'],row['cold_k'],row['current_a'],row['errors'])


if __name__=='__main__':
    main()
