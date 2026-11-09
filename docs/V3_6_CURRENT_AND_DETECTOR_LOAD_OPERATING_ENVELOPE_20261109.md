# V3.6: Three-stage TEC operating-current and detector-load engineering envelope

**9 November 2026 | Six independently audited full-device operating points | Provisional physical model, not measured hardware**

## Practical question

How much lower can the HgCdTe photoconductor temperature become as the thermoelectric cooler is driven harder, how much electrical power is required, and how sensitive is the detector temperature to additional thermal loading?

This study extends the existing V3.5 physical model without changing its construction, transport properties, original 88 individual nonlinear P/N legs, four spatial ceramic FEM fields (11,791 TET4), formed interstage copper tabs, three-contact return, installed TO supply leads, mounting and 100 Pa krypton/radiation terms. The only physical changes between accepted runs are **prescribed TEC drive current** and **applied detector heating**. The solver is not a full 430-domain 3D metal/P-N electrothermal PDE.

## A. TEC current versus cooling and electrical input

Constant: 300 K mounting reservoir, 2.00 mW imposed HgCdTe heat, 100 Pa krypton, and the same declared unmeasured copper/contact and thermoelectric constitutive laws.

| TEC current | Detector temperature | Cooling below 300 K | TEC voltage | Electrical input | Mounting-sink heat |
|---:|---:|---:|---:|---:|---:|
| 0.250 A | 238.567615 K | 61.432385 K | 1.006436 V | 0.251609 W | 0.254252 W |
| 0.400 A | 218.900024 K | 81.099976 K | 1.489170 V | 0.595668 W | 0.592331 W |
| 0.550 A | 205.992445 K | 94.007555 K | 1.935744 V | 1.064659 W | 1.051609 W |
| 0.600 A | 202.776789 K | 97.223211 K | 2.080911 V | 1.248547 W | 1.231472 W |

All four are actual converged full-system states, not points from a fitted curve.

**Marginal electrical cost of incremental cooling**

| Current change | Additional cooling | Additional electrical power | Incremental power per kelvin |
|---|---:|---:|---:|
| 0.25 to 0.40 A | 19.667591 K | 344.059 mW | 17.494 mW/K |
| 0.40 to 0.55 A | 12.907579 K | 468.991 mW | 36.335 mW/K |
| 0.55 to 0.60 A | 3.215656 K | 183.887 mW | 57.185 mW/K |

Thus the model predicts **diminishing additional cooling per extra watt** throughout the sampled interval. The 0.55 A setting gives about 12.91 K lower detector temperature than the 0.40 A setting at approximately 78.7% more power. At 0.60 A cooling still improves, so **an optimal TEC current was not established**. No thermal-cycling/current-capacity or OEM device rating has been verified. Higher drive increases the hot-side ceramic temperature: about 301.656 K at 0.25 A versus 307.707 K at 0.60 A.

[Source-derived engineering current/power figure](../reports/current/figures/v36_current_temperature_power.pdf).

## B. Detector heat loading at a constant 0.400 A

Constant: 300 K mounting reservoir and 100 Pa krypton.

| Imposed detector load | Calculated detector temperature | TEC voltage | TEC input |
|---:|---:|---:|---:|
| 1.0 mW | 218.589290 K | 1.489677 V | 0.595871 W |
| 2.0 mW | 218.900024 K | 1.489170 V | 0.595668 W |
| 6.0 mW | 220.144759 K | 1.487136 V | 0.594854 W |

The local finite-difference thermal responses are **310.734 K/W** from 1 to 2 mW and **311.184 K/W** from 2 to 6 mW. Across all measured simulation points, the secant response is approximately **311 K/W**, or 0.311 K of detector heating per additional milliwatt at the selected 0.40 A condition.

This is a package-level **synthetic thermal-load sensitivity**. The HgCdTe device's electrical resistance, gain, optical absorption and noise are not yet simulated self-consistently. This number is not a measured die-to-header intrinsic thermal resistance and does not automatically apply at another TEC current.

[Source-derived thermal-load sensitivity figure](../reports/current/figures/v36_detector_heat_load_response.pdf).

