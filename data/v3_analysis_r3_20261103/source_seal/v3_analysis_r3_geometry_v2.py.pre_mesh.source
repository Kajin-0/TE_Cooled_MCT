"""R3 source-conservative CAD: explicit jackets and boundary-only meridian splits.

No physical redesign, no constitutive coefficients and no PDE. The source
polymer volumes displace gas exactly; no parallel gas/shell surrogate remains.
"""
from pathlib import Path
import argparse,hashlib,json,time,resource,math
import numpy as np
import gmsh

ROOT=Path(__file__).resolve().parents[1]
R2=ROOT/'data/v3_analysis_r2_release_20261103'
R1=ROOT/'data/v3_derived_multiphysics_20261103'

def read(p):return json.loads(Path(p).read_text())
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint(dim,tag):
    oc=gmsh.model.occ
    return dict(area_or_volume=oc.getMass(dim,tag),center_mm=list(oc.getCenterOfMass(dim,tag)),bbox_mm=list(oc.getBoundingBox(dim,tag)))

def purge():
    for dim in (2,1,0):
        unused=[(dim,t) for d,t in gmsh.model.getEntities(dim) if not len(gmsh.model.getAdjacencies(dim,t)[0])]
        if unused:gmsh.model.occ.remove(unused,recursive=False);gmsh.model.occ.synchronize()

def face_records(names):
    reverse={tag:name for name,tag in names.items()};out={}
    signed={}
    for n,t in names.items():
        for d,f in gmsh.model.getBoundary([(3,t)],combined=False,oriented=True):signed[(t,abs(f))]=1 if f>0 else -1
    for _,f in gmsh.model.getEntities(2):
        up=sorted(map(int,gmsh.model.getAdjacencies(2,f)[0]))
        if not 1<=len(up)<=2:raise ValueError('Unowned/nonmanifold face '+str(f))
        if len(up)==2 and sum(signed[(t,f)] for t in up)!=0:raise ValueError('Same-signed interface normal')
        owners=[reverse[t] for t in up]
        if 'CAVITY_GAS' in owners and len(up)!=2:raise ValueError('Open native gas boundary')
        out[str(f)]=dict(face_tag=f,owners=owners,owner_volume_ids=up,
          orientation_signs=[signed[(t,f)] for t in up],type=gmsh.model.getType(2,f),
          face_area_mm2=gmsh.model.occ.getMass(2,f),**fingerprint(2,f))
    return out

def map_output(groups,names):
    out={}
    for name,items in zip(names,groups):
        tags=[t for d,t in items if d==3]
        if len(tags)!=1:raise ValueError('Unexpected volume split '+str((name,tags)))
        out[name]=tags[0]
    if len(set(out.values()))!=len(out):raise ValueError('Merged source volumes')
    return out

def resolved_faces(groups, names, phase, out):
    # OCC can return a standalone coincident face in the provenance map even
    # when the actual material boundary is a distinct, geometrically identical
    # owned entity. Rebind only exact independent CAD fingerprints; never fit.
    oc=gmsh.model.occ
    owned={t:fingerprint(2,t) for d,t in gmsh.model.getEntities(2)
           if len(gmsh.model.getAdjacencies(2,t)[0])}
    records=[];result={}
    for parent, group in zip(names,groups):
        children=[]
        for dim,tag in group:
            if dim!=2:continue
            if tag in owned:children.append(tag);continue
            q=fingerprint(2,tag)
            hit=[f for f,v in owned.items()
                 if abs(v['area_or_volume']/q['area_or_volume']-1)<1e-7
                 and max(abs(a-b) for a,b in zip(v['center_mm'],q['center_mm']))<1e-6
                 and max(abs(a-b) for a,b in zip(v['bbox_mm'],q['bbox_mm']))<1e-5]
            if len(hit)!=1:raise ValueError('Ambiguous orphan-face provenance '+str((parent,tag,hit)))
            children.append(hit[0]);records.append(dict(parent=parent,standalone=tag,owned=hit[0],fingerprint=q))
        result[str(parent)]=sorted(set(children))
    save(out/(phase+'_lineage_rebindings.json'),records)
    return result

