#!/usr/bin/env python3
"""Analytic source-coordinate test of a proposed 0.60 mm stack; not a CAD model."""
from pathlib import Path
from collections import Counter
import hashlib, json, math
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/tec_height_geometry_20261110'
SOURCE=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def build(design, height):
    assert height in (.5,.6)
    delta=height-.5
    bodies={b['name']:b for b in design['bodies']}; legs=design['legs']; offset=design['core_offset_mm']
    assert len(legs)==88 and Counter(l['stage'] for l in legs)=={0:58,1:22,2:8}
    plates=[]
    for j in range(4):
        q=bodies[f'ceramic{j}']['boxes_mm'][0]
        plates.append({'index':j,'source_z0_mm':q[2],'source_z1_mm':q[2]+q[5],
                       'candidate_z0_mm':q[2]+j*delta,'candidate_z1_mm':q[2]+q[5]+j*delta,
                       'width_mm':q[3],'thickness_mm':q[5]})
    out=[]
    for leg in legs:
        i,s=leg['index'],leg['stage'];q=bodies[f'leg{i}_{leg["polarity"]}']['boxes_mm'][0]
        h=bodies[f'solder{i}_hot']['boxes_mm'][0];c=bodies[f'solder{i}_cold']['boxes_mm'][0]
        assert all(abs(x-y)<1e-9 for x,y in ((q[3],.4),(q[4],.4),(q[5],.5),(h[5],.035),(c[5],.035)))
        assert abs(h[2]+h[5]-q[2])<1e-9 and abs(q[2]+q[5]-c[2])<1e-9
        z0=q[2]+s*delta; z1=z0+height; hot_hi=h[2]+s*delta+h[5]; cold_lo=c[2]+(s+1)*delta
        assert abs(z0-hot_hi)<1e-9 and abs(z1-cold_lo)<1e-9
        assert abs(h[2]-plates[s]['source_z1_mm']-.015)<1e-9
        assert abs(plates[s+1]['source_z0_mm']-(c[2]+c[5])-.015)<1e-9
        out.append({'index':i,'stage':s,'polarity':leg['polarity'],'xy_mm':leg['center_mm'],
                    'hot_node':leg['hot_node'],'cold_node':leg['cold_node'],
                    'leg_z0_mm':z0,'leg_z1_mm':z1,'hot_solder_z1_mm':hot_hi,'cold_solder_z0_mm':cold_lo,
                    'nominal_contact_area_mm2':q[3]*q[4]})
    # Name-preserving coordinate proposal, not a geometric solids/contact audit.
    tab=[]
    for n,increment in [(58,delta),(80,delta),(88,2*delta)]:
        b=bodies[f'formed_tab{n}'];length=sum(p['length'] for p in b['parts'])
        tab.append({'net':n,'source_neutral_length_mm':length,'proposed_neutral_length_mm':length+increment,
                    'length_change_mm':increment,'status':'REQUIRES RE-FORMING AND CAD/CONTACT/COLLISION CHECK'})
    pitch=.58;w=.4;die=bodies['p_HgCdTe_photoconductor']['boxes_mm'][0];window=bodies['window']['base'][2]
    wire=bodies['detector_bond7'];start=wire['points'][0][2];apex=wire['points'][1][2];bend=.15
    detector_top=die[2]+die[5]+3*delta
    return {'scope':'ANALYTIC COORDINATE PROPOSAL ONLY; no new CAD, mesh, contact graph or package solve',
      'height_mm':height,'width_mm':w,'pitch_mm':pitch,'min_adjacent_pitch_gap_mm':pitch-w,
      'plate_rows':plates,'legs':out,'nominal_leg_contact_pairs':len(out)*2,'area_each_mm2':w*w,
      'core_stack_height_mm':3.8+3*delta,'die_top_mm':detector_top,'die_to_window_mm':window-detector_top,
      'pn_side_area_mm2':88*4*w*height,'pn_volume_mm3':88*w*w*height,'tabs':tab,
      'existing_bond_start_mm':start,'proposed_die_bond_start_mm':start+3*delta,'original_bond_apex_mm':apex,
      'naive_bond_rise_mm':apex-start-3*delta,'registered_bend_radius_mm':bend,
      'naive_bond_bend_gate':'PASS' if apex-start-3*delta>=bend else 'FAIL: original apex cannot accommodate original bend radius',
      'full_cad_geometry':'NOT RUN','new_copper_contact_and_short_audit':'NOT RUN',
      'new_ceramic_operator_mapping':'NOT RUN','native_gas_void':'NOT RUN','full_system_solve':'NOT RUN'}
def main():
    reg=json.loads((DATA/'registration.json').read_text())
    for f,h in reg['source_sha256'].items():assert sha(ROOT/f)==h, f
    design=json.loads(SOURCE.read_text());results={str(x):build(design,x) for x in (.5,.6)}
    output={'status':'GEOMETRY PROMOTION STOP: CAD/contact, remapping and gas checks NOT RUN',
            'source_sha256':sha(SOURCE),'cases':results,'full_system_solves':0,
            'delta_side_area_mm2':results['0.6']['pn_side_area_mm2']-results['0.5']['pn_side_area_mm2'],
            'delta_PN_solid_volume_mm3':results['0.6']['pn_volume_mm3']-results['0.5']['pn_volume_mm3']}
    p=DATA/'analytic_coordinate_proposal.json';assert not p.exists();p.write_text(json.dumps(output,indent=2)+'\n')
    print('PASS source coordinate arithmetic; STOP candidate CAD and multiphysics promotion')
if __name__=='__main__':main()
