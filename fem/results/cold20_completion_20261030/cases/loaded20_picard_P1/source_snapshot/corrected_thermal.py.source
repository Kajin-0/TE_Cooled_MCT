"""Additive solid-only fully coupled thermoelectric reference on corrected CAD.

No earlier package geometry, enclosure registry, radiation or gas is imported.
P/N/Cu use unchanged G1 verification constants; passive sigma is computational.
"""
import argparse,json,shutil,datetime
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from .geometry_rebaseline import ROOT,sha,write
from .fem_g2a import PROPERTIES
from .fem_g1_run import execute
from .fem_g2b_physics import execute_solver

ARCHIVE=ROOT/'fem/results/geometry_complete_checkpoint_20261030'


def material(name,t,sigma=1e-12):
    t=np.asarray(t,dtype=float)
    if np.any(~np.isfinite(t)) or np.any(t<90) or np.any(t>400):raise ValueError('Outside numerical90..400K thermal reference domain')
    if name in ('P','N','Cu'):return [np.full_like(t,v) for v in PROPERTIES[name][:3]]
    if name=='Presolder' and np.any((t<290)|(t>320)):raise ValueError('Unidentified joint outside declared290..320K numerical interval')
    k={'Alumina':30.,'Kovar':17.3,'Pin':17.3,'Glass':1.,'Presolder':35.,'Attach':1.,'Au':315.}.get(name)
    if name=='MCT':k=np.interp(t,[90.,148.,298.,400.],[2.41,1.61,.973,.790])
    if k is None:raise ValueError('Unknown material '+name)
    return [np.full_like(t,k) if np.ndim(k)==0 else k,np.full_like(t,sigma),np.zeros_like(t)]


def endpoint_weights(mesh):
    d=np.load(mesh/'mesh.npz');p,f,tags=(d[n] for n in ('points','faces','boundaries'))
    rows=np.loadtxt(mesh/'elmer/mesh.nodes');dist,ix=cKDTree(rows[:,2:5]).query(p)
    if dist.max()>1e-12 or len(np.unique(ix))!=len(p) or not np.array_equal(rows[:,0].astype(int),np.arange(1,len(rows)+1)):
        raise ValueError('Actual Elmer endpoint node mapping differs')
    result={}
    for tag in (101,103,104,6001,6009,6007,6008,6107,6108):
        ff=f[tags==tag];xyz=p[ff];areas=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1)/2
        if not len(ff) or areas.sum()<=0:raise ValueError('Missing real thermal endpoint')
        w=np.zeros(len(p));np.add.at(w,ff.ravel(),np.repeat(areas/3,3));nodes=np.flatnonzero(w>0)
        result[str(tag)]={'area_m2':float(areas.sum()),'indices':nodes.tolist(),'nodes':rows[ix[nodes],0].astype(int).tolist(),
                          'weights':(w[nodes]/areas.sum()).tolist(),'centroid_m':(areas@xyz.mean(1)/areas.sum()).tolist()}
    if not all(abs(v['centroid_m'][2]-.001835)<1e-10 for k,v in result.items() if k in ('103','104')):raise ValueError('Cu endpoint is not module hot pad')
    if abs(result['101']['centroid_m'][2])>1e-12:raise ValueError('Bath is not Kovar underside')
    return result


