"""Separate compact candidate; stdlib source gates, optional isolated OCC roles.

Run this file directly on the host (package __init__ requires scientific deps).
No imports of v1's author, physics solvers or Gmsh until an explicit CAD role.
All coordinates below are millimetres, SI only at the independent reader.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
ID = 'rmt_inspired_29114_compact_v2'
FILM, SOLDER, FOIL, TRACK = .015, .035, .030, .20
BASES, WIDTHS, COUNTS = (.5, 1.6, 2.7), (6.4, 5.2, 3.8, 2.4), (29, 11, 4)
EPS = 1e-9


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def extent(b):
    return [b[i] + b[i + 3] for i in range(3)]


def spans(a, b):
    return [min(a[i]+a[i+3], b[i]+b[i+3])-max(a[i], b[i]) for i in range(3)]


def touches(a, b):
    s = spans(a, b)
    return min(s) >= -EPS and sum(v > EPS for v in s) >= 2


def union_volume(boxes):
    """Independent exact coordinate partition, not sum of overlapping primitives."""
    axes = [sorted(set(round(v, 12) for b in boxes for v in (b[i], b[i]+b[i+3])))
            for i in range(3)]
    total = 0.
    for cells in itertools.product(*(list(zip(a, a[1:])) for a in axes)):
        mid = [(a+b)/2 for a, b in cells]
        if any(all(b[i]-EPS <= mid[i] <= b[i]+b[i+3]+EPS for i in range(3)) for b in boxes):
            total += math.prod(b-a for a, b in cells)
    return total


def face_trace(a, b):
    """Flat on-ceramic trace; no vertical path is silently made a square post."""
    if abs(a[2]-b[2]) > EPS or sum(abs(a[i]-b[i]) > EPS for i in (0, 1)) != 1:
        raise ValueError('One nonzero planar trace segment required')
    return [min(a[0], b[0])-TRACK/2, min(a[1], b[1])-TRACK/2, a[2],
            abs(a[0]-b[0])+TRACK, abs(a[1]-b[1])+TRACK, FILM]


def design():
    bodies, legs, bridges = [], [], []
    copper = {n: [] for n in range(89)}
    def add(name, kind, boxes, **kw):
        bodies.append(dict(name=name, kind=kind, boxes_mm=boxes, **kw))
    for j, (w, z) in enumerate(zip(WIDTHS, (0., 1.1, 2.2, 3.3))):
        add(f'ceramic{j}', 'Al2O3', [[-w/2, -w/2, z, w, w, .5]])
    offset = 0
    for stage, (n, cols, rows, z) in enumerate(zip(COUNTS, (8, 6, 4), (8, 4, 2), BASES)):
        pos = []
        for row in range(rows):
            for col in (range(cols) if row % 2 == 0 else reversed(range(cols))):
                x, y = (col-(cols-1)/2)*.58, (row-(rows-1)/2)*.58
                if stage == 1: x, y = -x, -y
                if stage == 2: x = -x
                pos.append((round(x, 12), round(y, 12)))
        for k, (x, y) in enumerate(pos[:2*n]):
            j = offset+k; pol = 'N' if k % 2 == 0 else 'P'
            hot, cold = (j, j+1) if pol == 'N' else (j+1, j)
            add(f'leg{j}_{pol}', pol, [[x-.2, y-.2, z+.05, .4, .4, .5]],
                stage=stage, chain_index=j, hot_node=hot, cold_node=cold)
            legs.append(dict(index=j, stage=stage, polarity=pol, hot_node=hot,
                             cold_node=cold, center_mm=[x, y]))
            for face, node, sz, cz in [('hot', hot, z+FILM, z),
                                       ('cold', cold, z+.55, z+.55+SOLDER)]:
                add(f'solder{j}_{face}', 'SnSb', [[x-.2, y-.2, sz, .4, .4, SOLDER]],
                    leg=j, node=node, face=face)
                copper[node].append([x-.22, y-.22, cz, .44, .44, FILM])
        offset += 2*n
    for node, pads in copper.items():
        if len(pads) == 2 and abs(pads[0][2]-pads[1][2]) < EPS:
            a, b = pads
            copper[node].append([min(a[0], b[0]), min(a[1], b[1]), a[2],
                                 abs(a[0]-b[0])+.44, abs(a[1]-b[1])+.44, FILM])

    def trace(node, pts):
        copper[node].extend(face_trace(a, b) for a, b in zip(pts, pts[1:]))

    def step(node, x, side, ceramic, lower_z):
        """0.6-mm foil gap plus 0.5-mm ceramic-supported edge film, not 1.1 post.

        Foil spans metal on two supported lands; finite-area union with edge film.
        Explicit short lap lands on both ceramic faces; dielectric remains intact.
        """
        edge = side*WIDTHS[ceramic]/2
        cbot = (1.1, 2.2)[ceramic-1]
        cy = edge if side > 0 else edge-FOIL
        fy = edge if side > 0 else edge-FILM
        foil = [x-TRACK/2, cy, lower_z, TRACK, FOIL, cbot-lower_z]
        wrap = [x-TRACK/2, fy, cbot-FILM, TRACK, FILM, .5+2*FILM]
        # A .10-mm inward lap fixes each foil end to its ceramic-supported land.
        land_y = edge-.10 if side > 0 else edge-FOIL
        lowland = [x-TRACK/2, land_y, lower_z, TRACK, .10+FOIL, FILM]
        topland = [x-TRACK/2, land_y, cbot+.5, TRACK, .10+FOIL, FILM]
        bottomland = [x-TRACK/2, land_y, cbot-FILM, TRACK, .10+FOIL, FILM]
        copper[node].extend([foil, wrap, lowland, topland, bottomland])
        bridges.append(dict(node=node, ceramic=ceramic, side=side, x_mm=x,
                            free_gap_mm=cbot-lower_z, foil_box_mm=foil,
                            edge_film_box_mm=wrap, lower_z_mm=lower_z,
                            upper_z_mm=cbot+.5, lap_mm=.10))

    # The relocated end pads avoid v1's opposite-edge/perimeter detours.
    trace(0, [[-2.03, -2.03, .5], [-2.03, -2.8, .5]])
    copper[0].append([-2.28, -3.05, .5, .5, .5, FILM])
    trace(58, [[1.45, 2.03, .5], [1.45, 2.60, .5]])
    step(58, 1.45, 1, 1, .5)
    trace(58, [[1.45, 2.60, 1.6], [1.45, .87, 1.6]])

    trace(80, [[.29, -.87, 1.6], [.29, -1.90, 1.6]])
    step(80, .29, -1, 2, 1.6)
    trace(80, [[.29, -1.90, 2.7], [.29, -1.30, 2.7],
               [.87, -1.30, 2.7], [.87, -.29, 2.7]])

    trace(88, [[.87, .29, 2.7], [.87, 1.90, 2.7]])
    step(88, .87, 1, 2, 1.6)
    trace(88, [[.87, 1.90, 1.6], [.87, 2.60, 1.6]])
    step(88, .87, 1, 1, .5)
    trace(88, [[.87, 2.60, .5], [.87, 2.8, .5]])
    copper[88].append([.62, 2.55, .5, .5, .5, FILM])

    for node, boxes in copper.items():
        add(f'Cu_node{node}', 'Cu', boxes, node=node)
    add('auxiliary_attach', 'Attach', [[-.5, -.5, 3.8, 1., 1., .03]])
    add('hypothetical_MCT', 'MCT', [[-.5, -.5, 3.83, 1., 1., .2]])
    return dict(id=ID, coordinate_unit='mm', bodies=bodies, legs=legs, bridges=bridges,
                stage_couples_hot_to_cold=list(COUNTS), terminals=[
                    dict(node=0, center_mm=[-2.03, -2.8, .5+FILM], size_mm=[.5, .5]),
                    dict(node=88, center_mm=[.87, 2.8, .5+FILM], size_mm=[.5, .5])],
                layers_mm=dict(copper_film=FILM, solder=SOLDER, foil=FOIL, trace_width=TRACK),
                source_scope='Separate source-informed prototype; process dimensions assumed, not OEM construction',
                external_pin_wires='OFF / not modeled',
                material_thermal_and_reliability='NOT QUALIFIED')


def connected(boxes):
    seen = {0}
    while True:
        nxt = {j for i in seen for j in range(len(boxes)) if touches(boxes[i], boxes[j])}
        if nxt <= seen: return len(seen) == len(boxes)
        seen |= nxt


def signature_ok(volume_m3, bbox_m, reference):
    """SI-aware reader criterion, also exercised by wrong-scale controls."""
    return (math.isclose(volume_m3,reference['volume_m3'],rel_tol=1e-7,abs_tol=1e-20)
            and max(abs(a-b) for a,b in zip(bbox_m,reference['bbox_m']))<=2.1e-7)


def audit(d):
    bodies, legs = d['bodies'], d['legs']
    if d['coordinate_unit'] != 'mm': raise ValueError('Units must be millimetres')
    if d['layers_mm'] != dict(copper_film=FILM,solder=SOLDER,foil=FOIL,trace_width=TRACK):
        raise ValueError('Layer metadata differs from geometry')
    if len(set(b['name'] for b in bodies)) != len(bodies): raise ValueError('Duplicate body')
    for b in bodies:
        for q in b['boxes_mm']:
            if len(q) != 6 or not all(math.isfinite(v) for v in q) or min(q[3:]) <= 0:
                raise ValueError('Invalid finite/positive primitive')
    cu = {b['node']: b for b in bodies if b['kind'] == 'Cu'}
    if set(cu) != set(range(89)) or sum(b['kind']=='Cu' for b in bodies)!=89 or len(legs) != 88: raise ValueError('Circuit count')
    if Counter(l['stage'] for l in legs) != Counter({0:58, 1:22, 2:8}): raise ValueError('Stage count')
    degrees, contacts, pullbacks = Counter(), [], []
    for l in legs:
        j, st = l['index'], l['stage']; x, y = l['center_mm']
        if l['polarity'] != ('N' if j % 2 == 0 else 'P'): raise ValueError('Cooling polarity')
        expected = (j, j+1) if l['polarity'] == 'N' else (j+1, j)
        if (l['hot_node'], l['cold_node']) != expected: raise ValueError('Chain/polarity mapping')
        actual = next(b for b in bodies if b['name'] == f'leg{j}_{l["polarity"]}')
        if actual['kind'] != l['polarity'] or actual['hot_node'] != l['hot_node'] or actual['cold_node'] != l['cold_node']:
            raise ValueError('Leg body differs from circuit registry')
        if any(abs(a-b) > EPS for a,b in zip(actual['boxes_mm'][0], [x-.2,y-.2,BASES[st]+.05,.4,.4,.5])):
            raise ValueError('Leg dimensions/position')
        for face, node, cz in [('hot', l['hot_node'], BASES[st]),
                                ('cold', l['cold_node'], BASES[st]+.55+SOLDER)]:
            owners = [n for n,b in cu.items() if any(abs(q[2]-cz) < EPS and
                q[0] <= x-.2+EPS and q[1] <= y-.2+EPS and
                q[0]+q[3] >= x+.2-EPS and q[1]+q[4] >= y+.2-EPS and
                abs(q[5]-FILM) < EPS for q in b['boxes_mm'])]
            if owners != [node]: raise ValueError('Missing/ambiguous full pad ownership')
            pullback=WIDTHS[st+(face=='cold')]/2-max(abs(x),abs(y))-.22
            if pullback<.10-EPS:raise ValueError('Full P/N pad not supported on ceramic')
            pullbacks.append(pullback)
            s = next(b for b in bodies if b['name'] == f'solder{j}_{face}')
            sz = BASES[st]+FILM if face == 'hot' else BASES[st]+.55
            if s['node'] != node or s['kind'] != 'SnSb' or any(abs(a-b) > EPS for a,b in zip(s['boxes_mm'][0], [x-.2,y-.2,sz,.4,.4,SOLDER])):
                raise ValueError('Solder/contact layer mismatch')
            contacts.append(dict(leg=j, face=face, node=node, area_mm2=.16))
        degrees.update([l['hot_node'], l['cold_node']])
    if degrees != Counter({n:1 if n in (0,88) else 2 for n in range(89)}): raise ValueError('Branched chain')
    for b in cu.values():
        if not connected(b['boxes_mm']): raise ValueError('Disconnected Cu net: '+b['name'])
    mingap = math.inf
    actual_edges = set()
    electrical_kinds = {'Cu', 'P', 'N', 'SnSb'}
    for i,a in enumerate(bodies):
        for b in bodies[i+1:]:
            for p in a['boxes_mm']:
                for q in b['boxes_mm']:
                    s = spans(p,q)
                    if min(s) > EPS: raise ValueError('Positive-volume overlap '+a['name']+'/'+b['name'])
                    if a['kind'] in electrical_kinds and b['kind'] in electrical_kinds and touches(p,q):
                        actual_edges.add(tuple(sorted((a['name'],b['name']))))
                    if a['kind'] == b['kind'] == 'Cu':
                        gap = math.sqrt(sum(max(0.,-v)**2 for v in s))
                        mingap = min(mingap,gap)
                        if gap < .05-EPS: raise ValueError('Cu isolation gap below registered50um')
    expected_edges = set()
    for l in legs:
        j=l['index'];legname=f'leg{j}_{l["polarity"]}'
        for face,node in [('hot',l['hot_node']),('cold',l['cold_node'])]:
            solder=f'solder{j}_{face}'
            expected_edges.add(tuple(sorted((f'Cu_node{node}',solder))))
            expected_edges.add(tuple(sorted((legname,solder))))
    if actual_edges != expected_edges: raise ValueError('Physical conductor/contact graph differs from series circuit')
    if len(d['bridges']) != 4: raise ValueError('Four explicit gap/edge steps required')
    support = []
    for r in d['bridges']:
        c = next(b for b in bodies if b['name'] == f'ceramic{r["ceramic"]}')['boxes_mm'][0]
        q,f = r['edge_film_box_mm'],r['foil_box_mm']; edge = c[1]+c[4] if r['side'] > 0 else c[1]
        if q not in cu[r['node']]['boxes_mm'] or f not in cu[r['node']]['boxes_mm']:
            raise ValueError('Missing actual bridge geometry')
        if abs((q[1] if r['side']>0 else q[1]+q[4])-edge) > EPS or not touches(q,c):
            raise ValueError('Edge film not ceramic supported')
        if q[0] < c[0]-EPS or q[0]+q[3] > c[0]+c[3]+EPS or abs(q[2]-(c[2]-FILM))>EPS or abs(q[5]-(c[5]+2*FILM))>EPS:
            raise ValueError('Wrong edge coverage')
        if abs(f[2]-r['lower_z_mm'])>EPS or abs(f[5]-.6)>EPS or r['free_gap_mm']>.6+EPS:
            raise ValueError('Excessive free foil span')
        lower = next(b for b in bodies if b['name'] == f'ceramic{r["ceramic"]-1}')['boxes_mm'][0]
        if abs(lower[2]+lower[5]-f[2])>EPS or not (lower[0]<=f[0] and f[0]+f[3]<=lower[0]+lower[3] and lower[1]<=f[1] and f[1]+f[4]<=lower[1]+lower[4]):
            raise ValueError('Foil lower landing unsupported')
        support.append(dict(node=r['node'],ceramic=r['ceramic'],edge_support_mm=c[5],free_gap_mm=f[5]))
    terminals = d['terminals']
    if sorted(t['node'] for t in terminals) != [0,88]: raise ValueError('Two hot terminal nets')
    for t in terminals:
        x,y,z=t['center_mm']
        if abs(z-(.5+FILM))>EPS or not any(q[0]<=x-.25+EPS and q[0]+q[3]>=x+.25-EPS and q[1]<=y-.25+EPS and q[1]+q[4]>=y+.25-EPS and abs(q[2]-.5)<EPS for q in cu[t['node']]['boxes_mm']):
            raise ValueError('Missing hot-side terminal landing')
    # Conservative source-aligned context: all pins projected through full module height.
    native=json.loads((ROOT/'fem/results/geometry_complete_checkpoint_20261030/manifest.json').read_text())
    pins=[b for b in native['bodies'] if b['kind']=='pin']
    dims=native['registry']['dimensions']
    pin_radius=dims['pin_diameter']['simulated']/2
    seal_radius=dims['glass_od']['simulated']/2
    cap=json.loads((ROOT/'data/isolated_cap_native_gas_20261101/phase_A/qualification.json').read_text())
    outer=cap['expected_bbox_m']['shell'][3]*1000
    shell_height=(cap['expected_bbox_m']['shell'][5]-cap['expected_bbox_m']['shell'][2])*1000
    # Independent geometric inference from the qualified annular solid volume.
    ri=math.sqrt(outer**2-cap['cap_roles']['shell']['volume_m3']*1e9/(math.pi*shell_height))
    roof_z=cap['expected_bbox_m']['roof'][2]*1000
    pin_gap=math.inf;seal_gap=math.inf;rad=0.
    for b in bodies:
        for q in b['boxes_mm']:
            if max(abs(q[0]),abs(q[0]+q[3]),abs(q[1]),abs(q[1]+q[4]))>3.2+EPS:
                raise ValueError('Bottom6.4mm envelope')
            rad=max(rad, math.hypot(max(abs(q[0]),abs(q[0]+q[3])),max(abs(q[1]),abs(q[1]+q[4]))))
            if q[2]<-EPS or q[2]+q[5]>4.03+EPS: raise ValueError('Height envelope')
            for p in pins:
                x,y=[v*1000 for v in p['center_xy_m']]
                dist=math.hypot(max(q[0]-x,0.,x-q[0]-q[3]),max(q[1]-y,0.,y-q[1]-q[4]))
                pin_gap=min(pin_gap,dist-pin_radius);seal_gap=min(seal_gap,dist-seal_radius)
    ceramics=[b for b in bodies if b['kind']=='Al2O3']
    for j,c in enumerate(ceramics):
        if c['boxes_mm'] != [[-WIDTHS[j]/2,-WIDTHS[j]/2,round(j*1.1,12),WIDTHS[j],WIDTHS[j],.5]]:
            raise ValueError('Ceramic stack changed')
    if min(pin_gap,seal_gap)<=0 or rad>=ri or 1.55+4.03>=roof_z: raise ValueError('Native package clearance')
    return dict(status='PASS source-only',id=ID,bodies=len(bodies),legs=88,couples=list(COUNTS),
                circuit='One unbranched88-leg chain;89 disjoint connected Cu nets; two hot terminals',
                contacts=contacts,physical_electrical_contact_edges=len(actual_edges),
                minimum_Cu_gap_mm=mingap,minimum_pad_pullback_mm=min(pullbacks),bridge_support=support,
                stage_join_z_mm=1.1,return_z_mm=2.2,maximum_free_foil_mm=.6,
                ceramic_height_mm=3.8,header_gap_mm=1.55-dims['header_thickness']['simulated'],
                cap_radial_clearance_mm=ri-rad,cap_roof_clearance_mm=roof_z-(1.55+4.03),
                cap_inner_radius_from_native_volume_mm=ri,minimum_projected_pin_gap_mm=pin_gap,
                minimum_projected_glass_gap_mm=seal_gap,
                cross_section_mm2={'face_track':TRACK*FILM,'foil':TRACK*FOIL},
                one_A_average_J_A_m2={'face_track':1/(TRACK*FILM*1e-6),'foil':1/(TRACK*FOIL*1e-6)},
                limitations='Ideal sharp-corner foil/film union, contact/adhesion/fatigue/current rating and thermal shunts unqualified; no native pin wiring; STEP requires separate gate')


def source(out):
    if out.exists(): raise ValueError('New output required; preserve prior attempts')
    out.mkdir(parents=True);d=design();a=audit(d)
    for b in d['bodies']: b['volume_mm3']=union_volume(b['boxes_mm'])
    write(out/'design.json',d);write(out/'source_audit.json',a)
    write(out/'producer.json',dict(source_sha256=sha(__file__),v1_design_sha256=sha(ROOT/'data/tec_candidate_29114_20261101/geometry/design.json')))
    print(json.dumps({k:v for k,v in a.items() if k!='contacts'},indent=2))


def diagram(out):
    """Actual saved source-box projection; explicitly not a CAD/field rendering."""
    d=json.loads((out/'design.json').read_text())
    target=out/'source_projection.svg'
    if target.exists():raise ValueError('Existing diagram evidence')
    lines=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="650" viewBox="0 0 1000 650">',
           '<rect width="1000" height="650" fill="white"/>',
           '<g font-family="sans-serif" fill="#202630">',
           '<text x="30" y="35" font-size="22">Compact v2: source-coordinate assembly</text>',
           '<text x="30" y="60" font-size="14">88 legs, 176 P/N pad contacts; no solved field or manufacturing qualification</text>']
    colors={0:'#0072b2',58:'#d55e00',80:'#009e73',88:'#cc79a7'}
    def proj(p):return 320+39*(p[0]-p[1]),390+17*(p[0]+p[1])-58*p[2]
    draw=[]
    for b in d['bodies']:
        for box in b['boxes_mm']:
            x,y,z,dx,dy,dz=box
            points=[(x,y,z),(x+dx,y,z),(x+dx,y+dy,z),(x,y+dy,z),
                    (x,y,z+dz),(x+dx,y,z+dz),(x+dx,y+dy,z+dz),(x,y+dy,z+dz)]
            color=colors.get(b.get('node'),'#af8a42') if b['kind']=='Cu' else {'Al2O3':'#afc4d0','P':'#858b91','N':'#5b626a','SnSb':'#c4c7cc','MCT':'#283c54'}.get(b['kind'],'#b9bec2')
            opacity='.24' if b['kind']=='Al2O3' else '.92'
            for face in ((0,1,5,4),(0,3,7,4),(4,5,6,7)):
                pts=' '.join(f'{proj(points[i])[0]:.3f},{proj(points[i])[1]:.3f}' for i in face)
                draw.append((sum(sum(points[i][:2])+points[i][2]*3 for i in face)/4,
                    f'<polygon points="{pts}" fill="{color}" fill-opacity="{opacity}" stroke="#56616b" stroke-width=".25"/>'))
    lines.extend(s for _,s in sorted(draw,key=lambda p:p[0]))
    for i,(node,color) in enumerate(colors.items()):
        lines.extend([f'<rect x="665" y="{112+i*30}" width="22" height="12" fill="{color}"/>',
                      f'<text x="700" y="{123+i*30}" font-size="15">Net {node}</text>'])
    for y,text in [(285,'15 um face / edge metal'),(310,'30 um formed foil'),(335,'0.6 mm free gap per hop'),(360,'0.5 mm ceramic edge support'),(395,'Joins: 1.1 mm each'),(420,'Return: two explicit steps, 2.2 mm'),(455,'Two hot-side terminal lands'),(480,'No pin wires, Cu field or heat budget'),(540,'Layer sizes and sharp bends are'),(565,'engineering idealizations; process,'),(590,'contact and current rating unqualified.')]:
        lines.append(f'<text x="650" y="{y}" font-size="14">{text}</text>')
    lines.extend(['<text x="30" y="620" font-size="14">All 359 source bodies projected; transparent ceramics. STEP/SI status is recorded separately.</text>','</g></svg>'])
    target.write_text('\n'.join(lines)+'\n')


def writer(out):
    import gmsh
    if out.exists(): raise ValueError('Fresh CAD output required')
    out.mkdir(parents=True);start=time.monotonic();d=design();a=audit(d)
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',4)
    gmsh.option.setString('Geometry.OCCTargetUnit','MM');gmsh.model.add(ID);occ=gmsh.model.occ
    try:
        cube=occ.addBox(20,20,20,1,1,1);occ.synchronize();gmsh.write(str(out/'cube_mm.step'))
        occ.remove([(3,cube)],recursive=True);occ.synchronize();records=[]
        for b in d['bodies']:
            tags=[(3,occ.addBox(*q)) for q in b['boxes_mm']]
            if len(tags)>1: tags=occ.fuse(tags[:1],tags[1:])[0]
            if len(tags)!=1: raise ValueError('OCC disconnected solid '+b['name'])
            tag=tags[0][1];expected=union_volume(b['boxes_mm']);vol=occ.getMass(3,tag)
            if not math.isclose(vol,expected,rel_tol=1e-7,abs_tol=1e-11): raise ValueError('OCC union volume '+b['name'])
            records.append(dict(name=b['name'],tag=tag,volume_m3=vol*1e-9,bbox_m=[v*.001 for v in occ.getBoundingBox(3,tag)]))
        occ.synchronize()
        for r in records:gmsh.model.setEntityName(3,r['tag'],r['name'])
        gmsh.write(str(out/'candidate_v2_mm.step'))
        write(out/'writer.json',dict(status='PASS author only',records=records,unit='MM',CAD_imports=0,
              source_sha256=sha(__file__),STEP_sha256=sha(out/'candidate_v2_mm.step'),cube_sha256=sha(out/'cube_mm.step'),
              gmsh_version=gmsh.__version__,elapsed_seconds=time.monotonic()-start))
    finally:gmsh.finalize()
    print('v2 fresh-mm export PASS; SI reader still required')


def reader(out):
    import gmsh
    # Inspect declarations with existing independent parser, without running old writer.
    from tecooledmct.native_gas_audit import step_units
    out=Path(out)
    if (out/'si_reader.json').exists():raise ValueError('Existing reader evidence')
    r=json.loads((out/'writer.json').read_text())
    for n in ('cube_mm.step','candidate_v2_mm.step'):
        if step_units((out/n).read_text())['metres_per_coordinate_unit']!=1e-3:raise ValueError('Declared STEP units')
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.option.setString('Geometry.OCCTargetUnit','M')
    try:
        tags=gmsh.model.occ.importShapes(str(out/'cube_mm.step'));gmsh.model.occ.synchronize()
        cube_ref=dict(volume_m3=1e-9,bbox_m=[.020,.020,.020,.021,.021,.021])
        if len(tags)!=1 or not signature_ok(gmsh.model.occ.getMass(*tags[0]),gmsh.model.occ.getBoundingBox(*tags[0]),cube_ref):raise ValueError('SI1mm cube control')
        gmsh.model.occ.remove(tags,recursive=True);gmsh.model.occ.synchronize()
        tags=gmsh.model.occ.importShapes(str(out/'candidate_v2_mm.step'));gmsh.model.occ.synchronize()
        available={t for dim,t in tags if dim==3};errors=[]
        if len(available)!=len(r['records']):raise ValueError('SI solid count')
        for b in r['records']:
            matches=[t for t in available if signature_ok(gmsh.model.occ.getMass(3,t),gmsh.model.occ.getBoundingBox(3,t),b)]
            if len(matches)!=1:raise ValueError('SI signature ambiguity '+b['name'])
            t=matches[0];available.remove(t);errors.append(abs(gmsh.model.occ.getMass(3,t)/b['volume_m3']-1))
        write(out/'si_reader.json',dict(status='PASS',solids=len(tags),cube_m3=1e-9,
              max_relative_volume_error=max(errors),target_unit='M',separate_process=True,
              source_sha256=sha(__file__),STEP_sha256=sha(out/'candidate_v2_mm.step')))
    finally:gmsh.finalize()
    print('v2 independent SI import PASS')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('role',choices=('source','diagram','writer','reader'));p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();globals()[args.role](args.out)
