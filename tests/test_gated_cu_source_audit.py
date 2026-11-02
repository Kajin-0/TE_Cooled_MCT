"""Stdlib-only checks runnable even when the registered FEM runtime is absent."""
import importlib.util
import json,math
from pathlib import Path
import tempfile,unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('gated_cu_source_audit',ROOT/'fem/gated_cu_source_audit.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class SourceOnly(unittest.TestCase):
    def test_uniform_horizontal_resistance_control(self):
        r=module.segment([0,0,0],[1,0,0])
        self.assertTrue(math.isclose(r['area_m2'],3e-9,rel_tol=1e-14))
        self.assertTrue(math.isclose(r['R_ohm_estimate'],1.72e-8*.001/3e-9,rel_tol=1e-14))

    def test_vertical_source_section_is_square(self):
        r=module.segment([0,0,0],[0,0,1])
        self.assertTrue(math.isclose(r['area_m2'],1e-8,rel_tol=1e-14))
        self.assertTrue(math.isclose(r['section_average_J_at1A'],1e8,rel_tol=1e-14))

    def test_invalid_geometry_and_material_fail_closed(self):
        for a,b,kw in [([0,0,0],[1,1,0],{}),([0,0,0],[0,0,0],{}),([0,0,0],[1,0,0],{'rho':-1}),([0,0,0],[1,0,0],{'width':float('nan')})]:
            with self.assertRaises(ValueError):module.segment(a,b,**kw)

    def test_original_primitives_and_no_qualification_claim(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'outputs') as out:r=module.audit(out)
        self.assertTrue(all(x['source_primitive_matched'] for x in r['segment_rows']))
        self.assertTrue(math.isclose(r['vertical_length_m'],.0044,rel_tol=1e-12))
        self.assertTrue(math.isclose(r['difference_ohm'],r['independent_difference_ohm'],rel_tol=1e-12))
        self.assertIsNone(r['qualified_Cu_R_ohm']);self.assertEqual(r['actual_new_reduced_cases'],0)
        self.assertTrue(r['Stage_B'].startswith('NOT RUN') and r['Stage_C'].startswith('NOT RUN'))


if __name__=='__main__':unittest.main()