def link_powers(mesh,t,meta,ep=None):
    if ep is None:ep=endpoint_weights(mesh)
    links=json.loads((mesh/'wire_routes.json').read_text())['wires'];node=np.zeros(len(t));rows=[];conduction=np.zeros_like(node);joule=np.zeros_like(node)
    for link in links:
        on=meta['cu_leads_on'] if link['material']=='Cu' else meta['au_bonds_on']
        warm=ep[str(link['pin_face_tag'])];cold=ep[str(link['target_face_tag'])]
        tw=float(np.dot(warm['weights'],t[warm['indices']]));tc=float(np.dot(cold['weights'],t[cold['indices']]))
        q=link['G_W_K']*(tw-tc) if on else 0.
        heat=meta['current_a']**2*link['R_ohm'] if on and link['material']=='Cu' else 0.
        for e,power in ((warm,-q),(cold,q)):
            conduction[e['indices']]+=power*np.array(e['weights']);joule[e['indices']]+=heat/2*np.array(e['weights'])
        rows.append({**{k:link[k] for k in ('pin','material','pin_body','target_body','pin_face_tag','target_face_tag','length_m','G_W_K','R_ohm')},
                     'on':bool(on),'pin_k':tw,'pad_k':tc,'conduction_into_pad_w':q,'joule_w':heat,
                     'pin_source_w':-q+heat/2,'pad_source_w':q+heat/2})
    node=conduction+joule
    return node,rows,{'wire_conduction':conduction,'wire_joule':joule}


def callbacks(mesh,case,meta):
    ep=endpoint_weights(mesh);pieces=[]
    for link in json.loads((mesh/'wire_routes.json').read_text())['wires']:
        on=meta['cu_leads_on'] if link['material']=='Cu' else meta['au_bonds_on']
        if not on:continue
        warm=ep[str(link['pin_face_tag'])];cold=ep[str(link['target_face_tag'])]
        for tag,sign in ((link['pin_face_tag'],-1),(link['target_face_tag'],1)):
            def integers(a):return ','.join(map(str,a))
            def reals(a):return ','.join(f'{v:.17e}_dp' for v in a)
            heat=meta['current_a']**2*link['R_ohm'] if link['material']=='Cu' else 0.
            pieces.append(f'''FUNCTION Wire{tag}(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 TYPE(Variable_t),POINTER :: temp
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v,tw,tc
 INTEGER,PARAMETER :: wn({len(warm['nodes'])})=[{integers(warm['nodes'])}]
 INTEGER,PARAMETER :: cn({len(cold['nodes'])})=[{integers(cold['nodes'])}]
 REAL(KIND=dp),PARAMETER :: ww({len(warm['weights'])})=[{reals(warm['weights'])}]
 REAL(KIND=dp),PARAMETER :: cw({len(cold['weights'])})=[{reals(cold['weights'])}]
 temp => VariableGet(Model % Mesh % Variables, 'Temperature')
 IF (.NOT.ASSOCIATED(temp)) CALL Fatal('CorrectedWire','Missing global temperature')
 tw=0;tc=0
 DO i=1,SIZE(wn)
  tw=tw+ww(i)*temp % Values(temp % Perm(wn(i)))
 END DO
 DO i=1,SIZE(cn)
  tc=tc+cw(i)*temp % Values(temp % Perm(cn(i)))
 END DO
 v={sign*link['G_W_K']/ep[str(tag)]['area_m2']:.17e}_dp*(tw-tc)+{heat/2/ep[str(tag)]['area_m2']:.17e}_dp
END FUNCTION Wire{tag}
''')
    pieces.append('''FUNCTION MCTHeat(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v
 REAL(KIND=dp),PARAMETER :: tx(4)=[90.0_dp,148.0_dp,298.0_dp,400.0_dp]
 REAL(KIND=dp),PARAMETER :: yy(4)=[2.41_dp,1.61_dp,.973_dp,.790_dp]
 IF (.NOT.(T>=90.0_dp .AND. T<=400.0_dp)) CALL Fatal('CorrectedMCT','Outside local90..400K table')
 DO i=1,3
  IF(T<=tx(i+1)) EXIT
 END DO
 i=MIN(i,3);v=yy(i)+(T-tx(i))*(yy(i+1)-yy(i))/(tx(i+1)-tx(i))
END FUNCTION MCTHeat
FUNCTION JointHeat(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n
 REAL(KIND=dp) :: T,v
 IF (.NOT.(T>=290.0_dp .AND. T<=320.0_dp)) CALL Fatal('CorrectedJoint','Outside numerical290..320K interval')
 v=35.0_dp
END FUNCTION JointHeat
''')
    lib=case/'library';lib.mkdir();(lib/'SolidOnly.F90').write_text('\n'.join(pieces))
    execute(['elmerf90','-ffree-line-length-none','-o','CorrectedSolid','SolidOnly.F90'],lib,'compile')
    write(case/'endpoint_weights.json',ep);return lib/'CorrectedSolid',ep


