"""Source-derived custom 0.60 mm stack; geometry only, not solver qualification.

Preserves source body names as stable identifiers: embedded plane numbers in
names are historical labels, while actual coordinates and `plane` are updated.
"""
from __future__ import annotations
from pathlib import Path
import copy,hashlib,json,math,re
from tecooledmct.tec_assembly_v3 import fillet,body_bbox,area
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
OUT=ROOT/'data/tec_height_060_cad_20261110'
PLANE_STAGES={.5:0,1.1:1,1.6:1,2.2:2,2.7:2,3.3:3}
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stage_for_plane(z):
    for k,v in PLANE_STAGES.items():
        if abs(z-k)<1e-8:return v
    raise ValueError(f'Unknown source metallization plane {z}')
def stage_for_leg(i):return 0 if i<58 else 1 if i<80 else 2
def shift_body(b,dz):
    if b['shape']=='boxes':
        for q in b['boxes_mm']:q[2]+=dz
    elif b['shape']=='wedge':b['z']+=dz;b['bbox_mm'][2]+=dz;b['bbox_mm'][5]+=dz
    else:raise ValueError('Unregistered translated shape: '+b['name'])
def build(source,height=.6):
    if not (.5<=height<=.6):raise ValueError('Only registered 0.50–0.60 mm source construction')
    d=copy.deepcopy(source);delta=height-.5;by={b['name']:b for b in d['bodies']};assert len(by)==824
    legs={l['index']:l for l in d['legs']};assert len(legs)==88
    foot_by_number={f['number']:f for f in d['feet']};foot_shift={i:stage_for_plane(f['z'])*delta for i,f in foot_by_number.items()}
    for f in d['feet']:f['z']+=stage_for_plane(f['z'])*delta
    changed=[]
    for b in d['bodies']:
        name=b['name'];dz=0.;special=False
        if re.fullmatch(r'ceramic[0-3]',name):dz=int(name[-1])*delta
        elif b['material'] in ('P','N') and 'chain_index' in b:
            dz=stage_for_leg(b['chain_index'])*delta;b['boxes_mm'][0][5]+=delta;special=True
        elif re.fullmatch(r'solder\d+_(hot|cold)',name):
            j=b['leg'];dz=(stage_for_leg(j)+(1 if b['face']=='cold' else 0))*delta
        elif 'plane' in b and 'net' in b:
            dz=stage_for_plane(b['plane'])*delta;b['plane']+=dz
        elif re.fullmatch(r'tab_joint\d+',name):dz=foot_shift[int(name[9:])]
        elif re.fullmatch(r'fillet\d+_[-]?1',name):dz=foot_shift[int(re.match(r'fillet(\d+)_',name).group(1))]
        elif name.startswith(('cold_finish_','carrier_attach_','sapphire_carrier','die_attach_','p_HgCdTe_','det7_','det8_')):dz=3*delta
        elif name.startswith('formed_tab'):
            levels=sorted(set(round(p[1],9) for p in b['points']));n=int(name[10:]);start=1 if n==80 else 0
            for p in b['points']:
                level=min(range(len(levels)),key=lambda j:abs(p[1]-levels[j]));p[1]+=(start+level)*delta
            b['parts']=fillet(b['points'],.075);special=True
        elif name in ('detector_bond7','detector_bond8'):
            for k in (0,1,2):b['points'][k][2]+=3*delta
            b['parts']=fillet(b['points'],.15);special=True
        if abs(dz)>1e-14:shift_body(b,dz);special=True
        if special:
            b['bbox_mm']=body_bbox(b)
            if b['shape']=='boxes':b['volume_mm3']=area([[q[0],q[1],q[3],q[4]] for q in b['boxes_mm']])*b['boxes_mm'][0][5]
            elif b['shape']=='tab':b['volume_mm3']=b['width']*b['thickness']*sum(q['length'] for q in b['parts'])
            elif b['shape']=='wire':b['volume_mm3']=math.pi*(b['radius']**2-b.get('inner_radius',0)**2)*sum(q['length'] for q in b['parts'])
            changed.append(name)
    for c in d['explicit_contacts']:
        scope=c['scope'];dz=0
        if scope in ('PN_axial','PN_metal'):
            joint=c['b'] if scope=='PN_axial' else c['a'];m=re.fullmatch(r'solder(\d+)_(hot|cold)',joint)
            if not m:raise ValueError('Unknown solder contact')
            dz=(stage_for_leg(int(m.group(1)))+(m.group(2)=='cold'))*delta
        elif scope in ('tab_land','tab_foot'):
            m=re.fullmatch(r'tab_joint(\d+)',c['a']);assert m;dz=foot_shift[int(m.group(1))]
        elif scope=='detector_wire_die':dz=3*delta
        elif scope not in ('TEC_wire_land','TEC_wire_pin','TEC_land_joint','TEC_pin_joint','detector_wire_pin'):raise ValueError('Unknown contact scope '+scope)
        c['point'][2]+=dz
    d['id']='synthetic_architecture_B_custom_height_060';d['design_variant']={'leg_height_mm':height,'source_leg_height_mm':.5,'plate_shifts_mm':[j*delta for j in range(4)],'body_names':'stable source IDs; names containing plane numbers refer to original source planes','cad_qualification':'NOT RUN','manufacturer_equivalence':'NOT CLAIMED'}
    return d,changed

def main():
    src=json.loads(BASE.read_text());d,changed=build(src);p=OUT/'source_candidate';p.mkdir(exist_ok=False)
    (p/'design.json').write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
    (p/'producer.json').write_text(json.dumps({'source_design_sha256':digest(BASE),'producer_sha256':digest(__file__),'candidate_sha256':digest(p/'design.json'),'body_count':len(d['bodies']),'changed_body_count':len(changed),'changed_bodies':changed,'status':'GEOMETRY SOURCE BUILT; CAD AND CONTACT AUDITS PENDING'},indent=2)+'\n')
    print('BUILT',len(d['bodies']),'bodies;',len(changed),'body geometries changed')
if __name__=='__main__':main()
