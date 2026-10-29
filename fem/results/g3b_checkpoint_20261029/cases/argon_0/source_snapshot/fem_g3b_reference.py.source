"""Single coupled T/phi solve with passive package and conservative nonlocal 1D bonds."""
import json,math,shutil
import numpy as np
from scipy.spatial import cKDTree
from .g2d_data import ROOT,sha,dump
from .fem_g3b_data import registry
from .fem_g3a_data import wire_conductance
from .fem_g2a import PROPERTIES
from .fem_g1_run import execute


def material_properties(name,t,sigma=1e-12,attach_scale=1.,mount_scale=1.):
    r=registry();t=np.asarray(t)
    if name in PROPERTIES:return [np.full_like(t,v,dtype=float) for v in PROPERTIES[name][:3]]
    ks={'Steel':15.,'ZnSe':18.,'Kovar':17.3,'Pin':17.3,'Glass':1.,'Mount':r['hot_mount']['k_w_mk']*mount_scale,'Attach':r['die_attach']['k_w_mk']*attach_scale,'Au':315.}
    if name=='MCT':
        q=r['mct']
        if np.any(~np.isfinite(t)) or np.any(t<90) or np.any(t>400):raise ValueError('Actual local MCT T outside90..400 K')
        k=np.interp(t,q['temperature_k'],q['k_w_mk'])
    else:k=np.full_like(t,ks[name],dtype=float)
    return [k,np.full_like(t,sigma,dtype=float),np.zeros_like(t,dtype=float)]


def endpoint_weights(mesh):
    d=np.load(mesh/'mesh.npz');p,f,t=d['points'],d['faces'],d['boundaries'];rows=np.loadtxt(mesh/'elmer/mesh.nodes');dist,ix=cKDTree(rows[:,2:5]).query(p)
    if dist.max()>1e-12 or not np.array_equal(rows[:,0].astype(int),np.arange(1,len(rows)+1)):raise ValueError('Unsupported Elmer node index mapping')
    ids=rows[ix,0].astype(int);result={}
    for tag in (200,201,202,203):
        ff=f[t==tag];x=p[ff];area=np.linalg.norm(np.cross(x[:,1]-x[:,0],x[:,2]-x[:,0]),axis=1)/2;weights=np.zeros(len(p));np.add.at(weights,ff.ravel(),np.repeat(area/3,3));sel=weights>0
        result[tag]={'area':float(area.sum()),'nodes':ids[sel].tolist(),'weights':(weights[sel]/area.sum()).tolist(),'indices':np.flatnonzero(sel).tolist()}
    return result


def compile_callbacks(mesh,out,wire_scale=1.):
    out.mkdir(parents=True,exist_ok=True);ep=endpoint_weights(mesh);pieces=[]
    for tag in ep:
        i=(tag-200)//2;warm=ep[200+2*i];cold=ep[201+2*i]
        def ints(a):return ','.join(map(str,a))
        def reals(a):return ','.join(f'{v:.17e}_dp' for v in a)
        pieces.append(f'''FUNCTION Wire{tag}(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 TYPE(Variable_t),POINTER :: temp
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v,tw,tc
 INTEGER,PARAMETER :: wn({len(warm['nodes'])})=[{ints(warm['nodes'])}]
 INTEGER,PARAMETER :: cn({len(cold['nodes'])})=[{ints(cold['nodes'])}]
 REAL(KIND=dp),PARAMETER :: ww({len(warm['weights'])})=[{reals(warm['weights'])}]
 REAL(KIND=dp),PARAMETER :: cw({len(cold['weights'])})=[{reals(cold['weights'])}]
 temp => VariableGet(Model % Mesh % Variables, 'Temperature')
 IF (.NOT.ASSOCIATED(temp)) CALL Fatal('G3bReferenceWire','Missing global temperature field')
 tw=0;tc=0
 DO i=1,SIZE(wn)
  tw=tw+ww(i)*temp % Values(temp % Perm(wn(i)))
 END DO
 DO i=1,SIZE(cn)
  tc=tc+cw(i)*temp % Values(temp % Perm(cn(i)))
 END DO
 v={(-1 if tag%2==0 else 1)*wire_conductance(1)*wire_scale/ep[tag]['area']:.17e}_dp*(tw-tc)
END FUNCTION Wire{tag}
''')
    q=registry()['mct'];pieces.append('''FUNCTION MCTHeat(Model,n,T) RESULT(v)
 USE DefUtils
 IMPLICIT NONE
 TYPE(Model_t) :: Model
 INTEGER :: n,i
 REAL(KIND=dp) :: T,v
 REAL(KIND=dp),PARAMETER :: tx(4)=[90.0_dp,148.0_dp,298.0_dp,400.0_dp]
 REAL(KIND=dp),PARAMETER :: yy(4)=[2.41_dp,1.61_dp,.973_dp,.790_dp]
 IF (.NOT.(T>=90.0_dp .AND. T<=400.0_dp)) CALL Fatal('G3bMCT','Local MCT T outside qualified90..400 K')
 DO i=1,3
  IF (T<=tx(i+1)) EXIT
 END DO
 i=MIN(i,3);v=yy(i)+(T-tx(i))*(yy(i+1)-yy(i))/(tx(i+1)-tx(i))
END FUNCTION MCTHeat
''')
    f=out/'Package.F90';f.write_text('\n'.join(pieces));execute(['elmerf90','-ffree-line-length-none','-o','G3bReference',f.name],out,'compile');dump(out/'endpoint_weights.json',ep);return out/'G3bReference'