def write_case(mesh,case,current=.1,load=.002,cu=False,au=False,sigma=1e-12,restart=None):
    if not np.isfinite([current,load,sigma]).all() or load<0 or sigma<=0:raise ValueError('Invalid solid case')
    if case.exists():raise ValueError('Choose a new immutable case label')
    case.mkdir(parents=True);m=json.loads((mesh/'manifest.json').read_text());d=np.load(mesh/'mesh.npz')
    from .fem_g1 import tetra_geometry
    vol,_=tetra_geometry(d['points'],d['cells']);volume=float(vol[d['bodies']==303].sum())
    meta={'current_a':current,'deposited_power_w':load,'pbias_w':.75*load,'parametric_absorption_w':.25*load,
          'cu_leads_on':bool(cu),'au_bonds_on':bool(au),'package_sigma_s_m':sigma,'mct_volume_m3':volume,
          'material_status':'unchanged constant G1 P/N/Cu verification proxies; passive thermal laws and unidentified k35 joint; no OEM grade',
          'MCT_k_source':'Heckman/Gonzalez/Guha2008, DOI10.1364/AO.47.000578, Table2 x0.29, local90..400K; no carrier transport',
          'boundary_scope':'300K Kovar external underside tag101 only; all other exposed solids including pin ends adiabatic except hybrid endpoint fluxes',
          'enclosure':'absent; no radiation/gas imported or executed','transient':False,'mesh_path':str(mesh),'initial_state':'uniform300K, phi0',
          'electrical_pins':'passive computational potential; module current prescribed103/104; physical wire I*R/I2R lumped, no pin-current/shaft-Joule PDE'}
    lib,ep=callbacks(mesh,case,meta)
    for source in (mesh/'elmer').glob('mesh.*'):(case/source.name).symlink_to(source.resolve())
    text=f'''Check Keywords Warn
Header
 Mesh DB "{case.resolve()}" "."
End
Simulation
 Coordinate System = Cartesian 3D
 Simulation Type = Steady State
 Steady State Max Iterations = 1
 Output File = "solution.result"
 Post File = "fields.vtu"
End
Initial Condition 1
 Temperature = Real 300
 Potential = Real 0
End
Equation 1
 Active Solvers(1) = 1
End
Solver 1
 Equation = "ThermoElectric"
 Variable = POT[Temperature:1 Potential:1]
 Procedure = "ThermoElectricSolver" "ThermoElectricSolver"
 Element = "p:1"
 Nonlinear System Convergence Tolerance = 1e-9
 Nonlinear System Max Iterations = 60
 Nonlinear System Newton After Iterations = 2
 Nonlinear System Newton After Tolerance = 1e-7
 Linear System Solver = Direct
 Linear System Direct Method = UMFPACK
 Linear System Row Equilibration = Logical True
End
Body Force 1
 Volumetric Heat Source = Real 0
 Current Source = Real 0
End
Body Force 2
 Volumetric Heat Source = Real {load/volume:.17g}
 Current Source = Real 0
End
'''
    names=sorted({b['material'] for b in m['bodies']});mid={name:i+1 for i,name in enumerate(names)}
    for index,body in enumerate(m['bodies'],1):
        text+=f'''Body {index}
 Target Bodies(1) = {body['id']}
 Equation = 1
 Material = {mid[body['material']]}
 Body Force = {2 if body['id']==303 else 1}
 Initial Condition = 1
End
'''
    for name in names:
        k,s,S=[float(v) for v in material(name,300.,sigma)];text+=f'Material {mid[name]}\n'
        text+=(f' Heat Conductivity = Variable Temperature\n  Real Procedure "{lib.resolve()}" "'+('MCTHeat' if name=='MCT' else 'JointHeat')+'"\n' if name in ('MCT','Presolder') else f' Heat Conductivity = Real {k:.17g}\n')
        text+=f' Electric Conductivity = Real {s:.17g}\n Seebeck Coefficient = Real {S:.17g}\n Density = Real 1\n Heat Capacity = Real 1\nEnd\n'
    text+='Boundary Condition 1\n Target Boundaries(1) = 101\n Temperature = Real 300\nEnd\n'
    for i,tag in enumerate((103,104,6001,6009,6007,6008,6107,6108),2):
        text+=f'Boundary Condition {i}\n Target Boundaries(1) = {tag}\n'
        if tag==103:text+=f' Electric Flux = Real {current/ep["103"]["area_m2"]:.17g}\n'
        if tag==104:text+=' Potential = Real 0\n'
        if (cu and tag in (103,104,6001,6009)) or (au and tag in (6007,6008,6107,6108)):
            text+=f' Heat Flux = Variable Temperature\n  Real Procedure "{lib.resolve()}" "Wire{tag}"\n'
        text+='End\n'
    if restart:
        shutil.copy2(restart/'solution.result',case/'initial.result')
        text=text.replace(' Output File = "solution.result"',' Restart File = "initial.result"\n Restart Position = 0\n Output File = "solution.result"')
        meta['initial_state']={'case':str(restart),'result_sha256':sha(restart/'solution.result'),'same_mesh':True}
    (case/'case.sif').write_text(text);write(case/'case.json',meta);return meta