## C. Reproducibility, numerical closure, and preserved failures

- The accepted V3.6 reference at **0.400 A and 2 mW** reproduces the prior accepted V3.5 temperature, terminal voltage, power, mounting rejection, global residual and spatial iterations **exactly**. The original V3.5 source/results and all older versions are unchanged.
- All six saved full-device cases have an independently recomputed **electrical and global thermal balance**, all stage heat balances, actual original CAD lead-pad heat transfers and true three-contact copper-return heat. Maximum absolute independent stage and global energy residuals are below **2 × 10⁻⁹ W**.
- Every accepted case retains 88 nonlinear P/N legs, four original ceramic 3D source finite-element fields containing 11,791 tetrahedra, and the unchanged original package mounting/cavity assumptions. Final maximum spatial pad-temperature updates are below **3 × 10⁻⁷ K**.
- The first 0.25 A and 0.55 A runs deliberately remain **failed**: they tried to initialize a frozen 0.4 A spatial heat field with the new current's solder and lead Joule sources, violating source-ceramic heat balance before any nonlinear solve. The correction was **initialization-only**: the archived 0.4 A heat field is initialized with its original 0.4 A heat strengths, then the specified new current enters the actual nonlinear solve. Neither physical equations nor acceptance tolerances were relaxed.
- The three successful 0.4 A runs were computed before the initialization fix, with identical unchanged physics. All wrote independently accepted result and source-field archives; the command initially exited nonzero **after saving** because of an obsolete historical comparison-key in its final print statement. The corrected source fixes this reporting issue. Both source hashes, registrations and failed logs are preserved, so the six-case comparison does not conceal mixed historical solver-source identities.

**Numerical convergence is not measurement-based uncertainty.** The used copper conductivity, thermal/electrical contact impedances, P/N transport law, solder behavior, package cavity coefficients and lead geometry are currently synthetic/reference assumptions. A previous V3.5 extreme copper-interface experiment shifted predicted temperature by about 6.28 K, much greater than numerical discretization tolerances. It is not an uncertainty confidence interval.

## D. Direct source and independent evidence

- [All six frozen operating-point directories and input registrations](../data/v3_6_operating_envelope_20261109/)
- [Accepted combined machine-readable result](../data/v3_6_operating_envelope_20261109/accepted_envelope_summary.json)
- [Current runnable operating-envelope solver](../scripts/v3_6_current_heatload_envelope.py)
- [Original pre-warm-start-correction source and failed runs](../data/v3_6_operating_envelope_20261109/attempt01_initial_warm_start_source.py)
- [Independent source-geometry and energy audit](../scripts/v3_6_independent_energy_audit.py)
- [Result and provenance regression tests](../tests/test_v3_6_operating_envelope.py)
- [Cumulative hardware-focused engineering report](../reports/current/TEC_HgCdTe_Current_Architecture_20261108.pdf)

For reproduction, use each archived registration with the **exact matching source bytes** (source hash recorded in registration/result), and a fresh empty output directory. The three original 0.4 A cases use the archived pre-correction source; because it computes the repository root from its file location, restore that archival source file into the **scripts directory of a separate clean worktree** to reproduce it. Do not execute that archival file directly from the data directory (incorrect relative root), overwrite the active solver, or expect its obsolete post-save print statement to return zero. Independent audit of its saved result is the scientific acceptance gate. The new 0.25/0.55/0.60 A registrations use the current, corrected source in scripts. No material fitting, geometry change or global remeshing was conducted in this milestone.

## Next most consequential engineering question

This study establishes two practical design metrics: **the rising incremental electrical price of cooling** and **roughly 311 K/W detector heat-load sensitivity** at the nominal drive. The next substantive model improvement should introduce bounded temperature-dependent **HgCdTe resistance and bias/absorbed-optical heating**, so detector dissipation becomes part of a self-consistent feedback loop instead of a prescribed 1–6 mW number. The solder and plated-metallization thermal interfaces should also be constrained with credible material ranges; otherwise apparent current optimum and detector temperature have substantial physical-model uncertainty. Avoid extensive new mesh gates or report-only work before advancing these device-level physics.
