"""Three-stage reduced-order HgCdTe/TO-66 thermoelectric package model.

NOT an OEM material model. Nominal 28/12/4 stage allocation is inferred. Effective
Seebeck and thermal conductance multipliers are anchored to two different
2019 TEC Microsystems 3MC04-044-05 limiting conditions at Th=300 K.

Energy convention: Qc, Qh positive when heat is respectively extracted from
cold junction and rejected into the hot junction. The staged balance requires
Qc(bottom)=Qh(middle)+parasitic(bottom), and analogously for other stages.
"""
from dataclasses import dataclass, replace
from typing import Dict
import math
import numpy as np
from scipy.optimize import least_squares

SIGMA = 5.670374419e-8
GAS = {
    # approximate room-temperature reference values; NOT fit to measurements
    "N2": {"k":0.02583, "mfp":68e-9, "molar_mass":0.0280134, "mu":1.76e-5, "cp":1040.0},
    "Ar": {"k":0.01772, "mfp":68e-9, "molar_mass":0.039948, "mu":2.23e-5, "cp":520.0},
    "Kr": {"k":0.00943, "mfp":61e-9, "molar_mass":0.083798, "mu":2.48e-5, "cp":248.0},
}
R_GAS=8.314462618
# stage order: base/hot, intermediate, top/cold
COUPLES = np.array([28.,12.,4.])
LEG_LENGTH_M=np.array([1.07e-3, .82e-3, .64e-3]) # unverified CAD estimate
LEG_AREA_M2=(0.4e-3)**2
RAW_R=2*COUPLES*LEG_LENGTH_M*5.5e-6/LEG_AREA_M2
# Effective R distribution, nominal total AC resistance specified by OEM (2.89 ohms)
R_STAGE=RAW_R*(2.89/RAW_R.sum())
RAW_K=2*COUPLES*LEG_AREA_M2*1.45/LEG_LENGTH_M
# Parameters fit to: Qc_max(I=1A, zero overall dT)=0.5W; dT(I=1A,Q=0)=113K.
# TWO LIMITING POINTS ONLY; NOT validation of intermediate Q(T,I), stage T or gas.
ALPHA_MULTIPLIER=0.84819932
K_MULTIPLIER=1.48297574
ALPHA_STAGE=COUPLES*420e-6*ALPHA_MULTIPLIER
K_STAGE=RAW_K*K_MULTIPLIER

@dataclass(frozen=True)
class Scenario:
    """All input quantities explicit; SI unless name ends in _mm/_mm2."""
    ambient_k: float=300.0
    current_a: float=0.65
    hot_to_ambient_k_per_w: float=2.0
    gas: str="Ar"                     # N2, Ar, Kr; or "mixture" with mole fractions
    gas_mole_fractions: tuple|None=None # N2, Ar, Kr; when None use gas name
    gas_pressure_pa: float=101325.0
    gas_gap_mm: float=3.0
    gas_geometry_factor: float=1.0 # effective area/gap multiplier, UNKNOWN
    gas_accommodation_factor: float=2.0 # free-molecular correction, UNKNOWN
    detector_resistance_ohm: float=100.0
    detector_bias_v: float=0.5
    detector_optical_absorbed_w: float=0.0001
    thermistor_dissipation_w: float=0.00001
    wire_diameter_um: float=18.0
    bond_wire_length_mm: float=7.0
    bond_wire_count: int=4
    wire_conductivity_w_mk: float=315.0
    cap_emissivity: float=0.70
    surface_emissivity: float=0.50
    cap_view_factor: float=0.70
    aperture_area_mm2: float=0.0
    aperture_emissivity: float=0.90
    aperture_temperature_k: float=300.0
    aperture_view_factor: float=0.8
    cold_stage_area_mm2: float=2.4*2.4
    middle_exposed_area_mm2: float=3.25**2-2.4**2
    lower_exposed_area_mm2: float=4.55**2-3.25**2
    stage_surface_area_factor: float=2.0 # sidewalls + top/undersides effective
    # optional auxiliary parasitic heat loads are assigned hot-to-cold stage order
    extra_load_stage_w: tuple=(0.0,0.0,0.0)

    def validate(self):
        if self.ambient_k<=0 or self.aperture_temperature_k<=0: raise ValueError('temperature must be positive K')
        if not (0<=self.current_a<=1.1): raise ValueError('current must be within 0..1.1 A exploratory range')
        if self.hot_to_ambient_k_per_w<0 or self.gas_pressure_pa<0: raise ValueError('negative pressure or resistance')
        if self.gas_gap_mm<=0 or self.detector_resistance_ohm<=0 or self.bond_wire_length_mm<=0: raise ValueError('nonpositive dimension/resistance')
        if self.gas not in ("N2","Ar","Kr","mixture"):raise ValueError("gas must be N2, Ar, Kr or mixture")
        if self.gas_mole_fractions is not None and (len(self.gas_mole_fractions)!=3 or any(x<0 for x in self.gas_mole_fractions) or abs(sum(self.gas_mole_fractions)-1)>1e-6): raise ValueError('gas fractions must be N2/Ar/Kr and sum to one')
        if self.gas=="mixture" and self.gas_mole_fractions is None:raise ValueError("mixture needs mole fractions")
        for name in ['cap_emissivity','surface_emissivity','cap_view_factor','aperture_emissivity','aperture_view_factor']:
            if not 0<=getattr(self,name)<=1: raise ValueError(name+' outside 0..1')
        if self.aperture_area_mm2<0 or self.gas_geometry_factor<=0: raise ValueError('negative aperture or geometry factor')
        if any(x<0 for x in self.extra_load_stage_w): raise ValueError('negative added load')
        return self

