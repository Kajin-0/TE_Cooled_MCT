"""V10 visual-physics presentation gate; read-only verification."""
import bpy,json,hashlib
from pathlib import Path
root=Path('/home/User/TE_Cooled_MCT')
scene=bpy.context.scene
assert scene.frame_end==816 and scene.render.fps==24
assert (scene.render.resolution_x,scene.render.resolution_y)==(1080,1350)
assert not any(o.name.startswith(('V9_SOURCE_MCT_DETECTOR_OUTLINE',
 'V9_STAGE2_HOT_CERAMIC_TARGET','V9_HEAT_TERMINUS_')) for o in bpy.data.objects)
assert all(bpy.data.objects.get('formed_tab'+str(k)) for k in (58,80,88))
die=bpy.data.objects['CAD_detector']
cer=bpy.data.objects['CAD_ceramic']
assert len(die.data.polygons)==6 and len(cer.data.polygons)==24
assert len([x for x in cer.data.polygons if x.material_index==1])==6
assert len([o for o in bpy.data.objects if o.name.startswith('V10_TEXT_')])==6
assert len([o for o in bpy.data.objects if o.name.startswith('V10_ICON_')])==22
assert all(bpy.data.objects.get('V7_VOLTAGE_'+n) for n in ('CIRCLE','POS_LEADER','NEG_LEADER'))
assert all(bpy.data.objects.get('V8_CURRENT_PLUS_'+str(i)) for i in range(3))
assert all(bpy.data.objects.get('V8_CURRENT_RETURN_'+str(i)) for i in range(3))
scenarios=[
 (567,'WARM_TEMP','FLAME_FILL'),
 (658,'COLD_TEMP','SNOW_RAY_0'),
 (762,'RESULT','FLAME_SUMMARY_FILL'),
]
for f,name,icon in scenarios:
 scene.frame_set(f)
 visible=[o.name for o in bpy.data.objects if o.name.startswith('V10_TEXT_') and not o.hide_render]
 assert 'V10_TEXT_'+name in visible,(f,name,visible)
 assert bpy.data.objects['V10_ICON_'+icon].hide_render is False
 for other in ['WARM_TEMP','COLD_TEMP','RESULT']:
  if other!=name:assert bpy.data.objects['V10_TEXT_'+other].hide_render
mat=die.data.materials[0]
scene.frame_set(567);warm=tuple(mat.diffuse_color)
scene.frame_set(658);cold=tuple(mat.diffuse_color)
assert warm[0]>cold[0] and warm[2]<cold[2],(warm,cold)
base=json.loads((root/'data/nominal_gas_visibility_v327_20261111/coupled_attempt01/result.json').read_text())
off=json.loads((root/'data/copper_ablation_publication_20261112/result.json').read_text())
assert abs(base['calculated_detector_temperature_K']-off['calculated_detector_temperature_K']-7.634421834512921)<1e-8
print('V10_QA_PASS',json.dumps({'on_K':base['calculated_detector_temperature_K'],'off_K':off['calculated_detector_temperature_K'],
 'source_model_SHA256':hashlib.sha256((root/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_bytes()).hexdigest(),
 'real_detector_material_changes_color':True,'source_ceramic_top_6_faces':True,
 'no_3d_ring_objects':True,'three_exclusive_results':True,
 'warm_orange':warm,'cold_blue':cold}),flush=True)
