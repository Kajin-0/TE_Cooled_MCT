**A. Target and inspected scope**

Independent read-only audit of clean `main`, commit **962c78af2992accd3cd0b181ac0e838011bdd116**, covering the **new local net88/lead9 conductor experiment**.

I read the installed auditor role/skill, full current contract, README, relevant chronology, geometry/policy/audit documents, experiment registration and amendments, original V3/R1 reviews, relevant source catalogue/registry records, executed electrical/geometry/control code, tests and saved results.

I independently inspected both saved meshes and electrical fields, reconstructed gradients/contact integrals from their arrays, checked boundary incidence and terminals, and compared MSH millimetres against NPZ/VTU SI coordinates. No PDE was solved. Original source figures re-examined were TEC2019 p.4, Kryotherm printed p.22, Kyocera thin-film/thick-Cu images and RMT mounting Fig.2. I also inspected both final diagnostic plots and reopened the KEMPER primary property page.

Not reviewed anew: complete assembly manufacturability, every original STEP face, supplier capability, full source-library figures, actual hardware, or all 38 Rev3 pages. The historical R1 conditional review remains background; this audit grants no additional assembly acceptance.

All **100 packet-file and one cache hashes matched before and after**. All ten registered input hashes matched. HEAD and clean status remained unchanged through **2026-11-02T22:29:09Z**.

Preserved identities:

- 824-solid STEP: `5e46c10fb75713a9dffbc97c44a2b94ca23bee14a93df7f4c0c7c915eb761a73`
- Rev3: `882209b09796acdc5e7d3aafc376f1722fce2843230233c7a76542ebcb273248`

No files, tests, CAD, meshes, solutions, sessions, issues or PRs were changed. Existing `sim:0.0` was observed and left untouched.

**B. Verdict**

**STOP qualification of the present local electrical coupon and all dependent C/D conclusions.**

| Scope | Independent verdict |
|---|---|
| Source identity, retained-domain/contact mapping and SI transfer | **PASS**, inspected numerical/provenance scope |
| Laminate and finite-contact definitions; saved uniform analytic controls | **PASS**, mathematical scope only |
| Material/contact applicability to a synthetic hypothesis | **CONDITIONAL**, selected properties and unmeasured interfaces |
| B raw current-flux qualification | **FAIL / STOP** |
| B voltage boundedness | **FAIL** |
| B discrete power closure and resistance comparator | **PASS**, insufficient for qualification |
| C passive thermal operator | **NOT RUN / NOT QUALIFIED** |
| D electrothermal temperatures and heat partition | **NOT RUN / NOT QUALIFIED** |
| Exact-commit CI | **FAIL** |

The documentation correctly retains B failure and C/D NOT RUN. I found no unsupported promotion to full TEC resistance, actual current capability, Joule thermal partition or detector temperature in the reviewed experiment’s interpretation.

**C. Findings in severity order**

**V3ET-01 — Critical qualification failure: contact conservation does not qualify the resolved bulk flux.**

Locations: [cut evaluation](/home/User/TE_Cooled_MCT/tecooledmct/v3_et_fem.py:110), [fine result](/home/User/TE_Cooled_MCT/data/v3_interconnect_et_20261102/B/fine_field/result.json), [B gate](/home/User/TE_Cooled_MCT/data/v3_interconnect_et_20261102/B/gate_B.json).

My independent cofactor gradients and declared-property reconstruction reproduce the fine field to **4.1934e−14 relative J difference**. All eleven interface integrals reproduce the stored values within **2.4123e−15 of drive current**.

At `film0 → lead_land`, for unit excitation:

\[
I=34.0463045271\ {\rm A},
\]

\[
I_{\rm contact}=34.0463045272\ {\rm A},
\quad I_{\rm raw,film0}=4.8939860894\ {\rm A},
\quad I_{\rm raw,opposite}=-36.3285398479\ {\rm A}.
\]

The resulting **85.6254999%** mismatch fails the registered **0.1%** limit by approximately **856 times**. Independently reconstructed fine terminal errors are **0.836320%** and **3.322308%**; both also fail.

This is not explained away by a plotting convention or contact-current sign. Conservative contact integrals and weak power balance describe different observables from one-sided bulk-gradient flux.

**Minimum correction:** preserve this failed checkpoint. A future, separately authorized discretization experiment would need to demonstrate the unchanged raw-cut criterion across every registered cut and its comparator. No further run is authorized here.

