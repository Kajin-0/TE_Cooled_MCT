"""V7 editorial pass: single upper-left copy cluster, fade transitions,
 restrained camera drift, accurate 2D source tied to real TEC leads.

Blender 4.3 Workbench. Optical fades are implemented by gradual text-material
color interpolation toward the calibrated navy background, not by hiding,
moving or scattering captions. Color transitions must be checked in previews.
No model physics or source CAD geometry is altered.
"""
import bpy,math,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path('/home/User/TE_Cooled_MCT')
D=ROOT/'media/copper_3d_20261112'
OUT=D/'revision07'
OUT.mkdir(parents=True,exist_ok=True)
DESIGN=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
source=json.loads(DESIGN.read_text())
base=json.loads((ROOT/'data/nominal_gas_visibility_v327_20261111/coupled_attempt01/result.json').read_text())
abl=json.loads((ROOT/'data/copper_ablation_publication_20261112/result.json').read_text())
audit=json.loads((ROOT/'data/copper_ablation_publication_20261112/independent_audit.json').read_text())
assert source['body_count']==824 and audit['status'].startswith('PASS')
assert abs(base['calculated_detector_temperature_K']-abl['calculated_detector_temperature_K']-
  7.634421834512921)<1e-8
bodies={b['name']:b for b in source['bodies']}

bpy.ops.wm.open_mainfile(filepath=str(D/'revision06/Brooks_Copper_3D_V6.blend'))
s=bpy.context.scene;cam=s.camera
assert all(bpy.data.objects.get('formed_tab'+str(n)) for n in (58,80,88))
assert all(bpy.data.objects.get(k) for k in ('TEC_lead1','TEC_lead9'))
assert s.render.resolution_x==1080 and s.render.resolution_y==1350
assert s.render.fps==24 and s.frame_end==816

# Remove *all* V6 written content, and previous schematic strokes. Retain
# original geometry and V6 source-anchored animated arrows only.
for o in list(bpy.data.objects):
 if o.name.startswith(('V6_HUD_','V6_2D_')):
  bpy.data.objects.remove(o,do_unlink=True)
assert not any(o.type=='FONT' for o in bpy.data.objects)

# Gentle camera motion that maintains view continuity: ~10% change in lateral
# camera position over entire 34-second cut, not the V6 multi-angle orbit.
# The 2D power-source connection follows the source pin projections each frame.
if cam.animation_data:cam.animation_data_clear()
for frame,xyz in (
 (1,(-16.4,-2.0,11.6)),
 (256,(-15.3,-4.1,11.85)),
 (336,(-14.7,-5.0,12.0)),
 (528,(-13.9,-6.15,12.3)),
 (816,(-13.15,-7.2,12.5))):
 cam.location=xyz;cam.keyframe_insert(data_path='location',frame=frame)
if cam.animation_data and cam.animation_data.action and hasattr(cam.animation_data.action,'fcurves'):
 for fc in cam.animation_data.action.fcurves:
  for kp in fc.keyframe_points:kp.interpolation='BEZIER'

# Physical copper conductance path is still highlighted on authentic ribbons.
# Keep V6 current/thermal trace timing; no additional particle count.
assert len([o for o in bpy.data.objects if o.name.startswith('V6_APPLIED_CURRENT_')])==2
assert len([o for o in bpy.data.objects if o.name.startswith('V6_RETURN_CURRENT_')])==2
assert len([o for o in bpy.data.objects if o.name.startswith('V6_PARASITIC_HEAT_')])==6

# Workbench screenshot background near upper-left ≈rgb(29,39,53).
# Fading materials to calibrated background yields perceived opacity
# transitions in Workbench without switching to expensive Eevee rendering.
HIDDEN=(.041,.067,.099,1.0)
WHITE=(.97,.98,1.0,1.0)
MUTED=(.66,.76,.85,1.0)
CYAN=(.47,.91,1.0,1.0)
GOLD=(1.0,.79,.39,1.0)
def material(name,c):
 m=bpy.data.materials.new(name);m.diffuse_color=c;return m

Z=-6.5
font_bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
font_regular='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
fb=bpy.data.fonts.load(font_bold) if Path(font_bold).exists() else None
fr=bpy.data.fonts.load(font_regular) if Path(font_regular).exists() else None

