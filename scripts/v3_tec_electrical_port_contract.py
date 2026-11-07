#!/usr/bin/env python3
"""No-solve V3 source-CAD electric terminal / series path / couple port contract.

Graph edges are the accepted 430-region R3 source's 557 shared
solid-solid CAD interfaces only, WITHOUT assigning conductivity or
contact law. The graph is a connectivity witness, not a PDE or a
physical short-circuit/resistance prediction.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/v3_r32_global_surface_20261103/source_metadata.json'
INPUT=ROOT/'data/v3_physical_law_readiness_20261106/attempt01/law_and_subassembly_inventory.json'
GATE=ROOT/'data/v3_interconnect_et_20261102/B/gate_B.json'
CONDUCTIVE_CLASSES={
 'P','N','SnSb','SnBi57_43','In52Sn48','Cu','Au',
 'COMPOSITE_MULTILAYER','Kovar_pin','Kovar','EFFECTIVE_AXIAL_KOVAR_NI_AU'}
SEMICONDUCTOR_CLASS='pHgCdTe_PC'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def connected(graph,start,target,excluded=None):
    excluded=set(excluded or ())
    if start in excluded or target in excluded:return False,0
    seen={start};stack=[start]
    for v in stack:
        for w in sorted(graph[v]):
            if w not in seen and w not in excluded:
                seen.add(w);stack.append(w)
    return target in seen,len(seen)

def components(graph,allowed):
    remaining=set(allowed);out=[]
    while remaining:
        start=min(remaining);remaining.remove(start)
        seen={start};queue=[start]
        for v in queue:
            for w in sorted(graph[v]):
                if w in remaining:
                    remaining.remove(w);seen.add(w);queue.append(w)
        out.append(sorted(seen))
    return sorted(out,key=lambda x:(-len(x),x[0]))

def generate():
    j=json.loads(SOURCE.read_text())
    inp=json.loads(INPUT.read_text())
    legacy=json.loads(GATE.read_text())
    assert legacy['status']=='FAIL/STOP'
    assert j['stage_leg_counts']=={'0':58,'1':22,'2':8}
    assert len(j['faces'])==2440 and len(j['domains'])==430
    assert len(j['source_contacts'])==378
    assert inp['unreleased_volume_laws']==430
    d=j['domains'];faces=j['faces']
    inv={v['id']:k for k,v in d.items()}
    conductor={v['id'] for v in d.values() if v['material'] in CONDUCTIVE_CLASSES}
    assert len(conductor)==407
    semicon={v['id'] for v in d.values() if v['material']==SEMICONDUCTOR_CLASS}
    assert semicon=={408}
    electrical=collections.defaultdict(set)
    electric_semiconductor=collections.defaultdict(set)
    all_solid_edges=[]
    for key,face in faces.items():
        if face['class_']!='SOLID_SOLID':continue
        aa=face['owner_volume_ids']
        assert len(aa)==2
        a,b=aa
        all_solid_edges.append((int(key),a,b))
        if a in conductor and b in conductor:
            electrical[a].add(b);electrical[b].add(a)
        if a in conductor|semicon and b in conductor|semicon:
            electric_semiconductor[a].add(b);electric_semiconductor[b].add(a)
    assert len(all_solid_edges)==557
    assert all(not (face['class_']=='SOLID_SOLID' and len(face['owner_volume_ids'])!=2) for face in faces.values())
    p1,p7,p8,p9=[d['pin'+str(k)]['id'] for k in (1,7,8,9)]
    assert (p1,p7,p8,p9)==(424,425,426,427)
    assert j['terminal_faces']=={'pin1':[2414],'pin7':[2418],'pin8':[2422],'pin9':[2426]}
    assert connected(electrical,p1,p9)[0] is True
    assert connected(electrical,p7,p8)[0] is False
    assert connected(electric_semiconductor,p7,p8)[0] is True
    assert connected(electric_semiconductor,p1,p7)[0] is False
    assert connected(electric_semiconductor,p1,p8)[0] is False
    cc=components(electrical,conductor)
    assert sorted(map(len,cc),reverse=True)==[389,4,4,4,1,1,1,1,1,1]
    # All 88 N/P legs must be graph articulations between actual TEC
    # package pins. Test each leg's removal independently, with exactly
    # the original face graph and no conductivity properties.
    legs=[]
    for i in range(88):
        polarity='N' if i%2==0 else 'P'
        name=f'leg{i}_{polarity}'
        vid=d[name]['id']
        assert d[name]['material']==polarity
        stage=int(d[name]['stage'])
        assert stage==(0 if i<58 else (1 if i<80 else 2))
        survives,reached=connected(electrical,p1,p9,{vid})
        assert not survives,(name,'Unexpected bypass around leg')
        legs.append({'chain_index':i,'CAD_name':name,'volume_id':vid,
                     'polarity':polarity,'stage':stage,
                     'pin1_pin9_connection_after_removal':survives,
                     'pin1_reachable_conductor_domains_after_removal':reached,
                     'is_mandatory_graph_articulation':True})
    assert collections.Counter((x['stage'],x['polarity']) for x in legs)=={
      (0,'N'):29,(0,'P'):29,(1,'N'):11,(1,'P'):11,(2,'N'):4,(2,'P'):4}
    # Structural chain stage transitions: original geometry distinct
    # multi-plane copper net volumes connected by formed tabs, solder
    # and fillets; record interface graph, not a fitted ohmic short.
    stage_boundaries=[]
    for idx in (58,80):
        names=[k for k in d if k.startswith('net'+str(idx)+'_plane')]
        assert len(names)==2
        vids=[d[k]['id'] for k in names]
        ok,_=connected(electrical,vids[0],vids[1])
        assert ok
        # Connectivity in the full network isn't sufficient to prove a
        # LOCAL stage bridge. Find shortest graph path and require all
        # intermediate vertices be named copper/tab/joint/fillet, not legs.
        queue=[vids[0]];parent={vids[0]:None}
        for v in queue:
            if v==vids[1]:break
            for w in sorted(electrical[v]):
                if w not in parent and d[inv[w]]['material'] not in ('N','P'):
                    parent[w]=v;queue.append(w)
        assert vids[1] in parent
        path=[];cur=vids[1]
        while cur is not None:path.append(cur);cur=parent[cur]
        path.reverse()
        assert len(path)>=3
        stage_boundaries.append({
            'stage_transition_after_leg_index':idx-1,
            'source_net_index':idx,'native_distinct_net_domains':names,
            'native_net_domain_ids':vids,
            'source_connected_without_P_or_N_leg':True,
            'source_intermediates_CAD_names':[inv[k] for k in path[1:-1]],
            'local_conductive_path_CAD_names':[inv[k] for k in path],
            'interpretation':'CAD connectivity only; physical solder/contact and tensor laws UNSET'})
    # Pin1/net0 and pin9/net88 electrical source terminal path:
    def chain_to_net(pin,net_name):
        target=d[net_name]['id'];queue=[d[pin]['id']]
        parent={queue[0]:None}
        for v in queue:
            if v==target:break
            for w in sorted(electrical[v]):
                if w not in parent and d[inv[w]]['material'] not in ('N','P'):
                    parent[w]=v;queue.append(w)
        assert target in parent,(pin,net_name)
        path=[];cur=target
        while cur is not None:path.append(cur);cur=parent[cur]
        return [inv[x] for x in path[::-1]]
    leadpath1=chain_to_net('pin1','net0_plane0.500_Cu')
    leadpath9=chain_to_net('pin9','net88_plane0.500_Cu')
    # Real first couple ID-based source contact / electrical ports:
    ss=inp['selected_actual_P_N_subassembly']
    assert ss['selected_volume_count']==11
    left=d['net0_plane0.500_Cu']['id']
    right=d['net2_plane0.500_Cu']['id']
    # Neither net has a CAD "EXTERIOR" electrical port.
    exterior_on_pair=[
      int(tag) for tag,f in faces.items()
      if f['class_']=='EXTERIOR' and any(k in (left,right) for k in f['owner_volume_ids'])]
    assert exterior_on_pair==[]
    # The exact native series pathway remains in full 88 leg assembly.
    assert connected(electrical,left,right)[0]
    # Face from net0 to lead1 and from net2 to solder2 are physical
    # circuit adjacencies. These cannot be sealed as insulation.
    def between(a,b):
        a,b=d[a]['id'],d[b]['id']
        tags=[int(t) for t,f in faces.items()
              if f['class_']=='SOLID_SOLID' and set(f['owner_volume_ids'])=={a,b}]
        assert len(tags)==1
        return tags[0]
    pair_left=between('net0_plane0.500_Cu','lead1_land_joint')
    pair_right=between('net2_plane0.500_Cu','solder2_hot')
    assert (pair_left,pair_right)==(1531,162)
    # Verify detector separate conductor branches become one via
    # the actual HgCdTe active material at its two wedge faces.
    mct_faces=[int(t) for t,f in faces.items()
               if f['class_']=='SOLID_SOLID' and 408 in f['owner_volume_ids']
               and any(k in (409,410) for k in f['owner_volume_ids'])]
    assert sorted(mct_faces)==[2336,2337]
    def thermal_chain(names):
        links=[]
        for left,right in zip(names,names[1:]):
            ids={d[left]['id'],d[right]['id']}
            found=[(int(k),f['face_area_mm2']) for k,f in faces.items()
                if f['class_']=='SOLID_SOLID' and set(f['owner_volume_ids'])==ids]
            assert len(found)==1,(left,right,found)
            links.append({'source_pair_CAD_names':[left,right],
                          'source_face_tag':found[0][0],
                          'source_area_mm2':found[0][1],
                          'physical_thermal_law_qualified':False})
        return links
    hot_chain=thermal_chain(['VIGO_reference_header','header_finish_Ni',
                            'hot_mount_In52Sn48','underside_Au','ceramic0'])
    cold_chain=thermal_chain(['ceramic3','cold_finish_Au',
                             'carrier_attach_EP29LPSP','sapphire_carrier',
                             'die_attach_EP29LPSP','p_HgCdTe_photoconductor'])
    assert [f['source_face_tag'] for f in hot_chain]==[2228,2298,2303,6]
    assert [f['source_face_tag'] for f in cold_chain]==[119,2314,2319,2325,2330]
    sink_candidates=[int(t) for t,f in faces.items()
                     if f['class_']=='EXTERIOR' and
                        f['owner_volume_ids']==[d['VIGO_reference_header']['id']]]
    assert len(sink_candidates)==12
    return {
      'status':'PASS CAD circuit topology: pin1/pin9 TEC series with all 88 mandatory leg solids; physical electrical/thermal subassembly ports STOP',
      'analysis_scope':'exact native solid-solid shared-face graph only; no source conductivity nor measured heat/contact values',
      'source_domains':430,'source_faces':2440,
      'source_solid_solid_faces_used':len(all_solid_edges),
      'conductive_material_labels':sorted(CONDUCTIVE_CLASSES),
      'conductive_CAD_volumes':len(conductor),
      'connected_conductor_component_sizes':[len(c) for c in cc],
      'TEC_conductor_component_CAD_volume_count':next(len(c) for c in cc if p1 in c),
      'TEC_pin_port_face_tags':{'pin1':2414,'pin9':2426},
      'detector_pin_port_face_tags':{'pin7':2418,'pin8':2422},
      'TEC_pin1_pin9_graph_connected':True,
      'detector_pin7_pin8_without_MCT_graph_connected':False,
      'detector_pin7_pin8_with_MCT_graph_connected':True,
      'TEC_pin1_to_detector_pin7_with_MCT_graph_connected':False,
      'TEC_pin1_to_detector_pin8_with_MCT_graph_connected':False,
      'HgCdTe_detector_to_two_wedge_native_face_tags':mct_faces,
      'source_leg_articulation_count':len(legs),
      'thermal_hot_stack_native_contact_sequence':hot_chain,
      'thermal_detector_stack_native_contact_sequence':cold_chain,
      'hot_header_native_exterior_face_tags':sink_candidates,
      'hot_header_exterior_faces_are_candidate_sink_ports_only':True,
      'hot_thermal_sink_BC_qualified':False,
      'detector_spectral_or_heat_load_boundary_qualified':False,
      'source_88_series_leg_articulations':legs,
      'interstage_nonleg_connections':stage_boundaries,
      'TEC_input_pin1_to_stage0_net0_conductor_path':leadpath1,
      'TEC_output_pin9_to_net88_conductor_path':leadpath9,
      'selected_actual_first_pair':{
         'native_N_and_P_leg_volume_ids':[d['leg0_N']['id'],d['leg1_P']['id']],
         'net0_net2_volume_ids':[left,right],
         'net0_net2_are_real_package_external_CAD_faces':False,
         'net0_downstream_external_connection_to_lead1_face_tag':pair_left,
         'net2_downstream_connection_to_leg2_solder_face_tag':pair_right,
         'selected_11_source_volumes':ss['selected_volume_ids'],
         'selected_entire_source_ceramic0_and_ceramic1':True,
         'selected_union_external_to_selection_faces':ss['cut_boundary_faces_count'],
         'selected_union_external_to_selection_face_classes':{
            k:sum(1 for face in inp['face_law_rows']
                  if face['face_tag'] in ss['cut_boundary_face_tags'] and face['face_class']==k)
            for k in ('SOLID_SOLID','GAS_SOLID','EXTERIOR')},
         'true_electrical_bcs':'NOT ASSIGNED; only package pin1 and pin9 are TEC terminals',
         'hypothetical_cut_ports':'UNRELEASED: net0/net2 are connected to rest of real 88-leg circuit',
         'true_hot_and_cold_thermal_bcs':'NOT ASSIGNED; whole ceramic0/ceramic1 exchange with remaining 86 legs and gas',
         'subassembly_PDE':'NOT RUN',
         'physical_subassembly_port_readiness':'STOP'},
      'required_inputs':{
        'TEC_drive':'Measured pin1 to pin9 terminal I-V or imposed current; conductivity tensors and finite joining resistances must be assigned first',
        'TEC_heat_boundary':'Physical hot-side source/sink and cooling load, including full ceramic spreading and next-stage heat, not arbitrary adiabatic cuts',
        'isolated_couple_model':'Only a separately declared circuit/thermal network reduction with mathematical cut-boundary ports and independently supplied states/impedances; not measured physical pins',
        'detector_bias':'pin7/pin8 are a separate HgCdTe-linked circuit; not the pin1/pin9 TEC power loop'},
      'original_P1_Gate_B':'FAIL/STOP',
      'prospective_P2_Gate_B':'STOP',
      'thermal_C_D':'NOT RUN',
      'physical_material_and_face_law_release':'STOP',
      'source_geometry_mesh_modified':False,
      'new_PDE_runs':0,
      'source_input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (SOURCE,INPUT,GATE)}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path)
    p.add_argument('--verify-only',action='store_true')
    args=p.parse_args()
    out=generate()
    if args.verify_only:
        assert args.out and args.out.is_file()
        assert json.loads(args.out.read_text())==out
    elif args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        with args.out.open('x') as f:
            json.dump(out,f,indent=2)
            f.write('\n')
    print('V3_CIRCUIT_PORT_GRAPH',
        json.dumps({k:out[k] for k in ('status','connected_conductor_component_sizes','source_leg_articulation_count','interstage_nonleg_connections','TEC_input_pin1_to_stage0_net0_conductor_path','TEC_output_pin9_to_net88_conductor_path')},indent=2))
if __name__=='__main__':main()
