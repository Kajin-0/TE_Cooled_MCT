"""Revision 2: concise high-fidelity Blender 3D TEC explanation with schematic DC drive.

Loads existing original-CAD derived editable Blender scene. Keeps source bodies
untouched, gives explicit physical terminal anchors from source TEC lead1/lead9,
adds a visibly schematic DC supply and two cyan drive paths, and distinguishes
these from animated amber passive HEAT transport in formed Cu tabs.

No electrons are rendered inside P/N legs: P-type charge transport may involve
holes. The cyan dots denote electrical drive, NOT individual electrons.
"""
from pathlib import Path
import json, math, hashlib
import bpy
from mathutils import Vector

ROOT=Path('/home/User/TE_Cooled_MCT')
SRC=ROOT/'media/copper_3d_20261112/source_cad_copper_thermal_study.blend'
OUT=ROOT/'media/copper_3d_20261112/revision02'
OUT.mkdir(parents=True,exist_ok=True)
design=json.loads((ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_text())
baseline=json.loads((ROOT/'data/nominal_gas_visibility_v327_20261111/coupled_attempt01/result.json').read_text())
ablation=json.loads((ROOT/'data/copper_ablation_publication_20261112/result.json').read_text())
audit=json.loads((ROOT/'data/copper_ablation_publication_20261112/independent_audit.json').read_text())
assert audit['status'].startswith('PASS') and abs(
    baseline['calculated_detector_temperature_K']-ablation['calculated_detector_temperature_K']-
    7.634421834512921)<1e-8
assert design['body_count']==824
bpy.ops.wm.open_mainfile(filepath=str(SRC))
s=bpy.context.scene
s.render.fps=24
s.frame_step=1
s.frame_start=1
s.frame_end=528
s.render.resolution_x=1080
s.render.resolution_y=1350
s.render.resolution_percentage=100
s.render.engine='BLENDER_WORKBENCH'
cam=s.camera

# Remove verbose original text (but preserve all 3D geometry).
for o in list(bpy.data.objects):
    if o.name.startswith('LABEL_') or o.name.startswith('EXPLANATORY_HEAT_MARKER_'):
        bpy.data.objects.remove(o,do_unlink=True)
for key,color in {
 'DRIVE_CYAN':(0.30,0.84,0.94,1),
 'DRIVE_DARK':(0.24,0.35,0.51,1),
 'DRIVE_LIGHT':(0.52,0.69,0.81,1),
 'HEAT_GOLD':(1.,0.69,0.30,1),
}.items():
    if key not in bpy.data.materials:
        m=bpy.data.materials.new(key);m.diffuse_color=color
M={m.name:m for m in bpy.data.materials}
# Selected original two TEC power leads, hidden in V1. Their source geometry
# remains at source coordinates and directly terminates at ceramic contact pads.
for name in ('TEC_lead1','TEC_lead9'):
    o=bpy.data.objects.get(name)
    assert o is not None,name
    o.hide_render=False

def box(name,center,dims,mat,bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    o=bpy.context.object;o.name=name
    o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(M[mat])
    if bevel:
        b=o.modifiers.new('Shallow rounded instrument enclosure','BEVEL')
        b.width=bevel;b.segments=3
        o.modifiers.new('Weighted face normals','WEIGHTED_NORMAL')
    return o

def sphere(name,r,pos,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=r,location=pos)
    o=bpy.context.object;o.name=name;o.data.materials.append(M[mat])
    return o

def cylinder(name,r,start,end,mat):
    a=Vector(start);b=Vector(end);d=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=r,depth=d.length,
                                       location=(a+b)/2)
    o=bpy.context.object;o.name=name
    o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    o.data.materials.append(M[mat])
    return o

def polyline(name,points,r,material):
    c=bpy.data.curves.new(name,'CURVE')
    c.dimensions='3D';c.resolution_u=2
    c.bevel_depth=r;c.bevel_resolution=3
    spl=c.splines.new('POLY');spl.points.add(len(points)-1)
    for v,co in zip(spl.points,points):
        v.co=(*co,1)
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o)
    c.materials.append(M[material])
    return o

def get_body(name):
    return next(b for b in design['bodies'] if b['name']==name)

