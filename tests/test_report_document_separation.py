"""Regression checks for restored historical Rev3 vs distinct current TEC document."""
from pathlib import Path
import hashlib,json,subprocess,shutil
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
OLD='882209b09796acdc5e7d3aafc376f1722fce2843230233c7a76542ebcb273248'
INTERIM='6a9cb56fc3a78ac31639f4cb0b9c40e29d68997ea73b408ac68651eb1789faf5'
CURRENT='f989d75f0987456cf78a049f9876b420abf31969e1ea2fa84f04c9d31afe3e6c'
def test_document_edition_identity():
    a=ROOT/'reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf'
    b=ROOT/'reports/historical/rev3_pre_v33_20261108/report.pdf'
    c=ROOT/'reports/historical/rev3_v33_interim_43pp_20261108/report.pdf'
    d=ROOT/'reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf'
    assert sha(a)==sha(b)==OLD
    assert sha(c)==INTERIM
    assert sha(d)==CURRENT
    assert len({sha(a),sha(c),sha(d)})==3
    pointer=json.loads((ROOT/'reports/rev3_review/current.json').read_text())
    assert pointer['pdf_sha256']==OLD
    assert 'reports/master/generated'==pointer['edition']
def test_current_scientific_source_and_figures():
    p=ROOT/'reports/current'
    m=json.loads((p/'reproduction_manifest.json').read_text())
    assert m['new_physics_solves']==0
    assert m['n_legs']==88 and m['n_pad_faces']==95 and m['n_material_rows']==14
    for name,h in m['figures_sha256'].items():assert sha(p/'figures'/name)==h
    assert 'V3.3' in (p/'report.tex').read_text()
    assert 'Thermoelectric Cooling' in (p/'report.tex').read_text()
    assert 'Package parasitic heat loads' in (p/'report.tex').read_text()
    assert 'formed' in (p/'report.tex').read_text()
    assert 'v34_copper_stage_temperature_comparison' in (p/'report.tex').read_text()
    assert 'v34_copper_face_heat_budget' in (p/'report.tex').read_text()
    assert 'v33_ceramic_fields' in (p/'report.tex').read_text()
    assert 'v35_original_spatial_ceramic_fields' in (p/'report.tex').read_text()
    assert 'v35_full_system_scenario_temperature' in (p/'report.tex').read_text()
    for n in ('v35_full_system_scenario_temperature.pdf', 'v35_original_spatial_ceramic_fields.pdf'):
        assert sha(p/'figures'/n)==m['figures_sha256'][n]
    for name in ('v34_copper_stage_temperature_comparison.pdf','v34_copper_face_heat_budget.pdf'):
        assert sha(p/'figures'/name)==m['figures_sha256'][name]
    source=ROOT/'data/v3_4_copper_multiport_20261108/attempt03/result.json'
    assert sha(source)==m['source_hashes'][str(source.relative_to(ROOT))]
def test_report_page_counts_and_model_identity():
    for filename,n in [('reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf',38),
        ('reports/historical/rev3_v33_interim_43pp_20261108/report.pdf',43),
        ('reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf',28)]:
        # On CI the PDF SHA assertions pin the exact page structures; MuPDF
        # page-count inspection is optional because GitHub runners lack mutool.
        if shutil.which('mutool'):
            out=subprocess.run(['mutool','info',str(ROOT/filename)],capture_output=True,text=True,check=True)
            assert ('Pages: '+str(n)) in out.stdout
    m=(ROOT/'docs/CURRENT_MODEL_DOCUMENTATION_MAP_20261108.md').read_text()
    for marker in ('824','430','formed','net 88','NOT RUN','V3.3'):
        assert marker in m


def test_cumulative_scientific_figures_and_previous_edition_preservation():
    import re
    tex=(ROOT/'reports/current/report.tex').read_text()
    actual=set(re.findall(r"\\fig\[[^]]+\]\{([^}]+)\}",tex))
    required={
        'cad_package_shaded','cad_package_pinout','tec_solid_inspection',
        'tec_formed_tab_sections','v33_topology','tab_screen','mesh_quality',
        'v33_transport','v33_ceramic_fields','v33_cavity_loads','v33_versions',
        'v33_leg_budgets','v33_iterations','v34_copper_stage_temperature_comparison',
        'v34_copper_face_heat_budget','v35_full_system_scenario_temperature',
        'v35_fixed_field_lead_heat_screen','v35_fixed_field_interstage_contact_screen',
        'v35_original_spatial_ceramic_fields'
    }
    assert required<=actual, 'Previously published figures silently removed: '+str(required-actual)
    edition=ROOT/'reports/historical/current_model_editions'
    snapshots=[('v3_3_initial_19pp',19),('v3_3_hardware_22pp',22),
        ('v3_4_copper_25pp',25),('v3_5_leads_29pp',29),('v3_5_cumulative_30pp',30)]
    for folder,pages in snapshots:
        p=edition/folder
        info=json.loads((p/'edition.json').read_text())
        assert info['pages']==pages
        assert sha(p/'report.pdf')==info['sha256']
        assert info['source_commit']
    assert sha(ROOT/'reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf') not in {
        sha(edition/f/'report.pdf') for f,_ in snapshots}


def test_no_duplicate_cover_or_package_figures_and_complete_appendix_b():
    tex=(ROOT/'reports/current/report.tex').read_text()
    import re
    # Cover is a thermal-architecture schematic; internal geometry is shown once.
    assert r'figures/cover_thermal_architecture.pdf' in tex
    assert r'figures/tec_solid_inspection.png' not in tex
    names=re.findall(r'\\fig\[[^]]+\]\{([^}]+)\}\{(?:png|pdf)\}',tex)
    assert len(names)==len(set(names)), 'The same scientific figure is included twice.'
    assert names.count('cad_package_shaded')==1
    assert names.count('cad_package_pinout')==1
    assert 'cad_package_interior_detail' not in names
    # 88 source legs are rendered as 44 two-sided rows, preserving all entries.
    from re import findall
    d=(ROOT/'reports/current/derived_tables.tex').read_text()
    pair=d.split(r'\newcommand{\legpairrows}{',1)[1].split('}',1)[0]
    assert pair.count(' & ')==44*9
    assert pair.count(r'\\')==44
    src=(ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json')
    assert src.exists()
