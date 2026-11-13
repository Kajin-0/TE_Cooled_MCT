"""V11: targeted LinkedIn finish on user-approved V10, NOT a redesign.

Changes:
 - Remove overlapping flame in +7.63K final summary (no icon belongs there).
 - Align ON flame and OFF snowflake beside numeric temperature values.
 - Preserve frame-safe model footprint with eased-off final camera zoom.
 - Reflow camera-parented text/flat icons after lens change.
 - Make model-only Cu thermal path visibly muted in OFF control while retaining
   metal geometry, electrical circuit and camera.
 - Emphasize the REAL hot-side ceramic of coldest TEC stage in Act 2.
 - Slightly enlarge/clarify one supporting caption for mobile viewing.
Numerical results/geometry/source design untouched. The palette is a
comparison indicator, NOT a measured or FEM thermal field.
"""
import bpy,json,math,hashlib,sys
from mathutils import Vector
from pathlib import Path

ROOT=Path('/home/User/TE_Cooled_MCT')
D=ROOT/'media/copper_3d_20261112'
OUT=D/'revision11'
OUT.mkdir(parents=True,exist_ok=True)
DESIGN=ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json'
src=json.loads(DESIGN.read_text())
nom=json.loads((ROOT/'data/nominal_gas_visibility_v327_20261111/coupled_attempt01/result.json').read_text())
off=json.loads((ROOT/'data/copper_ablation_publication_20261112/result.json').read_text())
assert src['body_count']==824
assert abs(nom['calculated_detector_temperature_K']-off['calculated_detector_temperature_K']-7.634421834512921)<1e-8
assert abs(nom['Cu_form_tab_heat_into_ceramic_by_stage_W'][2]-.08741602697695144)<1e-11
bpy.ops.wm.open_mainfile(filepath=str(D/'revision10/Brooks_Copper_3D_V10.blend'))
s=bpy.context.scene
cam=s.camera
assert s.render.resolution_x==1080 and s.render.resolution_y==1350
assert s.render.fps==24 and s.frame_end==816
assert s.render.engine=='BLENDER_WORKBENCH'
assert all(bpy.data.objects.get('formed_tab'+str(n)) for n in (58,80,88))

# === 1. ICON FIX: SUMMARY MUST NOT HAVE AN OVERLAPPING FLAME =========
# Big +7.63 K headline is itself the focal point. No glyph should cover it.
for n in ('V10_ICON_FLAME_SUMMARY','V10_ICON_FLAME_SUMMARY_FILL'):
    o=bpy.data.objects.get(n)
    assert o,n
    bpy.data.objects.remove(o,do_unlink=True)
# Move ON / OFF icon shapes in data-space (not via camera/visibility transform).
# Result summary intentionally uses zero icons.
def shift_icon(o,dx):
    if o.type=='MESH':
        for v in o.data.vertices:v.co.x+=dx
        o.data.update()
    elif o.type=='CURVE':
        for sp in o.data.splines:
            for p in sp.points:p.co.x+=dx
    else:raise AssertionError(o.type)
for n in ('V10_ICON_FLAME_OUTLINE','V10_ICON_FLAME_FILL'):
    shift_icon(bpy.data.objects[n],-.75)
for o in bpy.data.objects:
    if o.name.startswith('V10_ICON_SNOW_'):
        shift_icon(o,-.82)

# === 2. LINKEDIN MOBILE-SAFE CAMERA: PREVENT CUT-OFF POWER LEADS ======
# The last 11.8mm ortho crop clips TEC lead9 slightly outside frame.
# A calm pullback in Act 3 is enough, without changing camera choreography.
s.frame_set(1)
for f,size in ((1,14.20),(252,14.20),(360,13.10),(528,13.25),
               (670,13.85),(816,13.85)):
    cam.data.ortho_scale=size
    cam.data.keyframe_insert(data_path='ortho_scale',frame=f)
target=bpy.data.objects['CAMERA_TARGET']
for f,z in ((1,3.75),(252,3.75),(360,4.20),(528,4.20),
            (670,4.23),(816,4.23)):
    target.location=(0,0,z)
    target.keyframe_insert(data_path='location',frame=f)

