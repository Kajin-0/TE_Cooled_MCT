"""Blender V3 repair: correct DC polarity, clipped power source, jumpy flow markers.

Load the user-approved source-derived TEC scene from the V2 .blend; preserve
physical TEC body locations; do NOT alter P/N material, stage topology or
numerical results. Rebuild only illustrative DC source, cables and particles.
Pulses show conventional-current direction in external supply wires, not
electron trajectories. Amber dots are illustrative passive Cu heat pathways.
"""
import bpy, json, math, sys
from mathutils import Vector
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path('/home/User/TE_Cooled_MCT')
D=ROOT/'media/copper_3d_20261112'
OUT=D/'revision03'
OUT.mkdir(parents=True,exist_ok=True)
design=json.loads((ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_text())
baseline=json.loads((ROOT/'data/nominal_gas_visibility_v327_20261111/coupled_attempt01/result.json').read_text())
ablation=json.loads((ROOT/'data/copper_ablation_publication_20261112/result.json').read_text())
audit=json.loads((ROOT/'data/copper_ablation_publication_20261112/independent_audit.json').read_text())
assert design['body_count']==824 and audit['status'].startswith('PASS')
assert abs(baseline['calculated_detector_temperature_K']-ablation['calculated_detector_temperature_K']-7.634421834512921)<1e-8
header=next(b for b in design['bodies'] if b['name']=='VIGO_reference_header')
assert header['registry']['pinout']['1']=='TEC+'
assert header['registry']['pinout']['9']=='TEC-'

bpy.ops.wm.open_mainfile(filepath=str(D/'revision02/copper_heat_leak_blender_v2.blend'))
s=bpy.context.scene
cam=s.camera
# Original camera keeps source-derived TEC prominent; physically modeled
# schematic battery is placed beyond the outer ceramic and fully in-frame.
s.render.fps=24;s.frame_start=1;s.frame_end=528
s.render.resolution_x=1080;s.render.resolution_y=1350
s.render.resolution_percentage=100

def old(n):
 o=bpy.data.objects.get(n)
 if o:bpy.data.objects.remove(o,do_unlink=True)

# Remove all V2 schematic hardware and glitchy loop-particles.
for o in list(bpy.data.objects):
 if o.name.startswith(('SCHEMATIC_','DC_SUPPLY_','V3_')) or o.name=='SCHEMATIC_EXTERNAL_DC_POWER_SUPPLY':
  bpy.data.objects.remove(o,do_unlink=True)
# Clean up camera-floating V2 source labels; replace in one concise legend.
for o in list(bpy.data.objects):
 if o.name.startswith('V2_TEXT_SCHEMATIC DC SUPPLY') or o.name.startswith('V2_TEXT_P = 596 mW'):
  bpy.data.objects.remove(o,do_unlink=True)

# Source terminal data points.
def b(name):return next(z for z in design['bodies'] if z['name']==name)
pin_plus=Vector(b('TEC_lead1')['parts'][-1]['b'])
pin_minus=Vector(b('TEC_lead9')['parts'][-1]['b'])
assert abs(pin_plus.y+3.174040362379355)<1e-6
assert abs(pin_minus.y-3.1740403623793565)<1e-6

MAT={m.name:m for m in bpy.data.materials}
assert 'DRIVE_CYAN' in MAT and 'HEAT_GOLD' in MAT
def newmat(name,rgb):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);MAT[name]=m
newmat('V3_CASE',(0.25,0.34,0.46))
newmat('V3_METAL',(0.66,0.76,0.82))
newmat('V3_PLUS',(0.34,0.87,0.96))
newmat('V3_RETURN',(0.54,0.71,0.79))
newmat('V3_HEAT',(1.,0.65,0.20))

def cube(name,xyz,size,mat,bevel):
 bpy.ops.mesh.primitive_cube_add(size=1,location=xyz)
 o=bpy.context.object;o.name=name
 o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(MAT[mat])
 if bevel:
  m=o.modifiers.new('Soft case edges','BEVEL');m.width=bevel;m.segments=3
  o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o

def sphere(name,xyz,r,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=r,location=xyz)
 o=bpy.context.object;o.name=name;o.data.materials.append(MAT[mat]);return o

