"""Independent interval/handedness controls; no V3 CAD or physical simulation."""
import copy
from fractions import Fraction
import importlib.util
import math
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v3_gate',ROOT/'scripts/v3_assembly_source_gate_20261102.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)


class V3Constraints(unittest.TestCase):
    def test_independent_interval_endpoints(self):
        expected=Fraction(44-40,100000)/2-Fraction(25,1000000)
        self.assertAlmostEqual(gate.worst_clearance(.00002,[25e-6]),float(expected))
        self.assertLess(expected,0)
        self.assertAlmostEqual(gate.worst_clearance(140e-6,[25e-6,25e-6]),90e-6)

    def test_unknown_does_not_become_zero_or_pass(self):
        self.assertIsNone(gate.worst_clearance(20e-6,[None,0]))
        self.assertIsNone(gate.thickness_bound(0,0,None,0))
        self.assertEqual(gate.worst_clearance(0,[0]),0)

    def test_invalid_bounds_fail_closed(self):
        for x in (-1,float('nan'),float('inf')):
            with self.subTest(x=x):
                with self.assertRaises(ValueError):gate.worst_clearance(1,[x])
                with self.assertRaises(ValueError):gate.thickness_bound(x,0,0,0)

    def test_layer_multiplicity_analytic(self):
        self.assertAlmostEqual(gate.thickness_bound(1e-6,2e-6,3e-6,4e-6),52e-6)

    def test_IA08_wrong_angle_certainty_and_source_reject(self):
        original=gate.read(ROOT/'data/physical_geometry_audit_20261102/physical_parameter_registry_v2.json')
        for pid,field,value in [('native.pin_step','units','degree'),
                                ('native.central_radius','evidence_class','DOCUMENTED_EXACT_PRODUCT'),
                                ('native.glass_od','source_refs',[{'id':'TEC-01'}])]:
            bad=copy.deepcopy(original)
            next(p for p in bad['parameters'] if p['parameter_id']==pid)[field]=value
            with self.assertRaises(ValueError):gate.pins_si(bad)

    def test_actual_pin_reflection_and_source_stop(self):
        a=gate.analyse();ep=a['pin_endpoints']
        self.assertEqual([(r['net'],r['pin']) for r in ep],[(0,1),(88,9)])
        self.assertAlmostEqual(ep[0]['top_view_pin_xy_m'][0],-.0054*math.cos(math.pi/5))
        self.assertLess(ep[0]['top_view_pin_xy_m'][1],0)
        self.assertGreater(ep[1]['top_view_pin_xy_m'][1],0)
        self.assertFalse(a['hot_mount']['V2_bottom_metallized'])
        self.assertIsNone(a['detector']['actual_pad_stack'])
        self.assertEqual(a['V3_STEP'],'NOT RUN');self.assertTrue(a['overall'].startswith('STOP'))

    def test_source_to_interface_registry_preserves_unknowns(self):
        choices=gate.read(ROOT/'data/tec_assembly_v3_20261102/assembly_choices.json')
        source_ids={s['id'] for s in gate.read(gate.BASE/'source_catalog.json')['sources']}
        inherited={p['parameter_id'] for p in gate.read(ROOT/choices['original_96_record_registry'])['parameters']}
        rows=choices['new_interface_parameters']
        self.assertEqual(len(rows),21);self.assertEqual(len({r['parameter_id'] for r in rows}),21)
        for row in rows:
            self.assertIn(row['inherited_parameter_id'],inherited)
            self.assertTrue(set(row['source_ids'])<=source_ids)
            self.assertIsNone(row['range_SI'])
            if row['evidence_class']=='UNKNOWN':self.assertIsNone(row['value_SI'])
            self.assertEqual(row['CAD'],'NOT AUTHORED; source/process STOP')
        self.assertEqual(choices['V3_STEP'],'NOT RUN')


if __name__=='__main__':unittest.main()
