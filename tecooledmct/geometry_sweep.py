"""Geometry-sensitive cascade TEC model; NOT spatial FEM or CAD-meshed physics.

Pellet length L and cross-section A control R~L/A and K~A/L. The effective
material values are Phase-0 fitted parameters, not measured P/N properties.
"""
from dataclasses import dataclass, replace
import numpy as np
from scipy.optimize import least_squares
from .model import Scenario, COUPLES, LEG_LENGTH_M, LEG_AREA_M2, R_STAGE, K_STAGE, ALPHA_STAGE, heat_breakdown

@dataclass(frozen=True)
class TECGeometry:
    leg_lengths_mm: tuple=(1.07, .82, .64)   # stage order: bottom/middle/top
    leg_side_mm: float=.40
    contact_fraction: float=0.0              # assumed baseline R contact fraction

    def validate(self):
        if len(self.leg_lengths_mm)!=3 or not all(.15<=v<=2 for v in self.leg_lengths_mm):
            raise ValueError("three lengths required, 0.15..2 mm")
        if not .2<=self.leg_side_mm<=.8: raise ValueError("leg side 0.2..0.8 mm")
        if not 0<=self.contact_fraction<.6: raise ValueError("contact_fraction 0..0.6")
        return self

def geometry_coefficients(g:TECGeometry):
    g.validate()
    L=np.asarray(g.leg_lengths_mm,dtype=float)*1e-3
    area=(g.leg_side_mm*1e-3)**2
    ratio=area/LEG_AREA_M2
    R=R_STAGE/ratio*((1-g.contact_fraction)*L/LEG_LENGTH_M+g.contact_fraction)
    K=K_STAGE*ratio*LEG_LENGTH_M/L
    return {"alpha_v_per_k":ALPHA_STAGE.copy(),"resistance_ohm":R,
            "thermal_conductance_w_per_k":K,"leg_lengths_m":L,
            "leg_area_m2":area,"couples":COUPLES.copy()}

def transport_geometry(i,I,Tc,Th,coeff):
    a=float(coeff["alpha_v_per_k"][i]);R=float(coeff["resistance_ohm"][i]);K=float(coeff["thermal_conductance_w_per_k"][i])
    leakage=K*(Th-Tc)
    return {"qc_w":a*I*Tc-I*I*R/2-leakage,
            "qh_w":a*I*Th+I*I*R/2-leakage,
            "voltage_v":I*R+a*(Th-Tc),
            "resistance_ohm":R,"conductance_w_per_k":K,
            "alpha_v_per_k":a,"joule_w":I*I*R}

def solve_geometry(s:Scenario,g:TECGeometry,coefficients=None):
    """OEM-fit by default; optionally inject a documented stage-property profile."""
    s.validate();c=geometry_coefficients(g) if coefficients is None else coefficients
    def evaluate(x):
        t1,t2,t3,th=x
        l=heat_breakdown(s,(t1,t2,t3),th)
        tr=[transport_geometry(0,s.current_a,t1,th,c),
            transport_geometry(1,s.current_a,t2,t1,c),
            transport_geometry(2,s.current_a,t3,t2,c)]
        return l,tr
    def residual(x):
        t1,t2,t3,th=x;l,tr=evaluate(x);q=l["total_w"]
        sink=(th-s.ambient_k)/s.hot_to_ambient_k_per_w-tr[0]["qh_w"] if s.hot_to_ambient_k_per_w>0 else th-s.ambient_k
        return [tr[0]["qc_w"]-tr[1]["qh_w"]-q[0],
                tr[1]["qc_w"]-tr[2]["qh_w"]-q[1],
                tr[2]["qc_w"]-q[2],sink]
    initial=np.clip(np.array([s.ambient_k-25,s.ambient_k-48,s.ambient_k-70,s.ambient_k+3]),120.001,599.999)
    fit=least_squares(residual,initial,bounds=(np.full(4,120.),np.full(4,600.)),
                      xtol=1e-11,gtol=1e-11,ftol=1e-11,max_nfev=200)
    err=float(np.max(np.abs(residual(fit.x)[:3])))
    if not fit.success or err>1e-6: raise RuntimeError(f"nonconverged geometry state, thermal residual {err:g} W")
    load,tr=evaluate(fit.x);v=sum(t["voltage_v"] for t in tr);power=s.current_a*v
    useful=s.detector_bias_v**2/s.detector_resistance_ohm+s.detector_optical_absorbed_w
    return {"stage_k":[float(x) for x in fit.x[:3]],"hot_k":float(fit.x[3]),
        "detector_k":float(fit.x[2]),"current_a":s.current_a,
        "voltage_v":float(v),"electrical_power_w":float(power),
        "top_cooling_load_w":float(load["total_w"][2]),
        "top_load_cop":float(load["total_w"][2]/power) if power>0 else None,
        "useful_detector_cop":float(useful/power) if power>0 else None,
        "stage_transport":tr,"load_breakdown_w":{k:[float(x) for x in a] for k,a in load.items()},
        "energy_balance_max_w":err,
        "material_status":"OEM-limits anchored effective values; individual parameters not validated",
        "leg_geometry":{"lengths_mm":list(g.leg_lengths_mm),"side_mm":g.leg_side_mm,
                        "couples":COUPLES.astype(int).tolist(),"contact_fraction":g.contact_fraction}}

def sweep_pellet_height(s=Scenario(),factors=None,stage="all",g=TECGeometry()):
    if factors is None: factors=np.linspace(.65,1.35,15)
    ids={"bottom":[0],"middle":[1],"top":[2],"all":[0,1,2]}
    if stage not in ids:raise ValueError("stage: bottom/middle/top/all")
    out=[]
    for f in factors:
        L=list(g.leg_lengths_mm)
        for i in ids[stage]:L[i]*=float(f)
        p=solve_geometry(s,replace(g,leg_lengths_mm=tuple(L)))
        out.append({"factor":float(f),"leg_lengths_mm":L,
                    "detector_k":p["detector_k"],"stage_k":p["stage_k"],
                    "TEC_resistance_ohm":sum(t["resistance_ohm"] for t in p["stage_transport"]),
                    "electrical_power_w":p["electrical_power_w"],
                    "useful_detector_cop":p["useful_detector_cop"],
                    "top_load_cop":p["top_load_cop"],
                    "energy_balance_max_w":p["energy_balance_max_w"]})
    return out
