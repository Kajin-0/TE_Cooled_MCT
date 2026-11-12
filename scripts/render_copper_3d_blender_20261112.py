"""Blender 4.3 production scene from TE_Cooled_MCT source-CAD design.json.

Authentic source-derived 0.50-mm 29/11/4 TEC materials, packages, Cu tabs.
Neither 3D thermal fields nor measured hardware depicted. Copper heat-path
tracers are schematic and intentionally NOT simulated CFD/thermal streamlines.

Output .blend is editable, MP4 is rendered via Blender FFmpeg.
"""
import bpy
import json
import math
import random
from mathutils import Vector
from pathlib import Path

ROOT=Path('/home/User/TE_Cooled_MCT')
DESIGN=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
BASE=ROOT/'data/nominal_gas_visibility_v327_20261111/coupled_attempt01/result.json'
ABL=ROOT/'data/copper_ablation_publication_20261112/result.json'
AUDIT=ROOT/'data/copper_ablation_publication_20261112/independent_audit.json'
CAMPAIGN=ROOT/'data/copper_sensitivity_publication_20261112'
OUT=ROOT/'media/copper_3d_20261112'
OUT.mkdir(parents=True,exist_ok=True)

data=json.loads(DESIGN.read_text())
base=json.loads(BASE.read_text())
off=json.loads(ABL.read_text())
audit=json.loads(AUDIT.read_text())
assert data['body_count']==824 and audit['status'].startswith('PASS')
assert abs(base['calculated_detector_temperature_K']-off['calculated_detector_temperature_K']-7.634421834512921)<1e-8
assert all((CAMPAIGN/k/'independent_audit.json').exists() for k in
           ('k80','k120','contact0p1x','contact10x','foil80','foil120'))
bpy.ops.wm.read_factory_settings(use_empty=True)
S=bpy.context.scene
S.render.engine='BLENDER_WORKBENCH'
S.render.resolution_x=960
S.render.resolution_y=1200
S.render.resolution_percentage=100
# Frame-step 2 retains 30 s of storyboard duration at 12 fps while halving
# VPS OpenGL/CPU workload. A future high-frame-rate export can use step 1.
S.render.fps=12
S.frame_step=2
S.frame_start=1
S.frame_end=720
S.render.image_settings.file_format='PNG'
S.render.film_transparent=False
S.view_settings.view_transform='Standard'
S.display.shading.light='STUDIO'
S.display.shading.color_type='MATERIAL'
S.display.shading.studio_light='paint.sl'
S.display.shading.show_shadows=True
S.display.shading.show_cavity=True
S.display.shading.cavity_type='BOTH'
S.display.shading.curvature_ridge_factor=1.25
S.display.shading.curvature_valley_factor=1.25
S.display.shading.show_specular_highlight=True
S.display.shading.background_type='WORLD'
S.world=bpy.data.worlds.new('DARK_STAGE')
S.world.color=(0.015,0.022,0.036)

# Original dimensions stay in mm; no geometry scaling or fictitious packaging.
C={
 'ceramic':(0.77,0.82,0.88,1.0),'N':(0.14,0.62,0.67,1.0),
 'P':(0.38,0.49,0.78,1.0),'Cu':(0.91,0.50,0.24,1.0),
 'Au':(0.89,0.72,0.30,1.0),'Ni':(0.45,0.54,0.64,1.0),
 'Ti':(0.35,0.47,0.60,1.0),'TiW':(0.38,0.44,0.55,1.0),
 'SnSb':(0.62,0.68,0.72,1.0),'SnBi':(0.74,0.66,0.63,1.0),
 'other':(0.40,0.48,0.58,1.0),'detector':(0.43,0.32,0.79,1.0),
 'Cu_hot':(1.0,0.56,0.22,1.0),'white':(0.95,0.98,1.,1),
 'muted':(0.58,0.70,0.83,1),'highlight':(1.0,0.70,0.33,1),
 'pale':(0.80,0.84,0.97,1),'accent':(0.66,0.49,0.94,1)}
mats={}
for key,color in C.items():
 mat=bpy.data.materials.new(key);mat.diffuse_color=color;mats[key]=mat

