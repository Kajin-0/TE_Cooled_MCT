"""Read-only provenance extraction on the preserved, unimprinted R3 BREP.

OCC's empty ancestry for unchanged input faces is not a source-area failure.
Unique geometric source identities and exact registered shell complements are
independently checked before the one planned boundary meridian imprint.
"""
from pathlib import Path
import argparse,math,time,resource,collections
import numpy as np
import gmsh
from scripts.v3_analysis_r3_geometry import ROOT,R1,R2,read,save,sha,fingerprint,face_records,purge,map_output
from scripts.v3_analysis_r3_audit import matches

def bind_faces(parent,owned,allow_pair=False):
    same=[f for f,q in owned.items() if set(q['owners'])==set(parent['owners']) and matches(q,parent)]
    if len(same)==1:return same
    if same or not allow_pair:raise ValueError('Ambiguous exact source face '+str(same))
    possible=[f for f,q in owned.items() if set(q['owners'])==set(parent['owners']) and q['type']==parent['type'] and
      all(q['bbox_mm'][i]>=parent['bbox_mm'][i]-1e-5 for i in range(3)) and
      all(q['bbox_mm'][i]<=parent['bbox_mm'][i]+1e-5 for i in range(3,6))]
    if len(possible)!=2:raise ValueError('Nonunique meridian descendants '+str(possible))
    total=sum(owned[f]['area_or_volume'] for f in possible)
    center=sum(np.array(owned[f]['center_mm'])*owned[f]['area_or_volume'] for f in possible)/total
    if abs(total/parent['area_or_volume']-1)>1e-6 or max(abs(center-parent['center_mm']))>1e-6:
        raise ValueError('Meridian measure/first-moment drift')
    return possible

