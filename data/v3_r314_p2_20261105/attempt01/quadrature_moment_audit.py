#!/usr/bin/env python3
"""Exact simplex-monomial moment audit for R3.14 quadrature rules, stdlib only."""
from pathlib import Path
import itertools,math,json
O=Path('/var/tmp/v3_r314_p2_20261105')
q4=[([.25]*4,-.07893333333333333)]
for k in range(4):
 a=[1/14]*4;a[k]=11/14
 q4.append((a,.04573333333333333))
for pair in itertools.combinations(range(4),2):
 a=[.1005964238332008]*4
 for k in pair:a[k]=.3994035761667992
 q4.append((a,.14933333333333335))
qface=[([1/3]*3,.225)]
for val,rest,w in ((.059715871789770,.470142064105115,.132394152788506),
                   (.797426985353087,.101286507323456,.125939180544827)):
 for i in range(3):
  a=[rest]*3;a[i]=val
  qface.append((a,w))
audit={}
for label,rule,dimension,max_degree in [('Keast_11pt_tetra',q4,4,4),('Dunavant_7pt_tri',qface,3,5)]:
 by_degree={}
 total=0
 for degree in range(max_degree+1):
  max_err=0;worst=None;nm=0
  for p in itertools.product(range(degree+1),repeat=dimension):
   if sum(p)!=degree:continue
   actual=sum(w*math.prod(x**power for x,power in zip(bary,p)) for bary,w in rule)
   exact=math.factorial(dimension-1)*math.prod(math.factorial(v) for v in p)/math.factorial(degree+dimension-1)
   err=abs(actual-exact)
   if err>max_err:max_err=err;worst=p
   nm+=1;total+=1
  by_degree[str(degree)]={'max_absolute_error':max_err,'worst_exponents':worst,'monomials':nm}
 audit[label]={'quadrature_points':len(rule),'certified_max_polynomial_degree':max_degree,
               'tested_monomials':total,'maximum_absolute_monomial_moment_discrepancy':max(x['max_absolute_error'] for x in by_degree.values()),
               'results_by_degree':by_degree}
assert audit['Keast_11pt_tetra']['maximum_absolute_monomial_moment_discrepancy']<1e-14
assert audit['Dunavant_7pt_tri']['maximum_absolute_monomial_moment_discrepancy']<1e-14
record={'status':'PASS all tetra monomials degree <= 4 and face monomials degree <= 5 against exact simplex factorial moments','source':'quad exact moments (dimension−1)! product factorial(exponents)/(degree+dimension−1)!','rules':audit}
(O/'quadrature_moment_audit.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:(v['tested_monomials'],v['maximum_absolute_monomial_moment_discrepancy']) for k,v in audit.items()}))