def _fractions(s:Scenario):
    return s.gas_mole_fractions if s.gas_mole_fractions is not None else tuple(float(s.gas==x) for x in ("N2","Ar","Kr"))

def gas_properties(fractions):
    x=np.array(fractions, dtype=float)
    # Linear mole-fraction interpolation is EXPLORATORY, not a validated mixture law.
    return {prop:float(sum(x[i]*GAS[gas][prop] for i,gas in enumerate(('N2','Ar','Kr'))))
            for prop in ('k','mfp','molar_mass','mu','cp')}

def gas_conductivity(s:Scenario, temperature_k:float=280.0):
    """Effective gas k(T,p) in W/(m K), including approximate rarefaction."""
    s.validate()
    if s.gas_pressure_pa==0: return 0.0
    p=gas_properties(_fractions(s))
    k=p['k']*(temperature_k/300.0)**0.75
    mfp=p['mfp']*(temperature_k/300.0)*(101325.0/s.gas_pressure_pa)
    kn=mfp/(s.gas_gap_mm*1e-3)
    return k/(1+s.gas_accommodation_factor*kn)

def rayleigh_number(s:Scenario, t_hot, t_cold):
    """Indicative Rayleigh for a sealed gap. Nu correlation is NOT a CFD result."""
    if s.gas_pressure_pa<=0: return 0.
    props=gas_properties(_fractions(s))
    tm=0.5*(t_hot+t_cold)
    rho=s.gas_pressure_pa*props['molar_mass']/(R_GAS*tm)
    nu=props['mu']/rho
    alpha=gas_conductivity(s,tm)/(rho*props['cp'])
    if alpha<=0: return 0.
    return 9.80665*abs(t_hot-t_cold)*(s.gas_gap_mm*1e-3)**3/(tm*nu*alpha)

def stage_transport(i, current_a, t_cold_k, t_hot_k):
    """Return Qc, Qh, voltage, Seebeck alpha, Joule and back-conduction (SI)."""
    a=float(ALPHA_STAGE[i]); r=float(R_STAGE[i]); k=float(K_STAGE[i]); I=current_a
    conduction=k*(t_hot_k-t_cold_k)
    q_c=a*I*t_cold_k-0.5*I*I*r-conduction
    q_h=a*I*t_hot_k+0.5*I*I*r-conduction
    voltage=I*r+a*(t_hot_k-t_cold_k)
    return {"qc_w":q_c,"qh_w":q_h,"voltage_v":voltage,"alpha_v_per_k":a,
            "resistance_ohm":r,"thermal_conductance_w_per_k":k,
            "joule_w":I*I*r,"conduction_w":conduction}

def heat_breakdown(s:Scenario, stage_k, hot_k):
    """Per-node parasitics, bottom/middle/top arrays, each in W; positive heat in."""
    s.validate()
    temperatures=np.asarray(stage_k,dtype=float)
    area=np.array([s.lower_exposed_area_mm2,s.middle_exposed_area_mm2,s.cold_stage_area_mm2])*1e-6*s.stage_surface_area_factor
    # sealed miniature gaps: mainly conduction. Above Ra=1708, heuristic Nu only.
    gm=np.array([gas_conductivity(s,0.5*(hot_k+t)) for t in temperatures])
    ra=np.array([rayleigh_number(s,hot_k,t) for t in temperatures])
    nu=1+0.12*np.maximum(ra/1708.-1.,0.)**(1/3)
    gas=gm*area/(s.gas_gap_mm*1e-3)*(hot_k-temperatures)*nu*s.gas_geometry_factor
    # Radiation view factor includes effective epsilon between cap and cold surfaces
    eps_eff=1/(1/s.surface_emissivity +1/s.cap_emissivity -1) if s.surface_emissivity*s.cap_emissivity else 0
    rad=s.cap_view_factor*eps_eff*SIGMA*area*(hot_k**4-temperatures**4)
    wires=np.zeros(3)
    wires[2]=s.bond_wire_count*s.wire_conductivity_w_mk*math.pi*(s.wire_diameter_um*1e-6/2)**2/(s.bond_wire_length_mm*1e-3)*(hot_k-temperatures[2])
    detector=np.zeros(3)
    detector[2]=s.detector_bias_v**2/s.detector_resistance_ohm+s.detector_optical_absorbed_w+s.thermistor_dissipation_w
    # Aperture physically introduces a new warm radiating area/view to the cold stage.
    # It need not increase load if an aperture shields a larger preexisting hot area;
    # this calculation only models ADDING an illuminated warm baffle.
    aperture=np.zeros(3)
    aperture[2]=s.aperture_view_factor*s.aperture_emissivity*s.surface_emissivity*SIGMA*(s.aperture_area_mm2*1e-6)*(s.aperture_temperature_k**4-temperatures[2]**4)
    extra=np.asarray(s.extra_load_stage_w)
    total=gas+rad+wires+detector+aperture+extra
    return {"gas_w":gas,"radiation_w":rad,"bond_wires_w":wires,"detector_and_thermistor_w":detector,"aperture_w":aperture,"other_w":extra,"total_w":total,"rayleigh":ra,"nusselt":nu}