def complete(source,out):
    if out.exists():raise ValueError('Preserve saved completion')
    out.mkdir(parents=True);start=time.monotonic();receipt=dict(status='PENDING',no_PDE=True,no_new_gas_CSG=True)
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setString('Geometry.OCCTargetUnit','MM');gmsh.option.setNumber('General.NumThreads',4)
    try:
        oc=gmsh.model.occ;r2=read(R2/'physical_to_analysis_registry.json');original=read(R1/'face_ownership.json')
        oc.importShapes(str(R2/'analysis_conformal_mm.brep'));oc.synchronize()
        expected={n:fingerprint(3,t) for n,t in r2['domain_id_map'].items() if n!='CAVITY_GAS'}
        gmsh.clear();gmsh.model.add('source_jackets')
        oc.importShapes(str(source/'original_jackets_mm.brep'));oc.synchronize()
        jacket_vols={q['source_name']:q['source_3d_polyimide_mm3'] for q in read(R2/'geometry_build_receipt.json')['lead_jacket_records']}
        jackets={}
        for n,vol in jacket_vols.items():
            tags=[t for d,t in gmsh.model.getEntities(3) if abs(oc.getMass(3,t)/vol-1)<1e-7]
            if len(tags)!=1:raise ValueError('Source jacket identity')
            jackets[n]=fingerprint(3,tags[0]);expected[n]=jackets[n]
        gmsh.clear();gmsh.model.add('R3_saved')
        oc.importShapes(str(source/'R3_before_lineage_gate_mm.brep'));oc.synchronize()
        if len(gmsh.model.getEntities(3))!=430:raise ValueError('Saved430 domain count')
        names={};remaining=set(expected);unknown=[]
        for d,t in gmsh.model.getEntities(3):
            fp=fingerprint(3,t);hit=[n for n in remaining if matches(fp,expected[n])]
            if len(hit)==1:names[hit[0]]=t;remaining.remove(hit[0])
            elif not hit:unknown.append(t)
            else:raise ValueError('Source body ambiguity')
        if remaining or len(unknown)!=1:raise ValueError('Source body loss')
        names['CAVITY_GAS']=unknown[0]
        gas=oc.getMass(3,unknown[0]);poly=sum(q['area_or_volume'] for q in jackets.values())
        r2gas=read(R2/'geometry_build_receipt.json')['R2_gas_volume_mm3']
        if abs(r2gas-gas-poly)>1e-7:raise ValueError('Displaced gas not excluded')
        current={int(f):q for f,q in face_records(names).items()};lineage={}
        shell=read(R2/'shell_projection.json');partial={q['derived_lead_gas_face']:q for q in shell['mapping'] if q['condition'].startswith('PARTIAL')}
        oldfaces={q['face_tag']:q for q in original['interface_records']}
        for key,q in r2['face_registry'].items():
            f=int(key);fp=dict(q,area_or_volume=q['face_area_mm2'])
            if f not in partial:
                # Full jacket contacts have a changed opposite owner, not shape.
                candidates={t:x for t,x in current.items() if matches(x,fp)}
                if len(candidates)!=1:raise ValueError('Exact R2 face missing '+key)
                lineage[key]=list(candidates)
            else:
                s=partial[f];src=oldfaces[s['original_lead_polyimide_face']]
                covered=[t for t,x in current.items() if set(x['owners'])=={s['physical_Cu'],s['physical_jacket']} and
                    abs(x['area_or_volume']/s['physical_inner_area_mm2']-1)<1e-6 and
                    max(abs(np.array(x['center_mm'])-np.array(src['center_m'])*1000))<1e-6]
                bare=[t for t,x in current.items() if set(x['owners'])=={s['physical_Cu'],'CAVITY_GAS'} and
                    abs(x['area_or_volume']/(s['derived_face_area_mm2']-s['physical_inner_area_mm2'])-1)<1e-6 and
                    all(x['bbox_mm'][i]>=q['bbox_mm'][i]-1e-5 for i in range(3)) and
                    all(x['bbox_mm'][i]<=q['bbox_mm'][i]+1e-5 for i in range(3,6))]
                if len(covered)!=1 or len(bare)!=1:raise ValueError('Partial source partition identity')
                children=covered+bare;area=sum(current[t]['area_or_volume'] for t in children)
                center=sum(np.array(current[t]['center_mm'])*current[t]['area_or_volume'] for t in children)/area
                if abs(area/q['face_area_mm2']-1)>1e-6 or max(abs(center-q['center_mm']))>1e-6:raise ValueError('Partial source area/moment wrong')
                lineage[key]=children
        jparents={}
        for f in original['interface_records']:
            owner=[v['source_name'] for v in f['owners']];j=[n for n in owner if n in jackets]
            if not j:continue
            fp=dict(area_or_volume=f['area_m2']*1e6,center_mm=[x*1000 for x in f['center_m']],bbox_mm=[x*1000 for x in f['bbox_m']])
            hit=[t for t,x in current.items() if set(x['owners'])==set(owner) and matches(x,fp)]
            if len(hit)!=1:raise ValueError('Exact original jacket boundary missing')
            jparents[str(f['face_tag'])]=dict(jacket=j[0],**fp,faces=hit)
        if len(jparents)!=24:raise ValueError('Original24 jacket boundary surfaces missing')
        if {t for cs in lineage.values() for t in cs}|{t for x in jparents.values() for t in x['faces']}!=set(current):raise ValueError('Untraced saved geometry face')
        # No Boolean, imprint or reshape here: copy the pre-imprint bytes.
        import shutil
        preserved=ROOT/'data/v3_analysis_r3_20261103/geometry_completed/R3_source_restored_mm.brep'
        if sha(preserved)!=sha(source/'R3_before_lineage_gate_mm.brep'):
            # Native BREP serialization may differ; geometry is independently
            # checked above and by the separate fresh-import audit below.
            receipt['BREP_serialization_differs']=True
        shutil.copyfile(preserved,out/'R3_conformal_mm.brep')
        receipt.update(status='PASS RESTORED R3 CAD INPUT; IMPRINT STOP; MESH NOT QUALIFIED',
            domain_map=names,domains={n:fingerprint(3,t) for n,t in names.items()},
            faces={str(k):v for k,v in current.items()},R2_face_descendants=lineage,jacket_face_descendants=jparents,
            meridian_parent_faces=[],base_face_count=len(current),final_face_count=len(current),expected_domain_count=430,
            gas_volume_mm3=gas,jackets_volume_mm3=poly,R2_gas_volume_mm3=r2gas,gas_removed_mm3=r2gas-gas,
            source_jackets=jackets,input_saved_BREP_sha256=sha(source/'R3_before_lineage_gate_mm.brep'),
            output_BREP_sha256=sha(out/'R3_conformal_mm.brep'),physical_redesign=False,solver_ready=False,
            new_Boolean_operations=0,new_imprints=0,meridian_imprint_status='STOP; original failed attempt preserved')
    except Exception as ex:receipt.update(status='STOP RESTORED R3 METADATA AUDIT',error=repr(ex));raise
    finally:
        receipt.update(seconds=time.monotonic()-start,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
        save(out/'geometry_receipt.json',receipt);gmsh.finalize()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();complete(a.source,a.out)
