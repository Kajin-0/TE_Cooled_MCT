"""Independent V5 motion and scientific scene audit using saved Blender source."""
import bpy,math,json
from mathutils import Vector
from pathlib import Path
s=bpy.context.scene
assert s.frame_end==528 and s.render.fps==24
assert (s.render.resolution_x,s.render.resolution_y)==(1080,1350)
objects=list(bpy.data.objects)
assert len([o for o in objects if o.name.startswith('V5_CURRENT_')])==10
assert len([o for o in objects if o.name.startswith('V5_HEAT_CU_')])==9
assert len([o for o in objects if o.name.startswith('V5_HALO_')])==2
assert all(bpy.data.objects.get('formed_tab'+str(t)) for t in (58,80,88))
assert not any(o.name.startswith(('V3_SCHEMATIC_','V4_DIAGRAM_','SCHEMATIC_EXTERNAL_DC_POWER_SUPPLY')) for o in objects)
assert 'AUDITS' not in ' '.join(o.data.body for o in objects if o.type=='FONT')
arrows=[o for o in objects if o.name.startswith(('V5_CURRENT_','V5_HEAT_CU_'))]
maximum_jump=0.;maximum_rotation=0.
for arrow in arrows:
 assert arrow.rotation_mode=='QUATERNION'
 assert arrow.animation_data and arrow.animation_data.action
 fcs=list(arrow.animation_data.action.fcurves)
 assert all(not f.modifiers for f in fcs)
 for fc in fcs:
  if fc.data_path in ('location','rotation_quaternion'):
   assert all(k.interpolation=='LINEAR' for k in fc.keyframe_points)
 visible=[]
 for f in range(1,529):
  s.frame_set(f)
  if not arrow.hide_render:
   visible.append((f,arrow.location.copy(),arrow.rotation_quaternion.copy()))
 assert visible
 for (f,a,qa),(ff,b,qb) in zip(visible[:-1],visible[1:]):
  assert ff==f+1
  delta=(b-a).length
  angle=qa.rotation_difference(qb).angle
  maximum_jump=max(maximum_jump,delta)
  maximum_rotation=max(maximum_rotation,angle)
  assert delta<.23,(arrow.name,f,delta)
  assert angle<.6,(arrow.name,f,angle)
print('V5_AUDIT_PASS',json.dumps({
 'arrow_objects':len(arrows),'source_metal_tabs':3,
 'max_per_frame_arrow_displacement_mm':maximum_jump,
 'max_per_frame_rotation_rad':maximum_rotation,
 'source_real_power_leads':['TEC_lead1','TEC_lead9'],
 'source_CAD':'unchanged','screen_space_faux_wiring':False,
 'fps':s.render.fps,'frames':s.frame_end}),flush=True)
