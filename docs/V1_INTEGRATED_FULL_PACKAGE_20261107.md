# V1 — First working integrated coarse 29/11/4 source-CAD electrothermal package

**Development milestone:** V1 working end-to-end conditional **reduced thermal-network** system, November 7, 2026. **Parent:** `9f294830b072203e40b2475cf1845ec66c83e31c`.

**Status: NUMERICAL PASS for exactly one registered operating condition. NOT 430-solid spatial FEM, material-grade qualification, or as-built detector prediction.**

[Executable single-case driver](../scripts/v1_integrated_full_package.py), [source-hashed preregistration](../data/v1_integrated_full_package_20261107/attempt01/registration.json), [complete I/V/P/T and stage-energy output](../data/v1_integrated_full_package_20261107/attempt01/result.json), [integrity manifest](../data/v1_integrated_full_package_20261107/attempt01/manifest.json).

## Why this is V1

The user directs **working system first, progressive coarse-to-fine iterations**, not more highly optimized isolated contact/interface studies. This script is **one executable workflow** linking actual-source 29/11/4 TEC leg geometry, existing 32-interval temperature-dependent nonlinear P/N transport, CAD source Cu/Au wires, HgCdTe detector dissipation and die attach, the three interstage temperature nodes, and a source-traceable *coarse scalar* hot-side thermal boundary back to 300 K ambient. It reuses the established `tecooledmct.integrated_reference.solve` function rather than cloning or rewriting solvers. One run returns terminal I/V/P, TEC stage heat budgets, five physical-equivalent temperature nodes, heat-sink rejection, and residuals.

The source original 824-solid STEP and accepted 430-domain geometry, 2,440 native faces, 29/11/4 stage allocations, original 3D header mesh and previous independent experiments are **unchanged**. V1 fidelity labels are developmental and **not** historical R3 geometry revisions.

## One fixed, source-CAD-backed conditional point

- **Current:** 0.400 A, 300 K ambient and pins.
- **Actual source CAD geometry:** stage 0/1/2 = 29/11/4 couples; each P/N leg 0.4 × 0.4 × 0.5 mm; original ceramic footprints 6.4/5.2/3.8/2.4 mm; 20 µm × 1 mm² die attach; source curved Cu power leads and Au detector bond wires.
- **Material coefficients:** unmatched Zhang2025 P-HE/N-HE-1 research specimens, nominal engineering factors, with the existing **ASSUMED** >300 K continuation; original Cu/Au room-temperature bulk wire-property proxies. Neither is an identified OEM source material grade.
- **Detector thermal dissipation:** **2.00 mW**; detector optical load zero and die-attach thermal conductivity assumed 1 W/(m K).
- **Excluded at this initial fidelity:** gas and cavity radiation, interstage bypasses, additional real contact thermal resistance or interface heat, actual electrical SnSb/contact Joule and junction Peltier physics, 3D ceramic spreading, and independent as-built manufacturer validation.

### Connected hot-side equivalent circuit

The hot ceramic → room thermal path uses four explicitly differentiated component estimates from immutable earlier source-CAD work. These are **not four independent manufacturer-measured resistances**.

| From ambient inward | Nominal resistance | Evidence class |
| --- | ---: | --- |
| External radiator to 300 K ambient | 2.000000 K/W | VIGO design recommendation, not installed measurement |
| Original R3.9 header + finite TIM Robin boundary | 2.759313 K/W | One original 47,702-tetra numerical 3D header study; hypothetical entire underside contact and TIM reference |
| Native In52Sn48 mount solder | 0.074074 K/W | CAD 80 µm / 36 mm², unmeasured (k=30) W/(m K) 1D hypothesis |
| Hot alumina ceramic0 | 0.447908 K/W | CAD 500 µm / 37.21 mm², unmatched AD995 (k=30) W/(m K) 1D analog |
| **V1 total single hot-side thermal resistance** | **5.281295 K/W** | Conditional series approximation; contact impedances and 3D ceramic spreading missing |

**Critical accounting:** The existing nonlinear stage solver accepts this **sum as its total effective hot-side resistance**; it does not add the old 5 K/W sink on top. The previously archived 3D header computation is reduced to one scalar because its own input heat and downstream radiator are modeled as a linear fixed-k response; V1 does **not** re-solve spatial header fields when its heat flow changes. The thermal component temperatures below are lumped equivalent-node estimates, not local measured temperatures or a newly solved full-package 3D field.

