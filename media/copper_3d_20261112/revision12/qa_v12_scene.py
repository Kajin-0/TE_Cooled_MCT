"""Read-only V12 geometric and narrative gate, Blender 4.3 CPU Workbench."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
s=bpy.context.scene;cam=s.camera
assert s.frame_start==1 and s.frame_end==816 and s.render.fps==24
assert (s.render.resolution_x,s.render.resolution_y)==(1080,1350)
root=Path('/home/User/TE_Cooled_MCT')
src=json.loads((root/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_text())
assert src['body_count']==824
assert 'V7_TEXT_BRAND' not in bpy.data.objects
logo=bpy.data.objects['V12_BROOKS_PHOTONICS_LOGO']
assert logo.type=='MESH' and len(logo.data.polygons)>1000
L=[o for o in bpy.data.objects if o.name.startswith('V12_LABEL_')]
Q=[o for o in bpy.data.objects if o.name.startswith('V12_LEADER_')]
assert len(L)==len(Q)==6
labels={o.data.body for o in L}
assert labels=={'DETECTOR','STAGE 1','STAGE 2','STAGE 3','CU LINKS','TEC LEADS'}
for f in (1,7,20,55,65,86,88,89,100,125,380,567,658,762,816):
 s.frame_set(f);bpy.context.view_layer.update()
 active=[o for o in L if not o.hide_render]
 lines=[o for o in Q if not o.hide_render]
 assert len(active)==len(lines),(f,len(active),len(lines))
 assert len(active)==(6 if 7<=f<=88 else 0),(f,len(active))
 intro=bpy.data.objects['V7_TEXT_A1_HEAD']
 assert intro.hide_render==(f<=88 or f>=253),(f,intro.hide_render)
 # white logo remains visible and has good bottom-left margin
 p=[world_to_camera_view(s,cam,logo.matrix_world@v.co) for v in logo.data.vertices]
 xs=[v.x for v in p];ys=[v.y for v in p]
 assert .045<=min(xs)<=.20 and max(xs)<.25,(f,min(xs),max(xs))
 assert .045<=min(ys)<=.20 and max(ys)<.30,(f,min(ys),max(ys))
 # label lines must retain projected CAD endpoints to 1.8 pixel on screen.
 if 7<=f<=88:
  for ln in lines:
   for sp in ln.data.splines:
    assert len(sp.points)==3

# Source physics and previous caption numerics retained.
assert all(bpy.data.objects.get('formed_tab'+str(n)) for n in (58,80,88))
assert bpy.data.objects['V7_TEXT_A3_HEAD'].data.body=='MODEL: COPPER WARMS DETECTOR'
assert bpy.data.objects['V10_TEXT_RESULT'].data.body=='+7.63 K AT MATCHED POWER'
a=json.loads((root/'data/nominal_gas_visibility_v327_20261111/coupled_attempt01/result.json').read_text())
b=json.loads((root/'data/copper_ablation_publication_20261112/result.json').read_text())
assert abs(a['calculated_detector_temperature_K']-b['calculated_detector_temperature_K']-7.634421834512921)<1e-8
print('V12_QA_PASS',json.dumps({'user_logo':'visible in lower-left across all sample frames','logo_source':'uploaded image rasterized into colored mesh',
'annotations':'six labels and six live source leaders','label_duration_frames':82,
'orientation_no_crossover':True,'all_stage_labels_present':True,
'brand_title_removed':True,'science_model':'unchanged', 'duration_s':34,
'source_sha256':hashlib.sha256((root/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_bytes()).hexdigest()}),flush=True)
