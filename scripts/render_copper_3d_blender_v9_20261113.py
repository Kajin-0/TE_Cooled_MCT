"""V9: scientific storyline on actual source-derived three-stage TEC.
- Remove two orphan pad specks from VISUAL CLOSE-UP only (source untouched).
- Clearly show copper heat into final-stage hot ceramic (ceramic2).
- Detector payoff uses an ANNOTATED schematic indicator, not a false FEM field.
- Direct language; single upper-left caption cluster.
- Gentle purposeful camera zoom and continuous source-anchored electrical motion.
"""
import bpy,bmesh,math,sys,json,hashlib
from pathlib import Path
from mathutils import Vector

ROOT=Path('/home/User/TE_Cooled_MCT')
D=ROOT/'media/copper_3d_20261112'
OUT=D/'revision09'
OUT.mkdir(parents=True,exist_ok=True)
DESIGN=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
design=json.loads(DESIGN.read_text())
src={x['name']:x for x in design['bodies']}
baseline=json.loads((ROOT/'data/nominal_gas_visibility_v327_20261111/coupled_attempt01/result.json').read_text())
abl=json.loads((ROOT/'data/copper_ablation_publication_20261112/result.json').read_text())
audit=json.loads((ROOT/'data/copper_ablation_publication_20261112/independent_audit.json').read_text())
assert design['body_count']==824
assert audit['status'].startswith('PASS')
assert abs(baseline['calculated_detector_temperature_K']-abl['calculated_detector_temperature_K']
           -7.634421834512921)<1e-8
assert src['VIGO_reference_header']['registry']['pinout']==src['VIGO_reference_header']['registry']['pinout']

bpy.ops.wm.open_mainfile(filepath=str(D/'revision08/Brooks_Copper_3D_V8.blend'))
s=bpy.context.scene;cam=s.camera
s.frame_start=1;s.frame_end=816;s.render.fps=24
s.render.resolution_x=1080;s.render.resolution_y=1350
assert s.render.engine=='BLENDER_WORKBENCH'
assert all(bpy.data.objects.get('formed_tab'+str(n)) for n in (58,80,88))

# === SOURCE-VERIFIED ANOMALY CORRECTION ================================
# Two stray yellow specks ARE orphaned Au bond pads:
# pin7_wedge_foot and pin8_wedge_foot located at y=+5.118mm, which project
# separately when the header/package body is hidden in the open-TEC close-up.
# Delete only these 12 visual faces from the merged CAD_Au Blender mesh.
# The source registry, STEP solids, and other pads remain entirely unchanged.
source_pin7=src['pin7_wedge_foot']['boxes_mm'][0]
source_pin8=src['pin8_wedge_foot']['boxes_mm'][0]
assert abs(source_pin7[1]-5.11820518799383)<1e-9
assert abs(source_pin8[1]-5.118205187993831)<1e-9
o=bpy.data.objects['CAD_Au']
bm=bmesh.new();bm.from_mesh(o.data)
dead=[]
for face in bm.faces:
 if all(5.11<v.co.y<5.16 and 1.61<abs(v.co.x)<1.76
        and 1.999<v.co.z<2.02 for v in face.verts):
  dead.append(face)
assert len(dead)==12,('Expected two isolated six-faced pin pads',len(dead))
bmesh.ops.delete(bm,geom=dead,context='FACES')
bm.to_mesh(o.data);bm.free();o.data.update()
print('REMOVED_TWO_ORPHAN_PAD_SPECKS_FROM_PRESENTATION_ONLY',len(dead),flush=True)

