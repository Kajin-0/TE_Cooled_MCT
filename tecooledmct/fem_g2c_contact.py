"""Explicit meshed resistive transition zones, separate from OEM solder claims.

Each leg end contains a thin domain with added area-specific electrical and
thermal resistance. Seebeck equals the adjacent leg: an ASSUMED transition law,
not Sn-Sb solder. At zero added resistance all properties equal the original leg
and the original continuum problem is recovered exactly (mesh error remains).
"""
from copy import deepcopy
import json
from pathlib import Path
import numpy as np
from .fem_g2a import stage_manifest,Stage,generate_mesh,validate_path
from .material_profiles import Profile,Curve,synthetic_profile
from .fem_g2c import compile_profile,write_case
from .fem_g2c_post import postprocess
from .fem_g2b_physics import execute_solver
from .fem_g1_run import execute
from .g2c_qualification import Contact


def manifest(thickness=20e-6):
    m=stage_manifest();legs=[b for b in m['bodies'] if b['kind']=='leg'];ends={}
    if not 0<thickness<Stage().leg_height_m/4:raise ValueError('Transition thickness must resolve positive leg core')
    for leg in legs:
        bid=leg['id'];x,y,z,w,ww,h=leg['box_m'];pair=[]
        for side,zz in (('bottom',z),('top',z+h-thickness)):
            new={'id':len(m['bodies'])+1,'name':leg['name']+'_'+side+'_transition','kind':'contact_layer','material':leg['material']+'_contact',
                'box_m':[x,y,zz,w,ww,thickness],'cut_axis':2,'cut_coordinate_m':zz+thickness*.500013,'current_sign':leg['current_sign'],'cut_area_m2':w*ww,'parent_leg':bid}
            m['bodies'].append(new);pair.append(new['id'])
        ends[bid]=pair;leg['box_m'][2]+=thickness;leg['box_m'][5]-=2*thickness
    for c in m['contacts']:
        for j,bid in enumerate(c['bodies']):
            if bid not in ends:continue
            other=m['bodies'][c['bodies'][1-j]-1]
            layer=ends[bid][0 if other['side']=='hot' else 1];c['bodies'][j]=layer;c['bodies'].sort()
    for bid,(bottom,top) in ends.items():
        for layer in (bottom,top):m['contacts'].append({'bodies':sorted([bid,layer]),'area_m2':Stage().leg_width_m**2,'electrical':True})
    for i,c in enumerate(sorted(m['contacts'],key=lambda c:c['bodies']),1001):c['boundary_id']=i
    path=[]
    for bid in m['conductor_path']:
        if bid in ends:
            a,b=ends[bid]
            path.extend([a,bid,b] if m['bodies'][bid-1]['current_sign']==1 else [b,bid,a])
        else:path.append(bid)
    m['conductor_path']=path;m['graph']=validate_path(path,list(zip(path,path[1:])),m['terminals'])
    m['graph_audit']=m['graph']
    m['contacts_assumed']='shared interfaces plus explicit opt-in resistive transition domains; not OEM solder'
    m['transition_model']={'thickness_m':thickness,'seebeck':'same as adjacent BiTe, assumed phenomenological transition zone','solder_grade':'not assigned','zero_excess_limit':'same continuum as original leg, no removed BiTe resistance/thermopower'}
    return m


def transition_profile(base,contact):
    cs={}
    for p,curves in base.curves.items():
        rho=curves['rho'];k=curves['k']
        cs[p]={'rho':Curve(rho.temperature_k,tuple(v+contact.electrical_ohm_m2/contact.thickness_m for v in rho.values),'ohm m',True),
            'k':Curve(k.temperature_k,tuple(1/(1/v+contact.thermal_m2_k_w/contact.thickness_m) for v in k.values),'W/(m K)',True),'S':curves['S']}
    return Profile({'id':base.metadata['id']+'_resistive_transition','status':'ASSUMED TRANSITION LAW; NOT OEM SOLDER'},cs)


