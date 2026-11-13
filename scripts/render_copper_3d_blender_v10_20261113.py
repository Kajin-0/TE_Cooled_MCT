"""V10 presentation revision: replace floating 3D target tubes/rings with
model-surface color + schematic heat/cool symbols.

Loaded from validated V9. Retains original 824-body design in source files,
3D copper-tab heat markers and source-pinned electrical diagram. Film only.
"""
import bpy,math,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/User/TE_Cooled_MCT')
D=ROOT/'media/copper_3d_20261112'
OUT=D/'revision10'
OUT.mkdir(parents=True,exist_ok=True)
B=json.loads((ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_text())
BASE=json.loads((ROOT/'data/nominal_gas_visibility_v327_20261111/coupled_attempt01/result.json').read_text())
OFF=json.loads((ROOT/'data/copper_ablation_publication_20261112/result.json').read_text())
assert B['body_count']==824
assert abs(BASE['calculated_detector_temperature_K']-OFF['calculated_detector_temperature_K']-7.634421834512921)<1e-8

bpy.ops.wm.open_mainfile(filepath=str(D/'revision09/Brooks_Copper_3D_V9.blend'))
s=bpy.context.scene;cam=s.camera
assert s.frame_end==816 and s.render.fps==24
# Delete ONLY the extraneous 3D rectangles/rings; do not touch actual
# ceramic FEM source objects, detector solids, copper tabs or electrical leads.
for ob in list(bpy.data.objects):
 if ob.name.startswith(('V9_HEAT_TERMINUS_','V9_SOURCE_MCT_DETECTOR_OUTLINE',
                        'V9_STAGE2_HOT_CERAMIC_TARGET','V9_RESULT_')):
  bpy.data.objects.remove(ob,do_unlink=True)
for name in ('V7_TEXT_A3_METRIC','V7_TEXT_A3_POWER'):
 ob=bpy.data.objects.get(name)
 if ob:bpy.data.objects.remove(ob,do_unlink=True)
assert not any(o.name.startswith(('V9_HEAT_TERMINUS_','V9_SOURCE_MCT_DETECTOR_OUTLINE',
                                   'V9_STAGE2_HOT_CERAMIC_TARGET')) for o in bpy.data.objects)

# Direct technical language, neither overclaiming real heat generation
# nor implying the thermal-off control is a buildable material.
copy={
 'V7_TEXT_A1_HEAD':'APPLY DC POWER',
 'V7_TEXT_A1_METRIC':'1.49 V  /  0.40 A',
 'V7_TEXT_A2_HEAD':'COPPER LINKS CARRY HEAT',
 'V7_TEXT_A2_METRIC':'87.4 mW INTO THE COLDEST STAGE',
 'V7_TEXT_A2_DETAIL':'Net heat into its hot-side ceramic',
 'V7_TEXT_A3_HEAD':'COPPER RAISES DETECTOR TEMPERATURE',
}
for name,msg in copy.items():
 ob=bpy.data.objects.get(name);assert ob,name
 ob.data.body=msg

# Color ONLY the source geometry: no circles, cages, oversized detector.
# The detector CAD mesh is exactly the original 1mm x 1mm x 0.2mm die.
det=bpy.data.objects['CAD_detector']
assert len(det.data.polygons)==6
original=det.data.materials[0]
warm=(1.,.22,.12,1.);cold=(.11,.69,1.,1.)
coolbaseline=(.45,.32,.79,1.)
mat=original.copy();mat.name='V10_DETECTOR_CASE_INDICATOR'
det.data.materials[0]=mat

# Assign independent tint only to the 2.4mm source top-ceramic slab, not
# the four-slab mesh as a whole. The source ceramic mesh contains 4 boxes
# (24 quad faces); identified from exact original z bounds, NOT visual guess.
cer=bpy.data.objects['CAD_ceramic']
assert len(cer.data.polygons)==24
top=cer.data.materials[0].copy();top.name='V10_TOP_CERAMIC_CASE_INDICATOR'
cer.data.materials.append(top)
topidx=len(cer.data.materials)-1
chosen=[]
for polygon in cer.data.polygons:
 coords=[cer.data.vertices[i].co for i in polygon.vertices]
 if all(4.87<=p.z<=5.40 for p in coords):
  polygon.material_index=topidx;chosen.append(polygon.index)
assert len(chosen)==6,chosen
# Material-color animation conveys comparison states; not a 3D FEM
# spatial temperature field or a calibrated temperature-to-RGB mapping.
frames=[
 (1,coolbaseline,(.77,.82,.88,1.)),
 (520,coolbaseline,(.77,.82,.88,1.)),
 (540,warm,(.89,.55,.50,1.)),
 (614,warm,(.89,.55,.50,1.)),
 (632,cold,(.51,.76,.91,1.)),
 (714,cold,(.51,.76,.91,1.)),
 (733,warm,(.89,.55,.50,1.)),
 (816,warm,(.89,.55,.50,1.)),
]
for f,dc,tc in frames:
 mat.diffuse_color=dc;mat.keyframe_insert(data_path='diffuse_color',frame=f)
 top.diffuse_color=tc;top.keyframe_insert(data_path='diffuse_color',frame=f)
# Linear color fades produce a soft thermal effect on the source geometry.
for m in (mat,top):
 if m.animation_data and hasattr(m.animation_data.action,'fcurves'):
  for fc in m.animation_data.action.fcurves:
   for k in fc.keyframe_points:k.interpolation='BEZIER'

# Camera-space caption/style from V9 compensates for orthographic zoom.
Z=-6.5
fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
font=bpy.data.fonts.load(fontfile) if Path(fontfile).exists() else None
COLORS={'hot':(1,.73,.40,1.),'cold':(.53,.88,1.,1.),
        'neutral':(.96,.97,.98,1.),'grey':(.73,.79,.86,1.)}
def show(o,start,end):
 if start>1:o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=start-1)
 o.hide_render=False;o.keyframe_insert(data_path='hide_render',frame=start)
 o.keyframe_insert(data_path='hide_render',frame=end)
 if end<816:o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=end+1)
