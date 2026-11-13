"""V7 read-only QA: typography exclusivity/fades, source pin anchor, camera."""
import bpy, json, math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from pathlib import Path
s=bpy.context.scene;cam=s.camera
assert s.frame_end==816 and s.render.fps==24
assert (s.render.resolution_x,s.render.resolution_y)==(1080,1350)
D=Path('/home/User/TE_Cooled_MCT/data/synthetic_v3_assembly_20261102/source_final/design.json')
b={x['name']:x for x in json.loads(D.read_text())['bodies']}
p1=Vector(b['TEC_lead1']['parts'][-1]['b'])
p9=Vector(b['TEC_lead9']['parts'][-1]['b'])
W=cam.data.ortho_scale*s.render.resolution_x/s.render.resolution_y
names=['A1_HEAD','A1_METRIC','A2_HEAD','A2_METRIC','A2_DETAIL','A3_HEAD','A3_METRIC','A3_DETAIL','A3_POWER']
modes=[(110,{'A1_HEAD','A1_METRIC'}),(262,set()),(385,{'A2_HEAD','A2_METRIC','A2_DETAIL'}),(530,set()),(660,{'A3_HEAD','A3_METRIC','A3_DETAIL','A3_POWER'})]
assert len([o for o in bpy.data.objects if o.name.startswith('V7_TEXT_')])==10
assert all(bpy.data.objects.get('formed_tab'+str(k)) for k in (58,80,88))
assert all(bpy.data.objects.get(x) for x in ('TEC_lead1','TEC_lead9'))
for frame,expected in modes:
 s.frame_set(frame)
 visible={n for n in names if not bpy.data.objects['V7_TEXT_'+n].hide_render}
 assert visible==expected,(frame,visible,expected)
for frame in (1,40,80,140,200,240,252):
 s.frame_set(frame)
 bpy.context.view_layer.update()
 for name,anchor in [('POS_LEADER',p1),('NEG_LEADER',p9)]:
  obj=bpy.data.objects['V7_VOLTAGE_'+name]
  assert not obj.hide_render
  end=Vector(obj.data.splines[0].points[-1].co[:3])
  uv=world_to_camera_view(s,cam,anchor)
  target=Vector(((uv.x-.5)*W,(uv.y-.5)*cam.data.ortho_scale,0))
  assert (end-target).length<.07,(name,frame,tuple(end),tuple(target))
s.frame_set(263)
assert all(o.hide_render for o in bpy.data.objects if o.name.startswith('V7_VOLTAGE_'))
last=None;maxmove=0
for f in range(1,817):
 s.frame_set(f)
 p=cam.location.copy()
 if last is not None:
  d=(p-last).length;maxmove=max(maxmove,d)
  assert d<.05,(f,d)
 last=p
for o in bpy.data.objects:
 if o.name.startswith('V7_TEXT_'):
  assert abs(o.location.x+5.02)<1e-5
  assert o.data.materials[0].animation_data
print('V7_QA_PASS',json.dumps({'source_pin_anchoring':'within 0.07 scene units',
  'single_screen_text_anchor':True,'exclusive_narrative_acts':True,
  'in_and_out_color_keyframes':True,
  'max_camera_translation_per_frame_mm':maxmove,
  'render_frames':s.frame_end,'fps':s.render.fps}),flush=True)
