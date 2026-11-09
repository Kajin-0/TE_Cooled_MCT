"""V3.10 independently evaluable p-type HgCdTe equilibrium photoconductor.

Research basis (source identity, NOT measurements on the simulated package):
Hansen, Schmit & Casselman, J Appl Phys 53, 7099 (1982) Eg(x,T);
Hansen & Schmit, J Appl Phys (1983) ni(x,T), DOI 10.1063/1.332153;
Pan et al., Adv Mater Interfaces 10, 2201932 (2023), DOI 10.1002/admi.202201932:
  bulk Ohmic R=L/[qWt(n*mue+p*muh)] and p-n=net ionized acceptors;
  electron/hole mobility ratio ~100 as a common HgCdTe proxy.
Published example p-HgCdTe mobilities: Thin Solid Films (2014), Elsevier S0040609013018300;
  actual x=.22 ~400-580 cm2/Vs,
  x=.30-.38 ~200-220 cm2/Vs, separate specimens, not matched.
DO NOT treat any illustrative inputs as measured detector/package parameters.

Assumptions: 50<T<300 K, .16<=x<=.40, positive Eg, nondegenerate
equilibrium / fully ionized net acceptors, uniform p-type material, Ohmic
low field, no surfaces/contacts/shunts, fixed mobility over T, no photo
carrier population or optical absorption transfer. Optical load is an
externally specified ABSORBED thermal power, never responsivity.
No noise beyond ideal equilibrium Johnson thermal noise.
"""
from __future__ import annotations
from math import exp,hypot,sqrt,isfinite
Q_C=1.602176634e-19
KB_EV_K=8.617333262145e-5
KB_J_K=1.380649e-23
HC_EV_UM=1.2398419843320026
BANDGAP_DOI='https://doi.org/10.1063/1.330018'
INTRINSIC_DOI='https://doi.org/10.1063/1.332153'
PHOTOCONDUCTOR_DOI='https://doi.org/10.1002/admi.202201932'
HOLE_MOBILITY_SOURCE='https://www.sciencedirect.com/science/article/abs/pii/S0040609013018300'
def _valid(x,T):
    if not (.16<=x<=.40 and 50.<T<=300. and isfinite(x) and isfinite(T)):
        raise ValueError('Out of source-bounded HgCdTe x/T domain (.16.. .40, 50<T<=300K)')
def bandgap_eV(x,T):
    _valid(x,T)
    eg=-.302+1.93*x-.810*x*x+.832*x**3+.000535*(1.-2*x)*T
    if eg<=0 or not isfinite(eg):raise ValueError('Non-positive electronic bandgap: ni formula invalid')
    return eg
def intrinsic_cm3(x,T):
    eg=bandgap_eV(x,T)
    a=5.585-3.820*x+.001753*T-.001364*x*T
    if a<=0:raise ValueError('Invalid Hansen-Schmit prefactor')
    return a*1e14*eg**.75*T**1.5*exp(-eg/(2*KB_EV_K*T))
def intrinsic_log_slope_per_K(x,T):
    eg=bandgap_eV(x,T)
    deg=.000535*(1-2*x)
    a=5.585-3.820*x+.001753*T-.001364*x*T
    da=.001753-.001364*x
    return da/a+.75*deg/eg+1.5/T-deg/(2*KB_EV_K*T)+eg/(2*KB_EV_K*T*T)
def state(T_K,voltage_V,absorbed_optical_W,
          composition_x,net_acceptors_cm3,
          channel_length_m,channel_width_m,channel_thickness_m,
          mu_h_cm2_Vs,mu_e_over_h_ratio):
    x=float(composition_x);T=float(T_K)
    eg=bandgap_eV(x,T)
    vals=(T,voltage_V,absorbed_optical_W,x,net_acceptors_cm3,
         channel_length_m,channel_width_m,channel_thickness_m,
         mu_h_cm2_Vs,mu_e_over_h_ratio)
    if not all(isfinite(v) for v in vals):raise ValueError('Nonfinite photoconductor input')
    if not (0<=voltage_V<=1.0 and 0<=absorbed_optical_W<=.01):
        raise ValueError('Voltage/absorbed optical load outside registered bound')
    if not (1e14<=net_acceptors_cm3<=1e17):
        raise ValueError('Hypothetical net fully ionized acceptors outside input range')
    if not (0<channel_length_m<=.001 and 0<channel_width_m<=.001
            and 0<channel_thickness_m<=.0001 and mu_h_cm2_Vs>0
            and 1<=mu_e_over_h_ratio<=200):
        raise ValueError('Invalid hypothetical device geometry/mobility')
    ni=intrinsic_cm3(x,T)
    D=hypot(net_acceptors_cm3,2*ni)
    p=.5*(net_acceptors_cm3+D)
    n=ni*ni/p
    assert abs(p-n-net_acceptors_cm3)<1e-7*max(p,1)
    dlnni=intrinsic_log_slope_per_K(x,T)
    dp=2*ni*ni*dlnni/D
    dn=n*(2*dlnni-dp/p)
    mu_h=mu_h_cm2_Vs*1e-4
    mu_e=mu_h*mu_e_over_h_ratio
    conductivity=Q_C*1e6*(n*mu_e+p*mu_h)
    d_sigma=Q_C*1e6*(dn*mu_e+dp*mu_h)
    R=channel_length_m/(conductivity*channel_width_m*channel_thickness_m)
    current=voltage_V/R
    joule=voltage_V*current
    qdet=joule+absorbed_optical_W
    dPdT=joule*d_sigma/conductivity
    vnoise=sqrt(4*KB_J_K*T*R)
    inoise=sqrt(4*KB_J_K*T/R)
    assert all(isfinite(z) for z in (R,current,joule,qdet,dPdT,vnoise,inoise))
    return {'temperature_K':T,'composition_x':x,'bandgap_eV':eg,
        'idealized_Eg_cutoff_um':HC_EV_UM/eg,
        'intrinsic_carriers_cm3':ni,'net_ionized_acceptors_cm3':net_acceptors_cm3,
        'electron_carriers_cm3':n,'hole_carriers_cm3':p,
        'electron_fraction_of_conductivity':n*mu_e/(n*mu_e+p*mu_h),
        'hole_mobility_cm2_Vs':mu_h_cm2_Vs,
        'electron_mobility_cm2_Vs':mu_h_cm2_Vs*mu_e_over_h_ratio,
        'dark_conductivity_S_m':conductivity,'dark_resistance_ohm':R,
        'voltage_V':voltage_V,'detector_dark_current_A':current,
        'detector_bias_Joule_W':joule,
        'absorbed_optical_heat_W':absorbed_optical_W,
        'total_applied_detector_heat_W':qdet,
        'd_bias_Joule_dT_W_K_at_constant_V':dPdT,
        'johnson_current_A_sqrtHz':inoise,
        'johnson_voltage_V_sqrtHz':vnoise,
        'bias_field_V_cm':(voltage_V/channel_length_m)*.01,
        'channel_length_m':channel_length_m,
        'channel_width_m':channel_width_m,
        'channel_thickness_m':channel_thickness_m,
        'independent_resistance_calibration':False,
        'qualification':'Unmeasured geometry, mobility and fully-ionized dopant hypotheses; absolute R is NOT OEM/actual detector-calibrated; noise ONLY equilibrium Johnson, cutoff ONLY Eg threshold; no response/noise D* inference'}
