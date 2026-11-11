"""Vectorized source-node paired gas operator; no 3D gas-field claim."""
import numpy as np
class SourceP1Gas:
 def __init__(self,pairs,node_ids):
  self.sets=[]
  for stage in range(3):
   p=[x for x in pairs if x['stage']==stage];assert p
   indices=[];weights=[]
   for side,plate in [('hot',stage),('cold',stage+1)]:
    ids=np.asarray(node_ids[plate]);assert np.all(ids[1:]>ids[:-1]);q=np.asarray([x[side]['node_ids'] for x in p],dtype=np.int64);idx=np.searchsorted(ids,q);assert np.all(idx<len(ids)) and np.array_equal(ids[idx],q)
    w=np.array([x[side]['weights'] for x in p]);assert np.max(abs(w.sum(axis=1)-1))<1e-12 and np.min(w)>-2e-8
    indices.append(idx);weights.append(w)
   self.sets.append({'ih':indices[0],'ic':indices[1],'wh':weights[0],'wc':weights[1],'area':np.array([x['area_mm2'] for x in p])*1e-6,'gap':np.array([x['gap_m'] for x in p])})
  self.counts=[len(x) for x in node_ids]
 def evaluate(self,T,pressure=100.,alpha=.8):
  if len(T)!=4 or not np.isfinite(pressure) or pressure<0 or not 0<alpha<=1:raise ValueError('invalid gas state')
  loads=[np.zeros(n) for n in self.counts];links=[];entropy=0.
  for j,s in enumerate(self.sets):
   vh=np.asarray(T[j])[s['ih']];vc=np.asarray(T[j+1])[s['ic']]
   th=vh[:,0]+s['wh'][:,1]*(vh[:,1]-vh[:,0])+s['wh'][:,2]*(vh[:,2]-vh[:,0]);tc=vc[:,0]+s['wc'][:,1]*(vc[:,1]-vc[:,0])+s['wc'][:,2]*(vc[:,2]-vc[:,0]);avg=(th+tc)/2
   if not np.all(np.isfinite(avg)) or np.any(avg<180) or np.any(avg>400):raise ValueError('gas law temperature domain')
   if pressure==0:q=np.zeros_like(avg)
   else:
    k=np.interp(np.maximum(avg,200),[200.,300.,400.],[.0064,.0095,.0122]);k=np.where(avg<200,k*(avg/200)**.75,k);R=99.218;gamma=5/3;cp=gamma/(gamma-1)*R;mu=k/(cp+1.25*R);pr=mu*cp/k;lam=mu/pressure*np.sqrt(np.pi*R*avg/2);jump=(2-alpha)/alpha*2*gamma/(gamma+1)*lam/pr;q=k*s['area']*(th-tc)/(s['gap']+2*jump)
   loads[j]+=np.bincount(s['ih'].ravel(),weights=(-q[:,None]*s['wh']).ravel(),minlength=self.counts[j]);loads[j+1]+=np.bincount(s['ic'].ravel(),weights=(q[:,None]*s['wc']).ravel(),minlength=self.counts[j+1]);links.append(float(np.sum(q)));entropy+=float(np.sum(q*(1/tc-1/th)))
  if abs(sum(float(x.sum()) for x in loads))>1e-12 or entropy < -1e-14:raise ValueError('nonconservative gas operator')
  return {'loads':loads,'links_W':links,'entropy_W_K':entropy}
