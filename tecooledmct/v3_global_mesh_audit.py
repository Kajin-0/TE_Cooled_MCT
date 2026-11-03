"""Strict arithmetic surface-mesh area gate; independent of Gmsh and any PDE."""
from __future__ import annotations
from collections import Counter
import math

def validate_face_area_records(faces, measured_by_face, threshold=0.01):
    """Reject missing, duplicated, nonpositive, or >tolerance CAD/mesh face areas."""
    if not 0<threshold<1:
        raise ValueError('invalid area tolerance')
    if not faces:
        raise ValueError('empty face registry')
    ids=[int(f['face_tag']) for f in faces]
    if len(set(ids))!=len(ids) or set(ids)!=set(measured_by_face):
        raise ValueError('missing, duplicate, or extra faces')
    rows=[]
    for f in faces:
        tag=int(f['face_tag'])
        data=measured_by_face[tag]
        mesh_area=float(data['mesh_area_mm2'])
        CAD_area=float(f['area_m2'])*1e6
        count=int(data['triangles'])
        if not math.isfinite(mesh_area) or not math.isfinite(CAD_area) or mesh_area<=0 or CAD_area<=0 or count<=0:
            raise ValueError('invalid face area/triangles for '+str(tag))
        diff=mesh_area/CAD_area-1.0
        rows.append({'face_tag':tag,'interface_class':f['interface_class'],
          'owners':[q['source_name'] for q in f['owners']],
          'CAD_mm2':CAD_area,'mesh_mm2':mesh_area,'signed_error_relative':diff,
          'absolute_error_relative':abs(diff),'triangles':count,'pass':abs(diff)<=threshold})
    failed=sorted((x for x in rows if not x['pass']),key=lambda x:-x['absolute_error_relative'])
    return {
        'status':'PASS SURFACE FACE AREA GATE' if not failed else 'FAIL SURFACE FACE AREA GATE',
        'face_count':len(rows),'fail_count':len(failed),'pass_count':len(rows)-len(failed),
        'threshold_relative':threshold,
        'triangle_count':sum(x['triangles'] for x in rows),
        'max_absolute_error_relative':max(x['absolute_error_relative'] for x in rows),
        'top_failures':failed[:30],
        'by_interface':{k:{'faces':sum(x['interface_class']==k for x in rows),
          'fail':sum(x['interface_class']==k for x in failed)} for k in sorted(set(x['interface_class'] for x in rows))},
        'solver_release':False,
        'note':'No 3D volume mesh or physics release is implied by a passing surface gate'
    }