# Fix camera-parented copy/flat icons so the physical size of typography
# remains CONSTANT in output pixels throughout the revised lens zoom.
s.frame_set(1)
position_orig={}
for o in bpy.data.objects:
    if o.name.startswith('V7_TEXT_'):
        position_orig[o.name]=tuple(o.location)
# Existing V7 text uses x~ -5.02 and positions from its original camera frame.
# For the brand, a little extra top padding protects it from LinkedIn UI.
for o in bpy.data.objects:
    if o.name.startswith('V7_TEXT_'):
        x,y,z=position_orig[o.name]
        if o.name=='V7_TEXT_BRAND':y-=.27
        for f in range(1,817,8):
            s.frame_set(f)
            fac=cam.data.ortho_scale/14.2
            o.location=(x*fac,y*fac,z)
            o.scale=(fac,fac,fac)
            o.keyframe_insert(data_path='location',frame=f)
            o.keyframe_insert(data_path='scale',frame=f)
        s.frame_set(816)
        fac=cam.data.ortho_scale/14.2
        o.location=(x*fac,y*fac,z);o.scale=(fac,fac,fac)
        o.keyframe_insert(data_path='location',frame=816)
        o.keyframe_insert(data_path='scale',frame=816)

# Correct exact labels use the SAME baseline x/y as V10 generator.
for o in bpy.data.objects:
    if o.name.startswith('V10_TEXT_'):
        tail=o.name[len('V10_TEXT_'):]
        x,y=-4.98,(5.03 if tail in ('WARM_TEMP','COLD_TEMP','RESULT') else 4.39)
        if tail.startswith('WARM'):start,end=540,620
        elif tail.startswith('COLD'):start,end=631,722
        else:start,end=734,816
        for f in sorted(set(list(range(start,end+1,8))+[start,end])):
            s.frame_set(f);fac=cam.data.ortho_scale/14.2
            o.location=(x*fac,y*fac,-6.5)
            o.scale=(fac,fac,fac)
            o.keyframe_insert(data_path='location',frame=f)
            o.keyframe_insert(data_path='scale',frame=f)
# Keep icons pinned in source-symbol text column; only lens compensation changes.
for o in bpy.data.objects:
    if o.name.startswith('V10_ICON_'):
        if 'SNOW_' in o.name:start,end=631,722
        else:start,end=540,620
        for f in sorted(set(list(range(start,end+1,8))+[start,end])):
            s.frame_set(f);fac=cam.data.ortho_scale/14.2
            o.scale=(fac,fac,fac)
            o.keyframe_insert(data_path='scale',frame=f)

# === 3. CONTROL STATE: SHOW THERMAL PATH DISABLED IN MODEL ===========
# The copper metal remains physically present and the feed still conducts
# current. Desaturating the three modeled Cu tabs is only a visual convention
# for switching OFF passive thermal coupling in the diagnostic calculation.
cu=bpy.data.materials['Cu_hot']
if cu.animation_data:cu.animation_data_clear()
copper=(.91,.54,.29,1)
disabled=(.44,.46,.49,1)
for f,color in (
    (1,copper),(260,copper),(540,copper),(614,copper),
    (632,disabled),(714,disabled),(734,copper),(816,copper)):
    cu.diffuse_color=color
    cu.keyframe_insert(data_path='diffuse_color',frame=f)
# Tame color flicker while still making the ON/OFF change apparent.
if cu.animation_data and hasattr(cu.animation_data.action,'fcurves'):
    for fc in cu.animation_data.action.fcurves:
        for k in fc.keyframe_points:k.interpolation='BEZIER'

# === 4. MODEL CAUSE: WARM ACTUAL HOT CERAMIC OF FINAL TEC STAGE =======
# The source has FOUR ceramic slabs for THREE thermoelectric stages.
# ceramic2 is the hot-side of stage 3; ceramic3 supports the detector.
# Highlight the CERAMIC, not a non-physical wire cage or frame.
cer=bpy.data.objects['CAD_ceramic']
assert len(cer.data.polygons)==24
stage=bpy.data.materials.new('V11_THERMAL_INPUT_TO_STAGE3_HOT_SIDE')
stage.diffuse_color=(.77,.82,.88,1)
cer.data.materials.append(stage)
idx=len(cer.data.materials)-1
faces=0
for p in cer.data.polygons:
    xyz=[cer.data.vertices[n].co for n in p.vertices]
    if all(3.775<=v.z<=4.30 for v in xyz):
        assert p.material_index==0
        p.material_index=idx
        faces+=1
