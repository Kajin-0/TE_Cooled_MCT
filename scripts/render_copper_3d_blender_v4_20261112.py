"""V4: editorial rebuild for photodetector engineers, source-CAD 3D model.

Not another amendment to V3's awkward supply. V4 starts with original, verified
Blender source-derived TEC geometry, discards all old labels and flow sprites,
and uses a compact INSET electrical circuit schematic. No fictitious wires
attached to a full 3D housing; no animated electrons, no invented thermal field.

Rendered 3D physical model retains original 0.50 mm 29/11/4 architecture.
Four concise acts: shunt mechanism, source-Cu heat budget, thermal-off paired
ablation, material sensitivity. All numbers independently audited elsewhere.
"""
import bpy,math,sys,json,hashlib
from mathutils import Vector
from pathlib import Path
ROOT=Path('/home/User/TE_Cooled_MCT')
D=ROOT/'media/copper_3d_20261112'
OUT=D/'revision04'
OUT.mkdir(exist_ok=True,parents=True)
SRC=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
BASE=ROOT/'data/nominal_gas_visibility_v327_20261111/coupled_attempt01/result.json'
OFF=ROOT/'data/copper_ablation_publication_20261112/result.json'
A=ROOT/'data/copper_ablation_publication_20261112/independent_audit.json'
SENS=ROOT/'data/copper_sensitivity_publication_20261112/k80/independent_audit.json'
g=json.loads(SRC.read_text())
nom=json.loads(BASE.read_text())
off=json.loads(OFF.read_text())
audit=json.loads(A.read_text())
sen=json.loads(SENS.read_text())
assert g['body_count']==824 and audit['status'].startswith('PASS') and sen['status'].startswith('PASS')
assert abs(nom['calculated_detector_temperature_K']-218.6933026695397)<1e-8
assert abs(off['calculated_detector_temperature_K']-211.05888083502677)<1e-8
assert abs(sen['case_minus_baseline_die_K']+1.174606401845523)<1e-8
assert abs(nom['Cu_form_tab_heat_into_ceramic_by_stage_W'][2]-.08741602697695144)<1e-12
header=next(z for z in g['bodies'] if z['name']=='VIGO_reference_header')
assert header['registry']['pinout']['1']=='TEC+'
assert header['registry']['pinout']['9']=='TEC-'

# Start from the original V1 editable source-CAD derived scene.
bpy.ops.wm.open_mainfile(filepath=str(D/'source_cad_copper_thermal_study.blend'))
s=bpy.context.scene
cam=s.camera
assert all(bpy.data.objects.get('formed_tab'+str(n)) for n in (58,80,88))
assert all(bpy.data.objects.get('CAD_'+n) for n in ('ceramic','P','N'))
# Remove all legacy storytelling objects. Preserve all source-derived geometry.
for o in list(bpy.data.objects):
 if o.type=='FONT' or o.name.startswith(('EXPLANATORY_HEAT_MARKER_','V2_','V3_','SCHEMATIC_','DC_SUPPLY_')):
  bpy.data.objects.remove(o,do_unlink=True)

s.frame_start=1;s.frame_end=528;s.render.fps=24;s.frame_step=1
s.render.resolution_x=1080;s.render.resolution_y=1350;s.render.resolution_percentage=100
s.render.engine='BLENDER_WORKBENCH'
cam.data.ortho_scale=14.2
# Minimal slow camera move; avoid dramatic orbit that hides source Cu connections.
# The source 3D cooler occupies the central region, not an enclosing fake package.
for f,xyz in ((1,(11.8,-13.4,12.6)),(121,(11.7,-11.7,12.4)),
              (262,(12.6,-10.0,12.4)),(401,(11.8,-12.0,12.6)),
              (528,(11.8,-13.4,12.6))):
 cam.location=xyz;cam.keyframe_insert(data_path='location',frame=f)
# Remove animation cyclicity if ever injected by earlier scripts.
if cam.animation_data and cam.animation_data.action and hasattr(cam.animation_data.action,'fcurves'):
 for fc in cam.animation_data.action.fcurves:
  for kp in fc.keyframe_points:kp.interpolation='BEZIER'

# The three interstage Cu ribbons have source-correct radii, widths, and pads.
tabmat=bpy.data.materials.get('Cu_hot')
assert tabmat is not None
tabmat.diffuse_color=(0.88,0.53,0.26,1.0)
for f,col in ((1,(.88,.53,.26,1)),(120,(.88,.53,.26,1)),
              (158,(1.,.73,.29,1)),(260,(1.,.73,.29,1)),
              (293,(.88,.53,.26,1)),(528,(.88,.53,.26,1))):
 tabmat.diffuse_color=col
 tabmat.keyframe_insert(data_path='diffuse_color',frame=f)
# Copper material color is illustrative highlighting, never a temperature map.

