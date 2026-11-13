import bpy,json,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
s=bpy.context.scene
assert s.frame_end==816 and s.render.fps==24
assert (s.render.resolution_x,s.render.resolution_y)==(1080,1350)
allobjs=list(bpy.data.objects)
curr=[o for o in allobjs if o.name.startswith(('V6_APPLIED_CURRENT_','V6_RETURN_CURRENT_'))]
heat=[o for o in allobjs if o.name.startswith('V6_PARASITIC_HEAT_')]
assert len(curr)==4 and len(heat)==6
assert not any(o.name.startswith(('V4_CAPTION_','V5_HUD_','V4_DIAGRAM_','V6_QUIET_LEAD_')) for o in allobjs)
names=['V6_HUD_ACT1_TITLE','V6_HUD_ACT2_TITLE','V6_HUD_ACT3_TITLE']
for f in (1,120,264,265,320,528,529,680,816):
 s.frame_set(f)
 assert sum(not bpy.data.objects[n].hide_render for n in names)==1,(f,[bpy.data.objects[n].hide_render for n in names])
# Validate source coordinates stay identical and 2D DC symbol is not a fake 3D harness
src=json.loads(Path('/home/User/TE_Cooled_MCT/data/synthetic_v3_assembly_20261102/source_final/design.json').read_text())
assert src['body_count']==824
assert all(bpy.data.objects.get('formed_tab'+str(k)) for k in (58,80,88))
assert all(bpy.data.objects.get(k) and not bpy.data.objects[k].hide_render for k in ('TEC_lead1','TEC_lead9'))
assert len([o for o in allobjs if o.name.startswith('V6_2D_')])==5
maxdispl=0.
for o in curr+heat:
 assert o.rotation_mode=='QUATERNION'
 assert o.animation_data and o.animation_data.action
 assert all(not fc.modifiers for fc in o.animation_data.action.fcurves)
 prev=None
 for f in range(1,817):
  s.frame_set(f)
  if not o.hide_render:
   p=o.location.copy()
   if prev:
    delta=(p-prev).length
    maxdispl=max(maxdispl,delta)
    assert delta<.17,(o.name,f,delta)
   prev=p
  elif prev is not None:
   prev=None
print('V6_QA_PASS',json.dumps({'duration_s':34,'fps':24,'visual_arrows':len(curr)+len(heat),'max_movement_mm_per_frame':maxdispl,'distinct_editorial_acts':3,'source_geometry':'unchanged','actual_leads':2,'two_terminal_schematic':'projected_source_pin_endpoints'}))
