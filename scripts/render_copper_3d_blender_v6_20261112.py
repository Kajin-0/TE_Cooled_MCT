"""V6 — slower three-beat Blender TEC animation, fixed-screen editorial labels.

Original source-derived 3D geometry and numerics unchanged.
Act 1 (0-11s): physical Cu feed leads illuminated; conventional current arrows
move slowly on ORIGINAL source lead arcs. A genuine two-terminal **2D voltage
source symbol** and tidy 2D connections tie to the projected actual source
pin1+/pin9− endpoints (not new 3D cables / a fake instrument).
Act 2 (11-22s): physical copper bypass tabs glow amber; 1D arrows travel only
on actual source centerlines; disclosure: conceptual heat path not a 3D field.
Act 3 (22-34s): fixed-layout quantitative comparison at equal terminal power.
No audit-count headlines. No orbit while the electrical schematic is active.
"""
import bpy,math,sys,json,hashlib
from mathutils import Vector,Quaternion
from bpy_extras.object_utils import world_to_camera_view
from pathlib import Path

ROOT=Path('/home/User/TE_Cooled_MCT')
D=ROOT/'media/copper_3d_20261112'
OUT=D/'revision06'
OUT.mkdir(parents=True,exist_ok=True)
DESIGN=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
B=json.loads(DESIGN.read_text())
source={q['name']:q for q in B['bodies']}
base=json.loads((ROOT/'data/nominal_gas_visibility_v327_20261111/coupled_attempt01/result.json').read_text())
abl=json.loads((ROOT/'data/copper_ablation_publication_20261112/result.json').read_text())
audit=json.loads((ROOT/'data/copper_ablation_publication_20261112/independent_audit.json').read_text())
assert B['body_count']==824 and audit['status'].startswith('PASS')
assert abs(base['calculated_detector_temperature_K']-abl['calculated_detector_temperature_K']-
  7.634421834512921)<1e-8
reg=source['VIGO_reference_header']['registry']['pinout']
assert reg['1']=='TEC+' and reg['9']=='TEC-'

bpy.ops.wm.open_mainfile(filepath=str(D/'revision05/Brooks_Source_TEC_Glow_Animated_V5.blend'))
s=bpy.context.scene;cam=s.camera
s.frame_start=1;s.frame_end=816;s.render.fps=24;s.frame_step=1
s.render.resolution_x=1080;s.render.resolution_y=1350;s.render.resolution_percentage=100
# Delete only explanatory artwork from V4/V5; source bodies remain untouched.
for o in list(bpy.data.objects):
 if o.type=='FONT' or o.name.startswith(('V4_DIAGRAM_','V5_','EXPLANATORY_HEAT_MARKER_')):
  bpy.data.objects.remove(o,do_unlink=True)
assert all(bpy.data.objects.get('formed_tab'+str(n)) for n in (58,80,88))
assert all(bpy.data.objects.get(n) for n in ('TEC_lead1','TEC_lead9'))
for n in ('TEC_lead1','TEC_lead9'):
 bpy.data.objects[n].hide_render=False

# Stable camera for electrical explanation, restrained 3-second transition,
# then a single fixed reading angle for both heat and result sections.
if cam.animation_data:cam.animation_data_clear()
for frame,loc in ((1,(-16.4,-2.0,11.6)),(264,(-16.4,-2.0,11.6)),
                  (345,(11.8,-11.5,12.8)),(528,(11.8,-11.5,12.8)),
                  (816,(11.8,-11.5,12.8))):
 cam.location=loc;cam.keyframe_insert(data_path='location',frame=frame)
if cam.animation_data and hasattr(cam.animation_data.action,'fcurves'):
 for fc in cam.animation_data.action.fcurves:
  for kp in fc.keyframe_points:kp.interpolation='BEZIER'

# Copper material remains copper-colored; any animated highlights refer to
# visual selection, not fabricated solved temperature values.
for m in bpy.data.materials:
 if m.name=='Cu_hot':
  if m.animation_data:m.animation_data_clear()
  m.diffuse_color=(.91,.51,.25,1)
palette={
 'V6_WHITE':(.97,.98,.99,1),
 'V6_MUTED':(.64,.74,.83,1),
 'V6_CYAN':(.47,.91,1,1),
 'V6_CYAN_SOFT':(.17,.58,.73,1),
 'V6_CYAN_HALO':(.08,.32,.41,1),
 'V6_GOLD':(1,.78,.32,1),
 'V6_GOLD_SOFT':(.83,.41,.12,1),
}
MAT={}
for name,col in palette.items():
 m=bpy.data.materials.new(name);m.diffuse_color=col;MAT[name]=m

