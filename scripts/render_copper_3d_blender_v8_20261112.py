"""V8: direct language and visibly SOURCE-ANCHORED current flowing from the
2D voltage source, into physical TEC+ (pin1), and returning from TEC- (pin9).

Run on the validated V7 Blender scene. Preserve source mesh and all thermal
numerics. Workbench first cut plus optional Cycles still, never a blind long
CPU-Cycles animation. Fixed single copy column and act transitions retained.
"""
import bpy,math,sys,json,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path('/home/User/TE_Cooled_MCT')
D=ROOT/'media/copper_3d_20261112'
OUT=D/'revision08'
OUT.mkdir(parents=True,exist_ok=True)
design=json.loads((ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_text())
source={b['name']:b for b in design['bodies']}
base=json.loads((ROOT/'data/nominal_gas_visibility_v327_20261111/coupled_attempt01/result.json').read_text())
off=json.loads((ROOT/'data/copper_ablation_publication_20261112/result.json').read_text())
audit=json.loads((ROOT/'data/copper_ablation_publication_20261112/independent_audit.json').read_text())
assert design['body_count']==824
assert audit['status'].startswith('PASS')
assert abs(base['calculated_detector_temperature_K']-off['calculated_detector_temperature_K']-
           7.634421834512921)<1e-8
assert source['VIGO_reference_header']['registry']['pinout']['1']=='TEC+'
assert source['VIGO_reference_header']['registry']['pinout']['9']=='TEC-'

bpy.ops.wm.open_mainfile(filepath=str(D/'revision07/Brooks_Copper_3D_V7.blend'))
s=bpy.context.scene;cam=s.camera
assert s.render.fps==24 and s.frame_end==816
assert s.render.resolution_x==1080 and s.render.resolution_y==1350

# Reuse existing single column, fades, and true source projected schematic.
# Change language, not the critical modeled quantities.
wording={
 'V7_TEXT_A1_HEAD':'APPLY DC VOLTAGE',
 'V7_TEXT_A1_METRIC':'1.49 V  /  0.40 A',
 'V7_TEXT_A2_HEAD':'COPPER LINKS CARRY HEAT',
 'V7_TEXT_A2_METRIC':'87.4 mW INTO THE COLDEST STAGE',
 'V7_TEXT_A2_DETAIL':'Net heat into its hot-side ceramic',
 'V7_TEXT_A3_HEAD':'DETECTOR RUNS WARMER',
 'V7_TEXT_A3_METRIC':'+7.63 K',
 'V7_TEXT_A3_DETAIL':'218.69 K with Cu heat path  /  211.06 K without',
 'V7_TEXT_A3_POWER':'Same 595.7 mW TEC power; thermal-off is a model test',
}
for n,msg in wording.items():
 ob=bpy.data.objects.get(n);assert ob,n
 ob.data.body=msg
# No extra captions will be added to the screen; grouping remains unchanged.

# In V7, source-line curves project onto the original two TEC pins.
# V8 generates small luminous pulses on those 2D connections. The animation
# adapts to the slowly moving camera at each key frame to retain exact pin
# alignment. Arrow direction is convention current, not carrier drift.
pplus=Vector(source['TEC_lead1']['parts'][-1]['b'])
pminus=Vector(source['TEC_lead9']['parts'][-1]['b'])
W=cam.data.ortho_scale*s.render.resolution_x/s.render.resolution_y
def projection(p):
 uv=world_to_camera_view(s,cam,p)
 return Vector(((uv.x-.5)*W,(uv.y-.5)*cam.data.ortho_scale,0))
# Need exact polarities as in the actual header registry.
assert pplus.y<pminus.y

# The original 2D strokes are drawn with camera-parent and position z = -6.46.
# These pulse objects are also camera-parented, a small amount in front of
# those line surfaces to prevent z fighting.
pulse_mat=bpy.data.materials.new('V8_SOURCE_CURRENT_CYAN')
pulse_mat.diffuse_color=(.82,.97,1.0,1)
halo_mat=bpy.data.materials.new('V8_SOURCE_CURRENT_HALO')
halo_mat.diffuse_color=(.23,.69,.86,1)
gold_mat=bpy.data.materials.new('V8_TAB_HEAT_AMBER')
gold_mat.diffuse_color=(1.,.81,.41,1)

def source_symbol():
 """Recover centroid/radius from actual camera-space 2D source line each frame."""
 co=bpy.data.objects['V7_VOLTAGE_CIRCLE'].data.splines[0].points
 p0=Vector(co[0].co[:3]);p18=Vector(co[18].co[:3]);p36=Vector(co[36].co[:3])
 cx=(p0.x+p36.x)/2.;cy=(p0.y+p36.y)/2.
 r=(p0-Vector((cx,cy,0))).length
 return cx,cy,r
def smooth_segment(a,b,t):
 return a.lerp(b,max(0,min(1,t)))
def along_poly(points,u):
 """Constant distance along the schematic, with softened corner geometry."""
 P=[Vector(p) for p in points]
 length=[(b-a).length for a,b in zip(P[:-1],P[1:])]
 d=max(0,min(1,u))*sum(length)
 for j,L in enumerate(length):
  if d<=L or j==len(length)-1:
   return P[j].lerp(P[j+1],max(0,min(1,d/L)))
  d-=L
 return P[-1]
def oriented_arrow(name,mat,size):
 bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=size*.42,
                                  radius2=0,depth=size*1.45)
 ob=bpy.context.object;ob.name=name
 ob.parent=cam;ob.rotation_mode='QUATERNION'
 ob.data.materials.append(mat)
 return ob