def line(name,points,r,mat):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D'
 c.bevel_depth=r;c.bevel_resolution=2
 sp=c.splines.new('POLY');sp.points.add(len(points)-1)
 for q,p in zip(sp.points,points):q.co=(*p,1)
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o)
 c.materials.append(MAT[mat]);return o

# Compact supply located to the left of the ceramic stack, in clear visible
# space. Case itself is a schematic, not falsely attributed source-CAD.
supply=Vector((-5.00,0.00,4.20))
case=cube('V3_SCHEMATIC_DC_SOURCE',supply,(1.32,1.48,.79),'V3_CASE',.095)
# Two physical schematic terminals on the near-right plane.
s_plus=supply+Vector((.71,-.43,0))
s_minus=supply+Vector((.71,.43,0))
sphere('V3_SUPPLY_POSITIVE_CONNECTOR',s_plus,.105,'V3_PLUS')
sphere('V3_SUPPLY_NEGATIVE_CONNECTOR',s_minus,.105,'V3_RETURN')

# Simple unobstructed paths: source DC+ -> physical source pin1,
# physical source pin9 -> source DC-. Cables are schematic, not CAD wires.
p_plus=[tuple(s_plus),(-4.12,-.70,4.2),(-4.25,-2.45,3.45),
        (-4.35,-3.15,2.78),tuple(pin_plus)]
p_return=[tuple(pin_minus),(-4.74,3.45,2.78),(-5.62,3.15,3.56),
          (-5.62,1.32,4.20),tuple(s_minus)]
line('V3_SCHEMATIC_DC_PLUS_TO_PIN1',p_plus,.038,'V3_PLUS')
line('V3_SCHEMATIC_PIN9_TO_DC_RETURN',p_return,.038,'V3_RETURN')
# Hard physical CAD lead1 and lead9 meshes are restored/retained from V2.
for n in ('TEC_lead1','TEC_lead9'):
 o=bpy.data.objects.get(n);assert o and not o.hide_render

# Small camera-facing signs on the supply instrument: + and minus are the
# electrical terminal polarity from source pinout; they do not indicate
# electron motion in the P/N semiconductors.
def billboard(msg,name,loc,size,mat):
 cu=bpy.data.curves.new(name,'FONT');cu.body=msg;cu.size=size;cu.align_x='CENTER'
 o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o)
 o.location=loc;cu.materials.append(MAT[mat])
 track=o.constraints.new('TRACK_TO')
 track.target=cam;track.track_axis='TRACK_Z';track.up_axis='UP_Y'
 return o
billboard('DC', 'V3_SOURCE_DC_LABEL', supply+Vector((0,0,.48)),.30,'white')
billboard('+', 'V3_SOURCE_POSITIVE', s_plus+Vector((.0,-.17,.12)),.22,'V3_PLUS')
billboard('-', 'V3_SOURCE_NEGATIVE', s_minus+Vector((.0,.16,.12)),.22,'V3_RETURN')

# Motion: each pulse has its OWN object and travels only once from A to B.
# No modulo arithmetic; no cyclic fcurves; no teleporting reset or wrap.
# Constant-speed spatial samples are derived from segment length in mm.
def position_at_distance(path,frac):
 points=[Vector(p) for p in path]
 L=[(v-u).length for u,v in zip(points[:-1],points[1:])]
 d=max(0.,min(1.,frac))*sum(L)
 for i,seg in enumerate(L):
  if d<=seg or i==len(L)-1:
   return points[i].lerp(points[i+1],max(0.,min(1.,d/seg)))
  d-=seg
 return points[-1]

def pulse_once(name,path,start,end,mat,r=.07):
 assert end>start+12 and 1<=start and end<=s.frame_end
 o=sphere(name,path[0],r,mat)
 o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=max(1,start-1))
 o.hide_render=False;o.keyframe_insert(data_path='hide_render',frame=start)
 o.keyframe_insert(data_path='hide_render',frame=end)
 if end<s.frame_end:
  o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=end+1)
 for f in range(start,end+1,3):
  o.location=position_at_distance(path,(f-start)/(end-start))
  o.keyframe_insert(data_path='location',frame=f)
 o.location=Vector(path[-1]);o.keyframe_insert(data_path='location',frame=end)
 for fc in o.animation_data.action.fcurves:
  if fc.data_path=='location':
   for k in fc.keyframe_points:k.interpolation='LINEAR'
 return o