def show(obj,first,last):
 assert 1<=first<=last<=816
 if first>1:
  obj.hide_render=True;obj.keyframe_insert(data_path='hide_render',frame=first-1)
 obj.hide_render=False;obj.keyframe_insert(data_path='hide_render',frame=first)
 obj.keyframe_insert(data_path='hide_render',frame=last)
 if last<816:
  obj.hide_render=True;obj.keyframe_insert(data_path='hide_render',frame=last+1)

def curve3(name,points,radius,mat,first,last):
 c=bpy.data.curves.new(name,'CURVE')
 c.dimensions='3D';c.resolution_u=1;c.bevel_depth=radius;c.bevel_resolution=3
 sp=c.splines.new('POLY');sp.points.add(len(points)-1)
 for v,pt in zip(sp.points,points):v.co=(*pt,1)
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o)
 c.materials.append(MAT[mat]);show(o,first,last)
 return o

def sample(parts):
 out=[]
 for seg in parts:
  a=Vector(seg['a']);b=Vector(seg['b'])
  if not out:out.append(tuple(a))
  if seg['type']=='arc':
   c=Vector(seg['c']);va=a-c;vb=b-c
   if len(a)==2:
    theta=math.atan2(va.y,va.x)
    d=(math.atan2(vb.y,vb.x)-theta+math.pi)%(2*math.pi)-math.pi
    for j in range(1,17):
     t=theta+d*j/16
     out.append((c.x+seg['r']*math.cos(t),c.y+seg['r']*math.sin(t)))
   else:
    axis=va.cross(vb)
    if axis.length<1e-9:out.append(tuple(b));continue
    angle=va.angle(vb)
    for j in range(1,17):
     out.append(tuple(c+Quaternion(axis.normalized(),angle*j/16)@va))
  else:out.append(tuple(b))
 assert (Vector(out[0])-Vector(parts[0]['a'])).length<1e-7
 assert (Vector(out[-1])-Vector(parts[-1]['b'])).length<1e-7
 return out

lead1=sample(source['TEC_lead1']['parts'])
lead9=sample(source['TEC_lead9']['parts'])
# Source lead geometry runs from P/N ceramic to package pin; conventional
# electrical input runs from TEC+ pin 1 into cooler, TEC− return to pin 9.
plus=list(reversed(lead1))
minus=lead9
for n,path in (('pin1',lead1),('pin9',lead9)):
 curve3('V6_CURRENT_HALO_'+n,path,.150,'V6_CYAN_HALO',1,264)
 curve3('V6_CURRENT_GLOW_'+n,path,.118,'V6_CYAN_SOFT',1,264)
 curve3('V6_CURRENT_CORE_'+n,path,.054,'V6_CYAN',1,264)
 # After the electrical act, leave the original source-defined lead visible.
 # Avoid overlapping nearly coplanar cylinder surfaces that create striping.

# Distance-parametric paths avoid apparent speed changes near source bends.
def at(path,t):
 pts=[Vector(p) for p in path]
 lengths=[(b-a).length for a,b in zip(pts[:-1],pts[1:])]
 d=max(0.,min(1.,t))*sum(lengths)
 for i,L in enumerate(lengths):
  if d<=L or i==len(lengths)-1:
   p=pts[i].lerp(pts[i+1],max(0,min(1,d/L)))
   return p
  d-=L
 return pts[-1]
def new_arrow(name,path,first,last,material,size):
 bpy.ops.mesh.primitive_cone_add(vertices=12,radius1=size*.42,radius2=0,depth=size*1.4)
 obj=bpy.context.object;obj.name=name;obj.data.materials.append(MAT[material])
 obj.rotation_mode='QUATERNION'
 prev_t=None;prev_q=None
 for f in range(first,last+1,3):
  t=(f-first)/(last-first)
  pos=at(path,t)
  ta=at(path,max(0.,t-.075));tb=at(path,min(1.,t+.075))
  tangent=(tb-ta).normalized()
  if prev_t is None:q=tangent.to_track_quat('Z','Y')
  else:
   q=prev_t.rotation_difference(tangent)@prev_q
   if q.dot(prev_q)<0:q=-q
  obj.location=pos;obj.rotation_quaternion=q
  obj.keyframe_insert(data_path='location',frame=f)
  obj.keyframe_insert(data_path='rotation_quaternion',frame=f)
  prev_t=tangent.copy();prev_q=q.copy()
 if (last-first)%3!=0:
  obj.location=at(path,1);obj.keyframe_insert(data_path='location',frame=last)
  obj.keyframe_insert(data_path='rotation_quaternion',frame=last)
 for fc in obj.animation_data.action.fcurves:
  if fc.data_path in ('location','rotation_quaternion'):
   for k in fc.keyframe_points:k.interpolation='LINEAR'
 show(obj,first,last)
 return obj