def matte_fade(mat,color,start,end):
 """One contiguous visibility interval. Smooth ~0.65s fade in and out."""
 fade=16
 keys=[
  (1,HIDDEN),
  (max(1,start-1),HIDDEN),
  (min(816,start+fade),color),
  (max(start+fade,end-fade),color),
  (end,HIDDEN),
  (816,HIDDEN)]
 distinct={}
 for f,c in keys:distinct[f]=c
 for f,c in sorted(distinct.items()):
  mat.diffuse_color=c;mat.keyframe_insert(data_path='diffuse_color',frame=f)
 if mat.animation_data and mat.animation_data.action and hasattr(mat.animation_data.action,'fcurves'):
  for fc in mat.animation_data.action.fcurves:
   for kp in fc.keyframe_points:kp.interpolation='BEZIER'

def label(name,msg,y,size,color,first,last,bold=True):
 cu=bpy.data.curves.new(name,'FONT');cu.body=msg;cu.size=size
 cu.align_x='LEFT'
 f=fb if bold else fr
 if f:cu.font=f
 ob=bpy.data.objects.new('V7_TEXT_'+name,cu)
 bpy.context.collection.objects.link(ob)
 ob.parent=cam;ob.location=(-5.02,y,Z)
 mat=material('V7_TEXT_MAT_'+name,HIDDEN)
 cu.materials.append(mat)
 matte_fade(mat,color,first,last)
 if first>1:
  ob.hide_render=True;ob.keyframe_insert(data_path='hide_render',frame=first-1)
 ob.hide_render=False;ob.keyframe_insert(data_path='hide_render',frame=first)
 ob.keyframe_insert(data_path='hide_render',frame=last)
 if last<816:
  ob.hide_render=True;ob.keyframe_insert(data_path='hide_render',frame=last+1)
 return ob

# ONE copy region, never bottom banners or right-side comparison numbers.
# Brand + heading + supporting metric use a single x coordinate across acts.
label('BRAND','BROOKS PHOTONICS',6.67,.27,MUTED,1,816)
label('A1_HEAD','APPLIED TEC DRIVE',5.80,.54,WHITE,1,252)
label('A1_METRIC','1.49 V DC  /  0.40 A',5.09,.43,CYAN,1,252)
label('A2_HEAD','INTERSTAGE COPPER',5.80,.53,WHITE,274,518)
label('A2_METRIC','87.4 mW  Cu HEAT INPUT',5.09,.43,GOLD,274,518)
label('A2_DETAIL','Into final-stage hot-side ceramic',4.54,.265,MUTED,274,518,False)
label('A3_HEAD','MODELED DETECTOR PENALTY',5.80,.46,WHITE,540,816)
label('A3_METRIC','+7.63 K',5.07,.67,GOLD,540,816)
label('A3_DETAIL','218.69 K ON  /  211.06 K OFF (diagnostic)',4.45,.270,WHITE,540,816,False)
label('A3_POWER','Matched 595.7 mW TEC input',3.97,.255,MUTED,540,816,False)
# Labels do not put provenance in the model; full limitations are documented
# in the report and LinkedIn caption, not crowded into the animation.

# Project the actual endpoints of BOTH terminal leads into the camera plane.
pplus=Vector(bodies['TEC_lead1']['parts'][-1]['b'])
pminus=Vector(bodies['TEC_lead9']['parts'][-1]['b'])
width=cam.data.ortho_scale*s.render.resolution_x/s.render.resolution_y
def proj(p):
 uv=world_to_camera_view(s,cam,p)
 return ((uv.x-.5)*width,(uv.y-.5)*cam.data.ortho_scale)

# Source-anchored 2D diagram stays centered below projected terminals even
# while camera drifts in act1; keyframe actual spline control-point geometry.
def draw(name,count,material_name):
 cu=bpy.data.curves.new(name,'CURVE')
 cu.dimensions='3D';cu.bevel_depth=.016;cu.bevel_resolution=2
 sp=cu.splines.new('POLY');sp.points.add(count-1)
 o=bpy.data.objects.new('V7_VOLTAGE_'+name,cu)
 bpy.context.collection.objects.link(o)
 o.parent=cam;o.location=(0,0,Z+.04)
 mat=material('V7_VOLTAGE_MAT_'+name,HIDDEN)
 cu.materials.append(mat)
 matte_fade(mat,CYAN,1,252)
 o.hide_render=False;o.keyframe_insert(data_path='hide_render',frame=1)
 o.keyframe_insert(data_path='hide_render',frame=252)
 o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=253)
 return o,sp