# === CLEARER PROFESSIONAL CAPTIONS ==================================
wording={
 'V7_TEXT_A1_HEAD':'TEC POWER ON',
 'V7_TEXT_A1_METRIC':'1.49 V DC  /  0.40 A',
 'V7_TEXT_A2_HEAD':'COPPER LINKS LEAK HEAT',
 'V7_TEXT_A2_METRIC':'87.4 mW INTO THE COLD STAGE',
 'V7_TEXT_A2_DETAIL':'Heat enters the top stage hot-side ceramic',
 'V7_TEXT_A3_HEAD':'MODEL: COPPER WARMS DETECTOR',
 'V7_TEXT_A3_METRIC':'+7.63 K  AT THE SAME POWER',
 'V7_TEXT_A3_DETAIL':'Cu heat path ON: 218.69 K   |   OFF: 211.06 K',
 'V7_TEXT_A3_POWER':'Thermal-off is a model control, not removed wiring',
}
for name,msg in wording.items():
 ob=bpy.data.objects.get(name)
 assert ob is not None,name
 ob.data.body=msg
# The actual electrical drive case is 0.399969 A and 1.489284 V;
# match the displayed 1.49V/0.40A to meaningful precision.
assert abs(baseline['operating_current_A']-.4)<1e-3
assert abs(baseline['terminal_voltage_V']-1.49)<.01
assert len([o for o in bpy.data.objects if o.name.startswith('V7_TEXT_')])==10

# === PURPOSEFUL, BUT SUBTLE CAMERA ZOOM ===============================
# Current lead and source: whole TEC. Copper thermal path: move toward stage2.
# Detector result: move closer to the actual die without cropping the stack.
target=bpy.data.objects['CAMERA_TARGET']
if target.animation_data:target.animation_data_clear()
for f,xyz in ((1,(0,0,3.75)),(252,(0,0,3.75)),
              (360,(0,0,4.25)),(528,(0,0,4.25)),
              (670,(0,0,4.70)),(816,(0,0,4.70))):
 target.location=xyz;target.keyframe_insert(data_path='location',frame=f)
if cam.data.animation_data:cam.data.animation_data_clear()
for f,size in ((1,14.2),(252,14.2),(360,12.75),(528,12.75),
               (670,11.8),(816,11.8)):
 cam.data.ortho_scale=size;cam.data.keyframe_insert(data_path='ortho_scale',frame=f)
# Camera's existing slow drift remains, but shot reframing follows relevant
# upper device physics. Keep the source-pinned 2D diagram moving with camera:
# V8 has 2D source leader points keyed from V7 camera, so do not reframe
# camera during the FIRST ACT (f <=252) when 2D source symbol is visible.
assert bpy.data.objects.get('V7_VOLTAGE_POS_LEADER')
assert bpy.data.objects.get('V7_VOLTAGE_NEG_LEADER')

# === VISUAL PHYSICAL TARGET MARKERS ==================================
col={
 'V9_TARGET_GOLD':(1,.70,.26,1),
 'V9_TARGET_GOLD_DARK':(.53,.26,.075,1),
 'V9_DETECTOR_COOL':(.34,.83,1.,1),
 'V9_DETECTOR_WARM':(1,.71,.31,1),
}
MAT={}
for n,rgba in col.items():
 m=bpy.data.materials.new(n);m.diffuse_color=rgba;MAT[n]=m

def visibility(ob,start,end):
 if start>1:
  ob.hide_render=True;ob.keyframe_insert(data_path='hide_render',frame=start-1)
 ob.hide_render=False;ob.keyframe_insert(data_path='hide_render',frame=start)
 ob.keyframe_insert(data_path='hide_render',frame=end)
 if end<816:
  ob.hide_render=True;ob.keyframe_insert(data_path='hide_render',frame=end+1)

def poly(name,points,r,material,start,end):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D'
 cu.bevel_depth=r;cu.bevel_resolution=3
 sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
 for a,pt in zip(sp.points,points):a.co=(*pt,1)
 ob=bpy.data.objects.new(name,cu)
 bpy.context.collection.objects.link(ob);cu.materials.append(MAT[material])
 visibility(ob,start,end)
 return ob

