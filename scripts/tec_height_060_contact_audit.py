"""Independent rectangular intersection and source-to-candidate geometry audit."""
from pathlib import Path
from collections import Counter
import json,hashlib,math
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/tec_height_060_cad_20261110'
def overlap_area(q,rects):
    clips=[]
    for r in rects:
        x0=max(q[0],r[0]);x1=min(q[0]+q[3],r[0]+r[3]);y0=max(q[1],r[1]);y1=min(q[1]+q[4],r[1]+r[4])
        if x1>x0 and y1>y0:clips.append((x0,x1,y0,y1))
    x=sorted({v for c in clips for v in c[:2]});total=0.
    for a,b in zip(x,x[1:]):
        intervals=sorted((c[2],c[3]) for c in clips if c[0]<(a+b)/2<c[1]);end=-math.inf;length=0.
        for lo,hi in intervals:length+=max(0,hi-max(lo,end));end=max(end,hi)
        total+=(b-a)*length
    return total
def audit(d):
    bodies={b['name']:b for b in d['bodies']};assert len(bodies)==824 and len(d['legs'])==88
    contacts=d['explicit_contacts'];assert Counter(c['scope'] for c in contacts)['PN_axial']==176
    refs={(c['a'],c['b']):c for c in contacts if c['scope']=='PN_axial'}
    metal={c['a']:c for c in contacts if c['scope']=='PN_metal'};assert len(refs)==len(metal)==176
    pn=[];sm=[];eps=1e-9
    for l in d['legs']:
        i=l['index'];leg=bodies[f'leg{i}_{l["polarity"]}'];q=leg['boxes_mm'][0]
        assert abs(q[3]-.4)<eps and abs(q[4]-.4)<eps and abs(q[5]-.6)<eps
        assert {l['hot_node'],l['cold_node']}=={i,i+1}
        for side in ('hot','cold'):
            sn=f'solder{i}_{side}';s=bodies[sn];sq=s['boxes_mm'][0];c=refs[(leg['name'],sn)];m=metal[sn];au=bodies[m['b']]
            assert s['group']==au['group']==l[side+'_node'] and au['material']=='Au'
            lface=q[2] if side=='hot' else q[2]+q[5];sface=sq[2]+sq[5] if side=='hot' else sq[2]
            assert abs(lface-sface)<eps and abs(c['point'][2]-lface)<eps
            ar=overlap_area(q,[sq]);assert abs(ar-.16)<eps;pn.append(ar)
            plane=sq[2] if side=='hot' else sq[2]+sq[5]
            faces=[a for a in au['boxes_mm'] if abs((a[2]+a[5] if side=='hot' else a[2])-plane)<eps]
            assert faces and abs(m['point'][2]-plane)<eps
            ar=overlap_area(sq,faces);assert abs(ar-.16)<eps;sm.append(ar)
    feet=Counter(f['net'] for f in d['feet']);assert feet=={58:2,80:2,88:3}
    for n in (1,9):assert bodies[f'pin{n}']['radius']==.38 and bodies[f'TEC_lead{n}']['radius']==.1
    for n in (7,8):assert bodies[f'detector_bond{n}']['radius']==.009
    return {'status':'PASS independent rectangular contact areas, source series ownership and pin radii; curved collision/STEP not covered',
       'leg_solder_contacts':len(pn),'solder_gold_contacts':len(sm),'minimum_leg_solder_area_mm2':min(pn),'minimum_solder_gold_area_mm2':min(sm),
       'foot_counts':dict(feet),'pin_diameter_mm':.76,'tec_lead_diameter_mm':.2,'detector_wire_diameter_mm':.018}
def main():
    p=OUT/'source_candidate/design.json';d=json.loads(p.read_text());r=audit(d);r['design_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();(OUT/'independent_contact_audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
if __name__=='__main__':main()
