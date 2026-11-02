"""Source-only assembly constraints; no CAD, mesh, transport or PDE imports.

The output describes the preserved V2 and missing V3 prerequisites. It never
creates or qualifies a V3 assembly from incomplete manufacturing evidence.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/tec_assembly_v3_20261102'
V2 = ROOT / 'data/tec_candidate_29114_v2_20261102/source_final/design.json'
NATIVE = ROOT / 'fem/results/geometry_complete_checkpoint_20261030/manifest.json'


def read(path):
    return json.loads(Path(path).read_text())


def finite_nonnegative(value):
    if not math.isfinite(value) or value < 0:
        raise ValueError('Finite nonnegative physical bound required')
    return value


def worst_clearance(nominal, independent_losses):
    finite_nonnegative(nominal)
    for loss in independent_losses:
        if loss is not None:
            finite_nonnegative(loss)
    if any(loss is None for loss in independent_losses):
        return None
    return nominal - math.fsum(independent_losses)


def thickness_bound(ceramic, leg, metal, solder):
    terms = (ceramic, leg, metal, solder)
    for term in terms:
        if term is not None:
            finite_nonnegative(term)
    if any(term is None for term in terms):
        return None
    return math.fsum(n * u for n, u in zip((4, 3, 6, 6), terms))


def pins_si(registry):
    rows = {r['parameter_id']: r for r in registry['parameters']}
    angle = rows['native.pin_step']
    if angle['units'] != 'rad' or not math.isclose(angle['value_SI'], math.pi / 5, abs_tol=1e-15):
        raise ValueError('IA-08 SI angular identity')
    for key in ('central_radius', 'ear_radius'):
        if rows['native.' + key]['evidence_class'] != 'DERIVED_SOURCE_CONTOUR':
            raise ValueError('Inferred contour promoted to exact')
    if [s['id'] for s in rows['native.glass_od']['source_refs']] != ['HYP-NATIVE']:
        raise ValueError('Analyst seal attributed to manufacturer')
    radius = rows['native.pin_pcd']['value_SI'] / 2
    return {n: [-radius * math.cos(-n * angle['value_SI']),
                radius * math.sin(-n * angle['value_SI'])] for n in range(1, 10)}


def analyse():
    d, native = read(V2), read(NATIVE)
    registry = read(ROOT / 'data/physical_geometry_audit_20261102/physical_parameter_registry_v2.json')
    rows = {r['parameter_id']: r for r in registry['parameters']}
    pins = pins_si(registry)
    for body in native['bodies']:
        if body['kind'] == 'pin':
            if math.dist(body['center_xy_m'], pins[body['pin_number']]) > 1e-14:
                raise ValueError('Native pin handedness mismatch')
    cu = [b for b in d['bodies'] if b['kind'] == 'Cu']
    bottom_metal = any(abs(box[2]) < 1e-12 for body in cu for box in body['boxes_mm'])
    # Only the existing 0.44mm pad / 0.4mm leg nominal geometry is evaluated.
    pad = rows['v2.PN_pad_width']['value_SI']
    leg = rows['v2.leg_section']['value_SI'][0]
    nominal_margin = (pad - leg) / 2
    terminals = {t['node']: [v * .001 for v in t['center_mm']] for t in d['terminals']}
    endpoints = []
    for node, pin in ((0, 1), (88, 9)):
        endpoints.append(dict(net=node, pin=pin, top_view_pin_xy_m=pins[pin],
            module_land_xy_m=terminals[node][:2],
            planar_endpoint_separation_m=math.dist(terminals[node][:2], pins[pin]),
            wire_solid='ABSENT; separation is not installed wire length'))
    return dict(scope='Preserved V2 source constraints; V3 geometry NOT RUN',
        overall='STOP before V3 CAD: source/process and complete-interface gates unresolved',
        original_module=dict(legs=len(d['legs']),Cu_nets=len(cu),source_contacts=176,
            new_contact_graph='NOT RUN; original independently reviewed353-node/352-edge graph unchanged'),
        IA08='PASS SI radians / estimated contour / analyst seal source independently rechecked',
        nominal_pad_margin_m=nominal_margin,
        pad_stress_controls=[dict(relative_offset_m=u,remaining_margin_m=worst_clearance(nominal_margin,[u]),
             evidence='Conditional geometric stress, not a manufacturing tolerance') for u in (10e-6,20e-6,25e-6)],
        worst_case_pad_margin_m=worst_clearance(nominal_margin,[None,None,None]),
        stack_nominal_m=4*.0005+3*.0005+6*15e-6+6*35e-6,
        stack_error_bound_m=thickness_bound(None,None,None,None),
        stack_requirement='4u_c+3u_l+6u_m+6u_s<=150um; constituent bounds UNKNOWN',
        analogy_only=dict(Au_face_edge_rule_m=100e-6,
            P_N_pad_edge_error_budget_m=rows['v2.pad_pullback']['value_SI']-100e-6,
            per_net_equal_edge_error_budget_m=(rows['v2.unrelated_Cu_gap']['value_SI']-100e-6)/2,
            validity='External Au face rule is not a Cu edge-wrap process specification'),
        hot_mount=dict(V2_bottom_metallized=bottom_metal,original_nominal_gap_m=50e-6,
            mounting_solid='ABSENT',finished_bondline_interval_m=None,
            source_prerequisite='Coherent pp13-14: solder attachment needs metallized ceramic'),
        pin_endpoints=endpoints,pin_diameter_m=.00076,PCD_m=.0108,
        illustrative_3quarter_turn_wire_arc_m=1.5*math.pi*(.00076+.0002)/2,
        arc_scope='Coherent header-post convention applied conditionally to stated diameters; no CAD route, wetting or clearance acceptance',
        cap_nominal_roof_clearance_m=.00965-(.00155+.00403),
        cap_worst_case_roof_clearance_m=None,
        detector=dict(source_kind='Bare hypothetical MCT block + attach only',
            actual_pad_stack=None,bonds_7_8='ABSENT; V3 cannot invent a bond to bare MCT'),
        thermistor='UNPOPULATED pins5/6; NOT DEVICE-COMPLETE',
        V3_STEP='NOT RUN',SI_import='NOT RUN',new_meshes=0,new_PDEs=0)


def main(out):
    if out.exists():
        raise ValueError('New output required; preserve previous evidence')
    out.mkdir(parents=True)
    result = analyse()
    (out / 'constraints.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    (out / 'producer.json').write_text(json.dumps(dict(
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        V2_sha256=hashlib.sha256(V2.read_bytes()).hexdigest()),indent=2)+'\n')
    drawings(out, result)
    print(json.dumps(result,indent=2))


def drawings(out, result):
    """Exact existing source-coordinate sections, not new V3 CAD snapshots."""
    d=read(V2);bridge=d['bridges'][0];x=bridge['x_mm']
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="650" viewBox="0 0 900 650">',
         '<rect width="900" height="650" fill="white"/><g font-family="sans-serif" font-size="16" fill="#182530">',
         '<text x="25" y="32" font-size="22">Preserved V2: actual foil/ceramic source section</text>',
         '<text x="25" y="61">x = 1.45 mm; y horizontal, z vertical. V3 CAD NOT RUN.</text>']
    def xy(y,z):return 80+(y-2.2)*560,590-(z-.25)*300
    for body in d['bodies']:
        if body['name'] not in ('ceramic0','ceramic1','Cu_node58'):continue
        for box in body['boxes_mm']:
            if not box[0]<=x<=box[0]+box[3]:continue
            y0,y1=max(2.2,box[1]),min(3.2,box[1]+box[4]);z0,z1=max(.25,box[2]),min(1.75,box[2]+box[5])
            if y1<=y0 or z1<=z0:continue
            px,py=xy(y0,z1);color='#d9e4eb' if body['kind']=='Al2O3' else '#c83e36' if box==bridge['foil_box_mm'] else '#2476a3'
            svg.append(f'<rect x="{px:.3f}" y="{py:.3f}" width="{(y1-y0)*560:.3f}" height="{(z1-z0)*300:.3f}" fill="{color}" stroke="#263746" stroke-width=".6"/>')
    for z in (.5,1.1,1.6):
        _,py=xy(2.2,z);svg.append(f'<text x="12" y="{py+5:.3f}">{z:.1f}</text>')
    for y in (2.2,2.6,3.2):
        px,_=xy(y,.25);svg.append(f'<text x="{px-15:.3f}" y="620">{y:.1f}</text>')
    for y,text in [(130,'Red: 30 um vertical foil'),(160,'Blue: 15 um film / lands'),(200,'0.600 mm open gap'),(230,'0.500 mm ceramic edge'),(275,'100 um film-land inset'),(305,'ZERO inward foil foot'),(345,'No joint / barrier / bend'),(375,'process qualified here.')]:
        svg.append(f'<text x="565" y="{y}">{text}</text>')
    svg.append('</g></svg>');(out/'preserved_v2_section.svg').write_text('\n'.join(svg)+'\n')
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="760" viewBox="0 0 1100 760">',
         '<rect width="1100" height="760" fill="white"/><g font-family="sans-serif" font-size="16" fill="#182530">',
         '<text x="25" y="32" font-size="22">Existing package pin / V2 land coordinates (top view)</text>',
         '<text x="25" y="61">No wire solids or proposed routes drawn. Axes in mm.</text>']
    def xy(x,y):return 370+x*48,390-y*48
    for j,w in enumerate((6.4,5.2,3.8,2.4)):
        a,b=xy(-w/2,w/2);svg.append(f'<rect x="{a}" y="{b}" width="{w*48}" height="{w*48}" fill="none" stroke="#9baeba" stroke-width="1.2"/>')
    reg=read(ROOT/'data/physical_geometry_audit_20261102/physical_parameter_registry_v2.json')
    for n,(x,y) in pins_si(reg).items():
        a,b=xy(x*1000,y*1000);color='#007c64' if n in (1,9) else '#8c4c9e' if n in (7,8) else '#65737d'
        svg.append(f'<circle cx="{a:.3f}" cy="{b:.3f}" r="18.24" fill="white" stroke="{color}" stroke-width="2"/>')
        svg.append(f'<text x="{a-5:.3f}" y="{b+6:.3f}" fill="{color}">{n}</text>')
    for t in d['terminals']:
        x,y,_=t['center_mm'];a,b=xy(x-.25,y+.25)
        svg.append(f'<rect x="{a}" y="{b}" width="24" height="24" fill="#007c64"/>')
        a,b=xy(x,y);svg.append(f'<text x="{a+18}" y="{b+6}">net{t["node"]}</text>')
    for y,text in [(180,'PCD 10.8 mm'),(210,'Shaft diameter 0.76 mm'),(260,'1(+),9(-): TEC'),(290,'7/8: detector, no bonds'),(320,'5/6: unpopulated'),(370,'Pin1 x = -4.36869 mm'),(400,'Pin9 x = -4.36869 mm'),(450,'Land-to-pin XY separation:'),(480,'net0 to1: 2.368414 mm'),(510,'net88 to9: 5.252028 mm'),(560,'These are endpoint distances,'),(590,'not wire lengths or routes.')]:
        svg.append(f'<text x="720" y="{y}">{text}</text>')
    svg.append('</g></svg>');(out/'preserved_v2_pin_map.svg').write_text('\n'.join(svg)+'\n')


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    main(parser.parse_args().out)
