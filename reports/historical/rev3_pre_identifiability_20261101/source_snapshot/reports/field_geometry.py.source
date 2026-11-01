"""Exact P1 tetrahedron/plane intersections and audited node/cell correspondence."""
import itertools
import numpy as np
from scipy.spatial import cKDTree

EDGES=tuple(itertools.combinations(range(4),2))


def node_map(reference,field,tolerance=1e-12):
    if len(reference)!=len(field):raise ValueError('Node counts differ')
    distance,index=cKDTree(field).query(reference)
    if not np.isfinite(distance).all() or distance.max()>tolerance or len(np.unique(index))!=len(reference):
        raise ValueError('VTU nodes are not a bijective geometric match')
    return index,float(distance.max())


def cell_map(reference,field):
    if reference.shape!=field.shape:raise ValueError('Tetrahedron counts differ')
    a=np.sort(reference,axis=1);b=np.sort(field,axis=1)
    ia=np.lexsort(a.T[::-1]);ib=np.lexsort(b.T[::-1])
    if not np.array_equal(a[ia],b[ib]):raise ValueError('VTU tetrahedron connectivity differs')
    index=np.empty(len(a),dtype=int);index[ia]=ib;return index


def plane_section(points,cells,axis=1,coordinate=0.,tolerance=1e-12):
    """Triangulated exact intersections, including coplanar faces once.

    At a coincident material/element face, retain the positive-side trace when
    available. Each vertex carries its source-tet P1 barycentric weights. No
    triangulation across voids or scattered-data interpolation is introduced.
    """
    distance=points[cells,axis]-coordinate;other=[a for a in range(3) if a!=axis]
    candidates=np.flatnonzero((distance.min(1)<=tolerance)&(distance.max(1)>=-tolerance))
    polygons={}
    for ci in candidates:
        d=distance[ci];v=points[cells[ci]];poly=[];weights=[]
        for j in np.flatnonzero(abs(d)<=tolerance):
            w=np.eye(4)[j];x=v[j].copy();x[axis]=coordinate;poly.append(x);weights.append(w)
        for a,b in EDGES:
            if d[a]*d[b]<0 and abs(d[a])>tolerance and abs(d[b])>tolerance:
                u=d[a]/(d[a]-d[b]);w=np.zeros(4);w[a]=1-u;w[b]=u;x=w@v;x[axis]=coordinate;poly.append(x);weights.append(w)
        if len(poly)<3:continue
        x=np.array(poly);w=np.array(weights);_,keep=np.unique(np.round(x,14),axis=0,return_index=True);x=x[keep];w=w[keep]
        if len(x)<3:continue
        rel=x[:,other]-x[:,other].mean(0);order=np.argsort(np.arctan2(rel[:,1],rel[:,0]));x=x[order];w=w[order]
        key=tuple(map(tuple,np.array(sorted(np.round(x,13).tolist()))));preference=float(v[:,axis].mean()-coordinate)
        if key not in polygons or preference>polygons[key][0]:polygons[key]=(preference,int(ci),x,w)
    triangles=[];bary=[];owners=[]
    for _,ci,x,w in polygons.values():
        for j in range(1,len(x)-1):
            tri=x[[0,j,j+1]]
            if np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))<=1e-24:continue
            triangles.append(tri);bary.append(w[[0,j,j+1]]);owners.append(ci)
    if not triangles:raise ValueError('Plane does not intersect any finite-area tetrahedron')
    return {'xyz':np.array(triangles),'barycentric':np.array(bary),'cells':np.array(owners),'axis':axis,'coordinate_m':coordinate,'trace':'positive-side preference for coplanar duplicate faces'}


def section_values(section,cells,values):
    return np.einsum('tvi,ti->tv',section['barycentric'],values[cells[section['cells']]])


def triangle_grid(triangles,values):
    """Explicit triangle connectivity; geometry gaps remain gaps."""
    p=triangles.reshape(-1,3);keys=np.round(p,13);_,first,index=np.unique(keys,axis=0,return_index=True,return_inverse=True)
    v=np.asarray(values).reshape(-1);result=np.zeros(len(first));count=np.zeros(len(first));np.add.at(result,index,v);np.add.at(count,index,1)
    spread=np.max(abs(v-result[index]/count[index]))
    if spread>1e-7:raise ValueError('Scalar discontinuity at merged P1 section vertices')
    return p[first],index.reshape(-1,3),result/count


def clip_triangles(triangles,values,axis=1,coordinate=0.):
    """Clip actual boundary triangles to a halfspace, linearly carrying nodal data."""
    result=[];data=[]
    for triangle,scalar in zip(triangles,values):
        poly=[];vs=[]
        for i in range(3):
            a,b=triangle[i-1],triangle[i];va,vb=scalar[i-1],scalar[i];da,db=a[axis]-coordinate,b[axis]-coordinate
            if (da>=0)!=(db>=0):
                u=da/(da-db);poly.append(a+u*(b-a));vs.append(va+u*(vb-va))
            if db>=0:poly.append(b);vs.append(vb)
        for i in range(1,len(poly)-1):
            tri=np.array([poly[0],poly[i],poly[i+1]])
            if np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))>1e-24:result.append(tri);data.append([vs[0],vs[i],vs[i+1]])
    return np.array(result),np.array(data)