# Top ("coldest") stage is TEC stage2: its HOT-SIDE ceramic is ceramic2,
# not ceramic3 or the HgCdTe chip itself.
cer=src['ceramic2']['boxes_mm'][0]
x,y,z,dx,dy,dz=cer
assert abs(dx-3.8)<1e-8 and abs(z-3.78425)<1e-8
zedge=z+dz+.045
x0,x1=x+.055,x+dx-.055
y0,y1=y+.055,y+dy-.055
edge=[(x0,y0,zedge),(x1,y0,zedge),(x1,y1,zedge),(x0,y1,zedge),(x0,y0,zedge)]
poly('V9_STAGE2_HOT_CERAMIC_TARGET',edge,.046,'V9_TARGET_GOLD',310,528)
# Pulsing large beacon on only the ceramic2 upper-right source tab contact.
# The ring is an illustrative target locator, NOT a thermal FEM contour.
point=(1.44,2.0,zedge)
r=.26
for f in (327,383,441,498):
 rad=(.23 if f in (327,441) else .31)
 circ=[(point[0]+rad*math.cos(i*2*math.pi/32),
        point[1]+rad*math.sin(i*2*math.pi/32),
        point[2]+.04) for i in range(33)]
 ob=poly('V9_HEAT_TERMINUS_'+str(f),circ,.035,'V9_TARGET_GOLD',
         f,min(f+35,528))

# Main payoff: draw attention to real 1mm HgCdTe die, not the grey plates.
die=src['p_HgCdTe_photoconductor']['boxes_mm'][0]
assert die[:3]==[-.5,-.5,5.57625]
# 3D die outline is a **marker** around real source geometry.
x,y,z,w,h,th=die
padding=.13
rx=x-padding;ry=y-padding;rz=z+th+.08
ring=[(rx,ry,rz),(x+w+padding,ry,rz),(x+w+padding,y+h+padding,rz),
      (rx,y+h+padding,rz),(rx,ry,rz)]
locator=poly('V9_SOURCE_MCT_DETECTOR_OUTLINE',ring,.065,'V9_DETECTOR_WARM',543,816)
# Make the payoff a visible event, not a static number: a deliberate
# detector indicator color change at the ON -> thermal-OFF counterfactual,
# reversing to the nominal ON state at the conclusion. The model die geometry
# and material remain unchanged: ONLY the locator ring color is animated.
mat=MAT['V9_DETECTOR_WARM']
for f,c in ((543,(1,.71,.31,1)),(570,(1,.71,.31,1)),
            (624,(1,.71,.31,1)),(648,(.34,.83,1,1)),
            (720,(.34,.83,1,1)),(749,(1,.71,.31,1)),
            (816,(1,.71,.31,1))):
 mat.diffuse_color=c;mat.keyframe_insert(data_path='diffuse_color',frame=f)

# Highlight actual 1mm detector geometry by preserving source-sized
# marker, not scaling or fabricating an enlarged MCT chip.
assert 'CAD_detector' in bpy.data.objects

# === RESULT ANIMATION AND PHONE-SAFE TYPOGRAPHY =======================
# V8 captions are camera-parented but their coordinates were NOT compensated
# when the orthographic camera zoomed. Lock all existing text to the same
# normalized screen position as the lens focal scale changes.
# This fixes the clipped V9 preview rather than suppressing camera motion.
labels=[ob for ob in bpy.data.objects if ob.name.startswith('V7_TEXT_')]
assert len(labels)==10
for ob in labels:
 x0,y0,z0=tuple(ob.location)
 for f in list(range(1,817,8))+[816]:
  s.frame_set(f)
  scale=cam.data.ortho_scale/14.2
  ob.location=(x0*scale,y0*scale,z0)
  ob.scale=(scale,scale,scale)
  ob.keyframe_insert(data_path='location',frame=f)
  ob.keyframe_insert(data_path='scale',frame=f)