**V3ET-02 — High: geometry approximation and voltage undershoot prevent interpreting resistance stability as local-field accuracy.**

Locations: [mesh generation](/home/User/TE_Cooled_MCT/tecooledmct/v3_et_geometry.py:124), [voltage gate](/home/User/TE_Cooled_MCT/tecooledmct/v3_et_run.py:18), both saved mesh audits and fields.

Independently reconstructed mesh/CAD volume ratios are:

- Coarse: **0.9561650713**
- Fine: **0.9835118659**

Thus total geometric deficits remain **4.38349%** and **1.64881%**. The recorded fine lead9 deficit is **2.38232%**.

Fine minimum unit potential is **−7.35136e−7 V**, violating the registered **−1e−8 V** floor. Coarse also undershoots.

Positive tetrahedra, complete face ownership and **0.315803%** resistance change do not establish resolved curved geometry, spreading or current crowding. The present evidence does not isolate one exclusive cause.

**Minimum correction:** a proposed future numerical design should explicitly control curved-volume error, thin-layer/spreading resolution, boundedness and every raw cut. Do not adjust material/contact values to make these gates pass.

**V3ET-03 — Medium release defect: exact-commit CI fails because a new test requires an undeclared development dependency.**

Locations: [unconditional import](/home/User/TE_Cooled_MCT/tests/test_v3_et.py:71), [CI installation](/home/User/TE_Cooled_MCT/.github/workflows/tests.yml:13), [optional dependencies](/home/User/TE_Cooled_MCT/pyproject.toml:10).

