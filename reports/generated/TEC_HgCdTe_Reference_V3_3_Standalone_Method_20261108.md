# Reference 3-stage TEC-cooled HgCdTe device: independently reproducible physical and numerical method

**Standalone scientific reproduction monograph | Model revision V3.3 | 8 November 2026 (UTC)**

**Scope and claim.** This document completely states a realistic, engineering-plausible *synthetic*
three-stage thermoelectric HgCdTe detector and package calculation. It does **not** represent a
specific fabricated TEC Microsystems or VIGO product. All dimensions and laws are independently
implementable without project history. The idealized pad geometry, measured-versus-assumed
coefficients, and stage/circuit topology are explicitly identified. The model evaluates a complete
0.400 A current-driven electrothermal operating point and includes nonlinear temperature-dependent
P/N transport, source-geometry ceramic 3D heat conduction, electrical solder Joule heat, detector
load, hot mounting, Cu/Au links, and cavity gas/radiation loads.

**Version distinction.** A separate 38-page historical engineering assessment designated
“Revision 3” primarily analyzed an earlier 216-solid 28/12/4 reduced configuration and a separate
3D solid-only 0.1 A case. This document instead describes the current 430-domain, 29/11/4
reference geometry and its coupled V3.3 working calculation. Never exchange numerical results
between those differing geometries or boundary conditions.

## 1. Coordinate system, actual reference geometry and electrical topology

Coordinates use **millimetres** for mechanical geometry and **SI units** in equations. Set
the package header normal as z. The four ceramic footprints and thicknesses are:

| Ceramic | Side (mm) | Thickness (mm) | Top contact/thermal position |
|:--|--:|--:|:--|
| C0 | 6.4 | 0.500 | C0 upper assembly pad |
| C1 | 5.2 | 0.500 | C1 upper assembly pad |
| C2 | 3.8 | 0.500 | C2 upper assembly pad |
| C3 | 2.4 | 0.500 | C3 upper assembly pad |

Source-composite design has **430 derived solid domains**, **2,440 native CAD face regions**,
and **88 thermoelectric legs** connected in series, comprising **29 P/N couples in stage 0**,
**11 in stage 1**, and **4 in stage 2**. The P and N legs are each 0.400 × 0.400 mm cross
section and **0.500 mm length**, so individual A = 1.600×10⁻⁷ m² and L = 5.000×10⁻⁴ m.
For electrical circuit orientation, individual current density magnitude is
J = 0.400 A / A = 2.500×10⁶ A m⁻², positive for the N leg and negative for the P leg
under the source transport convention. The leg ordering, x/y centroids and polarities are
tabulated in Appendix B, so the chosen virtual geometry can be regenerated independently.

There are two SnSb solder bodies per thermoelectric leg, **176 solder joints**, with **352**
distinct source leg/solder and solder/metallization electrical interfaces. Every solder
body has nominal thickness 35 µm and cross-sectional area 0.16 mm². Four original
ceramic FEM regions use **11,791 linear four-node tetrahedra**; retained initial one-mesh
region counts are 4,936 / 4,085 / 1,986 / 784 TET4. The finite-element mesh is a single
saved discretization, not a demonstrated grid-converged thermal solution. Appendix C gives
original ceramic-pad positions, areas and the final distributed loads.

A 1.0×1.0 mm² die is coupled to C3 by an assumed **20 µm EP29LPSP adhesive layer**,
k = 1.0 W m⁻¹ K⁻¹; R_die→carrier = thickness/(kA) = **20.000 K W⁻¹**.
No HgCdTe photocarrier PDE or optical transmission/absorption model is included.

## 2. Constitutive-law evidence and explicit model assumptions

Leg transport uses the published **J. Zhang et al., Chinese Physics Letters 42, 056304
(2025), DOI: 10.1088/0256-307X/42/5/056304**, figure-digitized data for distinct
hot-extruded P-HE and N-HE-1 specimens. These are engineering analogs, not
manufacturer-identified grades in this virtual design. Table 2A provides the entire
84-value, six-property input used. Numeric units:
Seebeck **S** = µV K⁻¹, resistivity **rho** = µΩ m, and thermal conductivity
**k** = W m⁻¹ K⁻¹. Multiply S and rho columns by 10⁻⁶ to obtain SI values.

