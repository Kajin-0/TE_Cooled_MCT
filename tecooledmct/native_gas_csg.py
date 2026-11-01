"""One bounded partition of source-native solids and the qualified SI cavity.

This module does not import comparative temperatures, create surrogate solids,
heal CAD, mesh, or solve a thermal field. A failed gate terminates the experiment.
"""
import argparse
from collections import Counter, defaultdict
import gzip
from pathlib import Path
import tempfile
import time

import numpy as np

from .native_gas_audit import ROOT, PACKAGE, read, write, sha
from .corrected_enclosure import assumptions
from .isolated_cap_reader import cap_roles
from .exchange_geometry import verify_sources


def source_bbox(body, dimensions):
    """Physical metre bounds from the immutable construction registry."""
    if 'boxes_m' in body:
        boxes = np.array(body['boxes_m'])
        return np.r_[boxes[:, :3].min(0), (boxes[:, :3]+boxes[:, 3:]).max(0)]
    value = lambda name: dimensions[name]['simulated']*.001
    h = value('header_thickness')
    if body['kind'] == 'header':
        x, y = value('flange_x')/2, value('flange_y')/2
        return np.array([-x, -y, 0., x, y, h])
    if body['kind'] not in ('pin', 'glass'):
        raise ValueError('Unregistered non-box solid')
    x, y = body['center_xy_m']
    pin = body['kind'] == 'pin'
    r = value('pin_diameter' if pin else 'glass_od')/2
    return np.array([x-r, y-r, -value('pin_below_header') if pin else 0.,
                     x+r, y+r, h+(value('pin_stub') if pin else 0.)])


def identify_sources(rows, manifest):
    """Match every source solid uniquely; never infer identity from tag order."""
    result = {}
    for row in rows:
        candidates = [b['id'] for b in manifest['bodies']
                      if np.isclose(row['volume_m3'], b['expected_volume_m3'], rtol=2e-7, atol=1e-20)
                      and np.max(abs(np.array(row['bbox_m'])-source_bbox(b, manifest['registry']['dimensions']))) <= 2.1e-7]
        if len(candidates) != 1 or candidates[0] in result.values():
            raise ValueError('Ambiguous/missing source body: '+str(row))
        result[row['tag']] = candidates[0]
    if set(result.values()) != {b['id'] for b in manifest['bodies']}:
        raise ValueError('Incomplete native source coverage')
    return result


def partition_owners(mapping, identities):
    """Independent set accounting: overlapping physical owners are forbidden."""
    owner = {}
    for body, entries in zip(identities, mapping[1:]):
        for dim, tag in entries:
            if dim != 3:
                raise ValueError('Non-volume Boolean output')
            if tag in owner and owner[tag] != body:
                raise ValueError('Positive-volume solid overlap: '+str((tag, owner[tag], body)))
            owner[tag] = body
    envelope = {tag for dim, tag in mapping[0] if dim == 3}
    gas = envelope-set(owner)
    if len(gas) != 1:
        raise ValueError('Expected one connected gas volume; found '+str(sorted(gas)))
    return owner, envelope, gas.pop()


def check_manifold(oriented_faces, face_edges):
    counts, winding = Counter(), Counter()
    for face in oriented_faces:
        for curve in face_edges[abs(face)]:
            counts[abs(curve)] += 1
            winding[abs(curve)] += int(np.sign(face)*np.sign(curve))
    bad = {e: {'incidences': n, 'signed_sum': winding[e]}
           for e, n in counts.items() if n != 2 or winding[e] != 0}
    if bad:
        raise ValueError('Open/nonmanifold/orientation-incompatible boundary curves: '+str(bad))
    return {'curves': len(counts), 'all_incidence_two': True, 'all_oriented_sums_zero': True}


