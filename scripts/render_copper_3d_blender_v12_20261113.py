"""V12 technical orientation + user-supplied white logo, V11 science untouched.

- White Brooks Photonics logo stays in lower-left; no branding headline.
- At t=0–3.8s annotate real HgCdTe die, three TEC stages (bottom stage1,
  middle stage2, coldest top stage3), source copper links and TEC power leads.
- CAD-anchored 2D leader lines, fade out before the original drive caption.
- Preserve V11 heating, active drive, matched-power thermal-off comparison.
- All graphics are presentation geometry, not FEM solution contours.
"""
import bpy,json,math,sys,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path('/home/User/TE_Cooled_MCT')
D=ROOT/'media/copper_3d_20261112'
OUT=D/'revision12'
OUT.mkdir(parents=True,exist_ok=True)
DESIGN=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
data=json.loads(DESIGN.read_text())
B={b['name']:b for b in data['bodies']}
A=json.loads((ROOT/'data/nominal_gas_visibility_v327_20261111/coupled_attempt01/result.json').read_text())
C=json.loads((ROOT/'data/copper_ablation_publication_20261112/result.json').read_text())
assert len(data['bodies'])==824 and abs(A['calculated_detector_temperature_K']-C['calculated_detector_temperature_K']-7.634421834512921)<1e-8

bpy.ops.wm.open_mainfile(filepath=str(D/'revision11/Brooks_Copper_3D_V11.blend'))
s=bpy.context.scene
cam=s.camera
assert s.frame_start==1 and s.frame_end==816 and s.render.fps==24
assert (s.render.resolution_x,s.render.resolution_y)==(1080,1350)
assert all(bpy.data.objects.get('formed_tab'+str(i)) for i in (58,80,88))

# Remove brand title, preserve all explanatory/scientific captions.
oldbrand=bpy.data.objects.get('V7_TEXT_BRAND')
assert oldbrand and oldbrand.data.body=='BROOKS PHOTONICS'
bpy.data.objects.remove(oldbrand,do_unlink=True)

# Construct a fully self-contained, antialiased logo MESH from the actual
# user-supplied transparent PNG. Workbench cannot draw image alpha directly
# with viewport material shading, so convert PNG alpha to camera-parented
# 128px rasterized strips (3 discrete alpha levels) at the intended small size.
logo_source=OUT/'Brooks_Photonics_Logo_White_128.png'
assert logo_source.exists(),logo_source
image=bpy.data.images.load(str(logo_source),check_existing=True)
assert image.size[0]==128 and image.size[1]==128
pix=list(image.pixels)
assert len(pix)==128*128*4
cameraZ=-6.49
logo_x,logo_y=(-4.87,-6.10)
size=1.00
# Cluster neighboring pixels in horizontal runs per opacity category.
logo_materials=[]
for level,grey in [(1,(.40,.42,.47,1)),(2,(.72,.75,.79,1)),(3,(.98,.99,1,1))]:
 m=bpy.data.materials.new('V12_BROOKS_LOGO_WHITE_L'+str(level))
 m.diffuse_color=grey
 logo_materials.append(m)
mesh=bpy.data.meshes.new('V12_IMPORTED_BROOKS_WHITE_LOGO_GEOMETRY')
verts=[];faces=[];levels=[]
for y in range(128):
 row=127-y
 x=0
 while x<128:
  alpha=pix[(row*128+x)*4+3]
  a=min(3,int(round(alpha*3)))
  if a==0:x+=1;continue
  end=x+1
  while end<128 and min(3,int(round(pix[(row*128+end)*4+3]*3)))==a:
   end+=1
  px0=logo_x+size*x/128
  px1=logo_x+size*end/128
  py0=logo_y+size*y/128
  py1=logo_y+size*(y+1)/128
  z=0
  j=len(verts)
  verts.extend([(px0,py0,z),(px1,py0,z),(px1,py1,z),(px0,py1,z)])
  faces.append((j,j+1,j+2,j+3));levels.append(a-1)
  x=end
