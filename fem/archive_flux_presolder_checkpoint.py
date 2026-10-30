#!/usr/bin/env python3
"""Audit and publish only the new scoped diagnostics/coupon checkpoint."""
import argparse,csv,gzip,json,re,shutil
from pathlib import Path
import numpy as np
from tecooledmct.g2d_data import ROOT,sha,dump
from tecooledmct.flux_presolder_common import guard,node_map,cell_map,affine_geometry,boundary_owners,outward_vectors

DIAG=ROOT/'outputs/flux-presolder-diagnosis-v3'
JUNCTION=ROOT/'outputs/flux-presolder-junction-v3'
METAL=ROOT/'outputs/flux-presolder-metal-coupons'


def read(path):return json.loads(path.read_text())


def coupon_audit(case):
    import meshio
    r=read(case/'verification.json')
    if not r['passed'] or r['solver_status']['exit_code']:raise ValueError('Unverified coupon')
    for name,digest in r['source_sha256'].items():
        if sha(case/'source_snapshot'/Path(name).name)!=digest:raise ValueError('Execution source snapshot mismatch')
        if sha(ROOT/name)!=digest:raise ValueError('Current coupon source differs from execution')
    for path,digest in [(case/'case.sif',r['sif_sha256']),(case/'mesh.npz',r['mesh_sha256']),(case/r['field_source'],r['vtu_sha256'])]:
        if sha(path)!=digest:raise ValueError('Execution input/field changed')
    d=np.load(case/'mesh.npz');p,c,b,f,tags=[d[k] for k in ('points','cells','bodies','faces','tags')];field=meshio.read(case/r['field_source'])
    ix,_=node_map(p,field.points);inverse=np.empty(len(ix),int);inverse[ix]=np.arange(len(ix));fc=np.concatenate([block.data for block in field.cells if block.type=='tetra']);order=cell_map(c,inverse[fc])
    rawb=np.concatenate([v for block,v in zip(field.cells,field.cell_data['GeometryIds']) if block.type=='tetra'])[order]
    if not np.array_equal(rawb,b):raise ValueError('Elmer body mapping differs')
    t=np.asarray(field.point_data['temperature']).ravel()[ix]
    if 'layers' in r['metadata']:k={i:row['k_w_mk'] for i,row in enumerate(r['metadata']['layers'],1)}
    else:k={1:17.3,2:1.,3:17.3}
    volume,g=affine_geometry(p,c);grad=np.einsum('ei,eij->ej',t[c],g);q=-np.array([k[int(v)] for v in b])[:,None]*grad
    bath=f[tags==1];owners=boundary_owners(c,bath);av=outward_vectors(p,c,bath,owners);direct=float(np.einsum('ij,ij->',q[owners],av))
    if abs(direct-r['bottom_raw_out_w'])>1e-10:raise ValueError('Independent archive field check failed')
    if 'manufactured_solution' in r['metadata']:
        amplitude=r['metadata']['quadratic_amplitude_k'];delta=-10. if case.name=='reverse' else 10.;z=p[:,2]/.0011
        if abs(t-(300+delta*z+amplitude*z*(1-z))).max()>1e-6:raise ValueError('Manufactured field mismatch')
        if abs(r['raw_relative_error']-r['expected_raw_relative_error_uniform_axial'])>1e-8:raise ValueError('Unexpected P1 truncation error')
    return {'passed':True,'cell_and_material_mapping_verified':True,'raw_flux_recomputed_w':direct,'raw_1pct_gate_passed':abs(r['raw_relative_error'])<.01,'scope':'coupon only; no device acceptance','verification_sha256':sha(case/'verification.json')}


def copy_case(source,target):
    target.mkdir(parents=True)
    for name in ['case.sif','execution.json','verification.json','solver.log','solver-status.json','grid.log','grid-status.json','mesh.npz']:
        shutil.copy2(source/name,target/name)
    shutil.copytree(source/'source_snapshot',target/'source_snapshot')
    r=read(source/'verification.json')
    with (source/r['field_source']).open('rb') as inp,gzip.GzipFile(filename=str(target/'fields.vtu.gz'),mode='wb',mtime=0) as out:
        shutil.copyfileobj(inp,out)
    dump(target/'field_provenance.json',{'source':r['field_source'],'uncompressed_sha256':r['vtu_sha256'],'compressed_sha256':sha(target/'fields.vtu.gz')})