| T (K) | S_P (µV/K) | rho_P (µΩ m) | k_P (W/mK) | S_N (µV/K) | rho_N (µΩ m) | k_N (W/mK) |
|--:|--:|--:|--:|--:|--:|--:|
| 40 | 31.477086 | 1.226120 | 2.776424 | -39.762194 | 0.837035 | 3.928920 |
| 60 | 44.991486 | 1.550968 | 2.488935 | -53.616397 | 1.156199 | 3.246955 |
| 80 | 60.679339 | 1.955036 | 2.260290 | -67.469437 | 1.522950 | 2.816874 |
| 100 | 77.996604 | 2.446265 | 2.072406 | -81.936140 | 1.920207 | 2.536709 |
| 120 | 96.944423 | 3.004830 | 1.909416 | -95.992742 | 2.354830 | 2.310364 |
| 140 | 115.755946 | 3.567364 | 1.764537 | -109.847998 | 2.820018 | 2.129254 |
| 160 | 133.684757 | 4.343818 | 1.630978 | -122.547039 | 3.319204 | 1.973635 |
| 180 | 150.458980 | 5.175731 | 1.515526 | -134.499967 | 3.835302 | 1.851971 |
| 200 | 166.078757 | 6.067058 | 1.415926 | -145.840430 | 4.371811 | 1.744414 |
| 220 | 179.321421 | 7.073284 | 1.332165 | -156.231255 | 4.932113 | 1.653884 |
| 240 | 190.594863 | 8.138932 | 1.257469 | -165.737958 | 5.570441 | 1.574639 |
| 260 | 199.219885 | 9.351143 | 1.194083 | -174.568277 | 6.232621 | 1.506729 |
| 280 | 205.739245 | 10.694094 | 1.137484 | -182.445326 | 6.884545 | 1.447332 |
| 300 | 212.462550 | 12.080611 | 1.099006 | -189.575244 | 7.543277 | 1.399227 |

Interpolate linearly between knots. The published range is **40–300 K**. In the modeled
range **300–390 K**, the code uses a *declared unmeasured continuation*
f(T) = f(300 K) + 0.25 (T−300 K) [f(300 K)−f(280 K)] / 20 K
for f ∈ {S,rho,k}. All property evaluations must remain within **180–390 K**.
Check positive rho and k and polarity S_P>0, S_N<0. Source-figure reading
errors are not material characterization uncertainty. For V3.2, all 58 stage-0 legs
required at least partial source-law extension above 300 K.

Ceramics: homogeneous hypothetical alumina k_c = **30 W m⁻¹ K⁻¹**, constant
from ~210 to 305 K; not an OEM measured k(T). All exposed ceramic faces
not explicitly represented by load tags are insulated in the 3D conduction submodel.

## 3. Nonlinear one-dimensional thermoelectric conservation equations

For one leg, with z directed from hot to cold, current density J signed by polarity,
temperature T(z), thermopower S(T), bulk electrical resistivity rho(T) and
Fourier thermal conductivity k(T), use the conservative formulation:

> q(z) = S(T) T J − k(T) dT/dz,
> d q/dz = J [rho(T) J + S(T) dT/dz],
> dV/dz = rho(T) J + S(T) dT/dz.

Using N=32 intervals, unknown T_1 … T_31, fixed end temperatures
T_0=T_hot, T_32=T_cold, and midpoint constitutive evaluations, define
q_i = S(T_mid) T_mid J − k(T_mid)(T_{i+1}−T_i)/Δz,
ΔV_i = J rho(T_mid) Δz + S(T_mid)(T_{i+1}−T_i).
The internal midpoint control-volume residual is
q_{i+1}−q_i − [J ΔV_{i+1}+J ΔV_i]/2 = 0.
Solve by damped Newton with a tridiagonal/banded Jacobian and positivity/domain checks.
At boundaries include half-control-volume electrical work in q_hot and q_cold.
Each leg must satisfy the integral conservation identity
**Q_hot − Q_cold − I V_leg = 0**, using sign-consistent circuit voltage.
The 29/11/4 stage heat and voltage are sums over the constituent P/N legs
rather than a single fitted effective Seebeck coefficient.

## 4. Electrical solder, Cu and Au wire paths

For each SnSb joint:
R_joint = rho_SnSb L_joint/A_joint + 2 r_c / A_joint.
Use **rho_SnSb = 1.7×10⁻⁷ Ω m** and **specific electrical contact
resistivity r_c = 1.0×10⁻¹¹ Ω m²**, hypothetical, not measured.
For 176 joints in series this yields R_solder=0.006545 Ω,
R_contact=0.022000 Ω, total added R=**0.028545 Ω**. At 0.400 A,
direct voltage=**11.418 mV**, Joule heating=**4.56720 mW**.
Place **25.950 µW** at each of 176 adjacent ceramic original metal pads;
the resulting ceramic0..3 electrical joint heat vector is
[1.50510,2.07600,0.77850,0.20760] mW.
The all-Joule-into-ceramic partition is a provisional engineering simplification.
It omits metal-net current crowding, finite interfacial thermal resistance and contact Peltier heat.

The two source Cu supply leads: radius 0.100 mm, lengths 3.451062 and
4.964887 mm, k=400 W/(m K), rho_e=1.72×10⁻⁸ Ωm,
G=[0.0036413051,0.0025310487] W/K,
R=[0.00188943245,0.00271824088] Ω. Model heat flow
G_Cu (T_ambient−T_hot) and partition the total Cu I²R equally
between room-temperature lead reservoir and hot ceramic.
The two Au detector bonds: radius 9 µm, length 9.679142 mm each,
k=315 W/(m K), G=8.28149215×10⁻⁶ W/K each. The Au electrical
response is NOT used to calculate detector signal or photocurrent.

## 5. Three-dimensional ceramic steady heat conduction

For each ceramic C_i solve **−∇·(k_c∇T)=0** over its 3D source volume
using continuous piecewise-linear tetrahedral FEM:

