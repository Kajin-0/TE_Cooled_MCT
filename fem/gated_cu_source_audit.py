"""Standard-library source-only audit; never a substitute for a3D Cu solve."""
import argparse
from datetime import datetime,timezone
import hashlib,json,math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/tec_candidate_29114_20261101'


def segment(a,b,width=.1,thickness=.03,rho=1.72e-8):
    delta=[abs(x-y) for x,y in zip(a,b)];axes=[i for i,x in enumerate(delta) if x>1e-10]
    if len(axes)!=1 or not all(math.isfinite(x) for x in (*a,*b,width,thickness,rho)) or min(width,thickness,rho)<=0:
        raise ValueError('Finite orthogonal positive conductor required')
    axis=axes[0];size=[width,width,thickness];box=[min(x,y)-s/2 for x,y,s in zip(a,b,size)]
    size[axis]+=delta[axis];box+=size
    area_mm2=width*width if axis==2 else width*thickness
    return dict(axis=axis,length_m=delta[axis]*.001,area_m2=area_mm2*1e-6,box_mm=box,
        R_ohm_estimate=rho*delta[axis]*.001/(area_mm2*1e-6),section_average_J_at1A=1/(area_mm2*1e-6))


def audit(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    design=json.loads((SOURCE/'geometry/design.json').read_text());rows=[];rho=1.72e-8
    for node,points in design['Cu_routes_mm'].items():
        body=next(b for b in design['bodies'] if b['name']==f'Cu_node{node}')
        for a,b in zip(points,points[1:]):
            row=segment(a,b);matches=[q for q in body['boxes_mm'] if all(abs(x-y)<1e-12 for x,y in zip(q,row['box_mm']))]
            if len(matches)!=1:raise ValueError('Frozen route primitive not uniquely matched')
            row.update(node=int(node),source_primitive_matched=True);rows.append(row)
    pair_R=85*rho*.58e-3/(.44e-3*.03e-3)
    tail_R=2*rho*1.5e-3/(math.pi*(.1e-3)**2)
    corrected=sum(r['R_ohm_estimate'] for r in rows)+pair_R+tail_R
    old=json.loads((SOURCE/'presentation/comparison.json').read_text())['post_hoc_Cu_omission_audit']['total_Cu_R_ohm_estimate']
    vertical_length=sum(r['length_m'] for r in rows if r['axis']==2)
    discrepancy=rho*vertical_length*(1/(.1e-3*.03e-3)-1/(.1e-3*.1e-3))
    if not math.isclose(old-corrected,discrepancy,rel_tol=1e-12,abs_tol=1e-15):raise ValueError('Independent area correction identity')
    result=dict(observed_UTC=datetime.now(timezone.utc).isoformat(),scope='Source-only algebra; no CAD import, mesh, PDE or fitting',
        frozen_design_sha256=hashlib.sha256((SOURCE/'geometry/design.json').read_bytes()).hexdigest(),
        segment_rows=rows,vertical_length_m=vertical_length,old_uniform_area_R_estimate_ohm=old,
        direction_aware_centerline_R_estimate_ohm=corrected,difference_ohm=old-corrected,
        independent_difference_ohm=discrepancy,qualified_Cu_R_ohm=None,
        interpretation='Vertical frozen pillars0.1x0.1mm differ from horizontal0.1x0.03mm ribbons. Estimate still omits spreading/corners/stubs/contact effects; NOT a qualified resistance.',
        Joule_partition='UNKNOWN: each fraction0..1, sum1, total I^2*Rcu; Rcu remains unqualified',
        Stage_A_3D='NOT RUN: exact pinned image unavailable',Stage_B='NOT RUN: A unmet',Stage_C='NOT RUN: B unmet',
        no_half_split=True,actual_new_reduced_cases=0)
    (out/'source_only_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Source-only estimate',corrected,'ohm; qualified R UNKNOWN; no physical solve')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);audit(p.parse_args().out)