## One solved operating point

| Observable | V1 saved result |
| --- | ---: |
| Source current | 0.400000 A |
| Terminal voltage | **1.506395 V** |
| Terminal electrical input | **0.602558 W** |
| Total heat rejected to 300 K bath | **0.586574 W** |
| Ambient | 300.0000 K |
| Equivalent radiator node | 301.1731 K |
| Equivalent header/finish node | 302.7917 K |
| Equivalent solder output node | 302.8351 K |
| TEC hot ceramic | **303.0979 K** |
| Intermediate stage 1 | 265.0839 K |
| Intermediate stage 2 | 234.6344 K |
| TEC cold ceramic | **208.9898 K** |
| **HgCdTe detector die** | **209.0599 K** |
| Die + Au wire cold-stage thermal load | **3.50624 mW** |
| Of which original source Au wire heat leak | **1.50624 mW** |

All four hot-side equivalent resistance drops sum to ((303.0978726-300)) K at the solved (Q_mathrm{bath}=0.5865744121) W. At the cold stage, the assigned 2.000 mW detector dissipation plus 1.50624 mW Au bond-wire conduction equals the predicted cold-stage (,Q_c=3.50624) mW. The original source Cu power-wire heat conduction and Joule partition are included through the existing reduced solver.

**Stage heat flows and electrical contributions:**

| Stage, hot-to-cold | Heat absorbed at its cold side | Heat discharged at its hot side | Stage voltage |
| --- | ---: | ---: | ---: |
| 29 couples | 0.171286 W | 0.605327 W | 1.085102 V |
| 11 couples | 0.0417235 W | 0.171286 W | 0.323907 V |
| 4 couples | 0.00350624 W | 0.0417235 W | 0.095543 V |

The stage voltages exclude the source Cu leads; terminal voltage **includes** them.

**Conservation and convergence at the chosen point:** max stage energy residual (1.81	imes10^{-13}) W; max node balance residual (2.38	imes10^{-13}) W; full source-network accounting residual (-3.37	imes10^{-13}) W; terminal (IV) and internal heat-path drop consistency passed. Those residuals are numerical self-consistency checks, **not accuracy compared with real hardware**.

### Baseline V0 versus V1, identical other conditions

The previous saved 29/11/4 V0 nominal 0.400 A, source-CAD wire-ON, 2 mW die, no gas/radiation, hypothetical *single* 5 K/W sink predicted **208.985312 K** die, **1.505019 V**, and **0.587030 W** to bath.

V1 replaces **only** this total sink scalar with its four source-traceable terms totaling 5.281295 K/W. It predicts **209.059878 K** die, **1.506395 V**, and **0.586574 W** to bath. This is a **+0.074566 K die temperature difference** for the single reference operating point, **not an error estimate**. The small difference tells us the precise sink resistance within these two assumptions is not the dominant uncertainty in this operating regime; it does **not** establish numerical convergence or experimental accuracy.

## Domain validity and next refinement

The model uses **measured research-specimen properties only over 40–300 K** and the hot stage operates up to **303.10 K**. Consequently the existing transport model's high-temperature extension is **explicitly assumed** and the result is not within a fully measured transport-property domain. Source TEC P/N grade, real joint transport, TIM pressure/thickness, external mounting conductance, cavity/radiation and detector optical/electrical operating loads remain unverified. The original electrical P1 Gate B **FAIL/STOP**, separate 3D pair's raw contact cut **FAIL 8/8**, prospective P2 **STOP**, and 430-domain thermal C/D **NOT RUN** are unchanged.

**Next V2 refinement:** Keep this exact V1 case and stable output schema, first link the coarse actual geometry's thermal and electrical regions into a prototype spatial model. Prefer a small physical subsystem or low-resolution whole-package 3D thermal representation that can be directly compared against the V1 die and stage outputs; do not switch to an unbounded grid of isolated contact and micromesh tests. If a model increment cannot produce a complete I/V/P/T_die and energy comparison, defer it unless it fixes a serious safety/physics violation. Future material-grade and interface-law validation will matter for predictive/as-built release, but need not block an honestly **CONDITIONAL** early integrated prototype.

**This milestone:** one registered solve; no new global meshing, no new separate TE solver, no Codex, no original CAD or historical gate mutation.