# Materials grouped into original source component classes, not arbitrary objects.
def family(body):
 name=body['name'];mat=body['material']
 if name.startswith('ceramic'):return 'ceramic'
 if name=='p_HgCdTe_photoconductor':return 'detector'
 if mat=='Cu':return 'Cu'
 if mat=='Au' or mat=='Au_ohmic':return 'Au'
 if mat in ('N','P'):return mat
 if mat in ('SnSb','SnBi57_43','In52Sn48'):return 'SnSb' if mat=='SnSb' else 'SnBi'
 if mat in ('Ni','Ti','TiW'):return mat
 return 'other'

groups={}
def cuboid(group, x,y,z,sx,sy,sz):
 if min(sx,sy,sz)<=0:return
 v,f=groups.setdefault(group,([],[]))
 n=len(v)
 v.extend([(x,y,z),(x+sx,y,z),(x+sx,y+sy,z),(x,y+sy,z),
           (x,y,z+sz),(x+sx,y,z+sz),(x+sx,y+sy,z+sz),(x,y+sy,z+sz)])
 f.extend([tuple(n+i for i in face) for face in
           ((0,3,2,1),(4,5,6,7),(0,1,5,4),
            (1,2,6,5),(2,3,7,6),(3,0,4,7))])
def make_group(name):
 verts,faces=groups[name]
 mesh=bpy.data.meshes.new('SOURCE_'+name)
 mesh.from_pydata(verts,[],faces);mesh.update()
 obj=bpy.data.objects.new('CAD_'+name,mesh)
 bpy.context.collection.objects.link(obj)
 mesh.materials.append(mats[name])
 return obj

# Exactly transferred boxes, including original P/N, pads, solder, thin films.
number_source_boxes=0
for b in data['bodies']:
 if b['shape']!='boxes':continue
 if b['name'].startswith(('header_finish','package_')):continue
 for q in b['boxes_mm']:
  cuboid(family(b),*q)
  number_source_boxes+=1
objects={k:make_group(k) for k in groups}

def tube_mesh(name,points,radius,material,sides=8):
 if len(points)<2:return None
 curve=bpy.data.curves.new(name,'CURVE')
 curve.dimensions='3D';curve.resolution_u=1;curve.bevel_depth=radius
 curve.bevel_resolution=2
 poly=curve.splines.new('POLY');poly.points.add(len(points)-1)
 for p,xyz in zip(poly.points,points):p.co=(*xyz,1.0)
 o=bpy.data.objects.new(name,curve)
 bpy.context.collection.objects.link(o)
 o.data.materials.append(mats[material])
 return o

def sampled_parts(parts,plane='yz'):
 points=[]
 for part in parts:
  a=Vector(part['a']);b=Vector(part['b'])
  if not points:points.append(tuple(a))
  if part['type']=='arc':
   c=Vector(part['c'])
   va=a-c;vb=b-c
   cross=(va.x*vb.y-va.y*vb.x) if len(a)==2 else va.cross(vb).length
   if len(a)==2:
    ta=math.atan2(va.y,va.x);tb=math.atan2(vb.y,vb.x)
    dt=(tb-ta+math.pi)%(2*math.pi)-math.pi
    for j in range(1,9):
     t=ta+dt*j/8
     points.append((c.x+part['r']*math.cos(t),c.y+part['r']*math.sin(t)))
   else:
    # circular 3D arc lying on the plane defined by start/center/end.
    v1=va.normalized()
    v2=vb.normalized()
    crossv=v1.cross(v2)
    angle=v1.angle(v2)
    if crossv.length<1e-10:
     points.append(tuple(b))
    else:
     from mathutils import Quaternion
     for j in range(1,9):
      q=Quaternion(crossv.normalized(),angle*j/8)
      points.append(tuple(c+q@va))
  else:
   points.append(tuple(b))
 return points