assert len(faces)>250
mesh.from_pydata(verts,[],faces);mesh.update()
for mat in logo_materials:mesh.materials.append(mat)
for poly,level in zip(mesh.polygons,levels):poly.material_index=level
logo=bpy.data.objects.new('V12_BROOKS_PHOTONICS_LOGO',mesh)
bpy.context.collection.objects.link(logo)
logo.parent=cam;logo.location=(0,0,cameraZ)
logo['source']='Uploaded Brooks Photonics white PNG, compressed 128px alpha reconstruction'
logo['raster_width']=128
# Keep a constant on-screen logo position and size through V11 camera zoom.
for f in sorted(set(list(range(1,817,8))+[816])):
 s.frame_set(f)
 fac=cam.data.ortho_scale/14.2
 logo.scale=(fac,fac,fac)
 logo.keyframe_insert(data_path='scale',frame=f)
print('LOGO_STRIPS',len(faces),flush=True)

# Orientation copy is short, in one opening window only. These are LABELS
# attached to source geometry; unlike narrative captions, these should sit
# around the device temporarily so scientists can learn its structure.
start,hold,end=7,65,88
z=-6.42
BG=(.045,.068,.10,1.0)
COL={'WHITE':(.94,.97,1,1),
     'MUTED':(.71,.79,.87,1),
     'CYAN':(.51,.89,1,1),
     'GOLD':(1,.78,.41,1)}
fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
font=bpy.data.fonts.load(fontfile) if Path(fontfile).exists() else None
def fade(m,color):
 for f,c in [(1,BG),(start,BG),(24,color),(hold,color),(end,BG),(816,BG)]:
  m.diffuse_color=c
  m.keyframe_insert(data_path='diffuse_color',frame=f)
 if m.animation_data and hasattr(m.animation_data.action,'fcurves'):
  for fc in m.animation_data.action.fcurves:
   for k in fc.keyframe_points:k.interpolation='BEZIER'
def timed(o):
 o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=start-1)
 o.hide_render=False;o.keyframe_insert(data_path='hide_render',frame=start)
 o.keyframe_insert(data_path='hide_render',frame=end)
 o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=end+1)

def caption(name,text,x,y,color='WHITE',size=.32):
 cu=bpy.data.curves.new(name,'FONT')
 cu.body=text;cu.size=size
 if font:cu.font=font
 ob=bpy.data.objects.new('V12_LABEL_'+name,cu)
 bpy.context.collection.objects.link(ob)
 ob.parent=cam;ob.location=(x,y,z)
 m=bpy.data.materials.new('V12_LABEL_COLOR_'+name)
 cu.materials.append(m);fade(m,COL[color]);timed(ob)
 return ob

# The coordinate targets are from the registered 824-solid assembly:
# Stage1=29 couples at lower ceramic, Stage2=11, Stage3=4 at detector end.
# No fictitious fourth Peltier stage. Labels are screen-space captions.
definitions=[
 # id, body, x,y, world source 3D endpoint, hue
 ('DETECTOR','DETECTOR',2.0,2.95,(.22,.18,5.78),'CYAN'),
 ('STAGE_3','STAGE 3',-4.8,1.57,(-1.15,-.15,4.60),'WHITE'),
 ('STAGE_2','STAGE 2',-4.8,.10,(-2.2,-.15,3.47),'WHITE'),
 ('STAGE_1','STAGE 1',-4.8,-1.40,(-2.55,-.25,2.37),'WHITE'),
 ('COPPER','CU LINKS',2.84,-.25,(2.05,-2.0,3.76),'GOLD'),
 ('LEADS','TEC LEADS',2.84,-3.42,(-2.03,-2.8,2.37),'CYAN'),
]
w=cam.data.ortho_scale*s.render.resolution_x/s.render.resolution_y
def projected(world):
 p=world_to_camera_view(s,cam,Vector(world))
 scale=cam.data.ortho_scale
 width=scale*s.render.resolution_x/s.render.resolution_y
 return ((p.x-.5)*width,(p.y-.5)*scale)