def write_case(mesh,case,current,pbias=0.,poptical=0.,wire_scale=1.,sigma=1e-12,attach_scale=1.,mount_scale=1.,restart=None):
    if not np.isfinite([current,pbias,poptical,wire_scale,sigma,attach_scale,mount_scale]).all() or min(pbias,poptical,wire_scale)<0 or min(sigma,attach_scale,mount_scale)<=0:raise ValueError('Invalid physical inputs')
    case.mkdir(parents=True,exist_ok=True);m=json.loads((mesh/'manifest.json').read_text());lib=compile_callbacks(mesh,case/'library',wire_scale);r=registry();v=r['mct']['width_m']**2*r['mct']['thickness_m']
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
 Volumetric Heat Source = Real {(pbias+poptical)/v:.17g}
 Current Source = Real 0
End
'''
    names=list(PROPERTIES)+['Kovar','Pin','Glass','Mount','Attach','Au','Steel','ZnSe','MCT'];mid={n:i+1 for i,n in enumerate(names)}
    for b in m['bodies']:
        text+=f'''Body {b['id']}
 Target Bodies(1) = {b['id']}
 Equation = 1
 Material = {mid[b['material']]}
 Initial Condition = 1
 Body Force = {2 if b['material']=='MCT' else 1}
End
'''
    for name in names:
        k,s,alpha=[float(x) for x in material_properties(name,300.,sigma,attach_scale,mount_scale)];text+=f'Material {mid[name]}\n'
        text+=(f' Heat Conductivity = Variable Temperature\n  Real Procedure "{lib.resolve()}" "MCTHeat"\n' if name=='MCT' else f' Heat Conductivity = Real {k:.17g}\n')
        text+=f' Electric Conductivity = Real {s:.17g}\n Seebeck Coefficient = Real {alpha:.17g}\n Density = Real {6830 if name=="MCT" else 1}\n Heat Capacity = Real 1\nEnd\n'
    text+=f'''Boundary Condition 1
 Target Boundaries(1) = 101
 Temperature = Real 300
End
Boundary Condition 2
 Target Boundaries(1) = 103
 Electric Flux = Real {current/m['terminal_planes']['103']['area_m2']:.17g}
End
Boundary Condition 3
 Target Boundaries(1) = 104
 Potential = Real 0
End
'''
    for i,tag in enumerate((200,201,202,203),4):text+=f'Boundary Condition {i}\n Target Boundaries(1) = {tag}\n Heat Flux = Variable Temperature\n  Real Procedure "{lib.resolve()}" "Wire{tag}"\nEnd\n'
    initial=None
    if restart:
        f=restart/'solution.result';shutil.copy2(f,case/'initial.result');text=text.replace(' Output File = "solution.result"',' Restart File = "initial.result"\n Restart Position = 0\n Output File = "solution.result"');initial={'case':str(restart),'result_sha256':sha(f)}
    (case/'case.sif').write_text(text);dump(case/'case.json',{'current_a':current,'pbias_w':pbias,'poptical_thermal_w':poptical,'deposited_power_w':pbias+poptical,'wire_scale':wire_scale,'package_sigma_s_m':sigma,'attach_k_scale':attach_scale,'mount_k_scale':mount_scale,'initial_actual_state':initial,'thermal_bath':'header underside300 K only','wire_model':'conservative hybrid1D flux callbacks in the coupled global nonlinear solve','TEC_profile':'original mixed constant verification law, no OEM-grade accuracy','transient':False})