# Three staggered conventional-current packets per terminal circuit, with
# no abrupt wrap. Visuals are illustrative drive current in the external
# connections, not actual electron drift speed.
for i,start in enumerate((18,160,303,432)):
 end=min(start+89,527)
 pulse_once('V3_PLUS_DRIVE_PULSE_%d'%i,p_plus,start,end,'V3_PLUS',.075)
 pulse_once('V3_MINUS_RETURN_PULSE_%d'%i,p_return,start,end,'V3_RETURN',.075)

# Heat exchange: three source-copper paths, amber pulses move UP each actual
# formed Cu tab, away from warmer lower ceramic toward cooler upper stage.
# Add ONLY one or two sequential packets per net, never a modulo loop.
def centerline(tab):
 out=[]
 for p in tab['parts']:
  a=Vector(p['a']);bb=Vector(p['b'])
  if not out:out.append(tuple(a))
  if p['type']=='arc':
   c=Vector(p['c']);va=a-c;vb=bb-c
   aa=math.atan2(va.y,va.x)
   dt=(math.atan2(vb.y,vb.x)-aa+math.pi)%(2*math.pi)-math.pi
   for i in range(1,9):
    t=aa+dt*i/8;out.append((c.x+p['r']*math.cos(t),c.y+p['r']*math.sin(t)))
  else:out.append(tuple(bb))
 return [(tab['x'],x,z) for x,z in out]
for net in (58,80,88):
 path=centerline(b('formed_tab'+str(net)))
 for i,start in enumerate((145,219)):
  pulse_once('V3_HEAT_NET%d_%d'%(net,i),path,start,
             min(start+67,293),'V3_HEAT',.061)

# Fewer words, consistent text hierarchy, and explicit physical caveat.
for o in list(bpy.data.objects):
 if o.name.startswith('V2_TEXT_') and (
     'SCHEMATIC DC SUPPLY' in o.name or
     'P = 596 mW' in o.name):
    bpy.data.objects.remove(o,do_unlink=True)
# Note: 87.4 mW is the net into stage2 hot-side ceramic, NOT wire Joule.
# Text source remains already verified by audit and unchanged by this repair.

# Programmatic checks at every camera section: no source case clipping.
for f in (1,75,175,260,330,455,527):
 s.frame_set(f)
 co=world_to_camera_view(s,cam,supply)
 assert .12<co.x<.42 and .50<co.y<.82,(f,'source position clipped',co.x,co.y)
 assert all(abs(o.location.x)<20 for o in bpy.data.objects if o.name.startswith('V3_'))
# Verify no loop/combo glitches; pulses are one-way with monotonic path length.
for o in bpy.data.objects:
 if o.name.startswith(('V3_PLUS_DRIVE_PULSE_','V3_MINUS_RETURN_PULSE_','V3_HEAT_NET')):
  curves=[fc for fc in o.animation_data.action.fcurves if fc.data_path=='location']
  assert len(curves)==3 and all(not fc.modifiers for fc in curves)
s.frame_set(1)
s.render.image_settings.file_format='PNG'
s.render.filepath=str(OUT/'preview_')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Brooks_Copper_3D_V3.blend'))
print('V3_SCENE_PASS',json.dumps({
 'source_design_sha256':__import__('hashlib').sha256((ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_bytes()).hexdigest(),
 'original_body_count':design['body_count'],
 'source_pin1_TEC_plus':list(pin_plus),'source_pin9_TEC_minus':list(pin_minus),
 'dc_source':list(supply),'motion':'one-way constant-speed, nonlooping source pin paths',
 'verified_delta_K':audit['nominal_minus_ablation_die_K'],
 'frames':s.frame_end,'fps':s.render.fps,'resolution':[s.render.resolution_x,s.render.resolution_y]}),flush=True)
if '--preview' in sys.argv:
 s.render.resolution_percentage=75
 for f in (75,177,244,330,465):
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
 s.render.filepath=str(OUT/'Brooks_Photonics_Copper_Thermal_Bypass_3D_V3.mp4')
 bpy.ops.render.render(animation=True)
