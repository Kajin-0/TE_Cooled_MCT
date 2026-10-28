"""Material-based *alternative* stage coefficients, explicitly NOT OEM calibrated.

Values constructed from separate room-temperature literature examples for P/N
bismuth telluride. These are not the specific 3MC04 formulation. Default model
remains the OEM-limit calibrated effective coefficients.
"""
import numpy as np
from .materials import P_BI_TE,N_BI_TE
from .geometry_sweep import TECGeometry
from .model import COUPLES

def literature_stage_coefficients(g:TECGeometry):
    g.validate()
    L=np.asarray(g.leg_lengths_mm)*1e-3
    A=(g.leg_side_mm*1e-3)**2
    n=COUPLES.copy()
    resistivity_pair=P_BI_TE.electrical_resistivity_ohm_m+N_BI_TE.electrical_resistivity_ohm_m
    k_pair=P_BI_TE.thermal_conductivity_w_mk+N_BI_TE.thermal_conductivity_w_mk
    alpha_pair=P_BI_TE.seebeck_v_k-N_BI_TE.seebeck_v_k
    R=n*L*resistivity_pair/A
    K=n*k_pair*A/L
    return {"alpha_v_per_k":n*alpha_pair,
            "resistance_ohm":R, "thermal_conductance_w_per_k":K,
            "leg_lengths_m":L, "leg_area_m2":A, "couples":n,
            "method":"Uncalibrated 300K literature material profile. NOT actual OEM P/N grade."}

def compare_coefficients(g=None):
    from .geometry_sweep import geometry_coefficients
    if g is None:g=TECGeometry()
    fitted=geometry_coefficients(g)
    literature=literature_stage_coefficients(g)
    return {name:{"Seebeck_total_v_k":float(np.sum(c["alpha_v_per_k"])),
                  "resistance_total_ohm":float(np.sum(c["resistance_ohm"])),
                  "stage_K_w_k":c["thermal_conductance_w_per_k"].tolist(),
                  "note":"Do NOT claim this contrast is measured uncertainty."}
            for name,c in (("OEM_limit_fitted",fitted),("uncalibrated_literature_300K",literature))}
