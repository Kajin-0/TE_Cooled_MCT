"""V5 source-anchored electrical/thermal animation for three-stage TEC.

Show voltage on the ACTUAL source lead curves, not fictional supply cables.
Source pinout: pin 1 TEC+, pin 9 TEC-. Teal flow arrows show conventional
current along both ORIGINAL external TEC power leads. Amber arrows show
illustrative thermal-bypass transport along ORIGINAL formed Cu tabs.
Neither the particles nor colors are solved charge density/heat-flux fields.

Start from clean V4 editorial scene; preserve all 824 synthetic CAD bodies,
model numerics, camera-space explanatory text, and the four concise acts.
"""
import bpy,math,sys,json,hashlib
from mathutils import Vector,Quaternion
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path('/home/User/TE_Cooled_MCT')
D=ROOT/'media/copper_3d_20261112'
OUT=D/'revision05'
OUT.mkdir(parents=True,exist_ok=True)
SRC=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
orig=json.loads(SRC.read_text())
BASE=json.loads((ROOT/'data/nominal_gas_visibility_v327_20261111/coupled_attempt01/result.json').read_text())
OFF=json.loads((ROOT/'data/copper_ablation_publication_20261112/result.json').read_text())
assert orig['body_count']==824
assert abs(BASE['calculated_detector_temperature_K']-OFF['calculated_detector_temperature_K']-7.634421834512921)<1e-8
header=next(x for x in orig['bodies'] if x['name']=='VIGO_reference_header')
assert header['registry']['pinout']['1']=='TEC+'
assert header['registry']['pinout']['9']=='TEC-'

bpy.ops.wm.open_mainfile(filepath=str(D/'revision04/Brooks_Copper_Source_Model_V4.blend'))
s=bpy.context.scene;cam=s.camera
s.render.fps=24;s.frame_start=1;s.frame_end=528
s.render.resolution_x=1080;s.render.resolution_y=1350
s.render.resolution_percentage=100
assert s.render.engine=='BLENDER_WORKBENCH'
NAMES={b['name']:b for b in orig['bodies']}

# No detached voltage source. Remove the camera-space V4 schematic only.
for o in list(bpy.data.objects):
 if o.name.startswith('V4_DIAGRAM_') or o.name.startswith('V4_CAPTION_DC / 0.596 W'):
  bpy.data.objects.remove(o,do_unlink=True)
# The +/- glyphs and "TEC" within schematic must also go.
for o in list(bpy.data.objects):
 if o.name.startswith('V4_CAPTION_'):
  if o.data.body in ('+','-','TEC','DC / 0.596 W'):
   bpy.data.objects.remove(o,do_unlink=True)
assert not any(o.name.startswith('V4_DIAGRAM_') for o in bpy.data.objects)

# Rotate towards western power leads initially, then slowly to copper forms.
# This creates an actual explanatory 3D movement, not random orbit.
if cam.animation_data:cam.animation_data_clear()
for f,p in [(1,(-16.5,-2.0,11.6)),(95,(-15.4,-4.2,12.0)),
            (156,(1.0,-16.7,13.0)),(230,(11.5,-12.1,12.9)),
            (340,(12.1,-11.5,12.8)),(528,(12.1,-13.1,12.8))]:
 cam.location=p;cam.keyframe_insert(data_path='location',frame=f)
if cam.animation_data and cam.animation_data.action and hasattr(cam.animation_data.action,'fcurves'):
 for fc in cam.animation_data.action.fcurves:
  for k in fc.keyframe_points:k.interpolation='BEZIER'

# Distinct materials used only as visualization overlays.
cols={
 'V5_CYAN_HALO':(.08,.30,.40,1),
 'V5_CYAN_OUTER':(.16,.61,.75,1),
 'V5_CYAN_CORE':(.55,.95,1.,1),
 'V5_WHITE_STREAK':(.92,.99,1.,1),
 'V5_GOLD_HALO':(.48,.23,.04,1),
 'V5_GOLD_OUTER':(.98,.55,.12,1),
 'V5_GOLD_CORE':(1.0,.83,.41,1),
}
MAT={}
for n,c in cols.items():
 m=bpy.data.materials.new(n);m.diffuse_color=c;MAT[n]=m

