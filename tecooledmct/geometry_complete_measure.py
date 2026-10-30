"""Independent dimensional measurements from the new actual tetrahedron skin."""
import argparse,json
from pathlib import Path
import numpy as np
from .geometry_registry import value,pins,ROOT
from .geometry_measurements import circle
from .geometry_rebaseline import sha,write


def measure(out):
    d=np.load(out/'mesh.npz');p=d['points']*1000;c=d['cells'];b=d['bodies'];m=json.loads((out/'manifest.json').read_text());r=m['registry']
    header=c[b==300];faces=header[:,[[1,2,3],[0,3,2],[0,1,3],[0,2,1]]].reshape(-1,3)
    f,n=np.unique(np.sort(faces,axis=1),axis=0,return_counts=True);f=f[(n==1)&(abs(p[f,2]).max(1)<1e-8)]
    edge=f[:,[[0,1],[1,2],[2,0]]].reshape(-1,2);edge,n=np.unique(np.sort(edge,axis=1),axis=0,return_counts=True);edge=edge[n==1]
    graph={}
    for a,z in edge:graph.setdefault(int(a),[]).append(int(z));graph.setdefault(int(z),[]).append(int(a))
    if any(len(v)!=2 for v in graph.values()):raise ValueError('Open underside boundary loop')
    unseen=set(graph);loops=[]
    while unseen:
        start=next(iter(unseen));cur=start;prev=None;loop=[]
        while True:
            loop.append(cur);unseen.remove(cur);neighbours=graph[cur];nxt=neighbours[0] if neighbours[0]!=prev else neighbours[1]
            if nxt==start:break
            prev,cur=cur,nxt
        xy=p[loop,:2];area=abs(np.sum(xy[:,0]*np.roll(xy[:,1],-1)-xy[:,1]*np.roll(xy[:,0],-1)))/2;loops.append((area,xy))
    loops.sort(key=lambda v:v[0],reverse=True)
    if len(loops)!=12:raise ValueError('Expected12 underside loops')
    holes=[]
    for area,xy in loops[1:]:
        center,radius,error=circle(xy)
        if error>1e-6:raise ValueError('Hole fit failed')
        holes.append({'xy_mm':center.tolist(),'diameter_mm':2*radius,'fit_error_mm':error})
    holes.sort(key=lambda v:v['diameter_mm'],reverse=True);mount=sorted(holes[:2],key=lambda v:v['xy_mm'][0])
    pitch=float(np.linalg.norm(np.diff([v['xy_mm'] for v in mount],axis=0)))
    if abs(pitch-value(r,'hole_pitch'))>1e-6 or any(abs(v['diameter_mm']-value(r,'hole_diameter'))>1e-6 for v in mount):raise ValueError('Mount dimensions differ')
    pinrows=[]
    for pin in pins(r):
        nodes=np.unique(c[b==500+pin['pin']]);nodes=nodes[abs(p[nodes,2])<1e-8];center,radius,error=circle(p[nodes,:2])
        if np.linalg.norm(center-pin['xy_mm'])>1e-6 or abs(2*radius-value(r,'pin_diameter'))>1e-6:raise ValueError('Pin identity/dimension differs')
        pinrows.append({'pin':pin['pin'],'function':pin['function'],'xy_mm':center.tolist(),'diameter_mm':2*radius})
    dimensions=[]
    for bid,width in ((1,'tec_hot_width'),(4,'tec_cold_width')):
        xyz=p[np.unique(c[b==bid])];extent=np.ptp(xyz,axis=0)
        if not np.allclose(extent[:2],value(r,width),atol=1e-6):raise ValueError('Actual ceramic footprint differs')
        dimensions.append({'body':bid,'bbox_mm':np.array([xyz.min(0),xyz.max(0)]).tolist()})
    ports=[]
    for tag in (103,104,6001,6009,6107,6108):
        ff=d['faces'][d['boundaries']==tag];q=p[ff];area=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)/2
        if not len(ff):raise ValueError('Missing physical wire endpoint face')
        centroid=np.dot(area,q.mean(1))/area.sum();ports.append({'tag':tag,'area_mm2':float(area.sum()),'centroid_mm':centroid.tolist()})
        if tag in (103,104) and (abs(area.sum()-.16)>1e-8 or abs(centroid[2]-1.835)>1e-8):raise ValueError('Wrong hot terminal pad')
    source=np.array(json.loads((ROOT/'data/geometry_rebaseline/vigo_outline_trace.json').read_text())['xy_mm']);outline=loops[0][1]
    def dist(points,line):
        a=line;v=np.roll(line,-1,axis=0)-a;t=np.clip(np.einsum('pni,ni->pn',points[:,None]-a,v)/(v*v).sum(1),0,1)
        return np.linalg.norm(points[:,None]-(a+t[:,:,None]*v),axis=2).min(1)
    error=float(max(dist(source,outline).max(),dist(outline,source).max()))
    if error>.08:raise ValueError('Actual mesh/source silhouette differs by more than0.08mm')
    result={'passed':True,'mesh_sha256':sha(out/'mesh.npz'),'source_sha256':sha(Path(__file__)),
            'basis':'actual tetrahedron boundary loops, least-squares circle fits and physical endpoint triangles',
            'mount_pitch_mm':pitch,'mount_holes':mount,'pins':pinrows,'ceramics':dimensions,'wire_ports':ports,
            'mesh_to_source_max_bidirectional_outline_error_mm':error,'outline_target_mm':.08,
            'scope':'source geometry agreement, not as-built tolerance or OEM assembly validation'}
    write(out/'measured_dimensions.json',result);print('Actual mesh dimensions PASS; source silhouette error mm',error,flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);measure(parser.parse_args().out.resolve())
