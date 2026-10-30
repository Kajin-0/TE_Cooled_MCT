"""Measure dimensions from actual tetrahedron skin loops, independent of CAD."""
import argparse
import numpy as np
from pathlib import Path
from .geometry_registry import load,value,pins
from .geometry_rebaseline import write,sha


def circle(xy):
    matrix=np.c_[2*xy,np.ones(len(xy))]
    a,b,c=np.linalg.lstsq(matrix,(xy*xy).sum(1),rcond=None)[0]
    r=np.sqrt(c+a*a+b*b); error=np.max(abs(np.linalg.norm(xy-[a,b],axis=1)-r))
    return np.array([a,b]),float(r),float(error)


def measure(directory):
    registry=load(directory/'registry_snapshot.json');m=np.load(directory/'mesh.npz')
    xyz=m['points']*1000;cells=m['cells'];tags=m['bodies'];header=cells[tags==1]
    faces=header[:,[[1,2,3],[0,3,2],[0,1,3],[0,2,1]]].reshape(-1,3)
    f,count=np.unique(np.sort(faces,axis=1),axis=0,return_counts=True)
    underside=f[(count==1)&(abs(xyz[f,2]).max(1)<1e-8)]
    edge=underside[:,[[0,1],[1,2],[2,0]]].reshape(-1,2)
    edge,count=np.unique(np.sort(edge,axis=1),axis=0,return_counts=True);edge=edge[count==1]
    graph={}
    for a,b in edge:graph.setdefault(int(a),[]).append(int(b));graph.setdefault(int(b),[]).append(int(a))
    if any(len(v)!=2 for v in graph.values()):raise ValueError('Underside boundary is not closed loops')
    unseen=set(graph);loops=[]
    while unseen:
        start=next(iter(unseen));cur=start;prev=None;loop=[]
        while True:
            loop.append(cur);unseen.remove(cur);neighbours=graph[cur]
            nxt=neighbours[0] if neighbours[0]!=prev else neighbours[1]
            if nxt==start:break
            prev,cur=cur,nxt
        xy=xyz[loop,:2];area=abs(np.sum(xy[:,0]*np.roll(xy[:,1],-1)-xy[:,1]*np.roll(xy[:,0],-1)))/2
        loops.append((area,xy))
    loops.sort(key=lambda row:row[0],reverse=True)
    if len(loops)!=12:raise ValueError('Expected one outline, two mounts, nine glass bores')
    holes=[]
    for area,xy in loops[1:]:
        center,r,error=circle(xy)
        if error>1e-7:raise ValueError('Actual hole vertices are not source circles')
        holes.append({'center_mm':center.tolist(),'diameter_mm':2*r,'circle_fit_max_radial_error_mm':error,'boundary_nodes':len(xy)})
    holes.sort(key=lambda row:row['diameter_mm'],reverse=True)
    mount=sorted(holes[:2],key=lambda r:r['center_mm'][0]);pitch=np.linalg.norm(np.diff([r['center_mm'] for r in mount],axis=0))
    if abs(pitch-value(registry,'hole_pitch'))>1e-6:raise ValueError('Actual mounting pitch differs')
    for row in mount:
        if abs(row['diameter_mm']-value(registry,'hole_diameter'))>1e-6:raise ValueError('Actual mount diameter differs')
    pin_rows=[];glass=holes[2:]
    for pin in pins(registry):
        nodes=np.unique(cells[tags==20+pin['pin']]);ix=nodes[abs(xyz[nodes,2])<1e-8]
        center,r,error=circle(xyz[ix,:2]);match=min(glass,key=lambda row:np.linalg.norm(np.array(row['center_mm'])-center))
        if np.linalg.norm(center-pin['xy_mm'])>1e-6 or abs(2*r-value(registry,'pin_diameter'))>1e-6:raise ValueError('Actual pin coordinate/diameter mismatch')
        if np.linalg.norm(center-match['center_mm'])>1e-6:raise ValueError('Metal/glass eccentricity')
        pin_rows.append({'pin':pin['pin'],'function':pin['function'],'measured_center_mm':center.tolist(),
                         'metal_diameter_mm':2*r,'glass_bore_diameter_mm':match['diameter_mm'],
                         'radial_insulation_mm':match['diameter_mm']/2-r,'circle_fit_max_error_mm':error})
    ceramics=[]
    for body,key in ((31,'tec_hot_width'),(32,'tec_cold_width')):
        pts=xyz[np.unique(cells[tags==body])];bound=np.array([pts.min(0),pts.max(0)]);extent=np.ptp(pts,axis=0)
        if not np.allclose(extent[:2],value(registry,key),atol=1e-8):raise ValueError('Actual TEC footprint differs')
        ceramics.append({'body':body,'bbox_mm':bound.tolist(),'footprint_mm':extent[:2].tolist()})
    corner=np.sqrt(2)*value(registry,'tec_hot_width')/2
    result={'basis':'actual tetrahedron skin loops and nodes; no CAD mass properties used',
            'mesh_sha256':sha(directory/'mesh.npz'),'measurement_source_sha256':sha(Path(__file__)),
            'underside_loops':len(loops),'mount_holes':mount,'hole_pitch_mm':float(pitch),
            'pin_measurements':pin_rows,'ceramics':ceramics,
            'TEC_hot_corner_to_case_OUTER_envelope_mm':value(registry,'cap_od')/2-corner,
            'clearance_scope':'positive envelope space only; true inside-wall/carrier/lead clearances not qualified',
            'geometry_dimensions_passed':True,'full_device_physics_passed':False}
    write(directory/'measured_dimensions.json',result);print('Independent actual-mesh dimensions passed;12 boundary loops,9 isolated pins')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--directory',type=Path,required=True)
    measure(parser.parse_args().directory.resolve())
