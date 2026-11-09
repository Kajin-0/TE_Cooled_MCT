"""Bounded electrical/thermal *proxy* for a voltage-biased HgCdTe photoconductor.

R(T)=Rref exp[(Eeff/kB)(1/T-1/Tref)].
Eeff is a selected effective DARK RESISTANCE slope, NOT the band gap, carrier
density, intrinsic optical absorption or measured HgCdTe recombination law.

Use a prescribed ABSORBED optical heat in parallel with bias Joule V^2/R(T).
No photo-current, signal/noise, self-consistent transport or junction physics.
"""
from math import exp,isfinite
BOLTZMANN_EV_K=8.617333262145e-5
HC_EV_UM=1.2398419843320026

def hsc_bandgap_eV(x,T_K):
    """Hansen-Schmit-Casselman Hg(1-x)Cd(x)Te Eg; for physical context only."""
    if not (0<=x<=1 and 5<=T_K<=300): raise ValueError("HSC domain")
    return -0.302+1.930*x-0.810*x*x+0.832*x**3+0.535*(1-2*x)*T_K/1000.

def photoconductor_at_T(T_K,bias_V,absorbed_optical_W,reference_R_ohm,
                       reference_T_K,activation_eV):
    assert 180<=T_K<=390 and 0<=bias_V<=2.0
    assert 0<=absorbed_optical_W<=.010
    assert 50<=reference_R_ohm<=5000 and 180<=reference_T_K<=300
    assert 0<=activation_eV<=.150
    exponent=activation_eV/BOLTZMANN_EV_K*(1/T_K-1/reference_T_K)
    assert abs(exponent)<20
    R=reference_R_ohm*exp(exponent)
    I=bias_V/R
    P=bias_V*I
    derivative=P*activation_eV/(BOLTZMANN_EV_K*T_K*T_K)
    Q=P+absorbed_optical_W
    assert all(isfinite(v) for v in (R,I,P,Q,derivative))
    assert abs(P-bias_V*I)<1e-16
    return {'temperature_K':float(T_K),
            'voltage_V':float(bias_V),
            'dark_resistance_ohm':float(R),
            'detector_dark_current_A':float(I),
            'detector_bias_Joule_W':float(P),
            'absorbed_optical_heat_W':float(absorbed_optical_W),
            'total_applied_detector_heat_W':float(Q),
            'd_bias_Joule_dT_W_K_at_constant_V':float(derivative),
            'R_ref_ohm':float(reference_R_ohm),
            'T_ref_K':float(reference_T_K),
            'effective_activation_eV':float(activation_eV),
            'qualification':'CONDITIONAL reference R and activation hypothesis; no measured HgCdTe R(T) or photoresponse'}
