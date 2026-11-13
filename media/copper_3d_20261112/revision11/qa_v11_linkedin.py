"""Read-only V11 mobile/safe-zone, icon collision, geometry and numerical QA."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
root=Path('/home/User/TE_Cooled_MCT')
s=bpy.context.scene
assert s.render.resolution_x==1080 and s.render.resolution_y==1350
assert s.render.fps==24 and s.frame_end==816
assert not any('FLAME_SUMMARY' in o.name for o in bpy.data.objects)
assert len([o for o in bpy.data.objects if o.name.startswith('V10_TEXT_')])==6
assert len([o for o in bpy.data.objects if o.name.startswith('V10_ICON_')])==20
assert len([o for o in bpy.data.objects if o.name.startswith('V7_VOLTAGE_')])==6
assert len([o for o in bpy.data.objects if o.name.startswith('V8_CURRENT_')])==6
assert all(bpy.data.objects.get('formed_tab'+str(n)) for n in (58,80,88))

def bounds(o):
 if o.type=='MESH': pts=[o.matrix_world@v.co for v in o.data.vertices]
 elif o.type=='FONT':pts=[o.matrix_world@Vector(p) for p in o.bound_box]
 elif o.type=='CURVE':pts=[o.matrix_world@Vector(p.co[:3]) for spl in o.data.splines for p in spl.points]
 else: pts=[o.matrix_world@Vector(p) for p in o.bound_box]
 a=[world_to_camera_view(s,s.camera,p) for p in pts]
 return (min(p.x for p in a),min(p.y for p in a),max(p.x for p in a),max(p.y for p in a))

# Phone-safe source model: important geometry stays within +/- 5% side margins
# even as final camera moves; no original wires disappear off the edge.
minsource=1.;maxsource=0.;minimum_bottom=1.
for f in (1,80,300,380,500,540,567,620,658,714,762,810,816):
 s.frame_set(f);bpy.context.view_layer.update()
 for n in ('CAD_ceramic','CAD_detector','TEC_lead1','TEC_lead9'):
  box=bounds(bpy.data.objects[n])
  minsource=min(minsource,box[0])
  maxsource=max(maxsource,box[2])
  minimum_bottom=min(minimum_bottom,box[1])
  assert box[0]>=.046 and box[2]<=.955,(f,n,'horiz clipping',box)
  assert box[1]>=.085,(f,n,'too close bottom',box)
 for o in bpy.data.objects:
  if o.type=='FONT' and not o.hide_render:
   b=bounds(o)
   assert b[0]>=.045 and b[2]<=.95,(f,'TEXT',o.name,b)
   assert b[1]>=.13 and b[3]<=.96,(f,'TEXT_VERTICAL',o.name,b)

# The warm/cool icons are reasonably close to the numbers but do NOT collide.
gaps=[]
for f in (540,548,567,590,610,620,631,658,680,715,722):
 s.frame_set(f);bpy.context.view_layer.update()
 if f<=620:
  text=bpy.data.objects['V10_TEXT_WARM_TEMP']
  symbols=['V10_ICON_FLAME_OUTLINE','V10_ICON_FLAME_FILL']
 else:
  text=bpy.data.objects['V10_TEXT_COLD_TEMP']
  symbols=['V10_ICON_SNOW_RAY_0','V10_ICON_SNOW_RAY_3']
 t=bounds(text)
 for n in symbols:
  ob=bpy.data.objects[n]
  assert not ob.hide_render
  b=bounds(ob)
  assert b[0]>t[2]+.013,(f,n,'glyph overlaps number',b,t)
  assert b[0]<t[2]+.071,(f,n,'glyph detached',b,t)
  gaps.append(b[0]-t[2])
for f in (734,762,784,816):
 s.frame_set(f)
 assert not bpy.data.objects['V10_TEXT_RESULT'].hide_render
 assert all('FLAME_SUMMARY' not in o.name for o in bpy.data.objects)

# The 3D Cu thermal connection remains present even when highlighted as
# visually disabled; the OFF state only mutes its Cu material.
cu=bpy.data.materials['Cu_hot']
s.frame_set(567);on=tuple(cu.diffuse_color)
s.frame_set(658);off=tuple(cu.diffuse_color)
assert sum(on[:3])>sum(off[:3])+0.28,(on,off)
assert all(bpy.data.objects.get('formed_tab'+str(k)) for k in (58,80,88))

# Validate unique identification of the stage three hot-side ceramic.
cer=bpy.data.objects['CAD_ceramic']
assert len(cer.data.polygons)==24
assert len([p for p in cer.data.polygons if p.material_index==2])==6

A=json.loads((root/'data/nominal_gas_visibility_v327_20261111/coupled_attempt01/result.json').read_text())
B=json.loads((root/'data/copper_ablation_publication_20261112/result.json').read_text())
assert abs(A['calculated_detector_temperature_K']-B['calculated_detector_temperature_K']-
           7.634421834512921)<1e-8
print('V11_QA_PASS',json.dumps({
 'mobile_format':'1080x1350,4:5,24fps,34s',
 'source_horizontal_range':[minsource,maxsource],
 'source_bottom_min':minimum_bottom,
 'icon_number_gaps_normalized':[min(gaps),max(gaps)],
 'summary_flame_present':False,
 'cold_copper_geometry_preserved':True,
 'stage_hot_side_highlighted':True,
 'source_evidence_unchanged':True,
 'project_source_sha256':hashlib.sha256((root/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_bytes()).hexdigest()}),flush=True)