# Place the power-supply glyph outside the original TEC geometry, connected to
# its SOURCE-VERIFIED pin1/pin9 lead endpoints. Instrument is intentionally
# schematic (not a physical integrated millimeter-sized battery).
term1=Vector(get_body('TEC_lead1')['parts'][-1]['b'])
term9=Vector(get_body('TEC_lead9')['parts'][-1]['b'])
ps=Vector((-4.65,-2.0,2.60))
# A miniature CAD-like two-terminal DC supply outside the TEC package.
supply=box('SCHEMATIC_EXTERNAL_DC_POWER_SUPPLY',ps,(1.55,2.1,1.15),
           'DRIVE_DARK',bevel=.12)
for k,(dy,label) in enumerate(((-.57,'1'),(.57,'9'))):
    st=Vector((ps.x+.86,ps.y+dy,ps.z+.05))
    sphere('DC_SUPPLY_PORT_'+label,.15,st,'DRIVE_CYAN')
    if label=='1':pstart1=st
    else:pstart9=st
# Source CAD external leads are at package pin1 and pin9 terminals. Schematic
# cables connect *those actual source-defined terminal points*, not fake Cu nets.
paths_drive=[
 [tuple(pstart1),(-5.13,-2.17,ps.z+.11),(-5.13,-3.25,2.22),tuple(term1)],
 [tuple(pstart9),(-4.92,-.93,ps.z+.11),(-6.10,3.45,2.24),tuple(term9)]]
for j,path in enumerate(paths_drive):
    polyline('SCHEMATIC_DC_FEED_PIN_'+str((1,9)[j]),path,.045,'DRIVE_CYAN')
# A small pale supply datum point: physical body is a schematic overlay.
sphere('SCHEMATIC_SOURCE_STATUS',.085,(ps.x-.52,ps.y-1.01,ps.z+.6),'DRIVE_CYAN')

# Animated cyan current indication ONLY on feed leads: not electrons, not a
# claim about carrier polarity in N vs P thermoelectric legs.
def animate_dots(prefix,path,r,mat,start,end,count=2,period=100,reverse=False):
    p=[Vector(v) for v in path]
    lengths=[(b-a).length for a,b in zip(p[:-1],p[1:])]
    total=sum(lengths)
    for dot in range(count):
        o=sphere(prefix+str(dot),r,p[0],mat)
        for f in range(start,end+1,8):
            phase=((f-start)/period+dot/count)%1
            u=(1-phase if reverse else phase)*total
            for j,L in enumerate(lengths):
                if u<=L or j==len(lengths)-1:
                    q=p[j].lerp(p[j+1],max(0,min(1,u/L)))
                    break
                u-=L
            o.location=q
            o.keyframe_insert(data_path='location',frame=f)
        # Workbench animated visibility remains held throughout the segment.
        if start>1:
            o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=start-1)
        o.hide_render=False;o.keyframe_insert(data_path='hide_render',frame=start)
        o.keyframe_insert(data_path='hide_render',frame=end)
        if end<s.frame_end:
            o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=end+1)

animate_dots('SCHEMATIC_DRIVE_PULSE_PIN1_',paths_drive[0],.085,
             'DRIVE_CYAN',1,528,count=2,period=112)
animate_dots('SCHEMATIC_DRIVE_PULSE_PIN9_',paths_drive[1],.085,
             'DRIVE_CYAN',1,528,count=2,period=112,reverse=True)

# The three original formed Cu source centerlines, bottom to upper; amber
# markers indicate possible heat-transfer pathways, NOT optical temperature data.
def centerline(tab):
    out=[]
    for p in tab['parts']:
        a=Vector(p['a']);b=Vector(p['b'])
        if not out:out.append(tuple(a))
        if p['type']=='arc':
            c=Vector(p['c']);v1=a-c;v2=b-c
            angle1=math.atan2(v1.y,v1.x)
            delta=(math.atan2(v2.y,v2.x)-angle1+math.pi)%(2*math.pi)-math.pi
            for j in range(1,9):
                th=angle1+j*delta/8
                out.append((c.x+p['r']*math.cos(th),c.y+p['r']*math.sin(th)))
        else:out.append(tuple(b))
    return [(tab['x'],y,z) for y,z in out]

for net in (58,80,88):
    p=centerline(get_body('formed_tab'+str(net)))
    animate_dots('SCHEMATIC_CU_THERMAL_TRANSFER_'+str(net)+'_',
                 p,.061,'HEAT_GOLD',133,268,count=3,period=84)