> K_ab = Σ_t ∫_Ωt (∇N_a)· k_c (∇N_b) dΩ.

Contact heat loads are Neumann terms b_a = Σ_f ∫_Af N_a q_f dA;
for constant q_f per triangular face this assigns q_f A_f /3 to
each of its three nodes. Native solder/metal pad heat is applied
on its specific 3D TRI3 source surface. The source thermal operator
is factorized once per ceramic; linear superposition updates the
nonuniform surface heat distribution as the coupled leg flux changes.
Temperature gauge is fixed by the lower pad area-mean temperature
for that ceramic; no arbitrary artificial heat is introduced.
Area-mean top minus bottom source temperatures couple to each
stage hot/cold transport temperature; local individual leg
temperatures are the proper native-pad mean, not all-leg averages.

For the present cavity prototype, the distributed physical gas and
radiation heat incident on each cold exposed ceramic is **mapped to
its upper native metal-pad basis in proportion to pad area**.
This is an explicit reduced-source approximation, not a fully
resolved bare-ceramic or gas-solid interface. A replica using
continuous exposed-face Neumann flux may differ at local nodes.

## 6. Cavity gas and gray radiation: declared approximate physical closure

The cavity cap/window reservoir, hot mounting ambience and external
lead reservoir are all held at **300.0 K**. The reference cold
enclosure uses krypton at **100 Pa**, 3.00 mm effective gas
gap, accommodation coefficient a=0.8, gas-area factor 1.0.
At 200/300/400 K, NIST-derived Kr dilute-gas k values are
[0.0064,0.0095,0.0122] W/(mK). Interpolate between tabulated
points; the calculation uses the existing Eucken approximation
μ = k/(cp+1.25 Rg), cp=γ Rg/(γ−1), γ=5/3, Rg=99.218 J/(kg K).
The mean free path λ = μ/p × sqrt(π Rg Tmean /2).
Thermal jump length δ = [(2−a)/a] [2γ/(γ+1)] λ/Pr, Pr=μcp/k.
For p>0 the effective heat-transfer conductance is
G_gas = k A_eff /(L_gap + 2δ); Q_gas = G_gas (300 K−T_cold).
At p=0, Q_gas is defined as **exactly zero**.
Mean temperatures below 200 K would invoke a separately flagged
k ∝ T^0.75 extension; the current case mean temperatures do not
cross that limit. No buoyant convection, pressure-driven flow,
CFD, molecular simulation, Xe mixture or free-convection model is claimed.

Effective cold-face areas from the source ceramic footprint differences
(C1−C2, C2−C3, C3−die, die) are
**[12.600,8.680,4.760,1.000] mm²**.
For gray diffuse opaque exchange against a 300 K reservoir use
Q_rad = F σ A_eff ε_eff (300⁴−T_cold⁴),
ε_eff = [1/ε_warm+1/ε_cold−1]⁻¹,
σ=5.670374419×10⁻⁸ W m⁻² K⁻⁴.
Use ceramic ε_cold=0.80, cap ε_warm=0.20,
cap view factor F=0.50 for three ceramic cold faces;
use window ε_warm=0.10 and window-to-die F=0.70 at the die.
This is a gray effective-view reservoir approximation, not the
14-surface radiosity and chord network discussed in the historical Rev3.
The cavity reservoir rejects the negative of the total gas plus radiation
heat supplied to cold-stage and die nodes; record this separately
to preserve thermodynamic energy accounting.

## 7. Full-device nonlinear coupling and boundary heat balances

Unknown temperatures are eight independent nodes:
(T0h,T0c,T1h,T1c,T2h,T2c,Tcarrier,Tdie).
The ceramic mean temperatures and local pad offsets are supplied
by the four 3D FEM fields. Let Qh_i and Qc_i be total nonlinear
P/N leg hot/cold heat for the three stages, Pj = 25.95 µW,
and E1,E2,E3,Edie denote the local gas+radiation heat loads.
The four conservative coupling equations are

> Qc_0 − Qh_1 − (58+22)Pj − E1 = 0,
> Qc_1 − Qh_2 − (22+8)Pj − E2 = 0,
> Qc_2 − Qattach − 8Pj − E3 = 0,
> Qattach − Pdie − QAu − Edie = 0.

Qattach = (Tdie−Tcarrier)/20 K W⁻¹, Pdie=0.002 W,
QAu = ΣG_Au(300−Tdie).
Source hot bath heat is Qbath=Qh_0+QCu+.5 I²R_Cu+58Pj,
QCu=ΣG_Cu(300−T0h).
C0 bottom mean is **300 K + Rext Qbath** with
Rext=**4.833386960805823 K/W** representing the assumed hot
header/TIM/radiator path EXCLUDING the first 3D ceramic.
Close the remaining four ceramic mean temperature-jump equations
using their latest 3D P1 heat solution. For stage 0 hot side,
T0h=300 K+Rext Qbath+ΔTceramic0.

The global steady electrical/thermal energy diagnostic is

