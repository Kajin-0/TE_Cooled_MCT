"""SI RT0 face-current recovery and independent mixed RT0/P0 discretization.

The original CG operator is imported, never modified. No thermal or TEC law.
An oriented face DOF is integral J.n [A]; one shared DOF gives H(div) normal
continuity. Recovery fixes CG terminal current; mixed computes its own current.
"""
from collections import defaultdict
import numpy as np
from scipy.sparse import coo_matrix, bmat, csr_matrix, diags, vstack
from scipy.sparse.linalg import splu


class FluxSpace:
    def __init__(self, op, contact_r, all_dirichlet=False, boundary_function=None):
        if not np.isfinite(contact_r) or contact_r <= 0:
            raise ValueError('Positive finite contact area resistance required')
        self.op = op
        self.re = contact_r
        self.all_dirichlet = all_dirichlet
        self.bc = boundary_function
        xyz = op.p[op.t]
        self.c = xyz.mean(axis=1)
        self.vol = op.volume
        self.rho = np.linalg.inv(op.tensor)
        if np.any(np.linalg.eigvalsh(self.rho) <= 0):
            raise ValueError('Positive conductivity tensor required')
        fmap = {}
        faces = []
        incidence = []
        cellfaces = np.empty_like(op.t)
        signs = np.empty_like(op.t, dtype=float)
        for c, row in enumerate(op.t):
            for i in range(4):
                key = tuple(sorted(np.delete(row, i)))
                if key not in fmap:
                    fmap[key] = len(faces)
                    faces.append(key)
                    incidence.append([])
                f = fmap[key]
                signs[c, i] = 1 if not incidence[f] else -1
                incidence[f].append((c, i))
                if len(incidence[f]) > 2:
                    raise ValueError('Nonmanifold tetrahedral face')
                cellfaces[c, i] = f
        self.faces = np.asarray(faces)
        self.incidence = incidence
        self.cf = cellfaces
        self.signs = signs
        pp = op.p[self.faces]
        self.area = np.linalg.norm(np.cross(pp[:,1]-pp[:,0], pp[:,2]-pp[:,0]), axis=1)/2
        self.meta = {}
        for tri, tag in zip(op.faces, op.fid):
            f = fmap[tuple(sorted(tri))]
            self.meta[f] = op.meta[int(tag)]
        nfaces = len(faces)
        self.contact = np.zeros(nfaces)
        self.active = np.ones(nfaces, bool)
        self.source = []
        self.ground = []
        self.b = np.zeros(nfaces)
        for f, ee in enumerate(incidence):
            if len(ee) == 2:
                if op.r[ee[0][0]] != op.r[ee[1][0]]:
                    if f not in self.meta or len(self.meta[f]['owners']) != 2:
                        raise ValueError('Unregistered material contact')
                    self.contact[f] = contact_r/self.area[f]
            else:
                info = self.meta[f]
                ep = info['electrical_port']
                if all_dirichlet:
                    # Quadratic Dirichlet face mean, exactly degree-two rule.
                    bary = np.array([[2/3,1/6,1/6],[1/6,2/3,1/6],[1/6,1/6,2/3]])
                    self.b[f] = boundary_function(bary @ op.p[self.faces[f]]).mean()
                elif ep >= 0:
                    self.b[f] = 1. if ep == 0 else 0.
                    (self.source if ep == 0 else self.ground).append(f)
                else:
                    self.active[f] = False
        if not all_dirichlet and (not self.source or not self.ground):
            raise ValueError('Both internal terminals required')
        # phi_i=(x-v_i)/(3 volume), unit outward integrated normal flux.
        a = self.c[:,None,:]-xyz
        centered = xyz-self.c[:,None,:]
        covariance = np.einsum('eia,eib->eab', centered, centered)/20
        moment = np.einsum('eab,eba->e', self.rho, covariance)
        local = (np.einsum('eia,eab,ejb->eij', a, self.rho, a)+moment[:,None,None])/(9*self.vol[:,None,None])
        self.local = local
        oriented = local*signs[:,:,None]*signs[:,None,:]
        rows = np.repeat(cellfaces,4,axis=1).ravel()
        cols = np.tile(cellfaces,(1,4)).ravel()
        self.mass = coo_matrix((oriented.ravel(),(rows,cols)),shape=(nfaces,nfaces)).tocsr()+diags(self.contact)
        self.D = coo_matrix((signs.ravel(),(np.repeat(np.arange(len(op.t)),4),cellfaces.ravel())),shape=(len(op.t),nfaces)).tocsr()

    def saddle(self, rhs, prescribed_current=None):
        use = self.active
        D = self.D[:,use]
        extra = prescribed_current is not None
        constraints = np.zeros(len(self.op.t)+int(extra))
        if extra:
            row = np.zeros(len(use)); row[self.source] = 1
            D = vstack([D,csr_matrix(row[use][None,:])]).tocsr()
            constraints[-1] = -prescribed_current
        M = self.mass[use][:,use]
        # Symmetric diagonal scaling is numerical only; equations unchanged.
        s = 1/np.sqrt(M.diagonal())
        S = diags(s)
        Ds = D @ S
        K = bmat([[S@M@S,-Ds.T],[-Ds,None]],format='csc')
        answer = splu(K).solve(np.r_[s*rhs[use],-constraints])
        q = np.zeros(len(use)); q[use] = s*answer[:sum(use)]
        potential = answer[sum(use):sum(use)+len(self.op.t)]
        if not np.isfinite(q).all() or not np.isfinite(potential).all():
            raise ValueError('Nonfinite flux solve')
        return q,potential

    def mixed(self):
        return self.saddle(-self.b)

    def recover(self, u, J, current=None):
        op = self.op
        # Constitutive least squares in bulk resistivity metric.
        a = self.c[:,None,:]-op.p[op.t]
        local = np.einsum('eia,eab,eb->ei',a,self.rho,J)/3
        rhs = np.zeros(len(self.faces))
        np.add.at(rhs,self.cf.ravel(),(local*self.signs).ravel())
        lookup = {(int(r),int(n)):i for i,(r,n) in enumerate(op.unique)}
        for f in np.flatnonzero(self.contact):
            left,right = self.incidence[f]
            r0,r1 = int(op.r[left[0]]),int(op.r[right[0]])
            jump = np.mean([u[lookup[(r0,int(n))]]-u[lookup[(r1,int(n))]] for n in self.faces[f]])
            rhs[f] += jump
        return self.saddle(rhs,current)

    def evaluate(self,q):
        # Independent four-point degree-two volume quadrature of RT0 losses.
        bary = np.full((4,4),.1381966011250105)
        np.fill_diagonal(bary,.5854101966249685)
        xyz = self.op.p[self.op.t]
        locations = np.einsum('qi,eia->eqa',bary,xyz)
        localq = q[self.cf]*self.signs
        J = np.einsum('ei,eqia->eqa',localq,locations[:,:,None,:]-xyz[:,None,:,:])/(3*self.vol[:,None,None])
        density = np.einsum('eqa,eab,eqb->eq',J,self.rho,J)
        loss = (density.mean(axis=1)*self.vol).sum()
        ip = self.contact*q*q
        scale = max(float(abs(q).max()),1e-30)
        div = np.asarray(self.D@q)
        I = -q[self.source].sum() if self.source else None
        out = dict(bulk_W=float(loss),interface_W=float(ip.sum()),total_W=float(loss+ip.sum()),
                   max_cell_imbalance_relative=float(abs(div).max()/scale),input_A=None if I is None else float(I),
                   terminal_relative_error=None if I is None else float(abs(q[self.ground].sum()-I)/abs(I)),
                   zero_current='Exact linear scaling; no current rating',J_quadrature=J,locations=locations,
                   interface_power_faces=ip)
        return out

    def contact_jump(self,q,potential):
        localq = q[self.cf]*self.signs
        trace = potential[:,None]-np.einsum('eij,ej->ei',self.local,localq)
        values = []
        for f in np.flatnonzero(self.contact):
            (c,i),(d,j) = self.incidence[f]
            values.append((trace[c,i]-trace[d,j],self.contact[f]*q[f]))
        return np.array(values)


def cg_solution(op, boundary_function=None):
    if boundary_function is None:
        result,u,J,H = op.electrical()
        return result,u,J
    u = np.zeros(op.ndof);fixed = np.zeros(op.ndof,bool)
    for j,da,f,M in op.boundaries:
        u[da] = boundary_function(op.p[op.unique[da,1]])
        fixed[da] = True
    free = ~fixed
    u[free] = splu(op.K[free][:,free].tocsc()).solve(-(op.K@u)[free])
    grad = np.einsum('ei,eij->ej',u[op.dofs]-u[op.dofs[:,:1]],op.grad)
    J = -np.einsum('eij,ej->ei',op.tensor,grad)
    return dict(manufactured=True),u,J
