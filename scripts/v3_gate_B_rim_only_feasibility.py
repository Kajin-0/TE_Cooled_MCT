#!/usr/bin/env python3
"""Original Gate B contact-rim-only fixed-field correction feasibility STOP.

No PDE. Reads source-hashed saved P2 contact-vs-raw face radial ledger.
Constructs an exact *fixed-field counterfactual*: remove all raw-vs-contact
bias attributed to r>=0.9 R_CAD centroid triangles while KEEPING interior
per-triangle error unchanged. This is NOT a lower bound for a future re-solve:
a new PDE solution would redistribute current globally.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/v3_physical_blocker_closure_20261106/attempt01/lead9_contact_operator_audit.json'
HISTORICAL=ROOT/'data/v3_interconnect_et_20261102/B/gate_B.json'
CANDIDATE=ROOT/'data/v3_gate_B_original_P2_20261106/attempt01/P2_coupon_result.json'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def evaluate():
    j=json.loads(SOURCE.read_text())
    original=json.loads(HISTORICAL.read_text())
    p2=json.loads(CANDIDATE.read_text())
    assert j['native_lead9_triangles']==318
    assert j['no_PDE_or_mesh_changes']
    assert original['status']=='FAIL/STOP'
    assert p2['status']=='STOP prospective P2 original coupon raw current gate'
    limit=0.001
    assert p2['P2_raw_cut_max_relative_error']>limit
    result={}
    for name,expected_n in (('lead_land',158),('lead_pin',160)):
        x=j['lead_interfaces'][name]
        op=x['contact_operator_consistency']
        bins=op['radial_triangle_centroid_bins']
        assert len(bins)==4
        assert x['source_registered_triangles']==expected_n
        assert bins[-1]['radius_over_CAD_radius_range']==[0.9,1.05]
        I=abs(op['weak_contact_current_A'])
        assert I>1
        i_core=sum(b['signed_other_side_bias_A'] for b in bins[:-1])
        i_rim=bins[-1]['signed_other_side_bias_A']
        i_core_lead=sum(b['signed_lead9_bias_A'] for b in bins[:-1])
        i_rim_lead=bins[-1]['signed_lead9_bias_A']
        assert abs(i_core+i_rim-op['raw_other_material_side']['signed_bias_A'])<1e-11
        assert abs(i_core_lead+i_rim_lead-op['raw_lead9_side']['signed_bias_A'])<1e-11
        r={
          'source_contact':'lead9 -> '+name,
          'original_source_interface_face_id':x['source_registered_face_tags'][0],
          'native_registered_TRI3':expected_n,
          'original_P2_raw_cut_error_fraction':x['prospective_P2_gate_error_rel'],
          'contact_law_current_magnitude_A':I,
          'fixed_field_other_material_inner_band_signed_bias_A':i_core,
          'fixed_field_other_material_rim_band_signed_bias_A':i_rim,
          'fixed_field_lead9_inner_band_signed_bias_A':i_core_lead,
          'fixed_field_lead9_rim_band_signed_bias_A':i_rim_lead,
          'counterfactual_other_material_error_if_all_rim_bias_removed_fraction':abs(i_core)/I,
          'counterfactual_lead9_error_if_all_rim_bias_removed_fraction':abs(i_core_lead)/I,
          'counterfactual_both_sides_max_error_if_all_rim_bias_removed_fraction':
              max(abs(i_core),abs(i_core_lead))/I,
          'registered_original_cut_gate_fraction':limit,
          'counterfactual_other_material_excess_factor':abs(i_core)/I/limit,
          'counterfactual_both_sides_excess_factor':max(abs(i_core),abs(i_core_lead))/I/limit,
          'rim_face_area_fraction_by_centroid':bins[-1]['area_fraction'],
          'rim_other_side_absolute_mismatch_share':bins[-1]['fraction_of_abs_mismatch_on_second_material_side'],
          'rim_lead9_side_absolute_mismatch_share':bins[-1]['fraction_of_abs_mismatch_on_lead9_side'],
          'conditional_rim_only_gate':'FAIL/STOP' if max(abs(i_core),abs(i_core_lead))/I>limit else 'PASS'}
        assert r['conditional_rim_only_gate']=='FAIL/STOP'
        result[name]=r
    return {
       'status':'NO GO: isolated contact-rim current correction cannot satisfy original 0.1% gate with saved interior field frozen',
       'decision':'Do not authorize a rim-only mesh/field correction campaign from this evidence',
       'scope':'strict fixed-original-P2-field counterfactual; NOT a PDE prediction, NOT a mathematical bound on a newly solved field',
       'counterfactual_definition':'Set all existing outer r>=0.9 R_CAD centroid-bin raw-current-minus-contact-law face biases to exactly zero, retain all inner-bin signed biases unchanged, preserve original unit-drive and denominator',
       'original_0p1pct_criterion':limit,
       'face_results':result,
       'alternative_readiness':'Require a separately registered full-interface numerical model whose predicted gradient and weak-contact consistency improve on all 16 cuts, and independent physical property evidence',
       'historical_original_Gate_B':'FAIL/STOP',
       'existing_prospective_P2':'STOP',
       'thermal_C_D':'NOT RUN',
       'physical_contact_material_law_release':'NOT QUALIFIED',
       'geometry_mesh_fields_modified':False,
       'new_PDE_runs':0,
       'codex_used':False,
       'input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (SOURCE,HISTORICAL,CANDIDATE)}
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path)
    parser.add_argument('--verify-only',action='store_true')
    arg=parser.parse_args()
    a=evaluate()
    if arg.verify_only:
        assert arg.out and arg.out.is_file()
        assert json.loads(arg.out.read_text())==a
    elif arg.out:
        arg.out.parent.mkdir(parents=True,exist_ok=True)
        with arg.out.open('x') as out:
            json.dump(a,out,indent=2)
            out.write('\n')
    print('ORIGINAL_GATE_B_RIM_ONLY_NO_GO')
    for k,v in a['face_results'].items():
        print(k,'other_inner_fixed_error_pct=',round(100*v['counterfactual_other_material_error_if_all_rim_bias_removed_fraction'],6),
          'worst_both_sides_fixed_error_pct=',round(100*v['counterfactual_both_sides_max_error_if_all_rim_bias_removed_fraction'],6),
          'gate_excess_factor=',round(v['counterfactual_both_sides_excess_factor'],3))
if __name__=='__main__':
    main()