leaders=[]
for label_id,txt,x,y,world,color in definitions:
 ob=caption(label_id,txt,x,y,color)
 cu=bpy.data.curves.new('V12_SOURCE_LEADER_'+label_id,'CURVE')
 cu.dimensions='3D';cu.bevel_depth=.012
 cu.bevel_resolution=2
 sp=cu.splines.new('POLY');sp.points.add(2)
 conn=bpy.data.objects.new('V12_LEADER_'+label_id,cu)
 bpy.context.collection.objects.link(conn)
 conn.parent=cam;conn.location=(0,0,z+.03)
 m=bpy.data.materials.new('V12_LEADER_COLOR_'+label_id)
 cu.materials.append(m);fade(m,COL[color]);timed(conn)
 for frame in sorted(set(list(range(start,end+1,7))+[start,end])):
  s.frame_set(frame);bpy.context.view_layer.update()
  scale=cam.data.ortho_scale/14.2
  # Scene's frozen initial camera has a small motion from its V7 original;
  # terminal follows the actual source point each frame.
  X,Y=projected(world)
  left=(x<0)
  text_end=x+(len(txt)*.18 if left else -.14)
  text_y=y+.085
  elbows=(text_end+.13 if left else text_end-.13,Y)
  for point,p in zip(sp.points,((text_end,text_y),elbows,(X,Y))):
   point.co=(p[0],p[1],0,1)
   point.keyframe_insert(data_path='co',frame=frame)
 leaders.append(conn)

# "APPLY DC POWER" and 1.49 V must enter only after orientation labels fade.
# V7 original text uses material-color fading, so hide its meshes for the
# first 88 frames, then animate a gentle 0.5s material fade in.
for n in ('V7_TEXT_A1_HEAD','V7_TEXT_A1_METRIC'):
 ob=bpy.data.objects[n]
 mat=ob.data.materials[0]
 ob.hide_render=True;ob.keyframe_insert(data_path='hide_render',frame=1)
 ob.keyframe_insert(data_path='hide_render',frame=88)
 ob.hide_render=False;ob.keyframe_insert(data_path='hide_render',frame=89)
 # no jump to 100% while label is still fading
 sample_color=COL['WHITE'] if n.endswith('HEAD') else COL['CYAN']
 for f,c in ((89,BG),(105,sample_color)):
  mat.diffuse_color=c;mat.keyframe_insert(data_path='diffuse_color',frame=f)

# Intro label content remains visible for <4 seconds; later CTA and results
# retain all V11 assumptions and the matched-power model comparison.
assert len([o for o in bpy.data.objects if o.name.startswith('V12_LABEL_')])==6
assert len(leaders)==6
assert 'V7_TEXT_BRAND' not in bpy.data.objects
assert len(logo.data.polygons)>250
assert all(bpy.data.objects.get('formed_tab'+str(n)) for n in (58,80,88))
s.frame_set(1)
s.render.image_settings.file_format='PNG'
s.render.filepath=str(OUT/'frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Brooks_Copper_3D_V12.blend'))
print('V12_SCENE_READY',json.dumps({
 'source_sha256':hashlib.sha256(DESIGN.read_bytes()).hexdigest(),
 'model_source_bodies':data['body_count'],
 'logo_import':'uploaded user white artwork; alpha raster strips',
 'logo_strips':len(faces),
 'temporary_CAD_labels':[t for _,t,*_ in definitions],
 'orientation_seconds':end/24,
 'science_results_unchanged':True,
 'duration_seconds':34,
 'res':[1080,1350], 'fps':24,
 'scene':str(OUT/'Brooks_Copper_3D_V12.blend')
}),flush=True)
if '--preview' in sys.argv:
 s.render.resolution_percentage=80
 for frame in (16,34,55,76,93,125,380,567,762):
  s.frame_set(frame);s.render.filepath=str(OUT/f'preview_{frame}.png')
  bpy.ops.render.render(write_still=True)
  print('V12_PREVIEW',frame,flush=True)
elif '--render' in sys.argv:
 s.render.resolution_percentage=100
 s.render.image_settings.file_format='FFMPEG'
 s.render.ffmpeg.format='MPEG4'
 s.render.ffmpeg.codec='H264'
 s.render.ffmpeg.constant_rate_factor='PERC_LOSSLESS'
 s.render.ffmpeg.ffmpeg_preset='GOOD'
 s.render.ffmpeg.audio_codec='NONE'
 s.render.filepath=str(OUT/'Brooks_Photonics_TEC_Cu_3D_V12.mp4')
 bpy.ops.render.render(animation=True)