# The result changes within Act 3, not just an idle camera move:
# one consistent caption location alternates two computed scenarios.
template=bpy.data.objects['V7_TEXT_A3_DETAIL']
template.hide_render=True
template.keyframe_insert(data_path='hide_render',frame=1)
segments=[
 ('CU_ON','Cu heat path ON: 218.69 K',540,625,'V9_DETECTOR_WARM'),
 ('CU_OFF','Diagnostic heat path OFF: 211.06 K',638,728,'V9_DETECTOR_COOL'),
 ('SUMMARY','Copper conduction warms detector by 7.63 K',741,816,'V9_DETECTOR_WARM')
]
for name,msg,start,end,matname in segments:
 cu=template.data.copy();cu.body=msg
 ob=bpy.data.objects.new('V9_RESULT_'+name,cu)
 bpy.context.collection.objects.link(ob)
 ob.parent=cam
 cu.materials.clear()
 m=bpy.data.materials.new('V9_TEXT_'+name)
 m.diffuse_color=((1,.80,.40,1) if matname=='V9_DETECTOR_WARM' else (.53,.88,1,1))
 cu.materials.append(m)
 # This paragraph inherits one upper-left location as the V7 original.
 x0,y0,z0=tuple(template.location)
 for f in list(range(start,end+1,8))+[start,end]:
  s.frame_set(f)
  sc=cam.data.ortho_scale/14.2
  # Reconstruct its original V7 camera-relative position, not the last
  # baked position after text screen-lock animation.
  ob.location=(-5.02*sc,4.45*sc,z0)
  ob.scale=(sc,sc,sc)
  ob.keyframe_insert(data_path='location',frame=f)
  ob.keyframe_insert(data_path='scale',frame=f)
 ob.hide_render=True;ob.keyframe_insert(data_path='hide_render',frame=max(1,start-1))
 ob.hide_render=False;ob.keyframe_insert(data_path='hide_render',frame=start)
 ob.keyframe_insert(data_path='hide_render',frame=end)
 if end<816:
  ob.hide_render=True;ob.keyframe_insert(data_path='hide_render',frame=end+1)
# The original V7 result line has its own visibility keys at frame 540.
# Delete the original after copying: otherwise it overlaps the new states.
bpy.data.objects.remove(template,do_unlink=True)
# All other Act3 text holds its intended contrast and placement.
# Copper/detector ring colors remain schematic indicators, not FEM maps.

# Sanity: source original 824-body CAD file is untouched; only presentation-
# local meshes and illustrative overlays are changed. Preserve V8 flow.
assert len([o for o in bpy.data.objects if o.name.startswith('V8_CURRENT_')])==6
assert len([o for o in bpy.data.objects if o.name.startswith('V8_HALO_')])==6
assert len([o for o in bpy.data.objects if o.name.startswith('V6_PARASITIC_HEAT_')])==6

s.frame_set(1)
s.render.image_settings.file_format='PNG'
s.render.filepath=str(OUT/'frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Brooks_Copper_3D_V9.blend'))
print('V9_SCENE_READY',json.dumps({
 'source_design_hash':hashlib.sha256(DESIGN.read_bytes()).hexdigest(),
 'source_bodies':design['body_count'],
 'source_visual_removed_pin_pad_faces':12,
 'source_CAD_and_physic_parameters_unchanged':True,
 'stage2_hot_ceramic_box_mm':cer,
 'detector_source_box_mm':die,
 'visual_note':'colored rings are illustrative comparison markers, not physical temperature contours',
 'delta_detector_K':audit['nominal_minus_ablation_die_K'],
 'frames':816,'fps':24,
 'file':str(OUT/'Brooks_Copper_3D_V9.blend')
}),flush=True)
if '--preview' in sys.argv:
 s.render.resolution_percentage=80
 for f in (80,380,455,560,675,754,810):
  s.frame_set(f);s.render.filepath=str(OUT/f'preview_{f}.png')
  bpy.ops.render.render(write_still=True)
  print('PREVIEW_READY',f,flush=True)
elif '--render' in sys.argv:
 s.render.resolution_percentage=100
 s.render.image_settings.file_format='FFMPEG'
 s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264'
 s.render.ffmpeg.constant_rate_factor='HIGH'
 s.render.ffmpeg.ffmpeg_preset='GOOD'
 s.render.ffmpeg.audio_codec='NONE'
 s.render.filepath=str(OUT/'Brooks_Photonics_TEC_Cu_3D_V9.mp4')
 bpy.ops.render.render(animation=True)