def screen_lock(o,base_x,base_y,start,end):
 for f in sorted(set(list(range(start,end+1,8))+[start,end])):
  s.frame_set(f)
  scale=cam.data.ortho_scale/14.2
  o.location=(base_x*scale,base_y*scale,Z)
  o.scale=(scale,scale,scale)
  o.keyframe_insert(data_path='location',frame=f)
  o.keyframe_insert(data_path='scale',frame=f)
def new_text(name,msg,x,y,size,color,start,end):
 data=bpy.data.curves.new(name,'FONT');data.body=msg;data.size=size
 if font:data.font=font
 ob=bpy.data.objects.new('V10_TEXT_'+name,data);bpy.context.collection.objects.link(ob)
 ob.parent=cam
 m=bpy.data.materials.new('V10_'+name);m.diffuse_color=COLORS[color]
 data.materials.append(m)
 screen_lock(ob,x,y,start,end);show(ob,start,end)
 return ob
# One fixed 3-line caption cluster; no bottom/right-side text.
new_text('WARM_TEMP','218.69 K',-4.98,5.03,.61,'hot',540,620)
new_text('WARM_DETAIL','Copper heat path ON',-4.98,4.39,.29,'grey',540,620)
new_text('COLD_TEMP','211.06 K',-4.98,5.03,.61,'cold',631,722)
new_text('COLD_DETAIL','Copper thermal path OFF (model)',-4.98,4.39,.29,'grey',631,722)
new_text('RESULT','+7.63 K AT MATCHED POWER',-4.98,5.03,.51,'hot',734,816)
new_text('RESULT_DETAIL','Copper heat path warms detector',-4.98,4.39,.29,'grey',734,816)
# 2D flame/snowflake symbols only, beside the large changing temperature.
# Symbols are intentionally abstract visual keys, not scientific images.
def stroke(name,pts,col,start,end,r=.021):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D'
 cu.bevel_depth=r;cu.bevel_resolution=2
 sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,xy in zip(sp.points,pts):p.co=(xy[0],xy[1],0,1)
 ob=bpy.data.objects.new('V10_ICON_'+name,cu)
 bpy.context.collection.objects.link(ob)
 ob.parent=cam
 m=bpy.data.materials.new('V10_ICON_MATERIAL_'+name);m.diffuse_color=COLORS[col]
 cu.materials.append(m)
 for f in sorted(set(list(range(start,end+1,8))+[start,end])):
  s.frame_set(f)
  q=cam.data.ortho_scale/14.2
  ob.location=(0,0,Z+.03)
  ob.scale=(q,q,q)
  ob.keyframe_insert(data_path='scale',frame=f)
 show(ob,start,end)
 return ob
