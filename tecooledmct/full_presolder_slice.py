"""Conformal plane splitting of existing joint tetrahedra; no moved old nodes."""
import numpy as np


def split_joint(points,cells,bodies,faces,tags,patch_index,cuts,region_bodies):
    p=[row.copy() for row in points];new_edges=[];cache={};joint_nodes=set(np.unique(cells[bodies==191]));tol=2e-13
    def intersection(a,b,z):
        if abs(p[a][2]-z)<tol:return a
        if abs(p[b][2]-z)<tol:return b
        u,v=sorted((int(a),int(b)));key=(u,v,float(z))
        if key in cache:return cache[key]
        t=(z-p[u][2])/(p[v][2]-p[u][2]);n=len(p);x=(1-t)*p[u]+t*p[v];x[2]=z;p.append(x);new_edges.append((u,v,t));cache[key]=n
        return n
    def clip(poly,z,below):
        result=[]
        for i,b in enumerate(poly):
            a=poly[i-1];da=p[a][2]-z;db=p[b][2]-z;ina=da<=tol if below else da>=-tol;inb=db<=tol if below else db>=-tol
            if ina!=inb:result.append(intersection(a,b,z))
            if inb:result.append(b)
        return list(dict.fromkeys(result))
    def triangles(poly):
        if len(poly)<3:return []
        i=poly.index(min(poly));poly=poly[i:]+poly[:i]
        return [[poly[0],poly[j],poly[j+1]] for j in range(1,len(poly)-1)]
    def divide(polyhedron,z):
        ids=set(sum(polyhedron,[]));zz=[p[v][2] for v in ids]
        if max(zz)<=z+tol:return polyhedron,None
        if min(zz)>=z-tol:return None,polyhedron
        lower=[clip(face,z,True) for face in polyhedron];upper=[clip(face,z,False) for face in polyhedron]
        cap=sorted({v for face in lower for v in face if abs(p[v][2]-z)<tol});xy=np.array([p[v][:2] for v in cap]);angle=np.arctan2(xy[:,1]-xy[:,1].mean(),xy[:,0]-xy[:,0].mean());cap=[cap[i] for i in np.argsort(angle)]
        return [v for v in lower if len(v)>=3]+[cap],[v for v in upper if len(v)>=3]+[cap[::-1]]
    cc=[];bb=[]
    for row,bid in zip(cells,bodies):
        if bid!=191:cc.append(row.tolist());bb.append(int(bid));continue
        pieces=[([np.delete(row,i).tolist() for i in range(4)],0)]
        for plane_index,z in enumerate(cuts):
            updated=[]
            for poly,region in pieces:
                if region!=plane_index:updated.append((poly,region));continue
                lower,upper=divide(poly,z)
                if lower:updated.append((lower,region))
                if upper:updated.append((upper,region+1))
            pieces=updated
        for poly,region in pieces:
            apex=min(sum(poly,[]))
            for face in poly:
                if apex in face:continue
                for tri in triangles(face):
                    child=[apex,*tri];x=np.array([p[v] for v in child]);det=np.linalg.det(x[1:]-x[:1])
                    if abs(det)<1e-28:continue
                    if det<0:child[0],child[1]=child[1],child[0]
                    cc.append(child);bb.append(region_bodies[region])
    ff=[];tt=[];pi=[]
    for row,tag,patch in zip(faces,tags,patch_index):
        polys=[row.tolist()]
        if all(v in joint_nodes for v in row):
            for z in cuts:
                result=[]
                for poly in polys:
                    zz=[p[v][2] for v in poly]
                    if min(zz)<z-tol and max(zz)>z+tol:
                        result.extend([v for v in [clip(poly,z,True),clip(poly,z,False)] if len(v)>=3])
                    else:result.append(poly)
                polys=result
        for poly in polys:
            for tri in triangles(poly):ff.append(tri);tt.append(int(tag));pi.append(int(patch))
    return np.array(p),np.array(cc,dtype=int),np.array(bb),np.array(ff,dtype=int),np.array(tt),np.array(pi),np.array(new_edges)