circ,spcirc=draw('CIRCLE',73,'V7_CYAN')
pos,spP=draw('POS_LEADER',3,'V7_CYAN')
neg,spN=draw('NEG_LEADER',3,'V7_CYAN')
# Short +/- signs are explicitly a symbol, not scattered video captions.
pmark,spPlus=draw('PLUS_VERTICAL',2,'V7_CYAN')
phmark,spPlusHorizontal=draw('PLUS_HORIZONTAL',2,'V7_CYAN')
nmark,spMinus=draw('MINUS',2,'V7_CYAN')
# Animate each 2D line's control points in the camera plane.
def assign_points(sp,pts,f):
 assert len(pts)==len(sp.points)
 for p,(x,y) in zip(sp.points,pts):
  p.co=(x,y,0,1)
  p.keyframe_insert(data_path='co',frame=f)
for f in list(range(1,263,8))+[262]:
 s.frame_set(f)
 bpy.context.view_layer.update()
 x1,y1=proj(pplus);x9,y9=proj(pminus)
 assert x1>x9 and x1-x9>3.9,(f,x1,x9)
 xm=(x1+x9)/2;cy=min(y1,y9)-1.03;r=.315
 assign_points(spcirc,[(xm+r*math.cos(t*2*math.pi/72),
                       cy+r*math.sin(t*2*math.pi/72)) for t in range(73)],f)
 assign_points(spP,[(xm+r,cy),(x1,cy),(x1,y1)],f)
 assign_points(spN,[(xm-r,cy),(x9,cy),(x9,y9)],f)
 assign_points(spPlus,[(xm+.13,cy+.045),(xm+.13,cy+.21)],f)
 assign_points(spPlusHorizontal,[(xm+.048,cy+.13),(xm+.212,cy+.13)],f)
 assign_points(spMinus,[(xm-.21,cy+.13),(xm-.05,cy+.13)],f)
# The source diagram is fully faded before the second text act.
# Actual source lead connection is maintained until the end of act1.
# All V7 positions are fixed in camera space; not attached to floating 3D wires.
assert len([o for o in bpy.data.objects if o.name.startswith('V7_TEXT_')])==10
assert len([o for o in bpy.data.objects if o.name.startswith('V7_VOLTAGE_')])==6
s.frame_set(1)
s.render.image_settings.file_format='PNG'
s.render.filepath=str(OUT/'frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Brooks_Copper_3D_V7.blend'))
print('V7_SCENE_READY',json.dumps({
 'source_bodies':source['body_count'],
 'source_SHA256':hashlib.sha256(DESIGN.read_bytes()).hexdigest(),
 'seconds':34,'fps':24,'camera':'slow single continuous orbit',
 'labels':'one upper-left column, faded material colors',
 'source_symbol':'animated 2D schematic connected to actual lead projections',
 'headline_result_K':audit['nominal_minus_ablation_die_K'],
 'output':str(OUT/'Brooks_Copper_3D_V7.blend')
}),flush=True)

if '--preview' in sys.argv:
 s.render.resolution_percentage=80
 for f in (1,16,75,250,262,276,380,515,530,548,665,812):
  s.frame_set(f);s.render.filepath=str(OUT/f'preview_{f}.png')
  bpy.ops.render.render(write_still=True)
  print('PREVIEW',f,flush=True)
elif '--render' in sys.argv:
 s.render.resolution_percentage=100
 s.render.image_settings.file_format='FFMPEG'
 s.render.ffmpeg.format='MPEG4'
 s.render.ffmpeg.codec='H264'
 s.render.ffmpeg.constant_rate_factor='HIGH'
 s.render.ffmpeg.ffmpeg_preset='GOOD'
 s.render.ffmpeg.audio_codec='NONE'
 s.render.filepath=str(OUT/'Brooks_Photonics_TEC_Cu_3D_V7.mp4')
 bpy.ops.render.render(animation=True)
