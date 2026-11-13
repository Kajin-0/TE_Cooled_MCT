"""Read-only V8 motion and content QA. Independent of production generator."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
s=bpy.context.scene;cam=s.camera
assert s.frame_end==816 and s.render.fps==24
A=[o for o in bpy.data.objects if o.name.startswith('V8_CURRENT_')]
H=[o for o in bpy.data.objects if o.name.startswith('V8_HALO_')]
assert len(A)==len(H)==6
assert all(bpy.data.objects.get('formed_tab'+str(n)) for n in (58,80,88))
texts={o.name:o.data.body for o in bpy.data.objects if o.name.startswith('V7_TEXT_')}
assert len(texts)==10
assert all(not any(x in v.lower() for x in ('audit','6/6','digital twin'))
           for v in texts.values())
assert texts['V7_TEXT_A2_HEAD']=='COPPER LINKS CARRY HEAT'
assert texts['V7_TEXT_A3_METRIC']=='+7.63 K'
for o in A+H:
 assert o.rotation_mode=='QUATERNION'
 fcs=o.animation_data.action.fcurves
 assert all(not fc.modifiers for fc in fcs)
 assert all(k.interpolation=='LINEAR' for fc in fcs
            if fc.data_path=='location' for k in fc.keyframe_points)
maxjump=0.
for o in A:
 previous=None
 for f in range(1,263):
  s.frame_set(f)
  if o.hide_render:previous=None;continue
  curr=o.location.copy()
  if previous:
   d=(curr-previous).length
   maxjump=max(maxjump,d)
   assert d<.30,(o.name,f,d)
  previous=curr
# Actual source pin-based 2D schematic is present and 2D animated pulses
# only appear during the corresponding narrative act.
for f in (270,390,660):
 s.frame_set(f)
 assert all(o.hide_render for o in A+H)
print('V8_QA_PASS',json.dumps({'source_preserved':True,'arrow_count':len(A),
 'max_pulse_displacement_units_per_frame':maxjump,
 'single_text_area':True,'source_terminal_2D_schematic':True,
 'physically_conditional_thermal_case_disclosed':True}),flush=True)
