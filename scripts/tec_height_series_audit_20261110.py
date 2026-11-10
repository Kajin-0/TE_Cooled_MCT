"""Independently inspect source P/N series ownership; candidate has no new CAD graph."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'data/tec_height_geometry_20261110'
def verify(d):
    bodies={b['name']:b for b in d['bodies']};legs=d['legs']; contacts=d['explicit_contacts']
    assert len(legs)==88 and len(bodies)==824
    check={(c['a'],c['b']):c for c in contacts if c['scope'] in ('PN_axial','PN_metal')}
    assert len(check)==352
    for l in legs:
        i=l['index'];p=l['polarity']; assert {l['hot_node'],l['cold_node']}=={i,i+1}
        assert p==('N' if (i if l['stage']==0 else i-58 if l['stage']==1 else i-80)%2==0 else 'P')
        for face in ('hot','cold'):
            joint=f'solder{i}_{face}';leg=f'leg{i}_{p}';node=l[face+'_node']
            assert bodies[joint]['group']==node
            c=check[(leg,joint)];assert abs(c['area']-.16)<1e-10
            matches=[v for (a,b),v in check.items() if a==joint and b.startswith(f'net{node}_') and b.endswith('_Au')]
            assert len(matches)==1 and abs(matches[0]['area']-.16)<1e-10
    return {'source_leg_count':88,'source_legs_per_stage':[58,22,8],
            'source_leg_solder_contacts':176,'source_solder_metal_contacts':176,
            'source_chain_nodes':list(range(89)),
            'source_copper_full_3D_connectivity':'NOT RE-EXAMINED',
            'candidate_chain_and_contacts':'PLANNED SAME IDENTITIES; NOT VERIFIED IN NEW CAD'}
def main():
 p=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json';d=json.loads(p.read_text())
 o=verify(d);o['source_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();o['scope']='SOURCE REGISTRY ONLY; no physical geometry check for proposed variant'
 out=P/'source_series_topology_audit.json';assert not out.exists();out.write_text(json.dumps(o,indent=2)+'\n');print('PASS source series and 352 declared interfaces; candidate CAD NOT RUN')
if __name__=='__main__':main()