assert faces==6,faces
colors=[
 (1,(.77,.82,.88,1)),(260,(.77,.82,.88,1)),
 (305,(.94,.68,.42,1)),(348,(1.,.76,.45,1)),
 (395,(.91,.62,.39,1)),(454,(.99,.72,.44,1)),
 (514,(.88,.66,.46,1)),(540,(.77,.82,.88,1)),
 (816,(.77,.82,.88,1)),
]
for f,c in colors:
    stage.diffuse_color=c;stage.keyframe_insert(data_path='diffuse_color',frame=f)

# === 5. SMALL COPY FIX FOR MOBILE, NOT A NEW LABEL LAYOUT ============
detail=bpy.data.objects['V7_TEXT_A2_DETAIL']
detail.data.body='Net heat into top-stage hot-side ceramic'
detail.data.size=.30
# Model control explicitly says copper *thermal path* is off, not metal gone.
casedetail=bpy.data.objects['V10_TEXT_COLD_DETAIL']
casedetail.data.body='Copper heat path OFF (model only)'
# Shorter model note reinforces evidence rather than overfilling the screen.
headline=bpy.data.objects['V7_TEXT_A3_HEAD']
headline.data.body='MODEL: COPPER WARMS DETECTOR'

# === OUTPUT AND AUDIT ================================================
assert not any(o.name in ('V10_ICON_FLAME_SUMMARY','V10_ICON_FLAME_SUMMARY_FILL')
               for o in bpy.data.objects)
assert len([o for o in bpy.data.objects if o.name.startswith('V10_TEXT_')])==6
assert len([o for o in bpy.data.objects if o.name.startswith('V10_ICON_')])==20
assert all(bpy.data.objects.get('formed_tab'+str(n)) for n in (58,80,88))
s.frame_set(1)
s.render.image_settings.file_format='PNG'
s.render.filepath=str(OUT/'frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Brooks_Copper_3D_V11.blend'))
print('V11_SCENE_READY',json.dumps({
 'source_design_sha256':hashlib.sha256(DESIGN.read_bytes()).hexdigest(),
 'source_bodies':src['body_count'],
 'source_model_and_evidence_unchanged':True,
 'act2_stage3_hot_side_faces':faces,
 'flame_summary_removed':True,
 'retained_warm_flame_and_cool_snowflake':True,
 'LinkedIn':'1080x1350 4:5, 24fps, 34seconds, mobile-safe framing',
 'simulation_delta_K':nom['calculated_detector_temperature_K']-off['calculated_detector_temperature_K'],
 'model_copper_off':'thermal coupling visualization disabled, Cu geometry remains',
 'scene':str(OUT/'Brooks_Copper_3D_V11.blend')
}),flush=True)

if '--preview' in sys.argv:
    s.render.resolution_percentage=80
    for f in (380,567,658,744,762,810):
        s.frame_set(f)
        s.render.filepath=str(OUT/f'preview_{f}.png')
        bpy.ops.render.render(write_still=True)
        print('PREVIEW_DONE',f,flush=True)
elif '--thumbnail' in sys.argv:
    s.frame_set(762)
    s.render.resolution_percentage=100
    s.render.filepath=str(OUT/'Brooks_Photonics_TEC_Cu_V11_LinkedIn_Cover.png')
    bpy.ops.render.render(write_still=True)
    print('LINKEDIN_COVER_DONE',flush=True)
elif '--render' in sys.argv:
    s.render.resolution_percentage=100
    s.render.image_settings.file_format='FFMPEG'
    s.render.ffmpeg.format='MPEG4'
    s.render.ffmpeg.codec='H264'
    s.render.ffmpeg.constant_rate_factor='PERC_LOSSLESS'
    s.render.ffmpeg.ffmpeg_preset='GOOD'
    s.render.ffmpeg.audio_codec='NONE'
    s.render.filepath=str(OUT/'Brooks_Photonics_TEC_Cu_3D_V11.mp4')
    bpy.ops.render.render(animation=True)
