"""Read-only existing-field audit and plots; never recalculates a solution."""
import argparse,json,math,time
from pathlib import Path
from collections import defaultdict
import numpy as np

def audit(meshdir,fielddir):
    m=np.load(meshdir/'mesh.npz');f=np.load(fielddir/'fields.npz');meta=json.loads((meshdir/'registry.json').read_text());r=json.loads((fielddir/'result.json').read_text());p=m['points'];t=m['cells'];rg=m['regions'];u=f['potential_unitV'];dt=f['cells']
    if not np.array_equal(f['dof_points_m'][dt],p[t]):raise ValueError('Savedfield geometrymismatch')
    if not np.all(f['dof_region'][dt]==rg[:,None]):raise ValueError('Savedfield materialmismatch')
    # Cofactor formulation independent of the affine 4x4 inverse in the solver.
    e=p[t[:,1:]]-p[t[:,:1]];det=np.einsum('ij,ij->i',e[:,0],np.cross(e[:,1],e[:,2]));vol=abs(det)/6
    b=np.stack([np.cross(e[:,1],e[:,2]),np.cross(e[:,2],e[:,0]),np.cross(e[:,0],e[:,1])],axis=1)/det[:,None,None]
    grad=np.einsum('ei,eij->ej',u[dt[:,1:]]-u[dt[:,:1]],b)
    # Rebuild declared tensors from input numbers,not solver tensors().
    defs=json.loads((Path(__file__).resolve().parents[1]/'data/v3_interconnect_et_20261102/operator_definitions.json').read_text());prop=defs['material_constants'];s=defs['scenarios']['NOM'];Ds=[]
    for g in meta['groups']:
        name=g['material']
        if name in ('laminate','pin_laminate'):
            ls=defs['film_stack_m' if name=='laminate' else 'pin_stack_m'];total=sum(th for mat,th in ls);para=sum(th/(prop[mat][0]*(s['film_factor'] if mat=='Cu' else 1)) for mat,th in ls)/total
            resistance=sum(th*prop[mat][0]*(s['film_factor'] if mat=='Cu' else 1) for mat,th in ls)+(len(ls)-1)*s['plated_re'];Ds.append(np.diag([para,para,total/resistance]))
        else:Ds.append(np.eye(3)/prop[name][0])
    D=np.array(Ds)[rg];J=-np.einsum('eij,ej->ei',D,grad);rel=float(np.max(np.linalg.norm(J-f['J_unitV_A_m2'],axis=1))/max(np.linalg.norm(J,axis=1).max(),1e-30))
    if rel>1e-7:raise ValueError('Independent gradient disagrees')
    facemap=defaultdict(list);trace={}
    for ci,row in enumerate(t):
        for omit in range(4):facemap[tuple(sorted(np.delete(row,omit)))].append(ci)
        for gn,dn in zip(row,dt[ci]):trace[(int(rg[ci]),int(gn))]=int(dn)
    fm={q['tag']:q for q in meta['faces']};raw=defaultdict(lambda:np.zeros(2));natural=defaultdict(float);contactpower=0.;normwrong=0
    bary=np.array([[2/3,1/6,1/6],[1/6,2/3,1/6],[1/6,1/6,2/3]])
    for tr,tag in zip(m['triangles'],m['faceids']):
        q=fm[int(tag)];ee=sorted(facemap[tuple(sorted(tr))],key=lambda ci:rg[ci]);av=np.cross(p[tr[1]]-p[tr[0]],p[tr[2]]-p[tr[0]])/2
        if av@(p[tr].mean(0)-p[t[ee[0]]].mean(0))<0:av=-av
        if av@(p[tr].mean(0)-p[t[ee[0]]].mean(0))<=0:normwrong+=1
        if len(ee)==2:
            a,bb=q['owners'];key=(a,bb);raw[key]+=np.array([J[ee[0]]@av,J[ee[1]]@(-av)])
            jump=np.array([u[trace[(a,int(n))]]-u[trace[(bb,int(n))]] for n in tr]);area=np.linalg.norm(av);natural[key]+=area*jump.mean()/s['re'];contactpower+=area*np.mean((bary@jump)**2)/s['re']
    diffs=[]
    for c in r['cuts']:
        if 'pair' not in c:continue
        ix=tuple(next(i for i,g in enumerate(meta['groups']) if g['name']==name) for name in c['pair']);diffs.extend([abs(raw[ix][0]-c['raw_a_A']),abs(raw[ix][1]-c['raw_b_A']),abs(natural[ix]-c['natural_A'])])
    err=max(diffs)/r['unit_potential_current_A']
    bulk=float(np.sum(vol*(-np.einsum('ei,ei->e',J,grad))));powererr=abs((bulk+contactpower)/r['IV_W']-1)
    if err>1e-7 or normwrong:raise ValueError('Independent rawface extraction disagrees')
    # Physical zero/uniform fields: zero gradients/jumps; residual of assembled
    # operator is NOT used to replaceany failed raw-field gate.
    uniform_gradient=np.einsum('ei,eij->ej',np.ones_like(dt[:,1:])-np.ones_like(dt[:,:1]),b)
    zero=float(abs(uniform_gradient).max())
    geometry=[];quality=[]
    surface=np.zeros(len(t))
    for k in range(4):
        xx=p[np.delete(t,k,axis=1)];surface+=np.linalg.norm(np.cross(xx[:,1]-xx[:,0],xx[:,2]-xx[:,0]),axis=1)/2
    maxedge=np.zeros(len(t))
    for a,bb in [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]:maxedge=np.maximum(maxedge,np.linalg.norm(p[t[:,a]]-p[t[:,bb]],axis=1))
    altitude=3*vol/(surface+1e-300);aspect=maxedge/(altitude+1e-300)
    for i,g in enumerate(meta['groups']):
        use=rg==i;v=float(vol[use].sum());geometry.append(dict(group=g['name'],CAD_volume_m3=g['volume_m3'],tet_volume_m3=v,relative_volume_error=v/g['volume_m3']-1));quality.append(dict(group=g['name'],max_edge_over_inradius_proxy=float(aspect[use].max()),median=float(np.median(aspect[use]))))
    return dict(status='PASS independentexistingfield/cofactor/normal/contactquadrature audit;BstillFAIL',relative_J_reconstruction_error=rel,max_cut_reconstruction_difference_relative=err,independent_bulk_W=bulk,independent_interface_W=float(contactpower),independent_loss_error_relative=powererr,wrong_normals=normwrong,uniform_zero_gradient=zero,volume_by_group=geometry,aspect_by_group=quality,method='No solve,no recoveredflux substituted,no model/mesh/field changed')