def visibility(o,start,end):
 if start>1:
  o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=start-1)
 o.hide_render=False;o.keyframe_insert(data_path='hide_render',frame=start)
 o.keyframe_insert(data_path='hide_render',frame=end)
 if end<816:
  o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=end+1)

def make_pulse(direction,start,duration,serial):
 """One pulse from DC symbol -> TEC+ or TEC- -> DC symbol.

 Movement is computed from the *true moving-source 2D leader geometry*, not
 from fake world-space wiring. Every pulse has one nonlooping trajectory.
 """
 end=start+duration
 ob=oriented_arrow(f'V8_CURRENT_{direction}_{serial}',pulse_mat,.18)
 core=oriented_arrow(f'V8_HALO_{direction}_{serial}',halo_mat,.25)
 for frame in range(start,end+1,3):
  s.frame_set(frame);bpy.context.view_layer.update()
  sym=bpy.data.objects['V7_VOLTAGE_CIRCLE'].data.splines[0].points
  # Source center/radius already animated by V7 and stays pinned to model.
  cx,cy,r=source_symbol()
  p1=projection(pplus);p9=projection(pminus)
  if direction=='PLUS':
   pts=[Vector((cx+r,cy,0)),Vector((p1.x,cy,0)),p1]
  else:
   pts=[p9,Vector((p9.x,cy,0)),Vector((cx-r,cy,0))]
  u=(frame-start)/duration
  pos=along_poly(pts,u)
  # Use smoothed tangent across the corner for arrow orientation.
  ta=along_poly(pts,max(0,u-.105))
  tb=along_poly(pts,min(1,u+.105))
  v=tb-ta
  if v.length<1e-9:v=Vector((1,0,0))
  q=v.normalized().to_track_quat('Z','Y')
  for shape in (ob,core):
   shape.location=(pos.x,pos.y,-6.36 if shape is ob else -6.38)
   shape.rotation_quaternion=q
   shape.keyframe_insert(data_path='location',frame=frame)
   shape.keyframe_insert(data_path='rotation_quaternion',frame=frame)
 # Exact terminal placement at end.
 s.frame_set(end);bpy.context.view_layer.update()
 cx,cy,r=source_symbol()
 anchor=projection(pplus if direction=='PLUS' else pminus)
 finish=anchor if direction=='PLUS' else Vector((cx-r,cy,0))
 for shape in (ob,core):
  shape.location=(finish.x,finish.y,-6.36 if shape is ob else -6.38)
  shape.keyframe_insert(data_path='location',frame=end)
  shape.keyframe_insert(data_path='rotation_quaternion',frame=end)
  visibility(shape,start,end)
  if shape.animation_data and hasattr(shape.animation_data.action,'fcurves'):
   for fc in shape.animation_data.action.fcurves:
    if fc.data_path in ('location','rotation_quaternion'):
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 return ob,core

# Six pulses are visually distinct and traverse schematic wires slowly enough
# to track. Each departs the source AFTER a deliberate lead-in. A matching
# pulse on source-defined 3D Cu lead is already rendered by original V6.
# A maximum of two pulses appear concurrently to avoid confusion.
for i,start in enumerate((27,105,184)):
 make_pulse('PLUS',start,57,i)
 make_pulse('RETURN',start+15,57,i)

# Workbench rendering cannot create true light emission. Avoid faking optical
# bloom using 3 overlapping solid cylinders along the physical lead: prior
# revisions showed z-fighting/striping. Pulses give direction on the schematic
# only; existing V6 arrows remain on physical 3D leads.
assert len([o for o in bpy.data.objects if o.name.startswith('V8_CURRENT_')])==6
assert len([o for o in bpy.data.objects if o.name.startswith('V8_HALO_')])==6
assert len([o for o in bpy.data.objects if o.name.startswith('V7_TEXT_')])==10

# Optional shadow-rich original material illumination can be treated as a
# future higher-quality full render. CPU Cycles feasibility was tested as one
# 30% still; full 816 frames would cost many hours and is not claimed here.
s.frame_set(1)
s.render.image_settings.file_format='PNG'
s.render.filepath=str(OUT/'frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Brooks_Copper_3D_V8.blend'))
print('V8_SCENE_READY',json.dumps({
 'source_bodies':design['body_count'],
 'source_sha256':hashlib.sha256((ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_bytes()).hexdigest(),
 'screen_text':'single upper-left cluster; direct engineering language',
 '2D_pulses':6,
 'source_pulses':'two color layered sets on exact projected source lead lines',
 'terminal_polarity':{'1':'TEC+','9':'TEC-'},
 'temperature_penalty_K':audit['nominal_minus_ablation_die_K'],
 'fps':24,'duration_sec':34,
 'file':str(OUT/'Brooks_Copper_3D_V8.blend')
}),flush=True)
if '--preview' in sys.argv:
 s.render.resolution_percentage=80
 for f in (20,43,67,125,209,271,390,560,700):
  s.frame_set(f);s.render.filepath=str(OUT/f'preview_{f}.png')
  bpy.ops.render.render(write_still=True)
  print('PREVIEW_PASS',f,flush=True)
elif '--render' in sys.argv:
 s.render.resolution_percentage=100
 s.render.image_settings.file_format='FFMPEG'
 s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264'
 s.render.ffmpeg.constant_rate_factor='HIGH'
 s.render.ffmpeg.ffmpeg_preset='GOOD'
 s.render.ffmpeg.audio_codec='NONE'
 s.render.filepath=str(OUT/'Brooks_Photonics_TEC_Cu_3D_V8.mp4')
 bpy.ops.render.render(animation=True)