# Actual 3D footprint of thin formed copper on source centerline: x width 0.3,
# centerline in yz; ribbon's 30um thickness follows path curvature.
def copper_tab(b):
 pts2=sampled_parts(b['parts'])
 x=b['x'];w=b['width'];th=b['thickness']
 P=[Vector((a,bb)) for a,bb in pts2]
 verts=[]
 for i,p in enumerate(P):
  tangent=(P[min(i+1,len(P)-1)]-P[max(i-1,0)]).normalized()
  normal=Vector((-tangent.y,tangent.x))*th*.5
  for xx,sgn in ((x-w*.5,-1),(x+w*.5,1)):
   for sy in (-1,1):
    center=p+sy*normal
    verts.append((xx,center.x,center.y))
 faces=[]
 for i in range(len(P)-1):
  a=4*i;d=4*(i+1)
  for j,k in ((0,1),(1,3),(3,2),(2,0)):
   faces.append((a+j,a+k,d+k,d+j))
 faces.append((0,2,3,1))
 a=4*(len(P)-1);faces.append((a,a+1,a+3,a+2))
 mesh=bpy.data.meshes.new(b['name']+'_source_reconstructed')
 mesh.from_pydata(verts,[],faces);mesh.update()
 o=bpy.data.objects.new(b['name'],mesh);bpy.context.collection.objects.link(o)
 mesh.materials.append(mats['Cu_hot'])
 return o,[(x,p.x,p.y) for p in P]

copper_objects=[];paths=[]
for b in data['bodies']:
 if b['shape']=='tab':
  o,p=copper_tab(b);copper_objects.append(o);paths.append(p)

def cyl(name,loc,r,depth,material):
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=depth,
                                      location=(loc[0],loc[1],loc[2]+depth*.5))
 obj=bpy.context.object;obj.name=name
 obj.data.materials.append(mats[material])
 return obj
def annulus(body):
 r=body['radius'];ri=body['inner_radius']
 base=body['base'];steps=48;v=[];f=[]
 for z in (base[2],base[2]+body['height']):
  for rr in (r,ri):
   for j in range(steps):
    th=j*2*math.pi/steps;v.append((base[0]+rr*math.cos(th),base[1]+rr*math.sin(th),z))
 for j in range(steps):
  k=(j+1)%steps
  f.extend(((j,k,steps+k,steps+j),
            (2*steps+j,3*steps+j,3*steps+k,2*steps+k),
            (j,2*steps+j,2*steps+k,k),
            (steps+j,steps+k,3*steps+k,3*steps+j)))
 mesh=bpy.data.meshes.new(body['name']);mesh.from_pydata(v,[],f);mesh.update()
 o=bpy.data.objects.new(body['name'],mesh)
 bpy.context.collection.objects.link(o);mesh.materials.append(mats['other'])
 return o

# Pin and glass shapes use real source dimensions but are hidden for the close TEC film.
package=[]
for b in data['bodies']:
 if b['shape']=='cylinder':
  p=cyl(b['name'],b['base'],b['radius'],b['height'],family(b))
  package.append(p)
 elif b['shape']=='annulus':
  p=annulus(b);package.append(p)
 elif b['shape']=='wire':
  pts=sampled_parts(b['parts'])
  o=tube_mesh(b['name'],pts,b['radius'],family(b))
  if o:package.append(o)
# Exclude case/header and pins from the main TEC close-up.
for p in package:p.hide_render=True

# Detector still visible above stage3: source MCT die is violet.
# The three stage Cu links remain visible at their authentic exact positions.
aim=bpy.data.objects.new('CAMERA_TARGET',None)
bpy.context.collection.objects.link(aim)
aim.location=(0,0,3.75)
cam_data=bpy.data.cameras.new('Camera')
cam=bpy.data.objects.new('Camera',cam_data)
bpy.context.collection.objects.link(cam)
S.camera=cam
cam_data.type='ORTHO';cam_data.ortho_scale=15.1
con=cam.constraints.new('TRACK_TO');con.target=aim
con.track_axis='TRACK_NEGATIVE_Z';con.up_axis='UP_Y'
for fr,position in ((1,(12,-15,13)),(150,(12,-11,11)),(300,(11,-10,10)),
                    (420,(12,-12,12)),(570,(11,-13,12)),(720,(12,-15,13))):
 cam.location=position;cam.keyframe_insert(data_path='location',frame=fr)
for curve in cam.animation_data.action.fcurves if hasattr(cam.animation_data.action,'fcurves') else []:
 for k in curve.keyframe_points:k.interpolation='BEZIER'