> ε_E = I Vterminal + Pdie + QAu + QCu − 0.5 I²R_Cu
>       + E1+E2+E3+Edie − Qbath.

An accepted result has |ε_E| < 10⁻⁸ W and each stage and
source ceramic heat budget within its declared residual tolerance.

## 8. Solver algorithm that can be implemented without this source repository

1. Form source rectangular 29/11/4 P/N leg geometry, hot/cold
   solder joints, four ceramic slabs, Cu/Au thermal leads and
   1 mm² detector attach. Represent native pads using the
   appendix centroid/area table if a spatial reconstruction is desired.
2. Assemble each 3D ceramic linear-tetrahedron P1 conduction
   stiffness K_i and factor once. Establish mean-pad-to-pad
   temperature influence vectors for the desired heat-source faces.
3. Initialize the eight temperatures from the fully specified
   V3.2 enclosure-OFF reference values in Section 9.
4. Evaluate Qgas and Qrad at the latest cold ceramic and die
   temperatures, then solve each of 88 P/N nonlinear axial
   32-interval transport problems for its local hot/cold pad T.
5. Sum all leg Qhot/Qcold/V, add the 176 solder sources, Cu/Au
   paths, detector 2 mW and cavity heat, and solve the eight-node
   nonlinear balance problem with bounded least-squares.
6. Recompute all four 3D ceramic fields with the new nonuniform
   native pad Neumann heat sources and cavity loads. Repeat
   with outer under-relaxation 0.95 until maximum relative
   pad/plate temperature update is below **2×10⁻⁵ K**.
7. Reject any unphysical property, nonconverged stage, material
   domain violation, incorrect source face-energy sum or
   global residual above **10⁻⁸ W**. Keep all numerical
   failure cases visible; no inferred parameters are adjusted
   to force convergence in this single registered reference case.

The outer stopping tolerance is intentionally **coarse** as an
initial proof of coupled cavity physics. It is NOT a 20 µK
independent mesh-convergence bound or as-built detector accuracy.

## 9. Independently checkable operating-point outputs

**Case A** is the identical complete model with cavity gas and
radiation disabled (V3.2 source reference); **Case B** is the
nominal 100 Pa Kr / gray radiation case (V3.3). All other
dimensions, materials, current and external conditions are held fixed.

| Quantity | Enclosure OFF (A) | Gas+radiation ON (B) |
|---|---:|---:|
| I (A) | 0.4 | 0.4 |
| Detector T (K) | 209.9879814 | 210.625214 |
| Terminal V (V) | 1.524070832 | 1.522462416 |
| Terminal P (W) | 0.609628333 | 0.6089849664 |
| Sink heat Qbath (W) | 0.590322603 | 0.594043746 |
| Global energy residual (W) | 1.378857029e-10 | 8.867374612e-09 |
| Ceramic TET4 count | 11791 | 11791 |

**Case B local enclosure inputs (mW)**:

| Cold location | Gas input (mW) | Gray radiation input (mW) | Total (mW) |
|:--|--:|--:|--:|
| C1 exposed | 1.15900974 | 0.20874186 | 1.36775160 |
| C2 exposed | 1.44533340 | 0.23389193 | 1.67922534 |
| C3 exposed | 1.06469312 | 0.15769702 | 1.22239014 |
| Detector window/die | 0.22351680 | 0.02374558 | 0.24726238 |
| **Total** | **3.89255306** | **0.62407640** | **4.51662946** |

Eight coupled temperature nodes in case B:

| Node | T (K) |
|:--|--:|
| stage0_hot | 303.65655327 |
| stage0_cold | 265.90328835 |
| stage1_hot | 266.34286716 |
| stage1_cold | 236.00258920 |
| stage2_hot | 236.15715707 |
| stage2_cold | 210.52764807 |
| carrier | 210.55066244 |
| die | 210.62521395 |

**V3.3 versus V3.2 detector temperature:** +0.63723256 K;
**outer iterations:** 5; maximum final spatial update:
1.6535e-05 K.

**Status:** full 88-leg and four original ceramic P1 field coupled-device
numerical calculation, not a fully spatial 430-domain electrical
transport + rarefied-gas CFD + gray spectral radiation solver.

## 10. Verification and limitations before physical claims

- Full device energy identity: 8.8674e-09 W
- Maximum interstage/detector nodal mismatch: 4.9061e-09 W
- Maximum ceramic native-pad net energy: 5.5025e-15 W
- Maximum individual P/N leg energy residual: 1.2364e-13 W
- Final spatial temperature update: 1.6535e-05 K
- The historical original P1 whole-assembly electrical Gate B remained FAIL/STOP;
  the first source P/N pair raw gradient-current test failed 8/8,
  prospective P2 stopped, and the original full 430-domain coupled
  3D C/D thermal qualification has NOT RUN.
- No OEM grade, installed cooler assembly or detector temperature
  measurement is claimed; neither numerical residual nor plotted
  precision is a manufacturing accuracy bound.
- Not modeled: true 3D P/N current transport, temperature-dependent
  ceramic grade, solder interfacial thermopower, cavity gas CFD,
  all-surface radiosity, optical window transmission,
  semiconductor carrier transport, thermistor or transient control.