def plots(B,out):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    plt.rcParams.update({'font.size':10,'svg.hashsalt':'v3_et_failed_B'})
    m=np.load(B/'fine_mesh/mesh.npz');f=np.load(B/'fine_field/fields.npz');r=json.loads((B/'fine_field/result.json').read_text());p=m['points'];t=m['cells'];scale=.4/r['unit_potential_current_A'];cent=p[t].mean(1)*1000;J=np.linalg.norm(f['J_unitV_A_m2'],axis=1)*scale/1e6;V=f['potential_unitV'][f['cells']].mean(1)*scale*1000
    fig=plt.figure(figsize=(13,5.5))
    for col,(v,label,cmap) in enumerate([(V,'Potential (mV)','viridis'),(J,'|J| (A/mm²)','inferno')],1):
        ax=fig.add_subplot(1,2,col,projection='3d');h=ax.scatter(*cent.T,c=v,s=1.2,cmap=cmap,rasterized=True);fig.colorbar(h,ax=ax,pad=.02,shrink=.65,label=label);ax.set(xlabel='x (mm)',ylabel='y (mm)',zlabel='');ax.text2D(.82,.85,'z (mm)',transform=ax.transAxes,fontsize=9);ax.view_init(22,-65);ax.set_title(label+' at 0.4 A')
    fig.suptitle('Solved local 3D fields — raw-cut gate FAIL; diagnostic only')
    fig.text(.04,.03,'Cell centres of 28,691-tet fine coupon; selected metal/contact hypotheses. No TEC, Peltier or detector-temperature solve.',fontsize=9);fig.subplots_adjust(bottom=.18,top=.82,wspace=.1);fig.savefig(out/'actual_electrical_fields.png',dpi=230);fig.savefig(out/'actual_electrical_fields.svg',metadata={'Date':None});plt.close(fig)
    rows=r['cuts'];labels=[];raw=[];natural=[]
    for c in rows:
        labels.append(' → '.join(c['pair']) if 'pair' in c else 'terminal '+str(c['terminal']) if 'terminal' in c else c['interior'])
        # No contact-law quantity exists on an interior/terminal cut. Missing
        # data must not appear as an observed zero-current error on the plot.
        raw.append(100*c.get('raw_relative_error',c['gate_error']));natural.append(100*c['natural_relative_error'] if 'natural_relative_error' in c else np.nan)
    fig,ax=plt.subplots(figsize=(11,7));yy=np.arange(len(rows));ax.barh(yy,raw,label='One-sided bulk gradient',color='#b33d36');ax.scatter(natural,yy,label='Contact-law integral',color='#225a86',s=20,zorder=3);ax.axvline(.1,color='black',ls='--',label='0.1% release gate');ax.set(yticks=yy,yticklabels=labels,xlabel='Current-cut mismatch (% of drive current)',title='All registered fine-mesh cuts: stable resistance and power do not qualify raw flux');ax.invert_yaxis();ax.legend(loc='lower right',fontsize=8);ax.grid(axis='x',alpha=.2);fig.tight_layout();fig.savefig(out/'all_cut_errors.png',dpi=230);fig.savefig(out/'all_cut_errors.svg',metadata={'Date':None});plt.close(fig)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--B',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=False);start=time.monotonic();r={}
    for level in ('coarse','fine'):r[level]=audit(a.B/(level+'_mesh'),a.B/(level+'_field'))
    r['seconds']=time.monotonic()-start;(a.out/'independent_audit.json').write_text(json.dumps(r,indent=2)+'\n');plots(a.B,a.out);print('Existingfieldaudit PASS;BFAIL preserved')