def solve(s:Scenario):
    """Solve 4-node nonlinear thermal balance (stage order: hot -> cold).

    Uses bounded least-squares and checks the heat-balance residual explicitly.
    Raises RuntimeError for infeasible operating points; do not trust extrapolation.
    """
    s.validate()
    def residual(x):
        t1,t2,t3,th=x
        loads=heat_breakdown(s,[t1,t2,t3],th)['total_w']
        st=[stage_transport(0,s.current_a,t1,th),stage_transport(1,s.current_a,t2,t1),stage_transport(2,s.current_a,t3,t2)]
        return np.array([st[0]['qc_w']-st[1]['qh_w']-loads[0],st[1]['qc_w']-st[2]['qh_w']-loads[1],st[2]['qc_w']-loads[2],(th-s.ambient_k)/max(s.hot_to_ambient_k_per_w,1e-12)-st[0]['qh_w'] if s.hot_to_ambient_k_per_w>0 else th-s.ambient_k])
    init=np.array([s.ambient_k-25,s.ambient_k-48,s.ambient_k-70,s.ambient_k+3],float)
    if s.current_a<0.05: init[:3]=s.ambient_k
    if s.hot_to_ambient_k_per_w==0:init[3]=s.ambient_k
    init=np.clip(init,121,599)
    fit=least_squares(residual,init,bounds=(np.full(4,120.),np.full(4,600.)),xtol=1e-11,gtol=1e-11,ftol=1e-11,max_nfev=200)
    t1,t2,t3,th=fit.x
    st=[stage_transport(0,s.current_a,t1,th),stage_transport(1,s.current_a,t2,t1),stage_transport(2,s.current_a,t3,t2)]
    loads=heat_breakdown(s,[t1,t2,t3],th)
    absolute_residual=np.max(np.abs(residual(fit.x)[:3]))
    if not fit.success or absolute_residual>1e-6 or (s.hot_to_ambient_k_per_w==0 and abs(th-s.ambient_k)>1e-6):
        raise RuntimeError(f'infeasible or nonconverged thermal state; max residual={absolute_residual:.3g} W')
    volts=sum(x['voltage_v'] for x in st)
    return {"ambient_k":s.ambient_k,"hot_k":float(th),"stage_k":[float(t1),float(t2),float(t3)],
            "stage_c":[float(v-273.15) for v in [t1,t2,t3]],
            "detector_k":float(t3),"detector_c":float(t3-273.15),"delta_t_k":float(th-t3),
            "current_a":s.current_a,"voltage_v":float(volts),"electrical_power_w":float(volts*s.current_a),
            "stage_transport":st,"loads_w":{k:[float(x) for x in v] for k,v in loads.items()},
            "energy_balance_max_w":float(absolute_residual),
            "nominal_provenance":"Two-point OEM envelope anchored; other thermal/electrical parameters inferred; not experimentally validated"}

def calibration_check():
    """Compute two reference corner points, *not* independent validation."""
    ref=Scenario(current_a=1.,gas_pressure_pa=0.,hot_to_ambient_k_per_w=0.,
        detector_bias_v=0.,detector_optical_absorbed_w=0.,thermistor_dissipation_w=0.,
        bond_wire_count=0,cap_view_factor=0.)
    unloaded=solve(ref)
    # impose Tc=Th=300, solve two intermediate stage energy balances at I=1A
    def two_stage(x):
        t1,t2=x
        st=[stage_transport(0,1.,t1,300),stage_transport(1,1.,t2,t1),stage_transport(2,1.,300,t2)]
        return [st[0]['qc_w']-st[1]['qh_w'],st[1]['qc_w']-st[2]['qh_w']]
    f=least_squares(two_stage,[310,305],bounds=([120,120],[600,600]),xtol=1e-12,gtol=1e-12,ftol=1e-12)
    qcap=stage_transport(2,1.,300,float(f.x[1]))['qc_w']
    return {"delta_t0_k":unloaded['delta_t_k'],"qmax_deltat0_w":qcap,"R_ac_nominal_ohm":float(R_STAGE.sum()),
            "voltage_no_load_v":unloaded['voltage_v'],"condition":"I=1A, Th=300K, vacuum, no parasitics; limits from distinct experiments"}
