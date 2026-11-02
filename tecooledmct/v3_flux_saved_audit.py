"""Independent saved-array audit of the stopped attempt. NO solve or mesh."""
import datetime,hashlib,json
from pathlib import Path
import numpy as np

BASE=Path('data/v3_conservative_flux_20261102')

def main():
    d=BASE/'geometry/L1';f=BASE/'geometry/L1_field'
    m=np.load(d/'mesh.npz');s=np.load(f/'fields.npz');reg=json.loads((d/'registry.json').read_text())
    p,t,r=m['points'],m['cells'],m['regions'];xyz=p[t];c=xyz.mean(axis=1)
    edge=xyz[:,1:]-xyz[:,:1];det=np.einsum('ei,ei->e',edge[:,0],np.cross(edge[:,1],edge[:,2]));v=abs(det)/6
    if np.any(v<=0):raise ValueError('Nonpositive saved element')
    defs=json.loads(Path('data/v3_interconnect_et_20261102/operator_definitions.json').read_text());pr=defs['material_constants'];sc=defs['scenarios']['NOM'];D=[]
    for g in reg['groups']:
        material=g['material']
        if material in ('laminate','pin_laminate'):
            layers=defs['film_stack_m' if material=='laminate' else 'pin_stack_m'];thick=sum(th for ma,th in layers)
            resist=[pr[ma][0]*(sc['film_factor'] if ma=='Cu' else 1) for ma,th in layers]
            para=sum(th/rho for (ma,th),rho in zip(layers,resist))/thick
            normal=thick/(sum(th*rho for (ma,th),rho in zip(layers,resist))+(len(layers)-1)*sc['plated_re'])
            D.append(np.diag([para,para,normal]))
        else:D.append(np.eye(3)/pr[material][0])
    D=np.array(D)[r];rho=np.linalg.inv(D)
    # Output writer overwrote method names with its final interior-cut label.
    # Last iteration was recovery. Never call this an independently retained mixed flux.
    assert 'mixed_q' not in s and 'recovered_q' not in s and 'lead9_q' in s
    q=s['lead9_q'];cf=s['cell_faces'];sign=s['cell_signs'];local=q[cf]*sign;div=local.sum(axis=1)
    Jc=np.einsum('ei,eia->ea',local,c[:,None,:]-xyz)/(3*v[:,None])
    jerr=np.max(np.linalg.norm(Jc-s['lead9_J'],axis=1))/np.linalg.norm(s['lead9_J'],axis=1).max()
    bary=np.full((4,4),.1381966011250105);np.fill_diagonal(bary,.5854101966249685)
    x=np.einsum('qi,eia->eqa',bary,xyz)
    J=Jc[:,None,:]+(x-c[:,None,:])*div[:,None,None]/(3*v[:,None,None])
    bulk=float(np.sum(v*np.einsum('eqa,eab,eqb->eq',J,rho,J).mean(axis=1)))
    lookup={tuple(row):i for i,row in enumerate(s['face_nodes'])};meta={row['tag']:row for row in reg['faces']}
    boundary={0:0.,1:0.};contact=0.;pairs={};first=np.empty(len(q),int)
    first[cf[sign>0]]=np.repeat(np.arange(len(t)),4)[sign.ravel()>0]
    for tr,tag in zip(m['triangles'],m['faceids']):
        row=meta[int(tag)];fi=lookup[tuple(sorted(tr))];flux=float(q[fi])
        if len(row['owners'])==2:
            area=np.linalg.norm(np.cross(p[tr[1]]-p[tr[0]],p[tr[2]]-p[tr[0]]))/2
            contact+=sc['re']*flux**2/area
            pair=tuple(row['owners']);pairs[pair]=pairs.get(pair,0)+flux*(1 if r[first[fi]]==pair[0] else -1)
        elif row['electrical_port']>=0:boundary[row['electrical_port']]+=flux
    I=-boundary[0];normal_error=0.
    for i in range(4):
        tri=np.delete(xyz,i,axis=1);fc=tri.mean(axis=1)
        av=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])/2
        av*=np.where(np.einsum('ei,ei->e',av,fc-c)>0,1.,-1.)[:,None]
        jf=Jc+(fc-c)*div[:,None]/(3*v[:,None])
        normal_error=max(normal_error,float(abs(np.einsum('ei,ei->e',jf,av)-local[:,i]).max()/I))
    # Separate cofactor reconstruction of the new raw P1 gradients.
    pair=np.stack([np.repeat(r,4),t.ravel()],axis=1);_,indices=np.unique(pair,axis=0,return_inverse=True);dc=indices.reshape(-1,4)
    cof=np.stack([np.cross(edge[:,1],edge[:,2]),np.cross(edge[:,2],edge[:,0]),np.cross(edge[:,0],edge[:,1])],axis=1)/det[:,None,None]
    grad=np.einsum('ei,eia->ea',s['P1_u'][dc[:,1:]]-s['P1_u'][dc[:,:1]],cof)
    rawJ=-np.einsum('eab,eb->ea',D,grad)
    rawerr=float(np.linalg.norm(rawJ-s['P1_J'],axis=1).max()/np.linalg.norm(s['P1_J'],axis=1).max())
    result=dict(observed_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        status='STOP retained: independent saved-field audit only; no solve',producer_defect='inner cut-name overwrote method name; only final recovered flux retained under lead9; mixed flux NOT RETAINED',
        recovered_field_J_reconstruction_relative=float(jerr),all_element_face_normal_error_relative=normal_error,
        P1_cofactor_J_reconstruction_relative=rawerr,independent_bulk_W=bulk,independent_contact_W=contact,
        independent_input_A=I,independent_terminal_relative_error=abs(boundary[1]-I)/I,
        independent_IV_loss_relative_error=abs((bulk+contact)/I-1),
        interface_fluxes_A={str(k):v for k,v in pairs.items()},
        mixed_comparison='NOT QUALIFIED: direct mixed flux export lost; no reconstruction solve attempted',
        thermal_C='NOT RUN',coupled_D='NOT RUN')
    assert jerr<1e-7 and normal_error<1e-7 and rawerr<1e-7
    out=BASE/'saved_audit.json'
    if out.exists():raise ValueError('Preserve audit')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