## Appendix B. Complete original-source 88-leg placement for independent replication

Leg area is 0.1600 mm², length 0.5000 mm; coordinates are CAD-body
bounding-box centre x/y in mm. Stage0 has 58 legs, stage1 22, stage2 8.

| Series index | Stage | P/N | X-centre (mm) | Y-centre (mm) |
|--:|--:|:--:|--:|--:|
| 0 | 0 | N | -2.030000 | -2.030000 |
| 1 | 0 | P | -1.450000 | -2.030000 |
| 2 | 0 | N | -0.870000 | -2.030000 |
| 3 | 0 | P | -0.290000 | -2.030000 |
| 4 | 0 | N | 0.290000 | -2.030000 |
| 5 | 0 | P | 0.870000 | -2.030000 |
| 6 | 0 | N | 1.450000 | -2.030000 |
| 7 | 0 | P | 2.030000 | -2.030000 |
| 8 | 0 | N | 2.030000 | -1.450000 |
| 9 | 0 | P | 1.450000 | -1.450000 |
| 10 | 0 | N | 0.870000 | -1.450000 |
| 11 | 0 | P | 0.290000 | -1.450000 |
| 12 | 0 | N | -0.290000 | -1.450000 |
| 13 | 0 | P | -0.870000 | -1.450000 |
| 14 | 0 | N | -1.450000 | -1.450000 |
| 15 | 0 | P | -2.030000 | -1.450000 |
| 16 | 0 | N | -2.030000 | -0.870000 |
| 17 | 0 | P | -1.450000 | -0.870000 |
| 18 | 0 | N | -0.870000 | -0.870000 |
| 19 | 0 | P | -0.290000 | -0.870000 |
| 20 | 0 | N | 0.290000 | -0.870000 |
| 21 | 0 | P | 0.870000 | -0.870000 |
| 22 | 0 | N | 1.450000 | -0.870000 |
| 23 | 0 | P | 2.030000 | -0.870000 |
| 24 | 0 | N | 2.030000 | -0.290000 |
| 25 | 0 | P | 1.450000 | -0.290000 |
| 26 | 0 | N | 0.870000 | -0.290000 |
| 27 | 0 | P | 0.290000 | -0.290000 |
| 28 | 0 | N | -0.290000 | -0.290000 |
| 29 | 0 | P | -0.870000 | -0.290000 |
| 30 | 0 | N | -1.450000 | -0.290000 |
| 31 | 0 | P | -2.030000 | -0.290000 |
| 32 | 0 | N | -2.030000 | 0.290000 |
| 33 | 0 | P | -1.450000 | 0.290000 |
| 34 | 0 | N | -0.870000 | 0.290000 |
| 35 | 0 | P | -0.290000 | 0.290000 |
| 36 | 0 | N | 0.290000 | 0.290000 |
| 37 | 0 | P | 0.870000 | 0.290000 |
| 38 | 0 | N | 1.450000 | 0.290000 |
| 39 | 0 | P | 2.030000 | 0.290000 |
| 40 | 0 | N | 2.030000 | 0.870000 |
| 41 | 0 | P | 1.450000 | 0.870000 |
| 42 | 0 | N | 0.870000 | 0.870000 |
| 43 | 0 | P | 0.290000 | 0.870000 |
| 44 | 0 | N | -0.290000 | 0.870000 |
| 45 | 0 | P | -0.870000 | 0.870000 |
| 46 | 0 | N | -1.450000 | 0.870000 |
| 47 | 0 | P | -2.030000 | 0.870000 |
| 48 | 0 | N | -2.030000 | 1.450000 |
| 49 | 0 | P | -1.450000 | 1.450000 |
| 50 | 0 | N | -0.870000 | 1.450000 |
| 51 | 0 | P | -0.290000 | 1.450000 |
| 52 | 0 | N | 0.290000 | 1.450000 |
| 53 | 0 | P | 0.870000 | 1.450000 |
| 54 | 0 | N | 1.450000 | 1.450000 |
| 55 | 0 | P | 2.030000 | 1.450000 |
| 56 | 0 | N | 2.030000 | 2.030000 |
| 57 | 0 | P | 1.450000 | 2.030000 |
| 58 | 1 | N | 1.450000 | 0.870000 |
| 59 | 1 | P | 0.870000 | 0.870000 |
| 60 | 1 | N | 0.290000 | 0.870000 |
| 61 | 1 | P | -0.290000 | 0.870000 |
| 62 | 1 | N | -0.870000 | 0.870000 |
| 63 | 1 | P | -1.450000 | 0.870000 |
| 64 | 1 | N | -1.450000 | 0.290000 |
| 65 | 1 | P | -0.870000 | 0.290000 |
| 66 | 1 | N | -0.290000 | 0.290000 |
| 67 | 1 | P | 0.290000 | 0.290000 |
| 68 | 1 | N | 0.870000 | 0.290000 |
| 69 | 1 | P | 1.450000 | 0.290000 |
| 70 | 1 | N | 1.450000 | -0.290000 |
| 71 | 1 | P | 0.870000 | -0.290000 |
| 72 | 1 | N | 0.290000 | -0.290000 |
| 73 | 1 | P | -0.290000 | -0.290000 |
| 74 | 1 | N | -0.870000 | -0.290000 |
| 75 | 1 | P | -1.450000 | -0.290000 |
| 76 | 1 | N | -1.450000 | -0.870000 |
| 77 | 1 | P | -0.870000 | -0.870000 |
| 78 | 1 | N | -0.290000 | -0.870000 |
| 79 | 1 | P | 0.290000 | -0.870000 |
| 80 | 2 | N | 0.870000 | -0.290000 |
| 81 | 2 | P | 0.290000 | -0.290000 |
| 82 | 2 | N | -0.290000 | -0.290000 |
| 83 | 2 | P | -0.870000 | -0.290000 |
| 84 | 2 | N | -0.870000 | 0.290000 |
| 85 | 2 | P | -0.290000 | 0.290000 |
| 86 | 2 | N | 0.290000 | 0.290000 |
| 87 | 2 | P | 0.870000 | 0.290000 |

