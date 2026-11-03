"""Independent fresh-import R3 CAD/source/contact/shell audit; no meshing or PDE."""
from pathlib import Path
import argparse,json,time,resource,collections,copy
import numpy as np
import gmsh
from scripts.v3_analysis_r3_geometry import ROOT,R1,R2,read,save,sha,fingerprint


def matches(a,b):
    return (abs(a['area_or_volume']/b['area_or_volume']-1)<1e-7 and
        max(abs(x-y) for x,y in zip(a['center_mm'],b['center_mm']))<1e-6 and
        max(abs(x-y) for x,y in zip(a['bbox_mm'],b['bbox_mm']))<1e-5)

def audit(directory,out):
    if out.exists():raise ValueError('Preserve independent audit')
    out.mkdir(parents=True);start=time.monotonic();result=dict(status='PENDING',no_PDE=True,solver_ready=False)
    receipt=read(directory/'geometry_receipt.json')
    if not receipt['status'].startswith('PASS'):raise ValueError('CAD gate not passed')
    r2=read(R2/'physical_to_analysis_registry.json');laws=read(R2/'domain_face_law_requirements.json')
    physical=read(ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json');byphysical={q['name']:q for q in physical['bodies']}
    oldshell=read(R2/'shell_projection.json');old=read(R1/'face_ownership.json')
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setString('Geometry.OCCTargetUnit','MM')
    try:
        oc=gmsh.model.occ;oc.importShapes(str(directory/'R3_conformal_mm.brep'));oc.synchronize()
        ids={};unused=set(receipt['domains'])
        for dim,t in gmsh.model.getEntities(3):
            fp=fingerprint(3,t);hit=[name for name in unused if matches(fp,receipt['domains'][name])]
            if len(hit)!=1:raise ValueError('Independent volume identity '+str((t,hit)))
            ids[hit[0]]=t;unused.remove(hit[0])
        if unused or len(ids)!=430:raise ValueError('Missing430 domain identities')
        rev={v:k for k,v in ids.items()};signed={}
        for name,t in ids.items():
            for d,f in gmsh.model.getBoundary([(3,t)],combined=False,oriented=True):signed[t,abs(f)]=1 if f>0 else -1
        faces={};old_to_new={};pairfaces=collections.defaultdict(list)
        candidates=collections.defaultdict(list)
        for f,q in receipt['faces'].items():candidates[tuple(sorted(q['owners']))].append((int(f),q))
        for dim,t in gmsh.model.getEntities(2):
            up=sorted(map(int,gmsh.model.getAdjacencies(2,t)[0]))
            if not 1<=len(up)<=2:raise ValueError('Nonmanifold/orphan face')
            owners=[rev[k] for k in up];fp=fingerprint(2,t)
            hit=[f for f,q in candidates[tuple(sorted(owners))] if matches(fp,q)]
            if len(hit)!=1:raise ValueError('Independent face identity '+str((t,hit)))
            if hit[0] in old_to_new:raise ValueError('Duplicate face identity')
            old_to_new[hit[0]]=t
            signs=[signed[k,t] for k in up]
            if len(signs)==2 and sum(signs)!=0:raise ValueError('Nonopposing volume normals')
            if 'CAVITY_GAS' in owners and len(up)!=2:raise ValueError('Open native gas')
            klass=('GAS_SOLID' if 'CAVITY_GAS' in owners else 'SOLID_SOLID') if len(up)==2 else 'EXTERIOR'
            faces[str(t)]=dict(face_tag=t,owners=owners,owner_volume_ids=up,orientation_signs=signs,
                face_area_mm2=fp['area_or_volume'],center_mm=fp['center_mm'],bbox_mm=fp['bbox_mm'],type=gmsh.model.getType(2,t),class_=klass,law_status='UNSET')
            if len(up)==2:pairfaces[tuple(sorted(owners))].append(t)
        if len(old_to_new)!=len(receipt['faces']):raise ValueError('Missing face migration')
        lineage={k:[old_to_new[f] for f in cs] for k,cs in receipt['R2_face_descendants'].items()}
        if len(lineage)!=2422:raise ValueError('R2 parent-face registry lost')
        for parent,children in lineage.items():
            expected=r2['face_registry'][parent]['face_area_mm2']
            if len(children)!=len(set(children)) or abs(sum(faces[str(f)]['face_area_mm2'] for f in children)/expected-1)>1e-6:
                raise ValueError('R2 source-face area not conserved '+parent)
        jparents={k:dict(q,faces=[old_to_new[f] for f in q['faces']]) for k,q in receipt['jacket_face_descendants'].items()}
        shell_regions=[]
        original_faces={q['face_tag']:q for q in old['interface_records']}
        for q in oldshell['mapping']:
            src=original_faces[q['original_lead_polyimide_face']]
            target_center=[x*1000 for x in src['center_m']]
            hit=[(k,j) for k,j in jparents.items() if j['jacket']==q['physical_jacket'] and
                 abs(j['area_or_volume']/q['physical_inner_area_mm2']-1)<1e-6 and
                 np.linalg.norm(np.array(j['center_mm'])-target_center)<1e-5]
            if len(hit)!=1:raise ValueError('Exact physical shell subface identity')
            covered=hit[0][1]['faces'];parent=lineage[str(q['derived_lead_gas_face'])]
            if not set(covered)<=set(parent):raise ValueError('Shell patch not in R2 parent')
            for f in covered:
                if set(faces[str(f)]['owners'])!={q['physical_Cu'],q['physical_jacket']}:raise ValueError('Shell contact ownership')
            bare=sorted(set(parent)-set(covered))
            for f in bare:
                if set(faces[str(f)]['owners'])!={q['physical_Cu'],'CAVITY_GAS'}:raise ValueError('Bare Cu ownership')
            area=sum(faces[str(f)]['face_area_mm2'] for f in covered)
            bare_area=sum(faces[str(f)]['face_area_mm2'] for f in bare)
            if abs(area/q['physical_inner_area_mm2']-1)>1e-6:raise ValueError('Source shell patch area drift')
            if abs(area+bare_area-q['derived_face_area_mm2'])>1e-7:raise ValueError('Partial shell complement wrong')
            shell_regions.append(dict(q,covered_R3_faces=covered,bare_R3_faces=bare,
                exact_covered_mm2=area,exact_bare_mm2=bare_area,
                representation='EXPLICIT_SOURCE_POLYMER_VOLUME; no whole-face average',boundary_quadrature='REAL_CAD_SUBFACES'))
        if sum(q['condition']=='FULL_FACE_MATCH' for q in shell_regions)!=6 or sum(q['condition'].startswith('PARTIAL') for q in shell_regions)!=4:
            raise ValueError('Original6 full/4partial regions lost')
        source_map=copy.deepcopy(r2['source_to_analysis'])
        for source,q in source_map.items():
            if q['name'] in ('lead1_insulation','lead9_insulation'):
                q.update(kind='EXPLICIT_VOLUMETRIC_DIELECTRIC',id=ids[q['name']],no_gas_parallel_path=True)
            else:q['id']=ids[q['name']]
        if len(source_map)!=824:raise ValueError('824-source mapping incomplete')
        contacts=[]
        for i,c in enumerate(physical['explicit_contacts']):
            a,b=source_map[c['a']]['name'],source_map[c['b']]['name']
            if a==b:
                contacts.append(dict(index=i,type='COLLAPSED_COMPOSITE',source=[c['a'],c['b']],source_witness_mm2=c['area']));continue
            ff=pairfaces.get(tuple(sorted((a,b))),[])
            area=sum(faces[str(f)]['face_area_mm2'] for f in ff)
            error=abs(area/c['area']-1)
            if not ff or error>1e-6:raise ValueError('Finite contact area/topology changed '+str(i))
            contacts.append(dict(index=i,type='FINITE_SHARED_FACE',source=[c['a'],c['b']],mapped=[a,b],face_tags=ff,source_witness_mm2=c['area'],new_shared_area_mm2=area,relative_error=error))
        if len(contacts)!=378:raise ValueError('378 finite witnesses missing')
        domains=copy.deepcopy(laws['domain_requirements'])
        for name in ('lead1_insulation','lead9_insulation'):
            domains[name]=dict(material='Polyimide_candidate',sources=[name],stage=None,
                constitutive_requirement='EXPLICIT 15um SOURCE ANNULUS; coefficient UNSET; no parallel gas',law_status='UNSET',solver_ready=False)
        for name,q in domains.items():q['id']=ids[name]
        for n in (1,7,8,9):
            q=domains['pin'+str(n)]
            if q['material']!='EFFECTIVE_AXIAL_KOVAR_NI_AU' or q['z_regions_mm']!=[[-12.7,2.0,'Kovar_pin'],[2.0,2.002,'Ni'],[2.002,2.0035,'Au']]:
                raise ValueError('Homogeneous pin fallback')
        nets={}
        for source,q in source_map.items():
            group=byphysical[source].get('group')
            if isinstance(group,int):nets.setdefault(q['name'],set()).add(group)
        if any(len(g)!=1 for g in nets.values()):raise ValueError('Cross-net condensed domain')
        shorts=[pair for pair in pairfaces if all(n in nets for n in pair) and nets[pair[0]]!=nets[pair[1]]]
        if shorts:raise ValueError('Unintended cross-net conductive adjacency '+str(shorts))
        dielectric={'Glass','Al2O3','EP29LPSP','Sapphire','Polyimide_candidate','ZnSe_candidate','IDEALIZED_CAVITY_GAS'}
        conductive={n for n,q in domains.items() if q['material'] not in dielectric}
        graph={n:set() for n in conductive}
        for a,b in pairfaces:
            if a in conductive and b in conductive:graph[a].add(b);graph[b].add(a)
        def reachable(start,skip=None):
            seen={start};todo=[start]
            while todo:
                x=todo.pop()
                for y in graph[x]:
                    if y!=skip and y not in seen:seen.add(y);todo.append(y)
            return seen
        leg_names=[n for n,q in domains.items() if q['material'] in ('P','N')]
        live=reachable('pin1')
        if 'pin9' not in live or not set(leg_names)<=live:raise ValueError('Open full TEC graph')
        if any('pin9' in reachable('pin1',skip=n) for n in leg_names):raise ValueError('TEC leg bypass')
        if 'pin7' in live or 'pin8' in live or 'pin8' not in reachable('pin7'):raise ValueError('Detector isolation/topology')
        terminals={}
        for f,q in faces.items():
            if len(q['owners'])==1 and q['owners'][0] in ('pin1','pin7','pin8','pin9') and abs(q['bbox_mm'][2]+12.7)<1e-5 and abs(q['bbox_mm'][5]+12.7)<1e-5:
                terminals.setdefault(q['owners'][0],[]).append(int(f))
        if set(terminals)!={'pin1','pin7','pin8','pin9'} or any(len(v)!=1 for v in terminals.values()):raise ValueError('Unique terminal faces lost')
        gas=oc.getMass(3,ids['CAVITY_GAS']);poly=sum(oc.getMass(3,ids[n]) for n in ('lead1_insulation','lead9_insulation'))
        if abs(receipt['R2_gas_volume_mm3']-gas-poly)>1e-7 or abs(poly-.077162028)<1e-7:raise ValueError('Gas displacement double counted')
        result.update(status='PASS R3 CAD/SOURCE/SHELL/GAS MIGRATION; NO PDE',domains=domains,domain_id_map=ids,
          volume_count=len(ids),face_registry=faces,face_count=len(faces),face_class_counts=dict(collections.Counter(q['class_'] for q in faces.values())),
          R2_face_descendants=lineage,jacket_face_descendants=jparents,shell_regions=shell_regions,
          full_shell_regions=6,partial_shell_regions=4,source_to_analysis=source_map,source_contacts=contacts,
          gas_volume_mm3=gas,excluded_polymer_volume_mm3=poly,gas_components=1,
          terminal_faces=terminals,unintended_cross_net_contacts=shorts,every_leg_required_for_series_path=True,
          stage_leg_counts=dict(collections.Counter(str(domains[n]['stage']) for n in leg_names)),
          input_BREP_sha256=sha(directory/'R3_conformal_mm.brep'),old_to_new_faces={str(k):v for k,v in old_to_new.items()},
          physical_redesign=False,geometry_type='Conformal explicit polymer volumes; heterogeneous effective pin caps retained')
        print(result['status'],len(ids),len(faces),'gas',gas,'poly',poly,flush=True)
    except Exception as ex:
        result.update(status='STOP R3 INDEPENDENT CAD AUDIT',error=repr(ex));raise
    finally:
        result.update(seconds=time.monotonic()-start,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
        save(out/'registry.json',result);gmsh.finalize()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--geometry',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();audit(a.geometry,a.out)