# UI text is scene text parented to the camera at an unchanging near plane;
# it is editable text, never an AI-generated typeface.
font_candidates=[
 '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
 '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf']
font_bold_candidates=[
 '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
 '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf']
def font(filenames):
 for p in filenames:
  if Path(p).exists():return bpy.data.fonts.load(p)
 return None
normalfont=font(font_candidates)
boldfont=font(font_bold_candidates)
ui=[]

def text_obj(txt,where,size,material='white',bold=False,align='LEFT',
             start=1,end=720,spacing=1.08):
 cu=bpy.data.curves.new('TXT_'+txt[:12],'FONT')
 cu.body=txt;cu.size=size
 cu.align_x=align;cu.space_line=spacing
 if bold and boldfont:cu.font=boldfont
 elif normalfont:cu.font=normalfont
 obj=bpy.data.objects.new('LABEL_'+txt[:25],cu)
 bpy.context.collection.objects.link(obj)
 obj.parent=cam;obj.location=(where[0],where[1],-8.0)
 obj.rotation_euler=(0,0,0)
 obj.data.materials.append(mats[material])
 # Workbench material alpha not used; strictly toggle at segment boundaries.
 if start>1:
  obj.hide_render=True;obj.keyframe_insert(data_path='hide_render',frame=start-1)
 obj.hide_render=False;obj.keyframe_insert(data_path='hide_render',frame=start)
 obj.keyframe_insert(data_path='hide_render',frame=end)
 if end<720:
  obj.hide_render=True;obj.keyframe_insert(data_path='hide_render',frame=end+1)
 ui.append(obj)
 return obj

text_obj('BROOKS PHOTONICS',(-5.48,6.84),.33,'white',True)
text_obj('SOURCE-DERIVED 3D TEC MODEL',(-5.48,-7.06),.265,'muted')
text_obj('SIMULATION  /  NOT MEASURED HARDWARE',(-5.48,-7.36),.245,'muted')
text_obj('01 / 04  |  THE DEVICE',(5.5,6.84),.24,'muted',align='RIGHT',start=1,end=168)
text_obj('02 / 04  |  THE HEAT PATH',(5.5,6.84),.24,'muted',align='RIGHT',start=169,end=348)
text_obj('03 / 04  |  THE CONTROL',(5.5,6.84),.24,'muted',align='RIGHT',start=349,end=540)
text_obj('04 / 04  |  THE EVIDENCE',(5.5,6.84),.24,'muted',align='RIGHT',start=541,end=720)

text_obj('THE COPPER CONNECTIONS',(-5.48,5.9),.53,'white',True,start=1,end=168)
text_obj('ALSO CARRY HEAT.',(-5.48,5.28),.65,'highlight',True,start=1,end=168)
text_obj('29 / 11 / 4  THERMOELECTRIC COUPLES',(-5.48,-5.68),.27,'pale',start=1,end=168)
text_obj('ORIGINAL 0.50 mm P/N LEG HEIGHT',(-5.48,-6.07),.27,'muted',start=1,end=168)

text_obj('THREE FORMED COPPER LINKS',(-5.48,5.9),.49,'white',True,start=169,end=348)
text_obj('NETS 58 / 80 / 88',(-5.48,5.28),.45,'highlight',True,start=169,end=348)
text_obj('87.4 mW NET INTO THE',(-5.48,-5.23),.46,'highlight',True,start=169,end=348)
text_obj('COLDEST STAGE\'S HOT-SIDE CERAMIC',(-5.48,-5.8),.31,'white',start=169,end=348)
text_obj('SCHEMATIC FLOW MARKERS; NOT A 3D HEAT FIELD',(-5.48,-6.23),.23,'muted',start=169,end=348)

