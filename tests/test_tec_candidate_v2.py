"""Fast independent geometry/circuit controls; no Gmsh/runtime/physics imports."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import unittest

PATH=Path(__file__).resolve().parents[1]/'tecooledmct/tec_candidate_v2.py'
spec=importlib.util.spec_from_file_location('compact_candidate_v2_source',PATH)
v2=importlib.util.module_from_spec(spec);spec.loader.exec_module(v2)


class CompactSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.original=v2.design()
    def fixture(self):return copy.deepcopy(self.original)
    def test_actual_physical_chain_and_envelope(self):
        a=v2.audit(self.fixture())
        self.assertEqual(a['legs'],88);self.assertEqual(len(a['contacts']),176)
        self.assertEqual(a['physical_electrical_contact_edges'],352)
        self.assertEqual(a['bodies'],359)
        self.assertAlmostEqual(a['minimum_Cu_gap_mm'],.14)
        self.assertGreater(a['minimum_projected_pin_gap_mm'],.78)
        self.assertGreater(a['cap_radial_clearance_mm'],2.57)
        self.assertEqual([r['node'] for r in a['bridge_support']],[58,80,88,88])
        self.assertTrue(all(abs(r['free_gap_mm']-.6)<1e-12 for r in a['bridge_support']))
    def test_independent_exact_union(self):
        self.assertAlmostEqual(v2.union_volume([[0,0,0,1,1,1],[.5,0,0,1,1,1]]),1.5)
        self.assertAlmostEqual(v2.union_volume([[0,0,0,1,1,1],[1,0,0,1,1,1]]),2.)
        self.assertTrue(v2.connected([[0,0,0,1,1,1],[1,0,0,1,1,1]]))
        self.assertFalse(v2.connected([[0,0,0,1,1,1],[1,1,0,1,1,1]]))
    def test_removed_real_foil_breaks_chain(self):
        d=self.fixture();r=d['bridges'][0]
        next(b for b in d['bodies'] if b.get('node')==58 and b['kind']=='Cu')['boxes_mm'].remove(r['foil_box_mm'])
        with self.assertRaisesRegex(ValueError,'Disconnected|Missing actual'):v2.audit(d)
    def test_pad_shrink_rejects(self):
        d=self.fixture();q=next(b for b in d['bodies'] if b['name']=='Cu_node0')['boxes_mm'][0];q[3]=.30
        with self.assertRaisesRegex(ValueError,'pad ownership'):v2.audit(d)
    def test_short_rejects(self):
        d=self.fixture();c=next(b for b in d['bodies'] if b['name']=='Cu_node2')
        c['boxes_mm'].append(copy.deepcopy(next(b for b in d['bodies'] if b['name']=='Cu_node0')['boxes_mm'][0]))
        with self.assertRaises(ValueError):v2.audit(d)
    def test_polarity_and_body_disagreement_reject(self):
        for which in ('registry','body'):
            with self.subTest(which=which):
                d=self.fixture()
                if which=='registry':d['legs'][0]['polarity']='P'
                else:next(b for b in d['bodies'] if b['name']=='leg0_N')['kind']='P'
                with self.assertRaisesRegex(ValueError,'polarity|Leg body'):v2.audit(d)
    def test_dimensions_and_units_reject(self):
        for val in (0,-.1,math.nan,math.inf):
            with self.subTest(val=val):
                d=self.fixture();d['bodies'][0]['boxes_mm'][0][3]=val
                with self.assertRaisesRegex(ValueError,'finite/positive'):v2.audit(d)
        d=self.fixture();d['coordinate_unit']='m'
        with self.assertRaisesRegex(ValueError,'Units'):v2.audit(d)
    def test_support_moved_rejects(self):
        d=self.fixture();d['bodies'][1]['boxes_mm'][0][1]+=.05
        with self.assertRaises(ValueError):v2.audit(d)
    def test_foil_cannot_become_tall_post(self):
        d=self.fixture();r=d['bridges'][0]
        next(b for b in d['bodies'] if b['name']=='Cu_node58')['boxes_mm'][
            next(b for b in d['bodies'] if b['name']=='Cu_node58')['boxes_mm'].index(r['foil_box_mm'])][5]=1.1
        with self.assertRaisesRegex(ValueError,'foil span|overlap'):v2.audit(d)
    def test_exposed_terminal_must_be_hot(self):
        d=self.fixture();d['terminals'][1]['center_mm'][2]=2.715
        with self.assertRaisesRegex(ValueError,'hot-side'):v2.audit(d)
    def test_replay_deterministic_and_v1_untouched(self):
        self.assertEqual(v2.design(),v2.design())
        self.assertEqual(v2.sha(v2.ROOT/'data/tec_candidate_29114_20261101/geometry/candidate_mm.step'),
                         '03a9b1e2aac418fdf4e9bc160955dd1f1c0428d616c29adf8c9ef03ad0e901d7')
    def test_SI_signature_rejects_both_thousand_scale_errors(self):
        ref=dict(volume_m3=1e-9,bbox_m=[.020,.020,.020,.021,.021,.021])
        self.assertTrue(v2.signature_ok(ref['volume_m3'],ref['bbox_m'],ref))
        for scale in (.001,1000):
            self.assertFalse(v2.signature_ok(ref['volume_m3']*scale**3,[x*scale for x in ref['bbox_m']],ref))
    def test_saved_source_and_actual_CAD_provenance(self):
        root=v2.ROOT/'data/tec_candidate_29114_v2_20261102'
        saved=json.loads((root/'source_final/design.json').read_text());current=v2.design()
        for b in current['bodies']:b['volume_mm3']=v2.union_volume(b['boxes_mm'])
        self.assertEqual(saved,current)
        producer=json.loads((root/'source_final/producer.json').read_text())
        self.assertEqual(v2.sha(root/'source_final/producer.py.source'),producer['source_sha256'])
        w=json.loads((root/'cad/writer.json').read_text());r=json.loads((root/'cad/si_reader.json').read_text())
        self.assertEqual(v2.sha(root/'cad/producer.py.source'),w['source_sha256'])
        self.assertEqual(r['source_sha256'],w['source_sha256'])
        self.assertEqual(v2.sha(root/'cad/candidate_v2_mm.step'),w['STEP_sha256'])
        self.assertEqual(r['STEP_sha256'],w['STEP_sha256'])
        self.assertEqual(r['solids'],359);self.assertLess(r['max_relative_volume_error'],1e-7)


if __name__=='__main__':unittest.main()
