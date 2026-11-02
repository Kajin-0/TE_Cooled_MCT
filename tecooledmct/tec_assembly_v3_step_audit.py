"""Independent imported-BRep contacts/overlap audit, no mesh or PDE.

SI reader first establishes physical units. This second fresh MM reader uses
millimetres for robust thin-film Boolean tolerances; no author is invoked.
"""
import argparse,itertools,json,time,math
from pathlib import Path
from tecooledmct.tec_assembly_v3_audit import bb_overlap

def certified_separation(a,b):
    """Conservative source envelopes, tied to independent imported identities.

    A sampled curve with maximum arc-step h is enclosed by balls of radius
    tube radius+h/2 about samples (arc length bounds Euclidean distance).
    A tab uses its exact X slab and analogous YZ capsule enclosure.
    """
    from tecooledmct.tec_assembly_v3 import samples
    for curved,other in ((a,b),(b,a)):
        box=other['bbox_mm']
        if curved['shape']=='annulus' and curved['base'][:2]==[0,0]:
            bound=max(math.hypot(x,y) for x in (box[0],box[3]) for y in (box[1],box[4]))
            if bound<curved.get('inner_radius',0)-1e-6:return 'inside annular void'
        if curved['shape'] not in ('wire','tab'):continue
        ss=samples(curved['parts'],.025);radius=curved['radius'] if curved['shape']=='wire' else curved['thickness']/2
        gap=math.inf
        for point,_ in ss:
            if curved['shape']=='wire':
                distance=math.sqrt(sum(max(box[i]-point[i],0,point[i]-box[i+3])**2 for i in range(3)))
            else:
                dx=max(box[0]-(curved['x']+curved['width']/2),0,(curved['x']-curved['width']/2)-box[3])
                distance=math.sqrt(dx*dx+sum(max(box[i+1]-point[i],0,point[i]-box[i+4])**2 for i in range(2)))
            gap=min(gap,distance-radius-.025/2)
        if gap>1e-6:return 'positive conservative curve-envelope clearance'
    return None

def main(cad,src,out):
    import gmsh
    if out.exists():raise ValueError('Preserve previous audit')
    start=time.monotonic();d=json.loads((src/'design.json').read_text());a=json.loads((src/'contact_audit.json').read_text())
    si=json.loads((cad/'si_reader.json').read_text());by={b['name']:b for b in d['bodies']}
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setString('Geometry.OCCTargetUnit','MM')
    result=dict(status='PENDING',contacts=[],overlap_tests=[],separation_certificates=[],seconds=None)
    try:
        occ=gmsh.model.occ;tags=occ.importShapes(str(cad/'synthetic_v3_mm.step'));occ.synchronize()
        # Reader identity is independently re-established from volume and approximate bounds;
        # wire torus bounds are conservative, then exact support distances resolve them.
        from tecooledmct.tec_assembly_v3 import support_planes,tight_bounds
        remain={t for dim,t in tags if dim==3};ident={};planes=support_planes(occ)
        cache={t:(occ.getMass(3,t),occ.getBoundingBox(3,t)) for t in remain}
        for b in d['bodies']:
            candidates=[t for t in remain if abs(cache[t][0]/b['volume_mm3']-1)<1e-7 and max(abs(x-y) for x,y in zip(cache[t][1],b['bbox_mm']))<.2]
            if b['shape']=='wire':candidates=[t for t in candidates if max(abs(x-y) for x,y in zip(tight_bounds(occ,t,planes),b['bbox_mm']))<.00021]
            else:candidates=[t for t in candidates if max(abs(x-y) for x,y in zip(cache[t][1],b['bbox_mm']))<.00021]
            if len(candidates)!=1:raise ValueError('Independent identity '+b['name'])
            ident[b['name']]=candidates[0];remain.remove(candidates[0])
        print('identity complete',len(ident),flush=True)
        boundaries={name:gmsh.model.getBoundary([(3,t)],False,False) for name,t in ident.items()}
        face_boxes={t:occ.getBoundingBox(dim,t) for fs in boundaries.values() for dim,t in fs}
        for iw,w in enumerate(a['witnesses']):
            dist=[]
            for name in (w['a'],w['b']):
                hits=[t for dim,t in boundaries[name] if all(face_boxes[t][i]-2e-7<=w['point_mm'][i]<=face_boxes[t][i+3]+2e-7 for i in range(3)) and gmsh.model.isInside(2,t,w['point_mm'],False)>0]
                dist.append(0. if hits else float('inf'))
            if iw%100==0:print('contact',iw,flush=True)
            if max(dist)>2e-7:raise ValueError('Imported contact missing '+str(w)+' distance '+str(dist))
            result['contacts'].append(dict(a=w['a'],b=w['b'],trimmed_face_membership=True,source_area_mm2=w['area_mm2']))
        # Source box/box intersection exact. All curved / header / fillet pairs
        # with positive AABB intersection are independently Boolean-intersected.
        print('contacts complete',len(result['contacts']),flush=True)
        for aa,bb in itertools.combinations(d['bodies'],2):
            if aa['shape']==bb['shape']=='boxes':continue
            spans=[min(aa['bbox_mm'][i+3],bb['bbox_mm'][i+3])-max(aa['bbox_mm'][i],bb['bbox_mm'][i]) for i in range(3)]
            if min(spans)<=1e-7:continue
            certificate=certified_separation(aa,bb)
            if certificate:
                result['separation_certificates'].append(dict(a=aa['name'],b=bb['name'],certificate=certificate));continue
            print('overlap',aa['name'],bb['name'],flush=True)
            copies=occ.copy([(3,ident[aa['name']]),(3,ident[bb['name']])])
            q=occ.intersect(copies[:1],copies[1:])[0]
            volume=sum(occ.getMass(dim,t) for dim,t in q if dim==3)
            if q:occ.remove(q,recursive=True)
            # Absolute 1e-12mm3 is below smallest modeled 50nm film volume.
            result['overlap_tests'].append(dict(a=aa['name'],b=bb['name'],volume_mm3=volume))
            if volume>1e-12:raise ValueError('Positive imported solid overlap '+str(result['overlap_tests'][-1]))
        result.update(status='PASS imported boundary witnesses and curved-body exclusivity',body_count=len(ident),independent_contacts=len(result['contacts']),curved_overlap_pairs=len(result['overlap_tests']),SI_STEP_sha256=si['STEP_sha256'])
    except Exception as e:
        result.update(status='FAIL',error=repr(e));raise
    finally:
        result['seconds']=time.monotonic()-start;out.write_text(json.dumps(result,indent=2)+'\n');gmsh.finalize()
    print({k:v for k,v in result.items() if k not in ('contacts','overlap_tests','separation_certificates')})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cad',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.cad,a.source,a.out)
