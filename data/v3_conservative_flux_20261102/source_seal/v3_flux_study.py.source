"""Fail-closed electrical study. Never runs thermal C/D or changes inputs."""
import argparse,datetime,hashlib,json,time
from pathlib import Path
import numpy as np
from .v3_et_geometry import read,write
from .v3_et_fem import Operator,tensors,SCENARIOS
from .v3_flux_rt0 import FluxSpace
from .candidate_cu_fem import plane_current

BASE=Path('data/v3_conservative_flux_20261102')
OLD=Path('data/v3_interconnect_et_20261102')


def sealed():
    r=read(BASE/'registration.json')
    for name,h in r['sealed_files'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=h:
            raise ValueError('Sealed input/source changed: '+name)


def geometry_audit(out):
    m=np.load(out/'mesh.npz');reg=read(out/'registry.json');p=m['points'];t=m['cells']
    v=abs(np.linalg.det(p[t[:,1:]]-p[t[:,:1]]))/6
    records=[]
    for i,g in enumerate(reg['groups']):
        vv=float(v[m['regions']==i].sum());records.append(dict(name=g['name'],relative_volume_error=vv/g['volume_m3']-1))
    total=float(v.sum()/sum(g['volume_m3'] for g in reg['groups'])-1)
    ok=abs(total)<=.0025 and all(abs(q['relative_volume_error'])<=.005 for q in records)
    r=dict(status='PASS' if ok else 'FAIL/STOP',total_relative_volume_error=total,individual=records,
           tets=len(t),current_CAD_volume_unchanged=True,mesh_unit='NPZ metres; MSH millimetres')
    write(out/'fidelity.json',r)
    return r


def coupon(meshdir,out):
    import meshio
    out.mkdir(exist_ok=False)
    m=np.load(meshdir/'mesh.npz');reg=read(meshdir/'registry.json')
    op=Operator(m['points'],m['cells'],m['regions'],m['triangles'],m['faceids'],reg,tensors(reg['groups']),SCENARIOS['NOM']['re'])
    raw,u,J,H=op.electrical();space=FluxSpace(op,SCENARIOS['NOM']['re'])
    qm,pm=space.mixed();qr,pr=space.recover(u,J,raw['unit_potential_current_A'])
    results={};arrays=dict(P1_u=u,P1_J=J,face_nodes=space.faces,cell_faces=space.cf,cell_signs=space.signs)
    for name,q,pressure in [('mixed',qm,pm),('recovered',qr,None)]:
        a=space.evaluate(q);j=a.pop('J_quadrature');locations=a.pop('locations');powers=a.pop('interface_power_faces')
        a['R_coupon_ohm']=1/a['input_A'];a['IV_loss_relative_error']=abs(a['total_W']/a['input_A']-1)
        a['interface_losses_by_pair_W']={}
        for f in np.flatnonzero(space.contact):
            info=space.meta[f];pair=str(tuple(info['owners']))
            a['interface_losses_by_pair_W'][pair]=a['interface_losses_by_pair_W'].get(pair,0)+float(powers[f])
        # Cuts use the original registry and current-path graph expectations.
        cuts=[]
        for c in raw['cuts']:
            if 'pair' not in c:continue
            owners=[next(i for i,g in enumerate(reg['groups']) if g['name']==n) for n in c['pair']]
            value=0.
            for f in np.flatnonzero(space.contact):
                if space.meta[f]['owners']==owners:
                    first_region=op.r[space.incidence[f][0][0]]
                    value+=q[f]*(1 if first_region==owners[0] else -1)
            cuts.append(dict(pair=c['pair'],A=float(value),relative_error=float(abs(value-c['expected_fraction']*a['input_A'])/a['input_A'])))
        a['interfaces']=cuts
        a['worst_interface_relative_error']=max(c['relative_error'] for c in cuts)
        # Source-free RT0 is cell-constant when Dq=0. Preserve all original
        # interior planes and report the residual controlling this limit.
        a['interior_cuts']=[]
        for c in raw['cuts']:
            if 'interior' not in c:continue
            name='lead9' if c['interior']=='lead9_mid' else 'tab88'
            region=next(i for i,g in enumerate(reg['groups']) if g['name']==name)
            use=op.r==region
            current,area=plane_current(op.p,op.t[use],j.mean(axis=1)[use],c['axis'],c['position_m'])
            a['interior_cuts'].append(dict(name=c['interior'],A=current,area_m2=area,
                relative_error=abs(current+a['input_A'])/a['input_A']))
        a['bounded']=None if pressure is None else bool(pressure.min()>=-1e-8 and pressure.max()<=1+1e-8)
        a['voltage_min']=None if pressure is None else float(pressure.min())
        arrays[name+'_q']=q;arrays[name+'_J']=j.mean(axis=1)
        if pressure is not None:arrays[name+'_cell_V']=pressure
        results[name]=a
        scale=.4/a['input_A']
        meshio.write(out/(name+'_0p4A.vtu'),meshio.Mesh(op.p,[('tetra',op.t)],
          cell_data={'J_A_m2':[j.mean(axis=1)*scale],'region':[op.r]}))
    np.savez_compressed(out/'fields.npz',**arrays)
    write(out/'P1_raw.json',raw);write(out/'alternative.json',results)
    # Strict combined release retains raw P1; no recovered substitute.
    ok=all(raw['gates'].values()) and raw['minimum_voltage']>=-1e-8 and raw['maximum_voltage']<=1+1e-8
    ok=ok and all(r['worst_interface_relative_error']<=.001 and r['terminal_relative_error']<=.001 and r['max_cell_imbalance_relative']<=1e-9 and max(c['relative_error'] for c in r['interior_cuts'])<=.001 and r['IV_loss_relative_error']<=.005 for r in results.values())
    ok=ok and results['mixed']['bounded']
    return dict(status='PASS' if ok else 'FAIL/STOP',R=results['mixed']['R_coupon_ohm'],raw_gate=raw['gates'],mixed_bounded=results['mixed']['bounded'])


def run(role,out):
    sealed()
    if role=='controls':
        from .v3_flux_controls import campaign
        campaign(out);return
    if read(BASE/'controls/gate.json')['status']!='PASS':raise ValueError('Control gate not PASS; no geometry')
    from .v3_flux_geometry import mesh
    out.mkdir(exist_ok=False);then=time.monotonic();previous=None
    for level,h in [('L1',.035),('L2',.025)]:
        directory=out/level
        mesh(directory,OLD/'geometry',h)
        audit=geometry_audit(directory)
        if audit['status']!='PASS':
            write(out/'gate.json',dict(status='FAIL/STOP',reason='geometry fidelity',level=level,coupon='NOT RUN',C='NOT RUN',D='NOT RUN'));return
        result=coupon(directory,out/(level+'_field'))
        if result['status']!='PASS':
            write(out/'gate.json',dict(status='FAIL/STOP',reason='raw or alternative field gate',level=level,C='NOT RUN',D='NOT RUN'));return
        if previous is not None:
            # Major interfaces >=1e-7 W at0.4A; all pair losses retained.
            current=read(out/(level+'_field/alternative.json'))
            errors=[]
            for method,r in current.items():
                for pair,power in r['interface_losses_by_pair_W'].items():
                    a=power*(.4/r['input_A'])**2
                    old=previous[method];b=old['interface_losses_by_pair_W'][pair]*(.4/old['input_A'])**2
                    errors.append(abs(a-b)/max(abs(a),abs(b),1e-7))
            rerr=max(abs(previous[method]['R_coupon_ohm']/r['R_coupon_ohm']-1) for method,r in current.items())
            write(out/'gate.json',dict(status='PASS' if rerr<=.01 and max(errors)<=.02 else 'FAIL/STOP',R_refinement=rerr,max_interface_loss_refinement=max(errors),C='NOT RUN',D='NOT RUN'))
        previous=read(out/(level+'_field/alternative.json'))
        if time.monotonic()-then>900:raise TimeoutError('900s phase budget')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('role',choices=['controls','geometry']);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();run(a.role,a.out)