# Native text/line overlay is parented to camera, intentionally separate from 3D
# source geometry. This is an abstract electrical diagram, NOT 3D power wiring.
colors={
 'V4_WHITE':(.97,.97,.98,1),
 'V4_MUTED':(.65,.72,.79,1),
 'V4_CYAN':(.41,.81,.94,1),
 'V4_GOLD':(1.,.76,.40,1),
 'V4_DARK':(.20,.31,.44,1),
}
materials={}
for n,col in colors.items():
 m=bpy.data.materials.new(n);m.diffuse_color=col;materials[n]=m
fonts=[
 '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
 '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf']
regular=[
 '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
 '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']
def get_font(paths):
 for p in paths:
  if Path(p).exists():return bpy.data.fonts.load(p)
 return None
bold=get_font(fonts)
reg=get_font(regular)
# All overlays share Z=-6.4 in camera space; no hidden mesh overlaps them.
Z=-6.6
def attach(o):o.parent=cam;return o
def visibility(o,first,last):
 if first>1:
  o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=first-1)
 o.hide_render=False;o.keyframe_insert(data_path='hide_render',frame=first)
 o.keyframe_insert(data_path='hide_render',frame=last)
 if last<s.frame_end:
  o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=last+1)
def txt(msg,x,y,sz,material='V4_WHITE',first=1,last=528,heavy=True,align='LEFT'):
 cu=bpy.data.curves.new('V4_'+msg[:18],'FONT')
 cu.body=msg;cu.size=sz;cu.align_x=align
 if (bold if heavy else reg) is not None:cu.font=bold if heavy else reg
 o=bpy.data.objects.new('V4_CAPTION_'+msg[:28],cu)
 bpy.context.collection.objects.link(o)
 attach(o);o.location=(x,y,Z)
 cu.materials.append(materials[material])
 visibility(o,first,last)
 return o
def poly(name,pts,rad,material):
 cu=bpy.data.curves.new('V4_LINE_'+name,'CURVE');cu.dimensions='3D'
 cu.resolution_u=1;cu.bevel_depth=rad;cu.bevel_resolution=2
 pl=cu.splines.new('POLY');pl.points.add(len(pts)-1)
 for p,xy in zip(pl.points,pts):p.co=(xy[0],xy[1],0,1)
 o=bpy.data.objects.new('V4_DIAGRAM_'+name,cu)
 bpy.context.collection.objects.link(o);attach(o)
 o.location=(0,0,Z+.03)
 cu.materials.append(materials[material])
 return o
def circle(name,cx,cy,r,mat):
 pts=[(cx+r*math.cos(2*math.pi*i/56),cy+r*math.sin(2*math.pi*i/56)) for i in range(57)]
 return poly(name,pts,.018,mat)
def rectangle(name,x0,y0,x1,y1,mat):
 return poly(name,[(x0,y0),(x1,y0),(x1,y1),(x0,y1),(x0,y0)],.018,mat)

# Small conventional electrical circuit inset in top-right. The left element
# is a DC voltage source with +/-; right element denotes the electrically
# powered TEC. NO 3D harness/wires/fictional electrical carrier trajectories.
# All geometry lives in screen/camera coordinates and never touches the CAD.
cx,cy=2.66,5.35
circle('DC_SUPPLY_SYMBOL',cx,cy,.39,'V4_CYAN')
txt('+',cx,cy+.095,.23,'V4_CYAN',heavy=True,align='CENTER')
txt('-',cx,cy-.16,.23,'V4_CYAN',heavy=True,align='CENTER')
rectangle('TEC_COMPONENT',4.13,5.07,4.91,5.63,'V4_CYAN')
txt('TEC',4.52,5.23,.22,'V4_WHITE',heavy=True,align='CENTER')
# two continuous, visibly schematic current-feed paths
poly('DC_PLUS_FEED',[(cx,cy+.39),(cx,5.86),(4.52,5.86),(4.52,5.63)],.018,'V4_CYAN')
poly('DC_MINUS_RETURN',[(4.52,5.07),(4.52,4.84),(cx,4.84),(cx,cy-.39)],.018,'V4_CYAN')
# small conventional-current arrowhead right on positive feed
poly('I_POSITIVE_ARROW',[(3.75,5.94),(3.86,5.86),(3.75,5.78)],.025,'V4_CYAN')
txt('DC / 0.596 W',4.52,4.40,.235,'V4_CYAN',heavy=True,align='CENTER')

# Small quiet permanent brand and disclosure; no numeric verification badges.
txt('BROOKS PHOTONICS',-4.99,6.71,.32,'V4_WHITE',heavy=True)
txt('MODEL STUDY  |  ASSUMED INTERFACES  |  PARTIAL CAVITY',
    -4.99,-6.98,.195,'V4_MUTED',heavy=False)

# STORY 1 (5 sec): this is an established effect we quantify, not a new law.
txt('AN ELECTRICAL LINK',-4.99,5.73,.48,'V4_WHITE',first=1,last=121)
txt('IS ALSO A HEAT PATH.',-4.99,5.10,.53,'V4_GOLD',first=1,last=121)
txt('3-STAGE TEC  /  HgCdTe DETECTOR',-4.99,-5.46,.27,'V4_MUTED',
    first=1,last=121)

