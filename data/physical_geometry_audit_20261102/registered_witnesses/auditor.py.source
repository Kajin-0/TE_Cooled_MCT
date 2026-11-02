"""Read-only source arithmetic/contact audit; no CAD writer, FEM or physics solve.

Only inputs are frozen JSON/source bytes. New output directories are mandatory.
This builds reviewer evidence, never an independent physical acceptance verdict.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/physical_geometry_audit_20261102'
V2=ROOT/'data/tec_candidate_29114_v2_20261102'
EPS=1e-10


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')


def rectangular_union_area(rectangles):
    if not rectangles:return 0.
    xs=sorted({v for r in rectangles for v in (r[0],r[2])})
    ys=sorted({v for r in rectangles for v in (r[1],r[3])})
    return sum((b-a)*(d-c) for a,b in zip(xs,xs[1:]) for c,d in zip(ys,ys[1:])
               if any(x0-EPS<(a+b)/2<x1+EPS and y0-EPS<(c+d)/2<y1+EPS for x0,y0,x1,y1 in rectangles))


def face_contacts(a,b):
    """Independent finite-area axis-aligned contacts, returns axis/plane/rectangle."""
    result=[]
    for axis in range(3):
        others=[i for i in range(3) if i!=axis]
        for plane in (a[axis],a[axis]+a[axis+3]):
            if not any(abs(plane-v)<EPS for v in (b[axis],b[axis]+b[axis+3])):continue
            # Both interiors must be on opposite sides; coincident outer planes alone aren't a contact.
            if abs(a[axis]+a[axis+3]-b[axis])>=EPS and abs(b[axis]+b[axis+3]-a[axis])>=EPS:continue
            lo=[max(a[i],b[i]) for i in others];hi=[min(a[i]+a[i+3],b[i]+b[i+3]) for i in others]
            if all(y-x>EPS for x,y in zip(lo,hi)):result.append((axis,plane,lo+hi))
    return result


def straight_branch(length,area,rho,k,current=1.):
    if not all(math.isfinite(x) for x in (length,area,rho,k,current)) or min(length,area,rho,k)<=0:
        raise ValueError('Positive finite SI geometry/material required')
    r=rho*length/area
    return dict(length_m=length,area_m2=area,R_ohm=r,J_average_A_m2=current/area,
                Joule_W=current**2*r,G_W_K=k*area/length)


def STEP_point_bounds(text):
    """Independent length declaration and Cartesian-point scale check.

    Not a CAD kernel/volume calculation. Raw points need not bound an arbitrary
    trimmed curved solid; here both controls are explicitly rectilinear exports.
    """
    declarations=re.findall(r'SI_UNIT\(\s*(\$|\.MILLI\.)\s*,\s*\.METRE\.\s*\)',text)
    if len(set(declarations))!=1:raise ValueError('Ambiguous/missing STEP metre units')
    scale={'.MILLI.':1e-3,'$':1.}[declarations[0]]
    point_map={}
    for tag,triplet in re.findall(r"#(\d+)\s*=\s*CARTESIAN_POINT\([^,]*,\s*\(([^()]*)\)\)",text):
        xyz=[float(v)*scale for v in triplet.split(',')]
        if len(xyz)==3:point_map[tag]=xyz
    vertices=re.findall(r"VERTEX_POINT\([^,]*,\s*#(\d+)\s*\)",text)
    if any(tag not in point_map for tag in vertices):raise ValueError('Unresolved STEP vertex')
    points=[point_map[tag] for tag in vertices]
    if not points or not all(math.isfinite(v) for p in points for v in p):raise ValueError('No finite3D STEP points')
    return dict(metres_per_unit=scale,bbox_m=[min(p[i] for p in points) for i in range(3)]+[max(p[i] for p in points) for i in range(3)],
                point_count=len(points),selection='Topological VERTEX_POINT references; unreferenced plane/datum origins excluded')


def check_bounds(actual,expected,tol=1e-10):
    if len(actual)!=6 or max(abs(a-b) for a,b in zip(actual,expected))>tol:raise ValueError('STEP/source physical scale mismatch')


def physical_graph(d):
    bodies={b['name']:b for b in d['bodies']};cond={n:b for n,b in bodies.items() if b['kind'] in ('Cu','P','N','SnSb')}
    for name,b in cond.items():
        boxes=b['boxes_mm'];roots=list(range(len(boxes)))
        def root(i):
            while roots[i]!=i:i=roots[i]
            return i
        for i,j in itertools.combinations(range(len(boxes)),2):
            p,q=boxes[i],boxes[j]
            lengths=[min(p[a]+p[a+3],q[a]+q[a+3])-max(p[a],q[a]) for a in range(3)]
            if min(lengths)>=-EPS and sum(x>EPS for x in lengths)>=2:roots[root(i)]=root(j)
        if len({root(i) for i in range(len(boxes))})!=1:raise ValueError('Disconnected primitive conductor '+name)
    adj={n:set() for n in cond}
    for (an,a),(bn,b) in itertools.combinations(cond.items(),2):
        if any(min(min(p[i]+p[i+3],q[i]+q[i+3])-max(p[i],q[i]) for i in range(3))>EPS for p in a['boxes_mm'] for q in b['boxes_mm']):
            raise ValueError('Overlapping separate conductors')
        if any(face_contacts(p,q) for p in a['boxes_mm'] for q in b['boxes_mm']):adj[an].add(bn);adj[bn].add(an)
    ends=sorted(n for n,links in adj.items() if len(links)==1)
    if ends!=['Cu_node0','Cu_node88'] or any(len(v) not in (1,2) for v in adj.values()):raise ValueError('Physical graph is not unbranched two-terminal')
    path=['Cu_node0'];previous=None
    while path[-1]!='Cu_node88':
        nxt=adj[path[-1]]-({previous} if previous else set())
        if len(nxt)!=1:raise ValueError('Open/branched physical path')
        previous=path[-1];node=nxt.pop()
        if node in path:raise ValueError('Loop in physical path')
        path.append(node)
    if set(path)!=set(cond):raise ValueError('Unvisited conductive component')
    legs=[n for n in path if bodies[n]['kind'] in ('P','N')]
    for n in legs:
        i=path.index(n);kind=bodies[n]['kind']
        if ('_hot' not in path[i-1] or '_cold' not in path[i+1]) if kind=='N' else ('_cold' not in path[i-1] or '_hot' not in path[i+1]):
            raise ValueError('Physical P/N current orientation reversed')
    return dict(vertices=len(cond),edges=sum(map(len,adj.values()))//2,terminals=ends,
                leg_count=len(legs),stage_legs=dict(Counter(bodies[n]['stage'] for n in legs)),path=path,
                external_pin1_9_connected=False,scope='Actual source-box contacts, not a meshed current field')


def thermal_contacts(d):
    rows=[]
    for cu in (b for b in d['bodies'] if b['kind']=='Cu'):
        for c in (b for b in d['bodies'] if b['kind']=='Al2O3'):
            patches=defaultdict(list)
            for p in cu['boxes_mm']:
                for q in c['boxes_mm']:
                    for axis,plane,rect in face_contacts(p,q):patches[axis,round(plane,10)].append(rect)
            area=sum(rectangular_union_area(r) for r in patches.values())*1e-6
            if area:rows.append(dict(net=cu['node'],ceramic=c['name'],source_contact_area_m2=area))
    return rows


def audit():
    d=read(V2/'source_final/design.json');graph=physical_graph(d);contacts=thermal_contacts(d)
    step=STEP_point_bounds((V2/'cad/candidate_v2_mm.step').read_text())
    points=[(b['boxes_mm']) for b in d['bodies']];boxes=[q for group in points for q in group]
    source_bbox=[min(q[i] for q in boxes)*1e-3 for i in range(3)]+[max(q[i]+q[i+3] for q in boxes)*1e-3 for i in range(3)]
    check_bounds(step['bbox_m'],source_bbox)
    cube=STEP_point_bounds((V2/'cad/cube_mm.step').read_text());check_bounds(cube['bbox_m'],[.020,.020,.020,.021,.021,.021])
    cube_vol=math.prod(cube['bbox_m'][i+3]-cube['bbox_m'][i] for i in range(3))
    if not math.isclose(cube_vol,1e-9,rel_tol=1e-10):raise ValueError('Independent1mm cube volume witness')
    rho,k=1.72e-8,400.
    foil=straight_branch(.6e-3,.2e-3*30e-6,rho,k)
    wrap=straight_branch(.5e-3,.2e-3*15e-6,rho,k)
    series_R=foil['R_ohm']+wrap['R_ohm'];series_G=1/(1/foil['G_W_K']+1/wrap['G_W_K'])
    bridge_rows=[]
    for r in d['bridges']:
        # The actual foil box has NO 0.10mm horizontal foot: metadata names a film land.
        c=next(b for b in d['bodies'] if b['name']==f'ceramic{r["ceramic"]}')['boxes_mm'][0]
        f=r['foil_box_mm'];edge=c[1]+c[4] if r['side']>0 else c[1]
        inward=max(0.,edge-f[1]) if r['side']>0 else max(0.,f[1]+f[4]-edge)
        bridge_rows.append(dict(net=r['node'],ceramic=r['ceramic'],declared_land_inset_m=r['lap_mm']*1e-3,
            actual_foil_inward_foot_m=inward*1e-3,foil_end_area_m2=f[3]*f[4]*1e-6,
            foil_lower_film_overlap_volume_m3=f[3]*f[4]*d['layers_mm']['copper_film']*1e-9,
            mechanical_lap_joint_qualified=False,reason='100um inset belongs to15um film land;30um foil is vertical only, ideal union has no resolved formed foot/solder fillet/adhesion process'))
    native=read(ROOT/'fem/results/geometry_complete_checkpoint_20261030/manifest.json')
    radius=native['registry']['dimensions']['pin_pcd']['simulated']*.0005
    mirror=[]
    for row in (b for b in native['bodies'] if b['kind']=='pin'):
        i=row['pin_number'];angle=-i*math.pi/5
        expected=[-radius*math.cos(angle),radius*math.sin(angle)]
        error=max(abs(a-b) for a,b in zip(expected,row['center_xy_m']))
        if error>1e-12:raise ValueError('Bottom-to-top pin mirror mismatch')
        mirror.append(dict(pin=i,top_xy_m=expected,max_error_m=error,function=row['function']))
    return dict(builder_scope='Independent arithmetic/geometry implementation, NOT independent reviewer signoff',
        frozen_V2_STEP_sha256=sha(V2/'cad/candidate_v2_mm.step'),physical_graph=graph,
        independent_STEP_points=dict(candidate=step,cube=cube,cube_bbox_volume_m3=cube_vol,
            scope='Independent SI declaration/rectilinear point bounds; complements prior actual OCC SI import,not a new CAD/mesh solve'),
        Cu_ceramic_contacts=contacts,foil_lap_findings=bridge_rows,pin_mirror_check=mirror,
        dimensions=dict(H_m=4*.5e-3+3*.5e-3+6*15e-6+6*35e-6,
            manufacturer_external_H_range_m=[3.65e-3,3.95e-3],
            worst_case_budget='4*u_ceramic+3*u_leg+6*u_Cu+6*u_solder <=150um; actual individual tolerances UNKNOWN',
            one_axis_full_pad_registration_budget_m=(.44e-3-.4e-3)/2,
            worst_case_stack_qualified=False),
        conductor_screen=dict(property_scope='Hypothetical bulk proxies rho1.72e-8ohm m,k400W/(m K) near300K from existing numerical material assumptions; not thin-film measurements',
            foil=foil,edge_film=wrap,ideal_series_R_ohm=series_R,ideal_series_G_W_K=series_G,
            assumed_temperature_difference_K=30.,ideal_series_heat_alarm_W=30*series_G,
            four_full_current_hops_Joule_alarm_W=4*series_R,
            interpretation='Only isolated straight-bar/series algebra; actual Cu R/G/Joule partition, temperature gradients and device load NOT QUALIFIED; distributed ceramic contacts invalidate two-reservoir interpretation'),
        physical_gate='STOP: missing package leads, unqualified joints/process/tolerances and nonlocal shunts',
        independent_review='NOT REVIEWED until separate serial auditor',new_CAD_mesh_PDE_fit_cases=0)


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    if args.out.exists():raise ValueError('New audit output required; no overwrite')
    args.out.mkdir(parents=True);write(args.out/'geometry_witnesses.json',audit())
    write(args.out/'producer.json',dict(source_sha256=sha(__file__),V2_design_sha256=sha(V2/'source_final/design.json')))


if __name__=='__main__':main()