def charts(out,diag,junction,metal):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'serif','font.size':10})
    out.mkdir();rows=[]
    for r in diag['cases']:
        i=r['discrete_residual_identity'];rows.append({'case':r['case'],'direct_out_w':r['direct_out_w'],'reaction_out_w':r['reaction_out_w'],'external_input_w':r['external_input_w'],'raw_error_w':r['direct_error_w'],'raw_error_percent':100*r['direct_relative_error'],'internal_jump_w':i['internal_face_weighted_jump_w'],'other_exterior_w':i['other_exterior_weighted_raw_out_w'],'identity_closure_w':i['closure_error_w']})
    with (out/'bath_summary.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    fig,ax=plt.subplots(figsize=(8,4));x=np.arange(4);ax.bar(x,[-1000*v['internal_jump_w'] for v in rows],label='Negative weighted internal jumps');ax.bar(x,[-1000*v['other_exterior_w'] for v in rows],bottom=[-1000*v['internal_jump_w'] for v in rows],label='Negative other exterior flux');ax.set(xticks=x,xticklabels=['Coarse','Global fine','Bath fine','Feedthrough fine'],ylabel='Raw minus reaction (mW)');ax.legend(frameon=False);fig.tight_layout();fig.savefig(out/'discrete_flux_identity.png',dpi=300);plt.close(fig)
    r=junction['cases'][2:];n=[v['metadata']['axial_layers'] for v in r]
    fig,ax=plt.subplots(figsize=(7,4));ax.loglog(n,[100*abs(v['raw_relative_error']) for v in r],'o-',label='Original raw P1 flux');ax.loglog(n,[100*abs(v['recovered_relative_error']) for v in r],'s--',label='Axial quadratic recovery, benchmark only');ax.axhline(1,color='r',ls=':',label='Unchanged raw1% criterion');ax.set(xlabel='Axial layers',ylabel='Absolute analytic-reference error (%)');ax.legend(frameon=False);ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/'junction_convergence.png',dpi=300);plt.close(fig)
    rows=[{'case':name,'R_analytic_K_W':v['analytic_R_K_W'],'raw_relative_error':v['raw_relative_error'],'bottom_out_w':v['bottom_raw_out_w']} for name,v in zip(['25um','50um','50um refined','100um','AuSn proxy','Contact films','Equal material','Old k2 mount'],metal['cases'])]
    with (out/'presolder_cases.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    fig,ax=plt.subplots(figsize=(8,4));ax.barh([v['case'] for v in rows],[v['R_analytic_K_W'] for v in rows],color='#436a82');ax.set(xlabel='Coupon thermal resistance (K/W)');fig.tight_layout();fig.savefig(out/'presolder_resistance.png',dpi=300);plt.close(fig)
    screen=[]
    for t in (20e-6,50e-6,100e-6):
        for k in (10.,35.,57.,80.):
            for wetted in (.5,.75,1.):
                resistance=(.0011/17.3+.00022/30+(t/k)/wetted)/1e-6
                screen.append({'thickness_m':t,'k_W_mK':k,'wetted_fraction':wetted,'analytical_series_R_K_W':resistance,'scope':'analytical screen only, solder area reduced uniformly; no3D void/spreading solution'})
    with (out/'analytical_wetting_screen.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(screen[0]));w.writeheader();w.writerows(screen)


def main(target):
    if target.exists():raise ValueError('Do not overwrite a checkpoint')
    integrity=guard();diag=read(DIAG/'summary.json');j=read(JUNCTION/'summary.json');m=read(METAL/'summary.json')
    if not diag['diagnostics_verified'] or not j['passed'] or not m['passed'] or len(diag['cases'])!=4:raise ValueError('Incomplete scoped evidence')
    for name,h in diag['diagnostic_source_sha256'].items():
        if sha(ROOT/name)!=h or sha(DIAG/'source_snapshot'/Path(name).name)!=h:raise ValueError('Diagnostic source changed')
    tests=(ROOT/'outputs/flux-presolder-full-tests.log').read_text()
    match=re.search(r'(\d+) passed(?:, (\d+) skipped)?',tests)
    if not match or match.group(2) or int(match.group(1))!=99 or re.search(r'\b\d+ failed\b|\bERRORS\b|Interrupted',tests):raise ValueError('Require completed99 full opt-in tests with no failures/skips')
    for name in ('cli','geometry'):read(ROOT/f'outputs/flux-presolder-{name}.log')
    audited={}
    for kind,source in [('junction',JUNCTION),('presolder',METAL)]:
        for case in source.iterdir():
            if case.is_dir() and (case/'verification.json').exists():audited[f'{kind}/{case.name}']=coupon_audit(case)
    if len(audited)!=14:raise ValueError('Expected exactly14 scoped coupon executions')
    target.mkdir(parents=True);shutil.copytree(DIAG,target/'bath_diagnosis')
    for kind,source in [('junction',JUNCTION),('presolder',METAL)]:
        for case in source.iterdir():
            if case.is_dir() and (case/'verification.json').exists():copy_case(case,target/'cases'/kind/case.name)
        shutil.copy2(source/'summary.json',target/(kind+'_summary.json'))
    shutil.copy2(METAL/'runtime_resources.json',target/'presolder_runtime_resources.json')
    charts(target/'charts',diag,j,m)
    provenance=target/'provenance';provenance.mkdir()
    for name in ['flux-presolder-full-tests.log','flux-presolder-cli.log','flux-presolder-geometry.log','flux-presolder-diagnosis.log','flux-presolder-diagnosis-v2.log','flux-presolder-diagnosis-v3.log','flux-presolder-junction.log','flux-presolder-junction-v2.log','flux-presolder-junction-v3.log','flux-presolder-metal-coupons.log']:
        shutil.copy2(ROOT/'outputs'/name,provenance/name)
    development=[]
    for source in [ROOT/'outputs/flux-presolder-junction',ROOT/'outputs/flux-presolder-junction-v2']:
        if not source.exists():continue
        for case in source.iterdir():
            if not case.is_dir() or not (case/'solver-status.json').exists():continue
            dest=target/'development'/source.name/case.name;dest.mkdir(parents=True)
            for name in ['case.sif','mesh.npz','solver.log','solver-status.json','grid-status.json','execution.json','verification.json']:
                if (case/name).exists():shutil.copy2(case/name,dest/name)
            shutil.copytree(case/'source_snapshot',dest/'source_snapshot')
            fields=list(case.rglob('fields*.vtu'))
            if fields:
                with fields[-1].open('rb') as inp,gzip.GzipFile(filename=str(dest/'fields.vtu.gz'),mode='wb',mtime=0) as out:shutil.copyfileobj(inp,out)
                dump(dest/'field_hash.json',{'uncompressed_sha256':sha(fields[-1])})
            development.append({'case':str(case.relative_to(ROOT)),'solver_status':read(case/'solver-status.json'),'accepted':False,'reason':'earlier driver postprocessing path failure or campaign stopped at declared mesh cap; no promotion'})
    source_paths=list((ROOT/'tecooledmct').glob('flux_presolder_*.py'))+[ROOT/'fem/run_flux_presolder_scoped.py',Path(__file__).resolve(),ROOT/'tests/test_flux_presolder.py']
    source_paths += list((ROOT/'data/flux_presolder').rglob('*'))
    source_paths += [ROOT/n for n in ['FLUX_PRESOLDER_QUALIFICATION_WORK_ORDER.md','G3B_FLUX_PRESOLDER_WORK_ORDER.md','docs/PHASE1_BATH_FLUX_QUALIFICATION.md','docs/PHASE1_FLUX_AND_PRESOLDER_RESULT.md','docs/PHASE1_G3B_FLUX_AND_PRESOLDER_RESULT.md','docs/REPRO_FLUX_PRESOLDER.md']]
    sources={str(p.relative_to(ROOT)):sha(p) for p in source_paths if p.is_file()}
    dump(target/'summary.json',{'scoped_verified':True,'full_G3b_qualified':False,'full_stack_presolder_solved':False,'OEM_validated':False,'original_raw_gate':.01,'qualified_coupon_executions':14,'unaccepted_development_executions':len(development),'development':development,'tests_passed':int(match.group(1)),'opt_in_solver_tests_executed':True,'baseline_integrity':integrity,'coupon_audits':audited,'interpretation':'Independent localization and limited analytic coupons only. No full-device correction, 3D equilibrated flux recovery, measured presolder alloy or new coupled88-leg solution.'})
    dump(target/'checksums.json',{'source_sha256':sources,'artifact_sha256':{str(p.relative_to(target)):sha(p) for p in sorted(target.rglob('*')) if p.is_file()},'baseline_report_unchanged':True,'full_G3b_qualified':False})
    print('Published audited scoped checkpoint:',target,'with14 coupon executions; full-device qualification remains false',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'fem/results/flux_presolder_checkpoint_20261030')
    parser.add_argument('--diagnosis',type=Path,default=DIAG);parser.add_argument('--junction',type=Path,default=JUNCTION);parser.add_argument('--presolder',type=Path,default=METAL)
    args=parser.parse_args();DIAG=args.diagnosis.resolve();JUNCTION=args.junction.resolve();METAL=args.presolder.resolve();main(args.out.resolve())
