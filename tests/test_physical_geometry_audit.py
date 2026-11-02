"""Source-only independent arithmetic/topology/evidence gates; no mesh or PDE."""
import copy
from fractions import Fraction
import importlib.util
import json
import math
from pathlib import Path
import tomllib
import unittest

ROOT=Path(__file__).resolve().parents[1]


def module(name):
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


audit=module('physical_geometry_audit_20261102')
registry=module('build_physical_parameter_registry_20261102')


class PhysicalAudit(unittest.TestCase):
    def test_fractional_analytic_R_G_and_sign_controls(self):
        rho=Fraction(172,10**10);k=400
        expected_R=rho*Fraction(6,10000)/Fraction(6,10**9)
        expected_G=Fraction(k)*Fraction(6,10**9)/Fraction(6,10000)
        r=audit.straight_branch(.0006,6e-9,float(rho),k)
        self.assertAlmostEqual(r['R_ohm'],float(expected_R));self.assertAlmostEqual(r['G_W_K'],float(expected_G))
        self.assertAlmostEqual(r['R_ohm']*r['G_W_K'],float(rho*k))
        rev=audit.straight_branch(.0006,6e-9,float(rho),k,-1)
        self.assertEqual(rev['Joule_W'],r['Joule_W']);self.assertEqual(rev['J_average_A_m2'],-r['J_average_A_m2'])
        self.assertEqual(audit.straight_branch(.0006,6e-9,float(rho),k,0)['Joule_W'],0)
    def test_invalid_physical_units_rejected(self):
        for value in (0,-1,float('nan'),float('inf')):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):audit.straight_branch(value,1e-9,1.72e-8,400)
    def test_union_contact_area_not_double_counted(self):
        self.assertAlmostEqual(audit.rectangular_union_area([[0,0,1,1],[.5,0,1.5,1]]),1.5)
        self.assertEqual(audit.face_contacts([0,0,0,1,1,1],[1,1,0,1,1,1]),[])
        self.assertEqual(len(audit.face_contacts([0,0,0,1,1,1],[1,0,0,1,1,1])),1)
    def test_actual_frozen_source_circuit(self):
        d=audit.read(audit.V2/'source_final/design.json');r=audit.physical_graph(d)
        self.assertEqual((r['vertices'],r['edges'],r['leg_count']),(353,352,88))
        self.assertFalse(r['external_pin1_9_connected'])
        del d['bodies'][next(i for i,b in enumerate(d['bodies']) if b['name']=='Cu_node58')]['boxes_mm'][4]
        # Removing an actual bridge primitive must not be hidden by one body label.
        with self.assertRaises(ValueError):audit.physical_graph(d)
    def test_topology_primitive_removal_control(self):
        d=audit.read(audit.V2/'source_final/design.json');f=d['bridges'][0]['foil_box_mm']
        cu=next(b for b in d['bodies'] if b['name']=='Cu_node58');cu['boxes_mm'].remove(f)
        with self.assertRaisesRegex(ValueError,'Disconnected'):audit.physical_graph(d)
    def test_complete_witness_and_unqualified_lap(self):
        r=audit.audit();self.assertEqual(len(r['foil_lap_findings']),4)
        self.assertTrue(all(x['actual_foil_inward_foot_m']==0 for x in r['foil_lap_findings']))
        self.assertTrue(all(not x['mechanical_lap_joint_qualified'] for x in r['foil_lap_findings']))
        self.assertAlmostEqual(r['conductor_screen']['ideal_series_heat_alarm_W'],.045)
        self.assertEqual({x['ceramic'] for x in r['Cu_ceramic_contacts'] if x['net']==88},{'ceramic0','ceramic1','ceramic2'})
        self.assertAlmostEqual(r['dimensions']['one_axis_full_pad_registration_budget_m'],20e-6)
    def test_topological_STEP_vertices_exclude_datum(self):
        text="SI_UNIT(.MILLI.,.METRE.);#1=CARTESIAN_POINT('',(0.,0.,0.));#2=CARTESIAN_POINT('',(20.,20.,20.));#3=VERTEX_POINT('',#2);#4=CARTESIAN_POINT('',(21.,21.,21.));#5=VERTEX_POINT('',#4);"
        r=audit.STEP_point_bounds(text);audit.check_bounds(r['bbox_m'],[.020,.020,.020,.021,.021,.021])
        for scale in (.001,1000):
            with self.assertRaises(ValueError):audit.check_bounds([x*scale for x in r['bbox_m']],r['bbox_m'])
        with self.assertRaises(ValueError):audit.STEP_point_bounds(text.replace('SI_UNIT(.MILLI.,.METRE.);',''))
    def test_registry_complete_and_deterministic(self):
        r=registry.build();self.assertEqual(r,registry.build());self.assertGreaterEqual(len(r['parameters']),96)
        ids=[p['parameter_id'] for p in r['parameters']];self.assertEqual(len(ids),len(set(ids)))
        for p in r['parameters']:
            for key in ('value_SI','range_SI','range_basis','source_refs','evidence_class','implementation','CAD','mesh_property_prediction','material_specimen_domain','validation','sensitivity','closure_test'):
                self.assertIn(key,p)
            self.assertTrue((ROOT/p['implementation']['path']).exists())
            for s in p['source_refs']:self.assertTrue(s['url'].startswith('https:'));self.assertTrue(s['publisher'] and s['location'])
        pins=next(p for p in r['parameters'] if p['parameter_id']=='v2.physical_pin1_9_connections')
        self.assertIsNone(pins['value_SI']);self.assertEqual(pins['evidence_class'],'UNKNOWN')
    def test_review_role_is_exact_read_only_PR_source(self):
        p=ROOT/'.codex/agents/physical-plausibility-auditor.toml';role=tomllib.loads(p.read_text())
        self.assertEqual(role['model'],'gpt-6.1-sol');self.assertEqual(role['model_reasoning_effort'],'xhigh')
        self.assertIn('STRICTLY READ-ONLY',role['developer_instructions'])
        manifest=audit.read(audit.BASE/'PR_integration.json');expected=next(r['sha256'] for r in manifest['files'] if r['path']==str(p.relative_to(ROOT)))
        self.assertEqual(audit.sha(p),expected)
    def test_IA08_native_units_certainty_and_hypothesis_sources(self):
        rows={p['parameter_id']:p for p in registry.build()['parameters']}
        angle=rows['native.pin_step']
        self.assertEqual(angle['units'],'rad');self.assertAlmostEqual(angle['value_SI'],math.pi/5,15)
        self.assertEqual(angle['inherited_provenance']['unit'],'degree')
        for name in ('central_radius','ear_radius'):
            p=rows['native.'+name]
            self.assertEqual(p['evidence_class'],'DERIVED_SOURCE_CONTOUR')
            self.assertEqual(p['inherited_provenance']['certainty'],'estimated')
        native=audit.read(ROOT/registry.NATIVE)['registry']['dimensions']
        for name,source in native.items():
            p=rows['native.'+name]
            self.assertEqual(p['inherited_provenance']['certainty'],source['certainty'])
            self.assertAlmostEqual(p['value_SI'],source['simulated']*(.001 if source['unit']=='mm' else math.pi/180))
            if source['source'] in ('hypothesis','inferred_stack'):
                self.assertEqual([s['id'] for s in p['source_refs']],['HYP-NATIVE'])
                self.assertEqual(p['evidence_class'],'SCENARIO')
        self.assertEqual(rows['native.flange_x']['evidence_class'],'DOCUMENTED_EXACT_PRODUCT')
        self.assertEqual(registry.build(),audit.read(audit.BASE/'physical_parameter_registry_v2.json'))


if __name__=='__main__':unittest.main()