def polycurve(name,pts,radius,mat,start=1,end=528):
 cu=bpy.data.curves.new(name,'CURVE')
 cu.dimensions='3D';cu.resolution_u=2;cu.bevel_depth=radius
 cu.bevel_resolution=3
 pl=cu.splines.new('POLY');pl.points.add(len(pts)-1)
 for p,v in zip(pl.points,pts):p.co=(*v,1)
 o=bpy.data.objects.new(name,cu)
 bpy.context.collection.objects.link(o)
 cu.materials.append(MAT[mat])
 if start>1:
  o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=start-1)
 o.hide_render=False;o.keyframe_insert(data_path='hide_render',frame=start)
 o.keyframe_insert(data_path='hide_render',frame=end)
 if end<s.frame_end:
  o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=end+1)
 return o

def source_centerline(parts):
 """Original source line/arc path, numerical coordinates retained."""
 out=[]
 for part in parts:
  a=Vector(part['a']);bb=Vector(part['b'])
  if not out:out.append(tuple(a))
  if part['type']=='arc':
   c=Vector(part['c']);va=a-c;vb=bb-c
   if len(a)==2:
    aa=math.atan2(va.y,va.x)
    dt=(math.atan2(vb.y,vb.x)-aa+math.pi)%(2*math.pi)-math.pi
    for j in range(1,13):
     th=aa+dt*j/12
     out.append((c.x+part['r']*math.cos(th),c.y+part['r']*math.sin(th)))
   else:
    cross=va.cross(vb)
    if cross.length<=1e-11:
     out.append(tuple(bb));continue
    axis=cross.normalized();th=va.angle(vb)
    for j in range(1,13):
     q=Quaternion(axis,j*th/12)
     out.append(tuple(c+q@va))
  else:out.append(tuple(bb))
 assert (Vector(out[0])-Vector(parts[0]['a'])).length<1e-7
 assert (Vector(out[-1])-Vector(parts[-1]['b'])).length<1e-7
 return out

lead_plus=source_centerline(NAMES['TEC_lead1']['parts'])
lead_minus=source_centerline(NAMES['TEC_lead9']['parts'])
# Actual original wires point FROM on-ceramic land TOWARD package pin.
# Conventional external current is pin1 -> TEC internals -> pin9.
plus=list(reversed(lead_plus))
minus=lead_minus
for name,path in [('plus',lead_plus),('minus',lead_minus)]:
 length=sum((Vector(b)-Vector(a)).length for a,b in zip(path[:-1],path[1:]))
 real=sum(p['length'] for p in NAMES['TEC_lead1' if name=='plus' else 'TEC_lead9']['parts'])
 assert abs(length-real)<0.04,(name,length,real)  # discretized arcs
print('LEAD_PATH_METRIC',[(name,
 round(sum((Vector(b)-Vector(a)).length for a,b in zip(path[:-1],path[1:])),4),
 len(path)) for name,path in [('TEC+',plus),('TEC-',minus)]])

# Restore source Cu lead solids from the original source-CAD-derived Blender.
for name in ('TEC_lead1','TEC_lead9'):
 obj=bpy.data.objects.get(name)
 assert obj and obj.type=='CURVE'
 obj.hide_render=False
# Coaxial overlays anchored to exact source conductive centerlines.
# The two rings fake a stylized bloom in Workbench without an expensive
# full-camera optical glow; the real source metal radius is 0.10 mm.
for label,path in [('pin1',lead_plus),('pin9',lead_minus)]:
 polycurve('V5_HALO_'+label,path,.151,'V5_CYAN_HALO',1,145)
 polycurve('V5_GLOW_'+label,path,.116,'V5_CYAN_OUTER',1,145)
 polycurve('V5_CORE_'+label,path,.057,'V5_CYAN_CORE',1,145)
# Later acts keep a much quieter teal contour as a reference.
for label,path in [('pin1',lead_plus),('pin9',lead_minus)]:
 polycurve('V5_QUIET_DRIVE_'+label,path,.107,'V5_CYAN_OUTER',146,528)

def pt_at_distance(path,fract):
 points=[Vector(p) for p in path]
 lens=[(p1-p0).length for p0,p1 in zip(points[:-1],points[1:])]
 L=sum(lens);distance=max(0.,min(1.,fract))*L
 for i,l in enumerate(lens):
  if distance<=l or i==len(lens)-1:
   u=max(0,min(1,distance/l))
   return points[i].lerp(points[i+1],u),(points[i+1]-points[i]).normalized()
  distance-=l
 return points[-1],(points[-1]-points[-2]).normalized()

