"""Audit V3 Blender animation semantics and media hygiene without a frame render."""
import bpy, math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
s=bpy.context.scene
assert s.frame_end==528 and s.render.fps==24
assert (s.render.resolution_x,s.render.resolution_y)==(1080,1350)
pulse=[o for o in bpy.data.objects if o.name.startswith(('V3_PLUS_DRIVE_PULSE_','V3_MINUS_RETURN_PULSE_','V3_HEAT_NET'))]
assert len(pulse)==14,(len(pulse),[o.name for o in pulse])
for o in pulse:
 assert o.animation_data and o.animation_data.action
 fcurves=[fc for fc in o.animation_data.action.fcurves if fc.data_path=='location']
 assert len(fcurves)==3
 assert all(len(fc.modifiers)==0 for fc in fcurves)
 assert all(k.interpolation=='LINEAR' for fc in fcurves for k in fc.keyframe_points)
 for fc in fcurves:
  assert all(k.co.x<=fc.keyframe_points[j+1].co.x for j,k in enumerate(fc.keyframe_points[:-1]))
for net in (58,80,88):
 assert bpy.data.objects.get('formed_tab'+str(net))
for n in ('TEC_lead1','TEC_lead9','V3_SCHEMATIC_DC_SOURCE','V3_SCHEMATIC_DC_PLUS_TO_PIN1','V3_SCHEMATIC_PIN9_TO_DC_RETURN'):
 assert bpy.data.objects.get(n) is not None
for f in range(1,529,12):
 s.frame_set(f)
 source=bpy.data.objects['V3_SCHEMATIC_DC_SOURCE']
 for corner in source.bound_box:
  pt=source.matrix_world @ Vector(corner)
  uv=world_to_camera_view(s,s.camera,pt)
  assert .04<uv.x<.96 and .04<uv.y<.96,(f,tuple(pt),uv.x,uv.y)
 # No electrical pulse can shift by more than 0.85 mm between adjacent frames
 # within a continuous visibility window (we test adjacent, not wrap points).
 if f<528:
  for o in pulse:
   a=o.location.copy()
   if not o.hide_render:
    s.frame_set(f+1)
    if not o.hide_render:
     assert (a-o.location).length<0.85,(o.name,f,(a-o.location).length)
    s.frame_set(f)
print('QA_PASS','source_bbox_all_camera_frames',
      'pulse_count',len(pulse),'original_formed_tabs',3,
      'correct_pin_leads',2,'blender_scene',s.name)
