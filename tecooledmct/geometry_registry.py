"""Independent source registry for an explicitly hypothetical reference assembly.

No dependency on any earlier CAD/FEM construction or solved field is permitted.
Lengths in the registry are millimetres; SI conversion is explicit in the mesher.
"""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'data/geometry_rebaseline/reference_v1.json'


def load(path=REGISTRY):
    data = json.loads(Path(path).read_text())
    required = {'nominal', 'tolerance', 'unit', 'definition', 'frame',
                'source', 'evidence', 'simulated', 'absolute_deviation',
                'certainty', 'hypothesis_range'}
    for name, row in data['dimensions'].items():
        if not required <= row.keys():
            raise ValueError('Incomplete dimension provenance: ' + name)
        if row['source'] not in data['sources']:
            raise ValueError('Unknown source: ' + name)
        if row['certainty'] not in ('OEM', 'estimated', 'test-only'):
            raise ValueError('Unknown certainty: ' + name)
        if row['nominal'] is not None and not np.isclose(
                abs(row['simulated']-row['nominal']), row['absolute_deviation']):
            raise ValueError('Wrong deviation: ' + name)
        limits = row['hypothesis_range']
        if limits and not limits[0] <= row['simulated'] <= limits[1]:
            raise ValueError('Outside hypothesis range: ' + name)
    if data['identity']['verified_commercial_assembly']:
        raise ValueError('No evidence establishes this composite commercial assembly')
    return data


def value(data, name):
    return data['dimensions'][name]['simulated']


def pins(data, view='top'):
    """Top axes: page up +y, z out of header; bottom x reverses, y retained."""
    if view not in ('bottom', 'top'):
        raise ValueError('Specify top or bottom')
    radius = value(data, 'pin_pcd') / 2
    angle = np.deg2rad(-np.arange(1, 10)*value(data, 'pin_step'))
    xy = np.c_[radius*np.cos(angle), radius*np.sin(angle)]
    if view == 'top':
        xy[:, 0] *= -1
    return [{'pin': n+1, 'xy_mm': xy[n].tolist(),
             'function': data['pinout'][str(n+1)]} for n in range(9)]


def profile(data, samples=2048):
    """Analytic tangent silhouette: three circular arcs and their common tangents.

    Return dense support points of the three-circle convex hull, independently
    of the Gmsh CSG implementation. The exact ear/central radii are inferred.
    """
    from scipy.spatial import ConvexHull
    theta = np.linspace(0, 2*np.pi, samples, endpoint=False)
    R = value(data, 'central_radius'); r = value(data, 'ear_radius')
    d = value(data, 'hole_pitch')/2
    cloud = np.concatenate([np.c_[x+s*np.cos(theta), s*np.sin(theta)]
                            for x, s in ((0, R), (-d, r), (d, r))])
    return cloud[ConvexHull(cloud).vertices]


def analytic_metrics(data):
    R = value(data, 'central_radius'); r = value(data, 'ear_radius')
    d = value(data, 'hole_pitch')/2; a = (R-r)/d
    theta = np.arccos(a); b = np.sqrt(1-a*a)
    # Green's theorem, four straight tangents plus exposed circle arcs.
    area = 2*R*R*(np.pi/2-theta)+2*r*r*theta+2*d*b*(R+r)
    perimeter = 4*R*(np.pi/2-theta)+4*r*theta+4*d*b
    holes = 2*np.pi*(value(data, 'hole_diameter')/2)**2
    bores = 9*np.pi*(value(data, 'glass_od')/2)**2
    h = value(data, 'header_thickness')
    A = area-holes-bores
    wall = 2*np.pi*value(data, 'hole_diameter')+9*np.pi*value(data, 'glass_od')
    return {'outline_area_mm2': float(area), 'outline_perimeter_mm': float(perimeter),
            'header_area_mm2': float(A), 'header_volume_mm3': float(A*h),
            'header_surface_mm2': float(2*A+(perimeter+wall)*h)}
