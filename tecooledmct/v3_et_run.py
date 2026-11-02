"""Gated local finite-contact electrical coupon; no automatic downstream solve."""
import argparse,json,hashlib,time,subprocess
from pathlib import Path
import numpy as np
from .v3_et_geometry import read,write,BASE
from .v3_et_fem import Operator,tensors,SCENARIOS

def solve(meshdir,out):
    import meshio
    if out.exists():raise ValueError('Preserve field solve')
    out.mkdir(parents=True);start=time.monotonic();data=np.load(meshdir/'mesh.npz');reg=read(meshdir/'registry.json')
    try:
        op=Operator(data['points'],data['cells'],data['regions'],data['triangles'],data['faceids'],reg,tensors(reg['groups']),SCENARIOS['NOM']['re'])
        result,u,J,H=op.electrical();scale=.4/result['unit_potential_current_A']
        np.savez_compressed(out/'fields.npz',potential_unitV=u,J_unitV_A_m2=J,bulk_joule_unitV_W_m3=H,dof_points_m=op.p[op.unique[:,1]],cells=op.dofs,dof_region=op.unique[:,0])
        meshio.write(out/'field_0p4A.vtu',meshio.Mesh(op.p[op.unique[:,1]],[('tetra',op.dofs)],point_data={'Potential_V':u*scale},cell_data={'J_A_m2':[J*scale],'Joule_W_m3':[H*scale**2],'region':[op.r]}))
        result.update(status='Solved;registeredB gates determine qualification',seconds=time.monotonic()-start,nodes=op.ndof,tets=len(op.t),scenario='NOM',solver='SciPy sparseLU3D P1finitecontact',mesh_sha256=hashlib.sha256((meshdir/'mesh.npz').read_bytes()).hexdigest(),no_P_N_Seebeck=True)
        result['gates']['voltage_bounded']=result['minimum_voltage']>=-1e-8 and result['maximum_voltage']<=1+1e-8
        write(out/'result.json',result);print({k:v for k,v in result.items() if k not in ('cuts','cases','interface_losses_unitV_W','material_losses_unitV_W')})
    except Exception as e:write(out/'failure.json',dict(error=repr(e),seconds=time.monotonic()-start));raise

def phase_B(out):
    if out.exists():raise ValueError('OneB campaignonly')
    out.mkdir(parents=True);start=time.monotonic();runs=[]
    gateA=read(BASE/'gate_A.json')
    if gateA['status']!='PASS':raise ValueError('A notpassed')
    try:
        for level,h in [('coarse',.075),('fine',.045)]:
            mesh=out/(level+'_mesh');field=out/(level+'_field')
            for role,cmd in [('mesh',['python','-u','-B','-m','tecooledmct.v3_et_geometry','mesh','--out',str(mesh),'--geometry',str(BASE/'geometry'),'--h',str(h)]),('solve',['python','-u','-B','-m','tecooledmct.v3_et_run','solve','--mesh',str(mesh),'--out',str(field)])]:
                remaining=900-(time.monotonic()-start)
                if remaining<=0:raise TimeoutError('Aggregate900sphasecap')
                with (out/(level+'_'+role+'.log')).open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=remaining)
                runs.append(dict(level=level,role=role,exit_code=r.returncode,phase_elapsed_s=time.monotonic()-start));write(out/'execution.json',runs)
                if r.returncode:raise ValueError('Local'+level+role+'failed;no retry')
        a=read(out/'coarse_field/result.json');b=read(out/'fine_field/result.json');refinement=abs(a['R_coupon_ohm']/b['R_coupon_ohm']-1);gates=dict(b['gates'],R_refinement_1pct=refinement<=.01)
        result=dict(status='PASS' if all(gates.values()) else 'FAIL/STOP',gate='B',acceptance=gates,R_coarse_ohm=a['R_coupon_ohm'],R_fine_ohm=b['R_coupon_ohm'],R_relative_refinement=refinement,worst_fine_cut_relative_error=b['worst_cut_relative_error'],fine_power_relative_error=b['loss_relative_error'],seconds=time.monotonic()-start,downstream='C/D NOT RUN unlessB passes;no automatic nextcampaign',source='Actual V3net88/lead9localcoupon;notTEC resistance',all_coarse_cuts_preserved=True)
        write(out/'gate_B.json',result)
        if result['status']!='PASS':write(out/'downstream_NOT_RUN.json',dict(C='NOT RUN:failedB',D='NOT RUN:failedB;Cnotqualified',criteria_unchanged=True))
        print(result)
    except Exception as e:
        write(out/'failure.json',dict(status='STOP',reason=repr(e),seconds=time.monotonic()-start,C='NOT RUN',D='NOT RUN'));raise
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('role',choices=['solve','B']);p.add_argument('--out',type=Path,required=True);p.add_argument('--mesh',type=Path);a=p.parse_args();solve(a.mesh,a.out) if a.role=='solve' else phase_B(a.out)