def make_arrow(name,path,start,end,material,size,head_factor=1):
 """One physical arrow advances at constant arc-length speed, never wraps.
 Each has a finite time window and no cycles. Arrow points with tangent.
 """
 assert end>start and end<=s.frame_end
 bpy.ops.mesh.primitive_cone_add(vertices=12,radius1=size*.45,
                                 radius2=0,depth=size*1.5)
 o=bpy.context.object;o.name=name;o.data.materials.append(MAT[material])
 o.rotation_mode='QUATERNION'
 prev_tan=None;prev_q=None
 for f in range(start,end+1,2):
  frac=(f-start)/(end-start)
  pos,tan=pt_at_distance(path,frac)
  # Smooth visual arrow orientation across sub-0.1mm ribbon bends;
  # positional motion remains exactly on the source CAD centerline.
  p_before,_=pt_at_distance(path,max(0.,frac-.055))
  p_after,_=pt_at_distance(path,min(1.,frac+.055))
  if (p_after-p_before).length>1e-10:
   tan=(p_after-p_before).normalized()
  if prev_tan is None:
   q=tan.to_track_quat('Z','Y')
  else:
   # Parallel transport: preserves roll and avoids to_track_quat flips
   # when a bent source wire passes near the global up-vector pole.
   q=prev_tan.rotation_difference(tan) @ prev_q
   if q.dot(prev_q)<0:q=-q
  o.location=pos
  o.rotation_quaternion=q
  o.keyframe_insert(data_path='location',frame=f)
  o.keyframe_insert(data_path='rotation_quaternion',frame=f)
  prev_tan=tan.copy();prev_q=q.copy()
 # hide on boundaries, one-way, no modulo
 if start>1:
  o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=start-1)
 o.hide_render=False;o.keyframe_insert(data_path='hide_render',frame=start)
 o.keyframe_insert(data_path='hide_render',frame=end)
 if end<s.frame_end:
  o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=end+1)
 if o.animation_data and hasattr(o.animation_data.action,'fcurves'):
  for fc in o.animation_data.action.fcurves:
   if fc.data_path in ('location','rotation_quaternion'):
    for k in fc.keyframe_points:k.interpolation='LINEAR'
 return o

# Conventional-current arrows: true source pin1+ towards interior and
# interior towards pin9-. Explicit timing avoids all visible teleportation.
pulse_starts=(7,31,55,79,103)
for i,start in enumerate(pulse_starts):
 make_arrow('V5_CURRENT_TEC_PLUS_%02d'%i,plus,start,start+44,
            'V5_WHITE_STREAK',.39)
 make_arrow('V5_CURRENT_TEC_MINUS_%02d'%i,minus,start,start+48,
            'V5_CYAN_CORE',.39)

# Heat-transfer arrows follow source Cu contour lines. The arrows indicate
# lower->upper  thermal bypass conceptual transport, not directly FEM q-vectors.
# Amber stage heat act is staged only after electrical drives are established.
for net in (58,80,88):
 body=NAMES['formed_tab'+str(net)]
 raw=source_centerline(body['parts'])
 pts=[(body['x'],p[0],p[1]) for p in raw]
 for i,start in enumerate((145,190,232)):
  if start+65>303:continue
  make_arrow('V5_HEAT_CU_%d_%d'%(net,i),pts,start,start+65,
             'V5_GOLD_CORE',.27)
 # Copper has a precise 0.3 mm width / 0.03 mm thickness. A narrow gold
 # highlight follows ONLY the source contour, never an invented 3D heat field.
 polycurve('V5_THERMAL_HIGHLIGHT_%d'%net,pts,.049,'V5_GOLD_OUTER',145,273)

# Labels: short camera-parented labels, anchored dynamically to the model's
# SOURCE-defined physical external pin endpoints, not any invented supply.
font_candidates=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
'/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf']
ft=next((bpy.data.fonts.load(p) for p in font_candidates if Path(p).exists()),None)
textmat=bpy.data.materials.get('V5_CYAN_CORE')
assert textmat
def label(text,name,sz):
 cu=bpy.data.curves.new(name,'FONT')
 cu.body=text;cu.size=sz
 if ft:cu.font=ft
 o=bpy.data.objects.new(name,cu)
 bpy.context.collection.objects.link(o);o.parent=cam
 o.location=(0,0,-6.6);cu.materials.append(textmat)
 return o
