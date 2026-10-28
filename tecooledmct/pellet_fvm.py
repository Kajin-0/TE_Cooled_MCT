"""Spatial 3D finite-volume pellet conduction / Joule simulation.

Solves -div(k grad T) = rho*(I/A)^2 in actual voxelized dimensions with
fixed end temperatures and Robin sidewall heat transfer. The Peltier
junction term is applied analytically AFTER the field solve. This is NOT
a full package CAD FEM or a fully coupled P/N electrical field solution.
"""
from dataclasses import dataclass
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from .geometry_sweep import TECGeometry, geometry_coefficients

@dataclass(frozen=True)
class PelletField:
    stage: int=2
    leg_height_mm: float=.64
    leg_side_mm: float=.4
    nx: int=6
    ny: int=6
    nz: int=20
    cold_k: float=195.5
    hot_k: float=225.5
    current_a: float=.65
    side_h_w_m2k: float=0.
    side_ambient_k: float=300.

    def validate(self):
        if self.stage not in (0,1,2): raise ValueError("stage")
        if self.leg_height_mm<=0 or self.leg_side_mm<=0: raise ValueError("dimensions")
        if any(n<2 or n>60 for n in (self.nx,self.ny,self.nz)): raise ValueError("mesh")
        if any(t<=0 for t in (self.cold_k,self.hot_k,self.side_ambient_k)):raise ValueError("temperature")
        if self.side_h_w_m2k<0:raise ValueError("side h")
        return self

def simulate_pellet(p:PelletField):
    p.validate()
    c=geometry_coefficients(TECGeometry())
    n_pairs=float(c["couples"][p.stage])
    l_ref=float(c["leg_lengths_m"][p.stage]);a_ref=float(c["leg_area_m2"])
    rho=float(c["resistance_ohm"][p.stage])/(2*n_pairs)*a_ref/l_ref
    k=float(c["thermal_conductance_w_per_k"][p.stage])*l_ref/(2*n_pairs*a_ref)
    S=float(c["alpha_v_per_k"][p.stage])/(2*n_pairs)
    w=p.leg_side_mm*1e-3;L=p.leg_height_mm*1e-3
    dx=w/p.nx;dy=w/p.ny;dz=L/p.nz
    n=p.nx*p.ny*p.nz
    qvol=(p.current_a/w**2)**2*rho
    def idx(i,j,m):return (m*p.ny+j)*p.nx+i
    rows=[];cols=[];vals=[];rhs=np.full(n,qvol*dx*dy*dz)
    directions=((1,0,0,dx,dy*dz),(-1,0,0,dx,dy*dz),
                (0,1,0,dy,dx*dz),(0,-1,0,dy,dx*dz),
                (0,0,1,dz,dx*dy),(0,0,-1,dz,dx*dy))
    for m in range(p.nz):
        for j in range(p.ny):
            for i in range(p.nx):
                row=idx(i,j,m);diag=0.
                for di,dj,dm,step,area in directions:
                    ii=i+di;jj=j+dj;mm=m+dm
                    if 0<=ii<p.nx and 0<=jj<p.ny and 0<=mm<p.nz:
                        G=k*area/step;diag+=G
                        rows.append(row);cols.append(idx(ii,jj,mm));vals.append(-G)
                    elif dm!=0:
                        G=2*k*area/step;diag+=G
                        rhs[row]+=G*(p.hot_k if dm>0 else p.cold_k)
                    elif p.side_h_w_m2k>0:
                        G=area/(step/(2*k)+1/p.side_h_w_m2k)
                        diag+=G;rhs[row]+=G*p.side_ambient_k
                rows.append(row);cols.append(row);vals.append(diag)
    T=spsolve(coo_matrix((vals,(rows,cols)),shape=(n,n)).tocsr(),rhs).reshape((p.nz,p.ny,p.nx))
    G_end=2*k*dx*dy/dz
    q_out_cold=float(np.sum(G_end*(T[0]-p.cold_k)))
    q_out_hot=float(np.sum(G_end*(T[-1]-p.hot_k)))
    h=p.side_h_w_m2k
    if h>0:
        gx=dy*dz/(dx/(2*k)+1/h);gy=dx*dz/(dy/(2*k)+1/h)
        q_sides=float(gx*(np.sum(T[:,:,0]-p.side_ambient_k)+np.sum(T[:,:,-1]-p.side_ambient_k))
              +gy*(np.sum(T[:,0,:]-p.side_ambient_k)+np.sum(T[:,-1,:]-p.side_ambient_k)))
    else:q_sides=0.
    joule=float(qvol*dx*dy*dz*n)
    qc=float(S*p.current_a*p.cold_k-q_out_cold)
    qh=float(S*p.current_a*p.hot_k+q_out_hot)
    voltage=float(p.current_a*rho*L/w**2+S*(p.hot_k-p.cold_k))
    return {"field_k":T,"height_mm":p.leg_height_mm,"side_mm":p.leg_side_mm,
      "grid":[p.nx,p.ny,p.nz],"dx_m":dx,"dy_m":dy,"dz_m":dz,
      "effective_resistivity_ohm_m":rho,"effective_conductivity_w_mk":k,
      "effective_seebeck_v_k_per_leg":S,
      "cold_surface_k":p.cold_k,"hot_surface_k":p.hot_k,
      "centerline_k":T[:,p.ny//2,p.nx//2],
      "heat_out_cold_w_per_pellet":q_out_cold,"heat_out_hot_w_per_pellet":q_out_hot,
      "heat_out_sides_w_per_pellet":q_sides,"joule_heating_w_per_pellet":joule,
      "qc_w_per_pellet":qc,"qh_w_per_pellet":qh,"voltage_v_per_pellet":voltage,
      "pde_energy_residual_w":abs(q_out_cold+q_out_hot+q_sides-joule),
      "pde_model":"3D voxel finite-volume heat+Joule; Peltier evaluated at terminal faces (not inside spatial PDE)."}