# Camera labels: no extra dense tables or screen-sized paragraphs.
fonts=[f for f in bpy.data.fonts if f.filepath and 'Bold' in f.name]
font=fonts[0] if fonts else None
def label(body,xy,size,material='white',start=1,end=528,bold=True,align='LEFT'):
    cu=bpy.data.curves.new('V2_LABEL','FONT');cu.body=body;cu.size=size
    if font and bold:cu.font=font
    cu.align_x=align
    o=bpy.data.objects.new('V2_TEXT_'+body[:23],cu)
    bpy.context.collection.objects.link(o)
    o.parent=cam;o.location=(xy[0],xy[1],-8)
    cu.materials.append(M[material])
    if start>1:
        o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=start-1)
    o.hide_render=False;o.keyframe_insert(data_path='hide_render',frame=start)
    o.keyframe_insert(data_path='hide_render',frame=end)
    if end<528:
        o.hide_render=True;o.keyframe_insert(data_path='hide_render',frame=end+1)
    return o

# Four 5.5 s acts. Persistent identity and unmissable model limitation.
label('BROOKS PHOTONICS',(-5.45,6.83),.31,'white',1,528)
label('SIMULATION  |  PARTIAL CAVITY',(-5.45,-7.20),.22,'muted',1,528)
# Schematic power source described on every act, not a fabricated source CAD part.
label('SCHEMATIC DC SUPPLY',(-5.45,3.84),.23,'DRIVE_CYAN',1,528)
label('P = 596 mW',(-5.45,3.47),.24,'white',1,528)

# Opening.
label('COPPER CARRIES CURRENT.',(-5.45,5.96),.51,'white',1,132)
label('AND HEAT.',(-5.45,5.27),.68,'HEAT_GOLD',1,132)
label('3-STAGE TEC  /  29-11-4 COUPLES',(-5.45,-5.75),.26,'muted',1,132)

# Heat path, distinguish from the cyan DC source traces.
label('87.4 mW',(-5.45,5.60),.88,'HEAT_GOLD',133,268)
label('INTO FINAL STAGE HOT SIDE',(-5.45,4.96),.32,'white',133,268)
label('AMBER: SCHEMATIC HEAT FLOW',(-5.45,-5.85),.24,'HEAT_GOLD',133,268)

# Controlled comparison.
label('+7.63 K',(-5.45,5.57),.88,'HEAT_GOLD',269,400)
label('MODELED DETECTOR PENALTY',(-5.45,4.94),.33,'white',269,400)
label('218.69 K  ON    /    211.06 K  OFF',(-5.45,-5.56),.31,'white',269,400)
label('THERMAL-OFF IS A DIAGNOSTIC',(-5.45,-5.98),.235,'muted',269,400)
label('MATCHED INPUT: 595.7 mW',(-5.45,-6.35),.23,'muted',269,400)

# Scientific checks, no invented confidence interval or empirical claim.
label('6 / 6 AUDITS PASSED',(-5.45,5.55),.61,'white',401,528)
label('Cu k / FOIL / CONTACT SCREENED',(-5.45,4.92),.27,'HEAT_GOLD',401,528)
label('UNMEASURED INTERFACES',(-5.45,-5.82),.25,'muted',401,528)

s.frame_set(1)
s.render.image_settings.color_mode='RGB'
s.render.image_settings.file_format='PNG'
s.render.filepath=str(OUT/'frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'copper_heat_leak_blender_v2.blend'))
print('REVISION_2_SCENE_READY',json.dumps({
 'source_design_bodies':design['body_count'],
 'source_terminal1':list(term1),'source_terminal9':list(term9),
 'schematic_power_supply':list(ps),'duration_s':s.frame_end/s.render.fps,
 'frame_rate':s.render.fps,'resolution':[s.render.resolution_x,s.render.resolution_y],
 'result_K':audit['nominal_minus_ablation_die_K'],
 'blend':str(OUT/'copper_heat_leak_blender_v2.blend')}),flush=True)

import sys
if '--preview' in sys.argv:
    for f in (75,190,330,460):
        s.frame_set(f)
        s.render.resolution_percentage=80
        s.render.filepath=str(OUT/f'preview_{f}.png')
        bpy.ops.render.render(write_still=True)
        print('PREVIEW_DONE',f,flush=True)
elif '--render' in sys.argv:
    s.render.resolution_percentage=100
    s.render.image_settings.file_format='FFMPEG'
    s.render.ffmpeg.format='MPEG4'
    s.render.ffmpeg.codec='H264'
    s.render.ffmpeg.constant_rate_factor='HIGH'
    s.render.ffmpeg.ffmpeg_preset='GOOD'
    s.render.ffmpeg.audio_codec='NONE'
    s.render.filepath=str(OUT/'Brooks_Photonics_Copper_Thermal_Bypass_3D_V2.mp4')
    bpy.ops.render.render(animation=True)
