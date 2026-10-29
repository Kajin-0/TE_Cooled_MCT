"""Reader-facing PDF policy: use the same checks during tests and PDF extraction."""
import importlib.util
from pathlib import Path
import pytest

_spec = importlib.util.spec_from_file_location(
    'reader_validation', Path(__file__).with_name('validate_report.py')
)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)


def test_reader_policy_rejects_internal_identifiers_across_line_breaks():
    for value in _module.FORBIDDEN_READER_TEXT:
        with pytest.raises(ValueError):
            _module.validate_reader_text('Assessment: ' + value.upper())
    for value in ['SHA\u2011256', 'nitrogen_\npatch1', 'G2a', 'G3a']:
        with pytest.raises(ValueError):
            _module.validate_reader_text(value)


def test_reader_policy_rejects_visible_hashes():
    with pytest.raises(ValueError):
        _module.validate_reader_text('Evidence ' + 'a19f2bcd' * 8)


def test_reader_policy_allows_standalone_science_and_public_citations():
    text = ('Verification matrix: coarse PASS; fine-mesh FAIL, not qualified. '
            '88 legs, 300 K, 0.1 A; pre-solder is physically present. '
            'NIST gas conductivity https://tsapps.nist.gov/publication/; '
            'doi:10.1364/AO.47.000578')
    assert _module.validate_reader_text(text)['passed']


def test_metadata_policy_checks_decoded_unicode_not_pdf_hex_encoding():
    title = 'Thermoelectrically Cooled HgCdTe Photodetector'
    encoded = '<' + title.encode('utf-16').hex() + '>'
    assert _module.validate_reader_text(_module.decode_pdf_metadata(encoded))['passed']
    hidden = '<' + 'Kajin'.encode('utf-16').hex() + '>'
    with pytest.raises(ValueError):
        _module.validate_reader_text(_module.decode_pdf_metadata(hidden))
