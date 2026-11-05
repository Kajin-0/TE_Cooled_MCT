#!/usr/bin/env python3
"""R3.8 read-only per-region quality concentration and worst-element audit."""
from pathlib import Path
import collections,json,time
import numpy as np
ROOT=Path("/work")
RUN=Path("/trial")
t0=time.monotonic()
metadata=json.loads((ROOT/"data/v3_r32_global_surface_20261103/source_metadata.json").read_text())
records=json.loads((RUN/"independent_audit.json").read_text())
root=RUN/"work"
nodes=np.loadtxt(root/"R38_430_domains.1.node",dtype=np.float64,skiprows=1)
ele=np.loadtxt(root/"R38_430_domains.1.ele",dtype=np.int64,skiprows=1)
coords=nodes[:,1:4]
tets=ele[:,1:5]
reg=ele[:,5]
v=coords[tets-1]
a=v[:,1]-v[:,0];b=v[:,2]-v[:,0];c=v[:,3]-v[:,0]
signed=np.einsum("ij,ij->i",a,np.cross(b,c))/6
s=np.zeros(len(ele),np.float64)
for i,j in [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]:
 delta=v[:,i]-v[:,j];s+=np.einsum("ij,ij->i",delta,delta)
q=12*(3*np.abs(signed))**(2/3)/s
by=[]
for name,tag in metadata["domain_id_map"].items():
 vals=q[reg==tag];n=len(vals)
 by.append({
 "name":name,"volume_id":tag,"material":metadata["domains"][name]["material"],
 "tetrahedra":n,"q_min":float(vals.min()),"q_median":float(np.median(vals)),
 "q_lt_0p01":int(np.count_nonzero(vals<.01)),
 "q_lt_0p05":int(np.count_nonzero(vals<.05)),
 "q_lt_0p1":int(np.count_nonzero(vals<.1)),
 "fraction_lt_0p05":float(np.count_nonzero(vals<.05)/n),
 "CAD_relative_volume_error":records["volume_error_all"][name]})
groups=collections.defaultdict(lambda:{"tets":0,"q_lt_0p05":0,"q_lt_0p01":0,"region_count":0})
for r in by:
 g=groups[r["material"]]
 g["tets"]+=r["tetrahedra"]
 g["q_lt_0p05"]+=r["q_lt_0p05"]
 g["q_lt_0p01"]+=r["q_lt_0p01"]
 g["region_count"]+=1
for g in groups.values():g["fraction_lt_0p05"]=g["q_lt_0p05"]/g["tets"]
worst_indices=np.argsort(q)[:30]
worst=[]
by_id={v["volume_id"]:v for v in by}
for i in worst_indices:
 pts=v[i]
 worst.append({"tet_id":int(ele[i,0]),"region":by_id[int(reg[i])]["name"],
 "material":by_id[int(reg[i])]["material"],"quality":float(q[i]),
 "signed_volume_mm3":float(signed[i]),"centroid_mm":pts.mean(axis=0).tolist(),
 "nodes":tets[i].tolist()})
report={"status":"INDEPENDENT REGION QUALITY DIAGNOSTIC; NOT OPTIMIZED",
 "total_tetrahedra":len(q),"regions":len(by),
 "worst_30_tetrahedra":worst,
 "worst_regions_by_bad_element_count":sorted(by,key=lambda x:-x["q_lt_0p05"])[:35],
 "worst_regions_by_fraction_bad_eligible_n_ge_100":sorted([r for r in by if r["tetrahedra"]>=100],key=lambda x:-x["fraction_lt_0p05"])[:35],
 "per_material":dict(sorted(groups.items(),key=lambda x:-x[1]["q_lt_0p05"])),
 "all_regions":by,
 "seconds":round(time.monotonic()-t0,2),"PDE":"NOT RUN"}
(RUN/"region_quality_diagnostic.json").write_text(json.dumps(report,indent=2)+"\n")
print("REGION_QA_DONE",report["seconds"],flush=True)
for r in report["worst_regions_by_bad_element_count"][:12]:
 print(r["name"],r["material"],r["tetrahedra"],r["q_lt_0p05"],r["fraction_lt_0p05"],r["q_min"],flush=True)
print("TOP MATERIALS",[(x,v["tets"],v["q_lt_0p05"]) for x,v in list(report["per_material"].items())[:10]],flush=True)