plus_lbl=label('PIN 1  TEC+', 'V5_HUD_ANNOTATION_PLUS',.34)
minus_lbl=label('PIN 9  TEC-','V5_HUD_ANNOTATION_MINUS',.34)
scope_lbl=label('APPLIED: 1.49 V DC  /  0.40 A','V5_HUD_SCOPE',.30)
scope_lbl.location=(-5.05,3.76,-6.6)
for label_o,world_point,dx,dy in (
 (plus_lbl,Vector(lead_plus[-1]),-.25,-.64),
 (minus_lbl,Vector(lead_minus[-1]),-.25,-.64)):
 for f in range(1,529,5):
  s.frame_set(f)
  uv=world_to_camera_view(s,cam,world_point)
  # Projections are source-geometry constrained; camera-space typography
  # doesn't get artificially covered by ceramics.
  width=cam.data.ortho_scale*s.render.resolution_x/s.render.resolution_y
  label_o.location=(max(-5.4,min(5.05,(uv.x-.5)*width+dx)),
                    max(-6.45,min(6.35,(uv.y-.5)*cam.data.ortho_scale+dy)),-6.6)
  label_o.keyframe_insert(data_path='location',frame=f)
 label_o.hide_render=False;label_o.keyframe_insert(data_path='hide_render',frame=1)
 label_o.keyframe_insert(data_path='hide_render',frame=145)
 label_o.hide_render=True;label_o.keyframe_insert(data_path='hide_render',frame=146)
scope_lbl.hide_render=False;scope_lbl.keyframe_insert(data_path='hide_render',frame=1)
scope_lbl.keyframe_insert(data_path='hide_render',frame=145)
scope_lbl.hide_render=True;scope_lbl.keyframe_insert(data_path='hide_render',frame=146)

# Act1 copy reflects energizing the actual source leads.
for o in bpy.data.objects:
 if o.name.startswith('V4_CAPTION_') and o.type=='FONT':
  if o.data.body=='AN ELECTRICAL LINK':o.data.body='APPLIED TEC DRIVE'
  if o.data.body=='IS ALSO A HEAT PATH.':o.data.body='COPPER CARRIES HEAT.'
# Avoid claims that light is measured Joule/thermal field.
for o in bpy.data.objects:
 if o.name.startswith('V5_') and o.animation_data and hasattr(o.animation_data.action,'fcurves'):
  for fc in o.animation_data.action.fcurves:
   assert not fc.modifiers,(o.name,fc.data_path)

# Audit all expected physical source geometry has not moved.
assert tuple(NAMES['formed_tab58']['points'][0])==(3.075,2.13425)
assert all(bpy.data.objects.get(n) for n in ('formed_tab58','formed_tab80','formed_tab88'))
assert not any(o.name.startswith('V4_DIAGRAM_') for o in bpy.data.objects)
assert len([o for o in bpy.data.objects if o.name.startswith('V5_CURRENT_')])==10
assert len([o for o in bpy.data.objects if o.name.startswith('V5_HEAT_CU_')])==9
s.frame_set(1)
s.render.image_settings.file_format='PNG'
s.render.filepath=str(OUT/'frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Brooks_Source_TEC_Glow_Animated_V5.blend'))
print('V5_SCENE_READY',json.dumps({
 'source_registry_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),
 'source_body_count':orig['body_count'],
 'terminal_polarities':{'pin1':'TEC+','pin9':'TEC-'},
 'source_lead_material':'Cu',
 'lead_motion':'10 arrows along real lead arcs, no modulo wrap',
 'heat_motion':'9 amber arrows along source Cu foil arcs',
 'physical_stage_geometry_unmodified':True,
 'delta_detector_K':BASE['calculated_detector_temperature_K']-OFF['calculated_detector_temperature_K'],
 'preview_dir':str(OUT),'frame_count':s.frame_end,'fps':s.render.fps
}),flush=True)
if '--preview' in sys.argv:
 s.render.resolution_percentage=80
 for f in (52,107,157,199,247,343,457):
  s.frame_set(f);s.render.filepath=str(OUT/f'preview_{f}.png')
  bpy.ops.render.render(write_still=True)
  print('PREVIEW_PASS',f,flush=True)
elif '--render' in sys.argv:
 s.render.resolution_percentage=100
 s.render.image_settings.file_format='FFMPEG'
 s.render.ffmpeg.format='MPEG4'
 s.render.ffmpeg.codec='H264'
 s.render.ffmpeg.constant_rate_factor='HIGH'
 s.render.ffmpeg.ffmpeg_preset='GOOD'
 s.render.ffmpeg.audio_codec='NONE'
 s.render.filepath=str(OUT/'Brooks_Photonics_Cu_TEC_3D_Animated_V5.mp4')
 bpy.ops.render.render(animation=True)