# Two deliberate slow passes, no wrap/teleport/glitch.
for j,start in enumerate((27,113)):
 new_arrow('V6_APPLIED_CURRENT_PIN1_'+str(j),plus,start,start+132,'V6_WHITE',.34)
 new_arrow('V6_RETURN_CURRENT_PIN9_'+str(j),minus,start,start+132,'V6_CYAN',.34)

# Six amber tracers (two per source copper tab) follow each source arc.
for net in (58,80,88):
 tab=source['formed_tab'+str(net)]
 path=[(tab['x'],p[0],p[1]) for p in sample(tab['parts'])]
 curve3('V6_HEAT_HIGHLIGHT_NET'+str(net),path,.055,'V6_GOLD_SOFT',322,528)
 for j,start in enumerate((347,400)):
  new_arrow('V6_PARASITIC_HEAT_NET%d_%d'%(net,j),path,start,start+120,'V6_GOLD',.28)

# Fixed-position editorial text and a 2D symbol. No moving text chasing leads.
Z=-6.5
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
font=bpy.data.fonts.load(fontpath) if Path(fontpath).exists() else None
def hud(msg,name,x,y,size,mat,first=1,last=816,align='LEFT'):
 cu=bpy.data.curves.new(name,'FONT');cu.body=msg;cu.size=size;cu.align_x=align
 if font:cu.font=font
 o=bpy.data.objects.new('V6_HUD_'+name,cu)
 bpy.context.collection.objects.link(o);o.parent=cam;o.location=(x,y,Z)
 cu.materials.append(MAT[mat]);show(o,first,last)
 return o
def screen_line(name,points,mat,r=.019,first=1,last=264):
 o=curve3('V6_2D_'+name,[(x,y,0) for x,y in points],r,mat,first,last)
 o.parent=cam;o.location=(0,0,Z+.04)
 return o

# Permanent understated brand/disclosure, no crowding around device.
hud('BROOKS PHOTONICS','BRAND',-5.04,6.65,.285,'V6_WHITE')
hud('SIMULATION  |  300 K RESERVOIR  |  2 mW DIE LOAD','FOOT',
    -5.04,-6.87,.205,'V6_MUTED')
# Same headline region for all scenes. One major claim visible at once.
hud('APPLIED TEC DRIVE','ACT1_TITLE',-5.04,5.77,.60,'V6_WHITE',1,264)
hud('COPPER ALSO CARRIES HEAT','ACT2_TITLE',-5.04,5.77,.56,'V6_WHITE',265,528)
hud('+7.63 K  AT MATCHED POWER','ACT3_TITLE',-5.04,5.77,.51,'V6_GOLD',529,816)

# Real pin1 and pin9 endpoints projected at the ACT 1 locked camera pose.
s.frame_set(1)
pplus=Vector(source['TEC_lead1']['parts'][-1]['b'])
pminus=Vector(source['TEC_lead9']['parts'][-1]['b'])
width=cam.data.ortho_scale*s.render.resolution_x/s.render.resolution_y
def proj(p):
 uv=world_to_camera_view(s,cam,p)
 return ((uv.x-.5)*width,(uv.y-.5)*cam.data.ortho_scale)
posx,posy=proj(pplus)
negx,negy=proj(pminus)
assert posx>negx and abs(posx-negx)>4,(posx,negx)
midx=(posx+negx)/2
# one centered source symbol between the projected physical endpoints;
# its lines are visibly a 2D explanatory diagram, not invented 3D hardware.
cy=min(posy,negy)-1.12
r=.33
circle=[(midx+r*math.cos(i*2*math.pi/72),
         cy+r*math.sin(i*2*math.pi/72)) for i in range(73)]