# STORY 2 (5.9 sec): precise modeled boundary; avoid implying 87mW
# is itself electrical Joule heat or gets dumped straight into the HgCdTe die.
txt('87.4 mW',-4.99,5.55,.77,'V4_GOLD',first=122,last=262)
txt('Cu NET HEAT INTO THE FINAL',-4.99,4.98,.315,'V4_WHITE',first=122,last=262)
txt('STAGE HOT-SIDE CERAMIC',-4.99,4.55,.31,'V4_WHITE',first=122,last=262)
txt('COPPER HIGHLIGHT = THERMAL PATH, NOT A 3D HEAT FIELD',
    -4.99,-5.70,.21,'V4_MUTED',first=122,last=262,heavy=False)

# STORY 3 (5.8 sec): values calculated at MATCHED 595.668mW terminal power.
txt('+7.63 K',-4.99,5.60,.82,'V4_GOLD',first=263,last=402)
txt('MODELED DETECTOR PENALTY',-4.99,4.95,.32,'V4_WHITE',
    first=263,last=402)
txt('Cu THERMAL ON',-4.99,-4.74,.255,'V4_GOLD',first=263,last=402)
txt('DIAGNOSTIC OFF',4.99,-4.74,.255,'V4_MUTED',first=263,last=402,align='RIGHT')
txt('218.69 K',-4.99,-5.33,.53,'V4_GOLD',first=263,last=402)
txt('211.06 K',4.99,-5.33,.53,'V4_WHITE',first=263,last=402,align='RIGHT')
txt('MATCHED INPUT POWER: 595.7 mW',-4.99,-5.92,.24,'V4_MUTED',
    first=263,last=402,heavy=False)

# STORY 4 (5.25 sec): scientifically meaningful controlled sensitivity,
# not an unexplained project-internal audit-count metric.
txt('Cu k: -20%',-4.99,5.61,.61,'V4_WHITE',first=403,last=528)
txt('Tdie: -1.17 K',-4.99,4.91,.60,'V4_GOLD',first=403,last=528)
txt('ONE-FACTOR MODEL SENSITIVITY',-4.99,-4.93,.29,'V4_MUTED',
    first=403,last=528)
txt('INTERCONNECT DESIGN AFFECTS COOLING.',-4.99,-5.55,.35,
    'V4_WHITE',first=403,last=528)

# Assertions targeted at what actually matters in a marketing/publication video.
label_texts=[o.data.body for o in bpy.data.objects if o.name.startswith('V4_CAPTION_')]
assert not any('AUDIT' in t or '6 / 6' in t for t in label_texts)
assert all(bpy.data.objects.get('formed_tab'+str(i)) for i in (58,80,88))
assert not any(o.name.startswith(('V2_','V3_','EXPLANATORY_HEAT_MARKER_'))
               for o in bpy.data.objects)
assert len([o for o in bpy.data.objects if o.name.startswith('V4_DIAGRAM_')])==5
s.frame_set(1)
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
s.render.filepath=str(OUT/'frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Brooks_Copper_Source_Model_V4.blend'))
print('V4_SCENE_READY',json.dumps({
 'source_registry_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),
 'source_body_count':g['body_count'],'no_3d_supply_harness':True,
 'electric_icon':'screen-space conventional DC schematic, not physical wiring',
 'no_current_particles':True,'diagnostic_delta_K':audit['nominal_minus_ablation_die_K'],
 'nominal_power_W':nom['electrical_power_W'],
 'heat_into_final_hot_ceramic_W':nom['Cu_form_tab_heat_into_ceramic_by_stage_W'][2],
 'k80_Tdie_delta_K':sen['case_minus_baseline_die_K'],
 'render_duration_s':s.frame_end/s.render.fps,'framerate':s.render.fps,
 'size':[s.render.resolution_x,s.render.resolution_y],
 'file':str(OUT/'Brooks_Copper_Source_Model_V4.blend')}),flush=True)
if '--preview' in sys.argv:
 s.render.resolution_percentage=80
 for f in (75,191,330,460):
  s.frame_set(f);s.render.filepath=str(OUT/f'preview_{f}.png')
  bpy.ops.render.render(write_still=True)
  print('V4_PREVIEW',f,flush=True)
elif '--render' in sys.argv:
 s.render.resolution_percentage=100
 s.render.image_settings.file_format='FFMPEG'
 s.render.ffmpeg.format='MPEG4'
 s.render.ffmpeg.codec='H264'
 s.render.ffmpeg.constant_rate_factor='HIGH'
 s.render.ffmpeg.ffmpeg_preset='GOOD'
 s.render.ffmpeg.audio_codec='NONE'
 s.render.filepath=str(OUT/'Brooks_Photonics_Interstage_Cu_Heat_Path_V4.mp4')
 bpy.ops.render.render(animation=True)