def run(out, phase_a):
    start = time.monotonic()
    out, phase_a = Path(out).resolve(), Path(phase_a).resolve()
    if out.exists():
        raise ValueError('One attempt only; use an absent output directory')
    out.mkdir(parents=True)
    status = {'qualified': False, 'phase': 'B', 'stage': 'input', 'Boolean_calls': 0,
              'mesh_attempts': 0, 'PDE_solves': 0, 'external_hybrid_wires': 'OFF'}
    def checkpoint(**fields):
        status.update(fields)
        status['elapsed_seconds'] = time.monotonic()-start
        write(out/'status.json', status)
    checkpoint()
    import gmsh
    initialized = False
    try:
        q = read(phase_a/'qualification.json')
        target = ROOT/q['derivative_path']
        if not q['phase_A_qualified'] or sha(target) != q['derivative_sha256']:
            raise ValueError('Unqualified or modified cap derivative')
        sources = verify_sources()
        m, a = read(PACKAGE/'manifest.json'), assumptions()
        write(out/'registration.json', {'input_sha256': sources,
              'cap_derivative_sha256': sha(target), 'code_sha256': sha(__file__),
              'registration': (ROOT/'docs/ISOLATED_CAP_AND_NATIVE_GAS_20261101.md').read_text().split('## Results')[0],
              'scope': 'One native Boolean partition, 216+3 solids, wires OFF; no thermal reference read'})
        gmsh.initialize(); initialized = True
        gmsh.option.setNumber('General.Terminal', 1)
        gmsh.option.setNumber('General.NumThreads', 4)
        gmsh.option.setString('Geometry.OCCTargetUnit', 'M')
        gmsh.model.add('native_gas_audit')
        occ = gmsh.model.occ
        with tempfile.TemporaryDirectory(dir=out) as tmp:
            source = Path(tmp)/'source.step'
            source.write_bytes(gzip.decompress((PACKAGE/'reference.step.gz').read_bytes()))
            native = occ.importShapes(str(source), highestDimOnly=True)
        occ.synchronize()
        rows = [{'tag': t, 'volume_m3': occ.getMass(3, t), 'bbox_m': occ.getBoundingBox(3, t)} for d, t in native if d == 3]
        identities = identify_sources(rows, m)
        cap = occ.importShapes(str(target), highestDimOnly=True); occ.synchronize()
        roles = cap_roles([{'tag': t, 'volume_m3': occ.getMass(3, t), 'bbox_m': occ.getBoundingBox(3, t)} for d, t in cap], a)
        cap_ids = {'shell': 7301, 'roof': 7302, 'window': 7303}
        identities.update({v['tag']: cap_ids[k] for k, v in roles.items()})
        expected = {b['id']: b['expected_volume_m3'] for b in m['bodies']}
        expected.update({cap_ids[k]: v for k, v in a['expected_solid_volumes_m3'].items()})
        write(out/'input_solids.json', {'package_count': len(rows), 'cap_count': len(cap),
              'tag_to_body': identities, 'package_import': rows, 'cap_import': roles})
        checkpoint(stage='Boolean partition', native_solids=len(identities), Boolean_calls=1)
        ri, z0, height = a['inner_radius_m'], a['header_top_z_m'], a['cavity_roof_z_m']-a['header_top_z_m']
        envelope = occ.addCylinder(0., 0., z0, 0., 0., height, ri)
        tags = sorted(identities)
        _, mapping = occ.fragment([(3, envelope)], [(3, t) for t in tags])
        occ.synchronize()
        owner, cylinder, gas = partition_owners(mapping, [identities[t] for t in tags])
        checkpoint(stage='source volume and face ownership', output_solids=len(owner), gas_tag=gas)
        masses = {t: occ.getMass(3, t) for _, t in gmsh.model.getEntities(3)}
        if any(not np.isfinite(v) or v <= 0 for v in masses.values()):
            raise ValueError('Nonpositive/nonfinite Boolean volume')
        totals = defaultdict(float)
        for tag, body in owner.items(): totals[body] += masses[tag]
        errors = {body: totals[body]/v-1 for body, v in expected.items()}
        if max(abs(e) for e in errors.values()) > 2e-7:
            raise ValueError('Source volume changed after Boolean: '+str(errors))
        envelope_volume = np.pi*ri**2*height
        enclosed_solids = sum(masses[t] for t in cylinder if t in owner)
        if not np.isclose(masses[gas]+enclosed_solids, envelope_volume, rtol=2e-7, atol=1e-20):
            raise ValueError('Void/solid partition volume fails conservation')
        contacts = defaultdict(float)
        for _, face in gmsh.model.getEntities(2):
            up, _ = gmsh.model.getAdjacencies(2, face)
            if len(up) > 2: raise ValueError('Nonmanifold solid face')
            if len(up) == 2 and all(int(t) in owner for t in up):
                bodies = tuple(sorted({owner[int(t)] for t in up}))
                if len(bodies) == 2: contacts[bodies] += occ.getMass(2, face)
        wanted = {tuple(sorted(c['bodies'])): c['area_m2'] for c in m['contacts']}
        wanted.update({(300,7301): np.pi*(a['outer_radius_m']**2-ri**2),
                       (7301,7302): np.pi*(a['outer_radius_m']**2-ri**2),
                       (7302,7303): 2*np.pi*a['window_radius_m']*(a['roof_top_z_m']-a['cavity_roof_z_m'])})
        contact_errors = {str(k): contacts.get(k,0.)/v-1 for k,v in wanted.items()}
        unexpected = {str(k):v for k,v in contacts.items() if k not in wanted}
        write(out/'partition.json', {'owner': owner, 'gas_tag': gas, 'gas_volume_m3': masses[gas],
              'cylinder_volume_m3': envelope_volume, 'inside_solid_volume_m3': enclosed_solids,
              'source_volume_relative_errors': errors, 'contacts_m2': {str(k):v for k,v in contacts.items()},
              'contact_relative_errors': contact_errors, 'unexpected_contacts_m2': unexpected})
        if unexpected or max(abs(v) for v in contact_errors.values()) > 1e-6:
            raise ValueError('Changed/unexpected native contact areas')
        oriented = [t for d,t in gmsh.model.getBoundary([(3, gas)], oriented=True) if d == 2]
        faces, edges = [], {}
        for signed in oriented:
            face = abs(signed)
            up, _ = gmsh.model.getAdjacencies(2, face)
            solids = [int(t) for t in up if int(t) != gas]
            if len(up) != 2 or len(solids) != 1 or solids[0] not in owner:
                raise ValueError('Gas boundary lacks exactly one native solid owner: '+str(face))
            edges[face] = [t for d,t in gmsh.model.getBoundary([(2,face)], combined=False, oriented=True) if d == 1]
            faces.append({'tag': face, 'oriented_tag': signed, 'body': owner[solids[0]],
                          'area_m2': occ.getMass(2,face), 'bbox_m': occ.getBoundingBox(2,face),
                          'centroid_m': occ.getCenterOfMass(2,face)})
        write(out/'gas_faces.json', faces)
        topology = check_manifold(oriented, edges)
        checkpoint(stage='normal and containment witnesses', gas_faces=len(faces))
        # A trimmed-face interior witness, not a bbox or centroid assumption.
        for record in faces:
            face = record['tag']; lower, upper = gmsh.model.getParametrizationBounds(2,face)
            found = False
            for s in (.5,.25,.75,.125,.875):
                for t in (.5,.25,.75,.125,.875):
                    uv = np.array(lower)+np.array([s,t])*(np.array(upper)-lower)
                    if not gmsh.model.isInside(2,face,uv,parametric=True): continue
                    point = np.array(gmsh.model.getValue(2,face,uv)); normal = np.array(gmsh.model.getNormal(face,uv))
                    if not np.isclose(np.linalg.norm(normal),1.,rtol=1e-8): raise ValueError('Nonunit face normal')
                    plus, minus = point+1e-6*normal, point-1e-6*normal
                    inside = [bool(gmsh.model.isInside(3,gas,p)) for p in (plus,minus)]
                    if sum(inside) != 1: continue
                    outside = plus if not inside[0] else minus
                    if not any(gmsh.model.isInside(3,t,outside) for t,b in owner.items() if b == record['body']): continue
                    record['normal_witness'] = {'point_m': point, 'outward_unit_normal': normal*(1 if inside[1] else -1),
                                                'probe_m':1e-6,'gas_inside':True,'solid_outside':True}
                    found=True; break
                if found: break
            if not found: raise ValueError('No verifiable gas-to-owner normal witness on face '+str(face))
        write(out/'gas_faces.json', faces)
        if not gmsh.model.isInside(3,gas,[.006,0.,.0043]) or gmsh.model.isInside(3,gas,[0.,0.,.00166]):
            raise ValueError('Independent gas/ceramic containment control failed')
        gmsh.model.setVisibility(gmsh.model.getEntities(),0,recursive=True)
        gmsh.model.setVisibility([(3,gas)],1,recursive=True)
        gmsh.option.setNumber('Geometry.OCCExportOnlyVisible',1)
        gmsh.write(str(out/'gas_only.brep'))
        write(out/'geometry.json', {'qualified':True,'gas_tag':gas,'volume_m3':masses[gas],
              'bbox_m':occ.getBoundingBox(3,gas),'topology':topology,'face_count':len(faces),
              'gas_boundary_area_m2':sum(f['area_m2'] for f in faces),
              'BREP_sha256':sha(out/'gas_only.brep'),'model_coordinate_unit':'metre',
              'boundary_assumptions':'Perfect nominal cap/header and window-rim seals; no porous or microleak geometry; external wires OFF',
              'source_volume_max_relative_error':max(abs(e) for e in errors.values()),
              'contact_max_relative_error':max(abs(e) for e in contact_errors.values()),'gas_PDE_field':None})
        checkpoint(qualified=True,stage='COMPLETE',phase_C='PENDING')
        print('Phase B PASS: one bounded native gas volume; every face has one source solid owner')
    except Exception as exc:
        checkpoint(stage='STOP',reason=str(exc),phase_C='NOT RUN')
        print('Phase B STOP:',exc)
        return False
    finally:
        if initialized: gmsh.finalize()
    return True


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--phase-a',type=Path,required=True)
    args=p.parse_args();run(args.out,args.phase_a)
