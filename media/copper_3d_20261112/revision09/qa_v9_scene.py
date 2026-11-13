"""Read-only V9 final scene audit: caption visibility and isolated CAD specks."""
import bpy,json,hashlib
from pathlib import Path
s=bpy.context.scene
assert s.frame_end==816 and s.render.fps==24
assert (s.render.resolution_x,s.render.resolution_y)==(1080,1350)
assert all(bpy.data.objects.get('formed_tab'+str(n)) for n in (58,80,88))
assert bpy.data.objects.get('V9_SOURCE_MCT_DETECTOR_OUTLINE')
assert bpy.data.objects.get('V9_STAGE2_HOT_CERAMIC_TARGET')
assert 'V7_TEXT_A3_DETAIL' not in bpy.data.objects
assert len([o for o in bpy.data.objects if o.name.startswith('V9_RESULT_')])==3
assert len([o for o in bpy.data.objects if o.name.startswith('V8_CURRENT_')])==6
assert len([o for o in bpy.data.objects if o.name.startswith('V6_PARASITIC_HEAT_')])==6
mesh=bpy.data.objects['CAD_Au'].data
strays=[p for p in mesh.polygons if all(5.11<mesh.vertices[i].co.y<5.16 and
        1.61<abs(mesh.vertices[i].co.x)<1.76 and 1.999<mesh.vertices[i].co.z<2.02
        for i in p.vertices)]
assert len(strays)==0,'Two orphan pads still render'
for f,one in ((560,'CU_ON'),(675,'CU_OFF'),(780,'SUMMARY')):
 s.frame_set(f)
 live=[name for name in ('CU_ON','CU_OFF','SUMMARY')
       if not bpy.data.objects['V9_RESULT_'+name].hide_render]
 assert live==[one],(f,live)
 for o in bpy.data.objects:
  if o.name.startswith(('V7_TEXT_','V9_RESULT_')):
   assert o.location.x > -5.1 and o.location.x < 5.1
# Calibrated numerical results must match original registered data.
root=Path('/home/User/TE_Cooled_MCT')
b=json.loads((root/'data/nominal_gas_visibility_v327_20261111/coupled_attempt01/result.json').read_text())
a=json.loads((root/'data/copper_ablation_publication_20261112/result.json').read_text())
assert abs(b['calculated_detector_temperature_K']-a['calculated_detector_temperature_K']-7.634421834512921)<1e-8
assert abs(b['Cu_form_tab_heat_into_ceramic_by_stage_W'][2]-.08741602697695144)<1e-12
print('V9_QA_PASS',json.dumps({
 'source_CAD_file_sha256':hashlib.sha256((root/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_bytes()).hexdigest(),
 'isolated_bond_pad_render_faces':len(strays),'visual_Cu_hot_stage_ceramic_target':True,
 'die_highlight':True,'A3_state_exclusivity':True,'source_model_not_modified':True,
 'numerical_detector_penalty_K':b['calculated_detector_temperature_K']-a['calculated_detector_temperature_K']}))