# Snowflake: 6 straight rays + small barbs, located in the same copy cluster.
sx,sy=-1.75,5.25
for i in range(6):
 theta=math.pi*i/3
 ux,uy=math.cos(theta),math.sin(theta)
 end=(sx+.22*ux,sy+.22*uy)
 stroke('SNOW_RAY_'+str(i),[(sx,sy),end],'cold',631,722,r=.017)
 for side in (-1,1):
  tx=sx+.145*ux;ty=sy+.145*uy
  a=theta+side*.58+math.pi
  stroke('SNOW_ARM_%d_%d'%(i,side),
         [(tx,ty),(tx+.075*math.cos(a),ty+.075*math.sin(a))],
         'cold',631,722,r=.013)
# Flame outline is flat 2D, NOT another bulky 3D cage.
fx,fy=-1.75,5.22
flame=[(0,-.20),(-.13,-.06),(-.12,.10),(-.04,.07),(.0,.28),
       (.11,.10),(.15,-.02),(.11,-.16),(0,-.20)]
stroke('FLAME_OUTLINE',[(fx+x,fy+y) for x,y in flame],
       'hot',540,620,r=.023)
stroke('FLAME_SUMMARY',[(fx+x,fy+y) for x,y in flame],
       'hot',734,816,r=.023)
# Flat filled icon inside the two outlines. The surface is only a UI symbol,
# camera-parented and does not alter the photoconductor or model geometry.
def flame_fill(name,start,end):
 pts=[(fx+x,fy+y) for x,y in flame[:-1]]
 verts=[(fx,fy-.025,0)]+[(x,y,0) for x,y in pts]
 faces=[(0,i+1,i+2) for i in range(len(pts)-1)]
 faces.append((0,len(pts),1))
 mesh=bpy.data.meshes.new(name)
 mesh.from_pydata(verts,[],faces);mesh.update()
 ob=bpy.data.objects.new('V10_ICON_'+name,mesh)
 bpy.context.collection.objects.link(ob);ob.parent=cam
 m=bpy.data.materials.new(name+'_MAT');m.diffuse_color=(1,.53,.21,1)
 mesh.materials.append(m)
 for f in sorted(set(list(range(start,end+1,8))+[start,end])):
  s.frame_set(f)
  q=cam.data.ortho_scale/14.2
  ob.location=(0,0,Z+.06);ob.scale=(q,q,q)
  ob.keyframe_insert(data_path='location',frame=f)
  ob.keyframe_insert(data_path='scale',frame=f)
 show(ob,start,end)
 return ob
flame_fill('FLAME_FILL',540,620)
flame_fill('FLAME_SUMMARY_FILL',734,816)

# No unnecessary 3D beacon remains. Only 2D icons and case colors.
assert len([o for o in bpy.data.objects if o.name.startswith('V10_TEXT_')])==6
assert len([o for o in bpy.data.objects if o.name.startswith('V10_ICON_')])==22
assert all(bpy.data.objects.get('formed_tab'+str(n)) for n in (58,80,88))
assert 'CAD_detector' in bpy.data.objects
s.frame_set(1)
s.render.image_settings.file_format='PNG'
s.render.filepath=str(OUT/'frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Brooks_Copper_3D_V10.blend'))
print('V10_SCENE_READY',json.dumps({
 'source_sha256':hashlib.sha256((ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_bytes()).hexdigest(),
 'source_geometry_unchanged':True,
 'removed_3D_target_tubes':True,
 'actual_detector_and_top_ceramic_colored':True,
 'source_top_ceramic_faces':len(chosen),
 'comparison':{'conduction_on_K':BASE['calculated_detector_temperature_K'],
               'conduction_off_K':OFF['calculated_detector_temperature_K']},
 'icons':'flame/orange for warmer; snowflake/blue for cooler; schematic comparisons',
 'fps':24,'length_s':34,
 'scene':str(OUT/'Brooks_Copper_3D_V10.blend')}),flush=True)
if '--preview' in sys.argv:
 s.render.resolution_percentage=80
 for frame in (380,567,658,762,810):
  s.frame_set(frame)
  s.render.filepath=str(OUT/f'preview_{frame}.png')
  bpy.ops.render.render(write_still=True)
  print('V10_PREVIEW_READY',frame,flush=True)
elif '--render' in sys.argv:
 s.render.resolution_percentage=100
 s.render.image_settings.file_format='FFMPEG'
 s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264'
 s.render.ffmpeg.constant_rate_factor='PERC_LOSSLESS'
 s.render.ffmpeg.ffmpeg_preset='GOOD';s.render.ffmpeg.audio_codec='NONE'
 s.render.filepath=str(OUT/'Brooks_Photonics_TEC_Cu_3D_V10.mp4')
 bpy.ops.render.render(animation=True)