## Appendix C. Native ceramic-pad geometry and solved surface heat flux

The following per-face heat source table (W) includes the true
individual leg heat and solder/contact Joule, plus the separately
declared area-weighted gas/radiation surrogate and hot Cu/sink/die
terms. Face centroids and exact CAD areas are given for an
independent geometrical placement; a matching custom mesh will
not reproduce exact local gradients without the complete original
face boundary polygon outlines.

| Ceramic | Face ID | X (mm) | Y (mm) | Z (mm) | CAD area (mm²) | Net heat into ceramic (W) |
|--:|--:|--:|--:|--:|--:|
| 0 | 6 | 0.000000 | 0.000000 | 1.584250 | 37.21000000 | -5.9404375264e-01 |
| 0 | 8 | -2.030000 | -2.415000 | 2.084250 | 0.58100000 | +6.9212449542e-03 |
| 0 | 9 | -1.160000 | -2.030000 | 2.084250 | 0.54000000 | +2.1001118011e-02 |
| 0 | 10 | -0.000000 | -2.030000 | 2.084250 | 0.54000000 | +2.0799385661e-02 |
| 0 | 11 | -2.030000 | -1.160000 | 2.084250 | 0.54000000 | +2.1333430585e-02 |
| 0 | 12 | -1.160000 | -1.450000 | 2.084250 | 0.54000000 | +2.0925106301e-02 |
| 0 | 13 | -1.160000 | -0.870000 | 2.084250 | 0.54000000 | +2.1098181465e-02 |
| 0 | 14 | -2.030000 | -0.000000 | 2.084250 | 0.54000000 | +2.1661444954e-02 |
| 0 | 15 | -1.160000 | -0.290000 | 2.084250 | 0.54000000 | +2.1280527762e-02 |
| 0 | 16 | -0.000000 | -1.450000 | 2.084250 | 0.54000000 | +2.0726535211e-02 |
| 0 | 17 | 0.000000 | -0.870000 | 2.084250 | 0.54000000 | +2.0872339885e-02 |
| 0 | 18 | -0.000000 | -0.290000 | 2.084250 | 0.54000000 | +2.1135046258e-02 |
| 0 | 19 | 1.160000 | -2.030000 | 2.084250 | 0.54000000 | +2.0762274895e-02 |
| 0 | 20 | 2.030000 | -1.740000 | 2.084250 | 0.54000000 | +2.0894962316e-02 |
| 0 | 21 | 1.160000 | -1.450000 | 2.084250 | 0.54000000 | +2.0664089207e-02 |
| 0 | 22 | 1.160000 | -0.870000 | 2.084250 | 0.54000000 | +2.0730610371e-02 |
| 0 | 23 | 1.160000 | -0.290000 | 2.084250 | 0.54000000 | +2.0987932670e-02 |
| 0 | 24 | 2.030000 | -0.580000 | 2.084250 | 0.54000000 | +2.1025501033e-02 |
| 0 | 25 | -1.160000 | 0.290000 | 2.084250 | 0.54000000 | +2.1501510390e-02 |
| 0 | 26 | -2.030000 | 1.160000 | 2.084250 | 0.54000000 | +2.2056807823e-02 |
| 0 | 27 | -1.160000 | 0.870000 | 2.084250 | 0.54000000 | +2.1665224003e-02 |
| 0 | 28 | -1.160000 | 1.450000 | 2.084250 | 0.54000000 | +2.1972015528e-02 |
| 0 | 29 | 0.000000 | 0.290000 | 2.084250 | 0.54000000 | +2.1329922044e-02 |
| 0 | 30 | -0.000000 | 0.870000 | 2.084250 | 0.54000000 | +2.1513476612e-02 |
| 0 | 31 | 0.000000 | 1.450000 | 2.084250 | 0.54000000 | +2.1762448001e-02 |
| 0 | 32 | 1.160000 | 0.290000 | 2.084250 | 0.54000000 | +2.1132384800e-02 |
| 0 | 33 | 2.030000 | 0.580000 | 2.084250 | 0.54000000 | +2.1315494607e-02 |
| 0 | 34 | 1.160000 | 0.870000 | 2.084250 | 0.54000000 | +2.1316483722e-02 |
| 0 | 35 | 1.160000 | 1.450000 | 2.084250 | 0.54000000 | +2.1497446937e-02 |
| 0 | 36 | 0.088570 | 2.858995 | 2.084250 | 0.67225000 | -2.2200926469e-02 |
| 0 | 37 | 2.030000 | 1.740000 | 2.084250 | 0.54000000 | +2.1652376653e-02 |
| 0 | 38 | 1.450000 | 2.379622 | 2.084250 | 0.51850000 | +1.4709356454e-02 |
| 1 | 44 | -1.740000 | -2.030000 | 2.684250 | 0.54000000 | -6.1717204457e-03 |
| 1 | 45 | -0.580000 | -2.030000 | 2.684250 | 0.54000000 | -5.7923394592e-03 |
| 1 | 46 | 0.580000 | -2.030000 | 2.684250 | 0.54000000 | -5.6313481447e-03 |
| 1 | 47 | -1.740000 | -1.450000 | 2.684250 | 0.54000000 | -5.8945158835e-03 |
| 1 | 48 | -1.740000 | -0.870000 | 2.684250 | 0.54000000 | -6.1272498337e-03 |
| 1 | 49 | -0.580000 | -1.450000 | 2.684250 | 0.54000000 | -5.6677985879e-03 |
| 1 | 50 | -0.580000 | -0.870000 | 2.684250 | 0.54000000 | -5.9073535857e-03 |
| 1 | 51 | -1.740000 | -0.290000 | 2.684250 | 0.54000000 | -6.2861601984e-03 |
| 1 | 52 | -1.740000 | 0.290000 | 2.684250 | 0.54000000 | -6.4929448577e-03 |
| 1 | 53 | -0.580000 | -0.290000 | 2.684250 | 0.54000000 | -6.1441766581e-03 |
| 1 | 54 | 0.580000 | -1.450000 | 2.684250 | 0.54000000 | -5.4949366062e-03 |
| 1 | 55 | 0.580000 | -0.870000 | 2.684250 | 0.54000000 | -5.6165637076e-03 |
| 1 | 56 | 0.580000 | -0.290000 | 2.684250 | 0.54000000 | -5.9284010470e-03 |
| 1 | 57 | 1.740000 | -2.030000 | 2.684250 | 0.54000000 | -5.5964450493e-03 |
| 1 | 58 | 1.740000 | -1.450000 | 2.684250 | 0.54000000 | -5.5750930796e-03 |
| 1 | 59 | 1.740000 | -0.870000 | 2.684250 | 0.54000000 | -5.5316729855e-03 |
| 1 | 60 | 1.740000 | -0.290000 | 2.684250 | 0.54000000 | -5.7862099653e-03 |
| 1 | 61 | -0.580000 | 0.290000 | 2.684250 | 0.54000000 | -6.4257386885e-03 |
| 1 | 62 | -1.740000 | 0.870000 | 2.684250 | 0.54000000 | -6.8576261766e-03 |
| 1 | 63 | -1.740000 | 1.450000 | 2.684250 | 0.54000000 | -7.0890067759e-03 |
| 1 | 64 | -0.580000 | 0.870000 | 2.684250 | 0.54000000 | -6.6249732312e-03 |
| 1 | 65 | -0.580000 | 1.450000 | 2.684250 | 0.54000000 | -7.0137372522e-03 |
| 1 | 66 | 0.580000 | 0.290000 | 2.684250 | 0.54000000 | -6.1746390641e-03 |
| 1 | 67 | 0.580000 | 0.870000 | 2.684250 | 0.54000000 | -6.3948651910e-03 |
| 1 | 68 | 0.580000 | 1.450000 | 2.684250 | 0.54000000 | -6.7126784447e-03 |
| 1 | 69 | 1.740000 | 0.290000 | 2.684250 | 0.54000000 | -6.0016216656e-03 |
| 1 | 70 | 1.740000 | 0.870000 | 2.684250 | 0.54000000 | -6.1198269805e-03 |
| 1 | 71 | 1.740000 | 1.450000 | 2.684250 | 0.54000000 | -6.5247521871e-03 |
| 1 | 72 | 1.740000 | 2.030000 | 2.684250 | 0.54000000 | -6.8707555753e-03 |
| 1 | 74 | 0.870000 | 2.300000 | 3.184250 | 0.12000000 | +2.3941388903e-05 |
| 1 | 75 | 1.450000 | 1.470862 | 3.184250 | 0.67900000 | +5.1504788556e-03 |
| 1 | 76 | -1.450000 | -0.580000 | 3.184250 | 0.54000000 | +1.6210670281e-02 |
| 1 | 77 | -0.580000 | -0.870000 | 3.184250 | 0.54000000 | +1.6207954022e-02 |
| 1 | 78 | -0.580000 | -0.290000 | 3.184250 | 0.54000000 | +1.6071664242e-02 |
| 1 | 79 | 0.290000 | -1.435162 | 3.184250 | 0.65650000 | +1.1539642240e-02 |
| 1 | 80 | 0.580000 | -0.290000 | 3.184250 | 0.54000000 | +1.6217492734e-02 |
| 1 | 81 | 1.450000 | 0.000000 | 3.184250 | 0.54000000 | +1.6376311378e-02 |
| 1 | 82 | -1.450000 | 0.580000 | 3.184250 | 0.54000000 | +1.6153119097e-02 |
| 1 | 83 | -0.580000 | 0.290000 | 3.184250 | 0.54000000 | +1.6048683270e-02 |
| 1 | 84 | -0.580000 | 0.870000 | 3.184250 | 0.54000000 | +1.6098735692e-02 |
| 1 | 85 | 0.580000 | 0.290000 | 3.184250 | 0.54000000 | +1.6138044094e-02 |
| 1 | 86 | 0.580000 | 0.870000 | 3.184250 | 0.54000000 | +1.6218414034e-02 |
| 2 | 92 | -1.160000 | -0.870000 | 3.784250 | 0.54000000 | -4.1229763184e-03 |
| 2 | 93 | -1.160000 | -0.290000 | 3.784250 | 0.54000000 | -4.0325885849e-03 |
| 2 | 94 | 0.000000 | -0.870000 | 3.784250 | 0.54000000 | -4.3372223253e-03 |
| 2 | 95 | -0.000000 | -0.290000 | 3.784250 | 0.54000000 | -4.1255544021e-03 |
| 2 | 96 | 1.160000 | -0.290000 | 3.784250 | 0.54000000 | -4.2477066490e-03 |
| 2 | 97 | -1.160000 | 0.290000 | 3.784250 | 0.54000000 | -3.9991911145e-03 |
| 2 | 98 | -1.160000 | 0.870000 | 3.784250 | 0.54000000 | -4.0132490723e-03 |
| 2 | 99 | 0.000000 | 0.290000 | 3.784250 | 0.54000000 | -4.0452781812e-03 |
| 2 | 100 | 1.160000 | 0.290000 | 3.784250 | 0.54000000 | -4.1617896577e-03 |
| 2 | 101 | -0.000000 | 0.870000 | 3.784250 | 0.54000000 | -4.1215621922e-03 |
| 2 | 102 | 1.160000 | 0.870000 | 3.784250 | 0.54000000 | -4.3855401752e-03 |
| 2 | 104 | 0.870000 | 0.829062 | 4.284250 | 0.64000000 | +8.5720985048e-03 |
| 2 | 105 | 0.692720 | -0.929413 | 4.284250 | 0.81350000 | +3.2580848072e-03 |
| 2 | 106 | -0.000000 | -0.290000 | 4.284250 | 0.54000000 | +1.1238504436e-02 |
| 2 | 107 | -0.870000 | 0.000000 | 4.284250 | 0.54000000 | +1.1290111066e-02 |
| 2 | 108 | 0.000000 | 0.290000 | 4.284250 | 0.54000000 | +1.1233859859e-02 |
| 3 | 114 | 0.580000 | 0.290000 | 4.884250 | 0.54000000 | -1.2327805666e-03 |
| 3 | 115 | -0.580000 | -0.290000 | 4.884250 | 0.54000000 | -1.2229792254e-03 |
| 3 | 116 | 0.580000 | -0.290000 | 4.884250 | 0.54000000 | -1.2662612022e-03 |
| 3 | 117 | -0.580000 | 0.290000 | 4.884250 | 0.54000000 | -1.2279447029e-03 |
| 3 | 119 | -0.000000 | -0.000000 | 5.384250 | 4.41000000 | +4.9499656971e-03 |