def run(out,base_mesh,baseline,base=None):
    """Actual four-couple layer PDE: zero limit, electrical and thermal checks."""
    import re,hashlib,gmsh
    base=synthetic_profile(False) if base is None else base
    from .fem_g2c_mesh import generate_transition_mesh
    out.mkdir(parents=True,exist_ok=True);mesh=out/'mesh';m=manifest()
    audit=generate_transition_mesh(mesh,.04e-3,m)
    from .fem_g2b_connectivity import connectivity
    arrays=np.load(mesh/'mesh.npz');audit['actual_tetra_connectivity']=connectivity(arrays['cells'],arrays['bodies'],{b['id'] for b in m['bodies'] if b['material']!='Alumina'})
    (mesh/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    execute(['ElmerGrid','14','2','stage.msh','-out','elmer'],mesh,'grid')
    from .fem_g2c_mesh import verify_elmer_tetra_mapping
    audit['elmer_tetra_mapping']=verify_elmer_tetra_mapping(mesh)
    (mesh/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    # The preserved template writer assigns base material properties. The final
    # SIF below explicitly maps the actual new body IDs to their transition law.
    proxy=out/'input_template';proxy.mkdir(exist_ok=True);normalized=deepcopy(m)
    for b in normalized['bodies']:b['material']=b['material'].replace('_contact','')
    (proxy/'manifest.json').write_text(json.dumps(normalized,indent=2)+'\n')
    if not (proxy/'elmer').exists():(proxy/'elmer').symlink_to((mesh/'elmer').resolve(),target_is_directory=True)
    lib=compile_profile(out/'base_library',base);cases={}
    for label,re_,rth,current,cold in (('zero_excess',0.,0.,.05,None),('electrical',1e-9,0.,.05,285.),('fixed_reference',0.,0.,.05,285.),
            ('passive_reference',0.,0.,0.,285.),('thermal',0.,1e-5,0.,285.),('coupled',1e-9,1e-5,.05,None)):
        contact=Contact(re_,rth,m['transition_model']['thickness_m']);cp=transition_profile(base,contact);clib=compile_profile(out/('library_'+label),cp)
        case=out/label;write_case(case,proxy,base,lib,current,.002,hot=295.,cold=cold,restart_from=out/'zero_excess' if label!='zero_excess' else None)
        text=(case/'case.sif').read_text()
        for body in m['bodies']:
            if body['kind']!='contact_layer':continue
            mid=5 if body['material'].startswith('P') else 6
            pattern=rf'(Body {body["id"]}\n.*?\n  Material = )\d+'
            text=re.sub(pattern,rf'\g<1>{mid}',text,flags=re.S)
        for polarity,mid in (('P',5),('N',6)):
            text+=f'\nMaterial {mid}\n'
            for key,symbol in (('Heat Conductivity','Heat'),('Electric Conductivity','Electric'),('Seebeck Coefficient','Seebeck')):
                text+=f'  {key} = Variable Temperature\n    Real Procedure "{clib.resolve()}" "{polarity}{symbol}"\n'
            text+='  Density = Real 7529\n  Heat Capacity = Real 544\nEnd\n'
        (case/'case.sif').write_text(text)
        meta=json.loads((case/'case.json').read_text());meta['contact']=contact.layer_parameters(Stage().leg_width_m**2);meta['contact']['solver_gate']='ACTUAL EXPLICIT 3D TRANSITION DOMAINS';meta['transition_model']=m['transition_model'];(case/'case.json').write_text(json.dumps(meta,indent=2)+'\n')
        status=execute_solver(case);r=postprocess(mesh,case,base,export=label=='coupled',contact_profile=cp)
        r.update(solver_status=status,sif_sha256=hashlib.sha256((case/'case.sif').read_bytes()).hexdigest(),vtu_sha256=hashlib.sha256((case/r['field_source']).read_bytes()).hexdigest(),case_path=str(case),mesh_path=str(mesh))
        cases[label]=r;(case/'metrics.json').write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
        print('contact',label,'Tc',r['cold_mean_k'],'V',r['voltage_v'],'Joule layers',r['contact_joule_w'],flush=True)
    checks={'mesh_quality':audit['min_tetra_sicn']>.01,
        'zero_excess_matches_original_baseline_5mK':abs(cases['zero_excess']['cold_mean_k']-baseline['cold_mean_k'])<.005,
        'zero_excess_voltage_matches_0p1pct':abs(cases['zero_excess']['voltage_v']/baseline['voltage_v']-1)<.001,
        'electrical_resistance_raises_fixed_T_voltage':cases['electrical']['voltage_v']>cases['fixed_reference']['voltage_v'],
        'thermal_resistance_reduces_passive_heat':abs(cases['thermal']['cold_out_w'])<abs(cases['passive_reference']['cold_out_w']),
        'global_energy_and_work':all(max(abs(r['energy_relative_residual']),abs(r['power_work_relative_residual']))<.01 for r in cases.values()),
        'driven_component_currents':all(r['max_cut_relative_error']<.005 for r in cases.values() if r['current_a']),
        'zero_drive_absolute_cut_currents':all(max(c['absolute_error_a'] for c in r['cuts'].values())<1e-6 for r in cases.values() if not r['current_a']),
        'contact_joule_positive':cases['electrical']['contact_joule_w']>0,
        'contact_extra_joule_matches_I2R_0p5pct':abs(cases['electrical']['extra_contact_joule_w']/(16*.05**2*1e-9/(.4e-3**2))-1)<.005}
    result={'passed':all(checks.values()),'checks':checks,'cases':cases,'mesh_audit':audit,'assumption':m['transition_model']}
    (out/'summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    if not result['passed']:raise RuntimeError('Contact transition numerical verification failed')
    return result


def main():
    import argparse,hashlib
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=Path('outputs/fem-g2c-contact'));p.add_argument('--baseline',type=Path,required=True);args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    paths=[*root.glob('tecooledmct/*g2c*.py'),root/'tecooledmct/material_profiles.py',*root.glob('tests/test_*g2c*.py')]
    hashes={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths}
    old=json.loads(args.baseline.read_text())
    if 'cases' in old:old=old['cases']['constant_regression']
    result=run(args.out.resolve(),Path(old['mesh_path']),old)
    result['baseline_metrics_sha256']=hashlib.sha256(args.baseline.read_bytes()).hexdigest();result['baseline_case']=old['case_path'];result['source_sha256']=hashes
    result['checks']['sources_unchanged']=all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in hashes.items());result['passed']=all(result['checks'].values())
    (args.out/'summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    if not result['passed']:raise SystemExit('Contact verification failed')
    print('Explicit transition checks PASS',json.dumps(result['checks']),flush=True)

if __name__=='__main__':main()