text_obj('ISOLATE ONE MECHANISM',(-5.48,5.93),.51,'white',True,start=349,end=540)
text_obj('PASSIVE Cu CONDUCTION',(-5.48,5.31),.48,'highlight',True,start=349,end=540)
text_obj('ELECTRICAL CIRCUIT + I²R RETAINED',(-5.48,4.75),.29,'pale',start=349,end=540)
text_obj('218.69 K',(-5.45,-4.05),.79,'highlight',True,start=349,end=540)
text_obj('Cu THERMAL ON',(-5.45,-4.55),.28,'muted',start=349,end=540)
text_obj('211.06 K',(5.45,-4.05),.79,'white',True,align='RIGHT',start=349,end=540)
text_obj('DIAGNOSTIC OFF',(5.45,-4.55),.28,'muted',align='RIGHT',start=349,end=540)
text_obj('+7.63 K DETECTOR PENALTY',(-5.45,-5.46),.51,'highlight',True,start=349,end=540)
text_obj('MATCHED ELECTRICAL INPUT: 595.668 mW',(-5.45,-6.03),.265,'pale',start=349,end=540)

text_obj('THE RESULT SURVIVES',(-5.48,5.93),.54,'white',True,start=541,end=720)
text_obj('SENSITIVITY SCREENING.',(-5.48,5.3),.52,'highlight',True,start=541,end=720)
text_obj('6 / 6',(-5.48,-4.15),.95,'white',True,start=541,end=720)
text_obj('INDEPENDENT AUDITS PASS',(-5.48,-4.7),.33,'pale',start=541,end=720)
text_obj('kCu ±20%    /    FOIL ±20%',(-5.48,-5.38),.29,'white',start=541,end=720)
text_obj('CONTACT Rth: 0.1x–10x',(-5.48,-5.78),.29,'white',start=541,end=720)
text_obj('PARTIAL-CAVITY MODEL  |  INTERFACES ASSUMED',(-5.48,-6.28),.23,'muted',start=541,end=720)

# Small transient dots traverse the source-geometry Cu ribbon, illustrative only.
# Workbench camera-safe highlights, geometrically located at tab centerlines.
for net,path in zip((58,80,88),paths):
 for number in range(4):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.052,
                                      location=path[0])
  o=bpy.context.object;o.name=f'EXPLANATORY_HEAT_MARKER_NET{net}_{number}'
  o.data.materials.append(mats['highlight'])
  for frame in range(1,721,12):
   progress=((frame-169)/105.+number/4.)%1.
   ix=progress*(len(path)-1)
   j=min(int(ix),len(path)-2);fraction=ix-j
   v=Vector(path[j]).lerp(Vector(path[j+1]),fraction)
   o.location=v
   o.keyframe_insert(data_path='location',frame=frame)
  o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=168)
  o.hide_render=False;o.keyframe_insert(data_path='hide_render',frame=169)
  o.keyframe_insert(data_path='hide_render',frame=348)
  o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=349)
  for fcurve in o.animation_data.action.fcurves if hasattr(o.animation_data.action,'fcurves') else []:
   for p in fcurve.keyframe_points:p.interpolation='LINEAR'

S.render.image_settings.color_mode='RGB'
S.render.filepath=str(OUT/'copper_3d_source_')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'source_cad_copper_thermal_study.blend'))

print('BLENDER_SCENE_READY',json.dumps({
 'bodies':data['body_count'],'source_boxes':number_source_boxes,
 'formed_tabs':len(copper_objects),'materials':len(mats),
 'source_model':str(DESIGN),'verified_delta_K':audit['nominal_minus_ablation_die_K'],
 'blend_file':str(OUT/'source_cad_copper_thermal_study.blend'),
 'frames':S.frame_end,'size':[S.render.resolution_x,S.render.resolution_y],
}))
# Optional preview frame to validate generated scene before expensive animation.
if '--preview' in __import__('sys').argv:
 S.frame_set(165)
 S.render.filepath=str(OUT/'preview_165.png')
 bpy.ops.render.render(write_still=True)
elif '--render' in __import__('sys').argv:
 S.render.image_settings.file_format='FFMPEG'
 S.render.ffmpeg.format='MPEG4'
 S.render.ffmpeg.codec='H264'
 S.render.ffmpeg.constant_rate_factor='HIGH'
 S.render.ffmpeg.ffmpeg_preset='GOOD'
 S.render.ffmpeg.audio_codec='NONE'
 S.render.filepath=str(OUT/'Brooks_Photonics_Copper_Thermal_Bypass_3D.mp4')
 bpy.ops.render.render(animation=True)