## Independent references and source limitations

1. J. Zhang et al., “Accurate Measurements and Error Analysis of
   Bi2Te3-Based Low-Temperature Thermoelectrics,” Chinese Physics
   Letters 42, 056304 (2025). DOI: 10.1088/0256-307X/42/5/056304.
   Six curve values here were digitized from published plots, not
   a commercial TEC factory material certificate.
2. M. L. Huber, “Thermal Conductivity of Gases,” NIST/CRC (2019).
   Reference Kr dilute-gas thermal-conductivity values at 200–400 K.
3. E. M. Heckman, L. P. Gonzalez, S. Guha, “Measurement of optical
   and thermal properties of Hg1−xCdxTe,” Applied Optics 47,
   578–582 (2008). DOI: 10.1364/AO.47.000578.
4. TEC Microsystems 3MC04-044-05 datasheet (2019), independent
   commercial performance envelope, not proof that the present
   synthetic TEC assembly or P/N materials are an identical product.
5. VIGO Photonics 3TE-TO66 9-pin reference package drawing, Rev. 9
   (2024); family-scale dimensional reference, not as-built validation.

**Replication policy.** Reported output numerics are conditional
simulation results. A fully independent implementation can
reproduce physically similar stage and detector responses with
this geometry, material table, equations, heat paths and inputs.
Bitwise field equivalence requires identical unstructured mesh,
per-face polygons, quadrature, solver libraries and tolerances;
those are not implied by this standalone report.
