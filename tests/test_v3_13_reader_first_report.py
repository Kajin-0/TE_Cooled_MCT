"""Reader-first scientific source-preservation and PDF release gates."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'reports/current'

def test_original_eighteen_major_sections_present_once_and_ordered():
    m=json.loads((R/'reader_first_organization_manifest.json').read_text())
    raw=(R/'cumulative_report.tex').read_text()
    new=(R/'reader_first_report.tex').read_text()
    original=set(m['original_section_SHA256'])
    assert len(original)==18
    for heading in original:
        assert raw.count('\\section{'+heading+'}')==1
        assert new.count('\\section{'+heading+'}')==1
    positions=[new.index('\\section{'+name+'}') for name in m['new_section_order'] if not name.startswith('@')]
    assert positions==sorted(positions)
    assert new.index('\\section{Device construction and thermal architecture}')<new.index('\\section{Current versus cooling performance: an operating envelope (V3.6)}')
    assert new.count('\\appendix')==1
    assert raw[raw.index('\\appendix'):]==new[new.index('\\appendix'):]

def test_includes_source_science_without_losing_old_reports():
    s=(R/'reader_first_report.tex').read_text()
    for name in ['expanded_tec_to_studies_20261109.tex','v312_contact_mounting_section.tex','v313_port_qualification_section.tex']:
        assert s.count('\\input{'+name+'}')==1
    assert (R/'TEC_HgCdTe_Cumulative_TEC_TO_20261109_Contact_Engineering_Rev4.pdf').is_file()
    assert (R/'TEC_HgCdTe_Current_Architecture_20261108.pdf').is_file()
    assert (R/'TEC_TO_Reader_First_Assessment_20261109_V313.pdf').is_file()

def test_report_organisation_source_hash_and_erratum():
    m=json.loads((R/'reader_first_organization_manifest.json').read_text())
    assert hashlib.sha256((R/'reader_first_report.tex').read_bytes()).hexdigest()==m['new_tex_sha256']
    sections=(R/'v312_contact_mounting_section.tex').read_text()
    assert 'Bi57Sn43' in sections
    assert 'Bi58Sn42' in sections
    assert '19~micrometre' in sections
    assert 'Sn95Sb5 bulk resistance' not in sections
    assert 'Sn95Sb5 used at the different P/N leg interfaces' in sections
