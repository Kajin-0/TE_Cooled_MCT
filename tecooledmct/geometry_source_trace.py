"""Extract only the selected numerical top-outline from the identified source.

Reproduction input: mutool draw -q -F svg -o vigo.svg <official.pdf> 1.
No whole manufacturer page, logo, or proprietary original image is published.
"""
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np

NUMBER = r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?'


def extract(svg, pdf):
    expected = '1f17637e02eb9ca0c340be6d936a485ae632ef7b12d9d7ea26e7664b42d6fc01'
    if hashlib.sha256(Path(pdf).read_bytes()).hexdigest() != expected:
        raise ValueError('Different source drawing: reinspection required')
    paths = [e for e in ET.parse(svg).getroot().iter()
             if e.tag.endswith('path') and not e.get('id', '').startswith('font')]
    # Explicit source-specific segment indices, visually checked against p1 top view.
    segments = []
    for element in paths[170:222]:
        matrix = list(map(float, re.findall(NUMBER, element.get('transform', ''))))
        numbers = list(map(float, re.findall(NUMBER, element.get('d', ''))))
        if matrix[:4] != [1, 0, 0, -1] or numbers[:2] != [0, 0]:
            raise ValueError('Unexpected source vector convention')
        start = np.array(matrix[-2:])
        text = element.get('d')
        delta = [numbers[2], 0] if 'H' in text else [0, numbers[2]] if 'V' in text else numbers[2:]
        if len(delta) != 2:
            raise ValueError('Unexpected source path command')
        segments.append([start, start+np.array(delta)*[1, -1]])
    segments = np.array(segments)
    closure = np.linalg.norm(segments[:, 1]-np.roll(segments[:, 0], -1, axis=0), axis=1).max()
    if closure > .001:
        raise ValueError('Not a closed source silhouette')
    # Uniform source scale from two top-view hole centres, NOT from the FEM fit.
    # Positions read from source circle extents: x=51.12,189.48 pt; common y=546.12.
    scale = (189.48-51.12)/24.4
    origin = np.array([120.30, 546.12])
    xy = (segments[:, 0]-origin)/scale*[1, -1]
    if not np.allclose(np.ptp(xy, axis=0), [31.5, 17.5], atol=.04):
        raise ValueError('Wrong source view/scale')
    return {'source': 'VIGO ZTM-TO66-Z030 Rev9 p1 top view', 'pdf_sha256': expected,
            'svg_sha256': hashlib.sha256(Path(svg).read_bytes()).hexdigest(),
            'selection': 'non-font SVG path segments170..221 inclusive; MuPDF SVG output',
            'scale_pt_per_mm': scale, 'source_origin_pt': origin.tolist(),
            'scale_basis': 'mounting hole pitch24.4mm; no anisotropic rescaling or contour fit',
            'segment_closure_pt': float(closure), 'reading_uncertainty_mm': .04,
            'tooling_contour_tolerance_known': False, 'xy_mm': xy.tolist()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--svg', type=Path, required=True)
    parser.add_argument('--pdf', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); data = extract(args.svg, args.pdf)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2)+'\n')