def build(out):
    if out.exists():raise ValueError('Preserve CAD attempt')
    out.mkdir(parents=True);start=time.monotonic();receipt=dict(status='PENDING',no_PDE=True)
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',4)
    gmsh.option.setString('Geometry.OCCTargetUnit','MM')
    try:
        oc=gmsh.model.occ
        old=read(R1/'face_ownership.json');r2=read(R2/'physical_to_analysis_registry.json')
        oc.importShapes(str(R1/'analysis_solids_mm.brep'));oc.synchronize()
        ids={n:q['tag'] for n,q in old['domain_metadata'].items() if n!='CAVITY_GAS'}
        keep={ids['lead1_insulation'],ids['lead9_insulation']}
        oc.remove([(3,t) for d,t in gmsh.model.getEntities(3) if t not in keep],recursive=True);oc.synchronize();purge()
        if len(gmsh.model.getEntities(3))!=2:raise ValueError('Source jackets missing')
        jackets={n:fingerprint(3,ids[n]) for n in ('lead1_insulation','lead9_insulation')}
        gmsh.write(str(out/'original_jackets_mm.brep'))
        gmsh.clear();gmsh.model.add('R3');gmsh.option.setString('Geometry.OCCTargetUnit','MM')
        oc.importShapes(str(R2/'analysis_conformal_mm.brep'));oc.synchronize()
        names=dict(r2['domain_id_map'])
        if {t for d,t in gmsh.model.getEntities(3)}!=set(names.values()):raise ValueError('R2 identity mismatch')
        r2_faces={int(k):v for k,v in r2['face_registry'].items()}
        oc.remove([(3,names.pop('CAVITY_GAS'))],recursive=True);oc.synchronize()
        if not set(r2_faces)<={t for d,t in gmsh.model.getEntities(2)}:raise ValueError('R2 source face deleted')
        imported=oc.importShapes(str(out/'original_jackets_mm.brep'));oc.synchronize()
        for name,fp in jackets.items():
            match=[t for d,t in imported if abs(oc.getMass(3,t)/fp['area_or_volume']-1)<1e-7 and np.linalg.norm(np.array(oc.getCenterOfMass(3,t))-fp['center_mm'])<1e-6]
            if len(match)!=1:raise ValueError('Jacket identity '+name)
            names[name]=match[0]
        solids=[(3,t) for t in names.values()]
        jacket_parent={}
        for name in jackets:
            for d,f in gmsh.model.getBoundary([(3,names[name])],combined=False,oriented=False):
                jacket_parent[int(f)]={'jacket':name,**fingerprint(2,int(f))}
        parent_faces=sorted(set(r2_faces)|set(jacket_parent))
        expected={name:fingerprint(3,t) for name,t in names.items()}
        void=oc.addCylinder(0,0,1.5,0,0,8.15,7.1)
        excluded={names[n] for n in ('cap_shell','cap_roof','window')}
        gas,_=oc.cut([(3,void)],[(3,t) for d,t in solids if t not in excluded],removeObject=True,removeTool=False)
        oc.synchronize()
        if len(gas)!=1 or gas[0][0]!=3:raise ValueError('Disconnected native gas')
        gas_volume=oc.getMass(3,gas[0][1])
        jacket_volume=sum(v['area_or_volume'] for v in jackets.values())
        r2gas=read(R2/'geometry_build_receipt.json')['R2_gas_volume_mm3']
        if abs(r2gas-gas_volume-jacket_volume)>1e-7:raise ValueError('Gas/polymer double-count exclusion failure')
        ordered=['CAVITY_GAS']+list(names)
        produced,mapping=oc.fragment(gas,solids+[(2,f) for f in parent_faces]);oc.synchronize()
        names=map_output(mapping[:len(ordered)],ordered)
        if len(names)!=430:raise ValueError('Expected430 explicit-material domains')
        lineage=resolved_faces(mapping[len(ordered):],parent_faces,'restoration',out)
        gmsh.write(str(out/'R3_before_lineage_gate_mm.brep'))
        save(out/'restoration_lineage_before_gate.json',lineage)
        purge()
        for f,children in lineage.items():
            target=r2_faces[int(f)]['face_area_mm2'] if int(f) in r2_faces else jacket_parent[int(f)]['area_or_volume']
            if abs(sum(oc.getMass(2,t) for t in children)/target-1)>1e-6:raise ValueError('Initial source-face area drift '+f)
        gmsh.write(str(out/'R3_source_restored_mm.brep'))
        base_faces=face_records(names)
        # Boundary-only generator curves split full periodic wire skins into
        # quadrilateral half-skins. No physical volume is redesigned or divided.
        cutters=[];cuts=[]
        for key,f in base_faces.items():
            if not any(n.startswith(('TEC_lead','lead1_insulation','lead9_insulation','detector_bond')) for n in f['owners']):continue
            kind=f['type'];tag=int(key)
            if kind not in ('Cylinder','Torus'):continue
            lo,hi=gmsh.model.getParametrizationBounds(2,tag)
            if kind=='Cylinder' and abs(hi[0]-lo[0]-2*math.pi)<1e-5:
                uv=[[(lo[0]+hi[0])/2,lo[1]],[(lo[0]+hi[0])/2,hi[1]]]
                p=[list(gmsh.model.getValue(2,tag,q)) for q in uv]
                v=[oc.addPoint(*q) for q in p];curve=oc.addLine(*v)
            elif kind=='Torus' and abs(hi[1]-lo[1]-2*math.pi)<1e-5:
                uv=[[x,(lo[1]+hi[1])/2] for x in (lo[0],(lo[0]+hi[0])/2,hi[0])]
                a,b,c=[np.array(gmsh.model.getValue(2,tag,q)) for q in uv]
                u=b-a;v=c-a;w=np.cross(u,v)
                center=a+(np.dot(u,u)*np.cross(v,w)+np.dot(v,v)*np.cross(w,u))/(2*np.dot(w,w))
                curve=oc.addCircleArc(oc.addPoint(*a),oc.addPoint(*center),oc.addPoint(*c))
            else:continue
            cutters.append((1,curve));cuts.append(tag)
        before={name:fingerprint(3,t) for name,t in names.items()}
        facekeys=sorted(map(int,base_faces));ordered_names=list(names)
        if cutters:
            result,changes=oc.fragment([(3,names[ordered_names[0]])],[(3,names[n]) for n in ordered_names[1:]]+[(2,f) for f in facekeys]+cutters)
            oc.synchronize();names=map_output(changes[:len(ordered_names)],ordered_names)
            second0=resolved_faces(changes[len(ordered_names):len(ordered_names)+len(facekeys)],facekeys,'meridian',out)
            second={int(k):v for k,v in second0.items()};purge()
            for f,children in second.items():
                if abs(sum(oc.getMass(2,t) for t in children)/base_faces[str(f)]['face_area_mm2']-1)>1e-6:raise ValueError('Meridian source-face area drift '+str(f))
            lineage={f:sorted({t for child in children for t in second[child]}) for f,children in lineage.items()}
        else:second={f:[f] for f in facekeys}
        if len(gmsh.model.getEntities(3))!=430:raise ValueError('Boundary imprint changed volume count')
        for name,tag in names.items():
            if abs(oc.getMass(3,tag)/before[name]['area_or_volume']-1)>1e-7:raise ValueError('Boundary imprint changed source volume '+name)
        records=face_records(names)
        all_lineage={t for cs in lineage.values() for t in cs}
        if all_lineage!=set(map(int,records)):raise ValueError('Untraced boundary after source migration')
        gmsh.write(str(out/'R3_conformal_mm.brep'))
        receipt.update(status='PASS R3 CAD; MESH NOT QUALIFIED',domain_map=names,domains={n:fingerprint(3,t) for n,t in names.items()},
            faces=records,R2_face_descendants={str(f):lineage[str(f)] for f in r2_faces},
            jacket_face_descendants={str(f):dict(jacket_parent[f],faces=lineage[str(f)]) for f in jacket_parent},
            meridian_parent_faces=cuts,base_face_count=len(base_faces),final_face_count=len(records),
            expected_domain_count=430,gas_volume_mm3=gas_volume,jackets_volume_mm3=jacket_volume,
            R2_gas_volume_mm3=r2gas,gas_removed_mm3=r2gas-gas_volume,
            source_jackets=jackets,R2_BREP_sha256=sha(R2/'analysis_conformal_mm.brep'),
            output_BREP_sha256=sha(out/'R3_conformal_mm.brep'),physical_redesign=False,solver_ready=False)
    except Exception as ex:
        receipt.update(status='STOP R3 CAD',error=repr(ex));raise
    finally:
        receipt.update(seconds=time.monotonic()-start,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
        save(out/'geometry_receipt.json',receipt);gmsh.finalize()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);build(p.parse_args().out)