screen_line('DC_CIRCLE',circle,'V6_CYAN',.025)
# Connect right/source positive and left/return negative with neat orthogonal
# 2D leader segments; endpoints exactly match CAD pin projections.
screen_line('POS_WIRE',[(midx+r,cy),(posx,cy),(posx,posy)],'V6_CYAN',.017)
screen_line('NEG_WIRE',[(midx-r,cy),(negx,cy),(negx,negy)],'V6_CYAN',.017)
screen_line('POS_DOT',[(posx-.075,posy),(posx+.075,posy)],'V6_CYAN',.045)
screen_line('NEG_DOT',[(negx-.075,negy),(negx+.075,negy)],'V6_CYAN',.045)
hud('+','SOURCE_PLUS',midx+.11,cy-.15,.27,'V6_CYAN',1,264,align='CENTER')
hud('-','SOURCE_MINUS',midx-.13,cy-.15,.27,'V6_CYAN',1,264,align='CENTER')
hud('DC   1.49 V / 0.40 A','ACT1_VOLTAGE',midx,cy-.87,.285,
    'V6_CYAN',1,264,align='CENTER')

# Clear, static, timed evidence in the same bottom caption zone.
hud('87.4 mW','ACT2_VALUE',-5.04,-4.91,.67,'V6_GOLD',265,528)
hud('Cu net heat into final-stage hot ceramic','ACT2_DETAIL',
    -5.04,-5.48,.27,'V6_WHITE',265,528)
hud('218.69 K','ACT3_ON_K',-5.04,-4.90,.60,'V6_GOLD',529,816)
hud('Cu conduction ON','ACT3_ON_NAME',-5.04,-5.43,.255,'V6_MUTED',529,816)
hud('211.06 K','ACT3_OFF_K',5.04,-4.90,.60,'V6_WHITE',529,816,align='RIGHT')
hud('Thermal OFF (diagnostic)','ACT3_OFF_NAME',5.04,-5.43,.255,
    'V6_MUTED',529,816,align='RIGHT')
hud('TERMINAL INPUT: 595.7 mW IN BOTH CASES','ACT3_POWER',
    -5.04,-6.09,.235,'V6_MUTED',529,816)

# Gate: no V4/V5 text is retained; all new labels are stationary in screen
# coordinates, each explanation has >= 10 seconds, source icon is visible only
# when actual pinned leads are highlighted, later acts do not overlap labels.
assert not any(o.name.startswith(('V4_CAPTION_','V5_HUD_','V4_DIAGRAM_'))
               for o in bpy.data.objects)
assert len([o for o in bpy.data.objects if o.name.startswith('V6_APPLIED_CURRENT_')])==2
assert len([o for o in bpy.data.objects if o.name.startswith('V6_RETURN_CURRENT_')])==2
assert len([o for o in bpy.data.objects if o.name.startswith('V6_PARASITIC_HEAT_')])==6
assert abs(posx-negx)>4
for f in (1,110,264,266,345,500,530,700,816):
 s.frame_set(f)
 assert bpy.data.objects['V6_HUD_BRAND'].hide_render is False
 assert bpy.data.objects['V6_HUD_FOOT'].hide_render is False
 assert sum(not bpy.data.objects['V6_HUD_ACT%d_TITLE'%i].hide_render for i in (1,2,3))==1
s.frame_set(1)
s.render.image_settings.file_format='PNG'
s.render.filepath=str(OUT/'frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Brooks_Copper_3D_V6.blend'))
print('V6_SCENE_READY',json.dumps({
 'source_design_sha256':hashlib.sha256(DESIGN.read_bytes()).hexdigest(),
 'source_CAD_bodies':B['body_count'],'actual_pin_positions_camera':{'TEC+':[posx,posy],'TEC-':[negx,negy]},
 'source_2D_symbol_camera':[midx,cy],
 'act_lengths_seconds':[264/24,(528-264)/24,(816-528)/24],
 'fps':s.render.fps,'duration_sec':s.frame_end/s.render.fps,
 'glowing_source_leads':2,'current_arrows':4,'copper_heat_arrows':6,
 'temperature_delta_K':audit['nominal_minus_ablation_die_K'],
 'destination':str(OUT)},indent=2),flush=True)
if '--preview' in sys.argv:
 s.render.resolution_percentage=80
 for frame in (80,170,267,382,485,560,710):
  s.frame_set(frame);s.render.filepath=str(OUT/f'preview_{frame}.png')
  bpy.ops.render.render(write_still=True)
  print('V6_PREVIEW',frame,flush=True)
elif '--render' in sys.argv:
 s.render.resolution_percentage=100
 s.render.image_settings.file_format='FFMPEG'
 s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264'
 s.render.ffmpeg.constant_rate_factor='HIGH'
 s.render.ffmpeg.ffmpeg_preset='GOOD'
 s.render.ffmpeg.audio_codec='NONE'
 s.render.filepath=str(OUT/'Brooks_Photonics_TEC_Cu_Heat_Path_V6.mp4')
 bpy.ops.render.render(animation=True)