[Run 41536865775](https://github.com/Kajin-0/TE_Cooled_MCT/actions/runs/41536865775), job `125590810168`, completed with **1 failed, 568 passed, 12 skipped**. I inspected the job log and confirmed its checkout contains the exact audited SHA. The sole failure is:

`ModuleNotFoundError: No module named 'meshio'`

CI installs `.[dev]`; `meshio` belongs only to the `fem` extra. The pinned-environment verification remains separate evidence and cannot be reported as exact-commit CI success.

**Minimum correction:** a separately recorded test-only successor can remove this optional dependency from the existing ASCII-MSH coordinate check, preserving its assertions. Retain this original failure and verify the successor’s exact CI. No physics rerun is needed.

**V3ET-04 — Procedural limitation: not every implementation detail has a demonstrated pre-control immutable seal.**

Witnesses: [original registration](/home/User/TE_Cooled_MCT/data/v3_interconnect_et_20261102/registration.json), [operator definitions](/home/User/TE_Cooled_MCT/data/v3_interconnect_et_20261102/operator_definitions.json), [B freeze](/home/User/TE_Cooled_MCT/data/v3_interconnect_et_20261102/B_frozen_inputs.json).

The original protocol is timestamped **21:45:48Z**. The thermal-sign amendment is timestamped **21:47:43Z** and records zero prior numerical solves. The detailed operator manifest is timestamped **21:55:23Z**, explicitly **after analytic controls**, and includes internal plated-interface excess resistances absent from the original protocol. B’s source/input freeze is timestamped **22:00:17Z**.

The record candidly discloses this distinction. I can verify preserved definitions and source identities; I cannot independently certify that every detailed coefficient and implementation hash was immutably sealed before the first control merely from the final snapshots.

**Minimum correction:** retain the current precise disclosure. For any future authorized experiment, seal its complete operator, interface assumptions and executed source before its first numerical control. Do not retroactively describe this packet as completely frozen before A.

**D. Evidence matrix**

| Topic | Evidence and applicable conclusion | Remaining uncertainty |
|---|---|---|
| Geometry/topology | 31 original solids map into 12 domains, 11 interfaces and 105 physical faces. Both saved meshes have complete, unique physical-face coverage and maximum tetrahedral-face incidence two. | Original assembly process/tolerance qualification is unchanged. |
| Finite contacts | Separate region traces and symmetric triangle contact terms retain voltage jumps and positive interface dissipation. Same-phase solder fillets are fused. | Contact resistivities are selected scenarios, not measured joints. |
| Thin layers | Actual 15 µm film and 3.5 µm pin-finish envelopes use anisotropic series/parallel tensors. | Uniform slab/sheet equivalence does not validate nonuniform local spreading. |
| Materials | [KEMPER Cu-ETP physical-properties table and footnote](https://www.kemper-group.com/en-en/rolled-products/alloys/cu-etp/) supports approximately 58 MS/m and 385 W/(m·K), soft state at ambient temperature. | Bulk-family analogy; plated Cu, barrier layers, solder and interfaces are not measured specimens. |
| Construction sources | [TEC2019 p.4](https://www.tec-microsystems.com/Download/Datasheets/Thermoelectric%20Coolers/MC04%20Series/3MC04-044-05_Datasheet_2019.pdf), [Kryotherm p.22](https://shop.amstechnologies.com/media/d7/44/1a/1720719247/Multistage-Thermoelectric-Coolers-Kryotherm-Datasheet.pdf?ts=1734638881), [Kyocera figures](https://global.kyocera.com/prdct/semicon/technology_strengths/detail/thinfilm_technology.html) and [RMT Fig.2](https://www.rmt-tec.com/support/recommendations-for-use/) supply construction-family precedents. | They do not measure this selected conductor stack, certify its process or establish its current rating. Kyocera’s viewed cross-section is Ti/Pt/Au on AlN, not the selected laminate. |
| Boundaries | Active thermal definitions are C0/C1/C2, PIN9_HEAD and PN87_HOT. Electrical terminals are internal P87/pin9 cuts. | Pin shaft, pin1, P/N legs and external circuit impedances are omitted. |
| Gas/radiation | Explicitly absent from this coupon. | No package exchange or device-performance inference permitted. |

C3, header, pin1, detector7/8 and ambient are declared absent/adiabatic channels. They are not represented thermal reservoirs. The selected **290–330 K** constant-property interval is a modeling restriction, not source-measured coverage.

**E. Independent SI calculations and controls**

MSH spans multiplied by \(10^{-3}\) match both SI meshes within **4.34e−19 m**. Their spans are approximately **5.86869 × 3.51404 × 2.34925 mm**. Saved VTU potentials and current densities exactly match the registered 0.4 A scaling of the NPZ fields.

For NOM film assumptions, independent series/parallel arithmetic gives:

\[
\sigma_\parallel=2.79923\times10^7,\quad
\sigma_\perp=2.24743\times10^7\ {\rm S/m},
\]

\[
k_\parallel=186.281,\quad k_\perp=114.427\ {\rm W/(m\,K)}.
\]

The sheet resistance is **2.38160 mΩ/square**. LOW/HIGH arithmetic gives **1.22698/4.49797 mΩ/square**; these are selected scenario alternatives, not measured uncertainty bounds.

The independent tangential slab formula gives **314.913890515 S**, matching the saved analytic control. Eight stored explicit-layer/homogenized controls have maximum relative error **8.5853e−11** against \(10^{-7}\). The genuine Elmer bar has the correct analytic resistance **1.724137931e−4 Ω** and stored affine error **5.7732e−15 V**. These controls establish mathematical limits, not local coupon-field qualification.

From the fine saved field:

\[
P_{\rm bulk}=31.9010136787\ {\rm W},\qquad
P_{\rm contact}=2.1452908485\ {\rm W}
\]

at unit voltage. Their sum agrees with \(IV\) to **9.9187e−13 relative**.

The diagnostic discrete resistance is **0.02937176336 Ω**. At 0.4 A this scales to **11.74870535 mV**, **4.69948214 mW**, and peak discrete \(|J|=1.30188\times10^8\ {\rm A/m^2}\). These remain **unqualified local numerical observables**. None is full TEC resistance, allowable current density or a predicted device heat load.

**F. Blocked claims and proposed-only correction**

Keep **C and D NOT RUN**. No thermal conductance matrix, thermal bypass magnitude, port-resolved Joule partition, temperature rise, full TEC resistance, actual current rating or detector temperature is qualified. LOW/HIGH field sensitivities and temperature-dependent conductor transport remain unexecuted.

The thermal-sign correction—positive heat **from port into coupon**, yielding PSD conductance—is mathematically appropriate. It does not supply a thermal solution. D would additionally require independently qualified interface-source treatment after genuine B/C passes.

Permissible remaining work is preservation, documentation, the bounded test-only CI correction and review of its successor. A new flux-resolving discretization experiment is **proposed only**, requires separate authorization, and must retain the original failure, boundaries and raw criteria.

[Issue #2](https://github.com/Kajin-0/TE_Cooled_MCT/issues/2) was independently confirmed **OPEN** and must remain open. Historical manufacturing conditions and bath/cold/gas/side-port failures are unchanged.