def run(mesh,case,current=.1,load=.002,cu=False,au=False,sigma=1e-12,restart=None,timeout=900):
    from .corrected_thermal_post import postprocess
    sources=[Path(__file__),ROOT/'tecooledmct/corrected_thermal_post.py']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    # Exact new mesh, no remesh or state transfer from earlier assumed packages.
    ledger=json.loads((ARCHIVE/'checksums.json').read_text())
    if sha(mesh/'mesh.npz')!=ledger['artifact_sha256']['mesh.npz']:raise ValueError('Require exact corrected original mesh')
    meta=write_case(mesh,case,current,load,cu,au,sigma,restart);snap=case/'source_snapshot';snap.mkdir()
    for p in sources:shutil.copy2(p,snap/(p.name+'.source'))
    started=datetime.datetime.now(datetime.timezone.utc).isoformat();status=execute_solver(case,timeout)
    if any(sha(ROOT/n)!=h for n,h in hashes.items()):raise ValueError('Source changed during actual coupled execution')
    field=sorted(case.rglob('fields*.vtu'))[-1]
    write(case/'execution.json',{'source_sha256':hashes,'mesh_sha256':sha(mesh/'mesh.npz'),'manifest_sha256':sha(mesh/'manifest.json'),
          'sif_sha256':sha(case/'case.sif'),'vtu_sha256':sha(field),'field_source':str(field.relative_to(case)),
          'solver_status':status,'started_UTC':started,'finished_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'resource_cap':'4CPU/12GiB pinned Docker, network none'})
    result=postprocess(mesh,case);print('Converged real coupled case',case.name,'NUMERICALLY PASS' if result['passed'] else 'EXPLORATORY / FAILED GATE',result['die_mean_k'],result['voltage_v'],result['direct_bath_relative_error'],flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mesh',type=Path,required=True);parser.add_argument('--case',type=Path,required=True)
    parser.add_argument('--current',type=float,default=.1);parser.add_argument('--load',type=float,default=.002)
    parser.add_argument('--cu',action='store_true');parser.add_argument('--au',action='store_true');parser.add_argument('--sigma',type=float,default=1e-12)
    parser.add_argument('--restart',type=Path);parser.add_argument('--timeout',type=float,default=900)
    a=parser.parse_args();run(a.mesh.resolve(),a.case.resolve(),a.current,a.load,a.cu,a.au,a.sigma,a.restart.resolve() if a.restart else None,a.timeout)
