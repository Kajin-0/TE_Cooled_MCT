#!/usr/bin/env python3
"""Independent exact quadratic H1 error integral vs tetra Gaussian degree-2 formula."""
from pathlib import Path
import json,numpy as np,math
o=Path('/out')
rng=np.random.default_rng(20261105)
a=0.5854101966249685
b=0.1381966011250105
bary=np.array([[a,b,b,b],[b,a,b,b],[b,b,a,b],[b,b,b,a]])
maxdiff=0.0
for _ in range(125):
 p=rng.standard_normal((4,3))
 mat=np.stack((p[1]-p[0],p[2]-p[0],p[3]-p[0]),axis=1)
 if abs(np.linalg.det(mat))<.05:continue
 vol=abs(float(np.linalg.det(mat)))/6
 c=p.mean(axis=0)
 scale=np.array([1.13,2.27,0.71])
 origin=np.array([-0.3,.4,1.2])
 invsq=1/scale**2
 test_grad=rng.standard_normal(3)
 gc=2*(c-origin)*invsq
 var=((p-c)**2).sum(axis=0)/20
 exact=vol*(np.dot(test_grad-gc,test_grad-gc)+np.sum(4*(invsq**2)*var))
 sample=bary@p
 quad=vol/4*np.sum(np.sum((test_grad[None,:]-2*(sample-origin)*invsq)**2,axis=1))
 maxdiff=max(maxdiff,abs(exact-quad)/max(abs(exact),1e-30))
assert maxdiff<2e-12,maxdiff
receipt={'status':'PASS exact tetra quadratic-gradient H1 integral against independent degree-2 four-point Gaussian quadrature','trials_attempted':125,'max_relative_discrepancy':maxdiff,'quadrature_barycentric_weights':[a,b,b,b],'function':'squared error between constant P1 gradient and analytic affine gradient'}
(o/'H1_integration_independent_check.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(receipt)
