# R3 29/11/4 reduced TEC: finite hot-side sink and original CAD wire sensitivity

**Date:** November 7, 2026. **Parent:** `7b6c803ce4d01c9bf6e799b7aa78e3837f2f8cb9`.
**Scientific verdict:** **18/18 bounded numerical scenarios ACCEPTED**; **no manufacturer-specific physical prediction or full 3D Gate C/D qualification**. This is a separate, source-hashed continuation of the initial [nine-case ideal R3 study](V3_R3_REDUCED_THERMOELECTRIC_REFERENCE_20261107.md), using the existing conservative nonlinear 1D P/N plus five-node solver without geometry, historical physics or calibration changes.

[Original preregistration and immutable input digests](../data/v3_r3_sink_wire_20261107/attempt01/registration.json), [case-by-case energy/temperature/heat-path ledger](../data/v3_r3_sink_wire_20261107/attempt01/cases.json), [saved scenario summary](../data/v3_r3_sink_wire_20261107/attempt01/summary.json), [integrity manifest](../data/v3_r3_sink_wire_20261107/attempt01/manifest.json), and [replayable one-shot source](../scripts/v3_r3_sink_wire_sensitivity.py).

## 1. Physical basis versus deliberately chosen conditions

Original accepted R3 CAD 29/11/4 couple layout and original 0.4 × 0.4 × 0.5 mm individual legs are **unchanged**. This study uses the same Zhang2025 research P-HE/N-HE-1 *unmatched* P/N transport specimens and registered engineering material factors as the prior reduced reference study. No claim of proprietary production-grade matching is made. Ambient and external pin heat reservoirs are assumed **300 K**. The die dissipates **2.00 mW**, and the hypothetical die-attach layer is 20 µm / 1 mm² at **1 W/(m·K)**. Both gas and radiation are disabled; nonlocal ceramic spreading, interface thermal contact resistance, solder heat capacity and actual sensor thermistor remain unmodeled.

Hot-side sink resistance is the original solver's effective, thermal-circuit parameter **Rθ = 0, 2 and 5 K/W**. All three are **engineering scenarios**, not a vendor-specified or measured installed heat-sink interface. The hot ceramic obeys \(T_h=300\,\mathrm{K}+R_\theta Q_\mathrm{sink}\), with actual signed model sink heat **not automatically equal to (IV)**.

For each sink, compare a deliberate wire-OFF control with a **geometry-derived wire-ON proxy**. Both copper TEC leads and both gold detector bonds are extracted from the **actual original CAD centerline curve lengths and radii** rather than older 28/12/4 wire coefficients.

| Original R3 conductor | Source radius | Native centerline length | Assumed representative bulk (k) | Reconstructed (G=k\pi r^2/L) |
| --- | ---: | ---: | ---: | ---: |
| `TEC_lead1`, Cu | 100 µm | 3.451 mm | 400 W/(m·K) | 3.6413 mW/K |
| `TEC_lead9`, Cu | 100 µm | 4.965 mm | 400 W/(m·K) | 2.5310 mW/K |
| `detector_bond7`, Au | 9 µm | 9.679 mm | 315 W/(m·K) | 0.0082815 mW/K |
| `detector_bond8`, Au | 9 µm | 9.679 mm | 315 W/(m·K) | 0.0082815 mW/K |

Copper resistivity **1.72×10⁻⁸ Ωm** and Au resistivity **2.30×10⁻⁸ Ωm** are room-temperature proxies retained in `tecooledmct/materials.py` and [material provenance](materials_and_provenance.md). The Cu lead DC resistances from these simple geometry/proxy formulas are **1.8894 mΩ** and **2.7182 mΩ**. Au leads serve as thermal die-to-pin shunts; their high electrical resistance is **not** included in the TEC power circuit. Four wire lengths, source material identities, heat conductances, resistance proxies and input file hashes are separately recorded.

**Limitations:** The wires are curved and real contact interfaces are finite. The 1D formula assumes a uniform circular conductor, constant room-temperature (k) and (
ho) at 185–303 K, perfect end thermalisation, fixed 300 K pin temperatures, and no solder/wedge contact heat resistance. This is a **plausible geometric proxy**, **not** a released thermal-circuit measurement or a numerical 3D solid solve.

## 2. Predeclared limited numerical matrix

Three operating cases `(nominal, 0.25 A)`, `(nominal, 0.40 A)`, `(higher, 0.40 A)` times three sinks (R_\theta=0,2,5\,\mathrm{K/W}) times two wire states (OFF / CAD-derived proxy ON): **18 fixed cases**, no optimization or second-solve adaptation. Original code retains a 12 s per-case cap and 150 s single-study limit.

The **0 K/W** scenarios use only source-interpolated P/N transport data with complete local axial temperatures (le 300) K. For every finite-resistance sink, the source temperature field rises *above* 300 K. Accordingly, **12/18 otherwise numerically accepted cases use the pre-existing assumed quarter-terminal-tangent continuation of the research data**. They are explicitly marked `ACCEPTED_ASSUMED_GT300K`, **not** a measured-domain validation.

## 3. Numerical die temperatures

All entries are calculated Kelvin, at **300 K ambient / 2.0 mW detector heat**, and are **conditional reduced-model outputs**, not real detector temperatures.

| Material and current | Rθ (K/W) | Wires OFF, die T (K) | CAD wire proxies ON, die T (K) | Wires-ON hot ceramic (K) |
| --- | ---: | ---: | ---: | ---: |
| Nominal, 0.25 A | 0 | **229.072** | **229.483** | 300.000 |
| Nominal, 0.25 A | 2 | 229.368 | 229.775 | 300.515 |
| Nominal, 0.25 A | 5 | 229.816 | **230.204** | 301.270 |
| Nominal, 0.40 A | 0 | **207.169** | **207.647** | 300.000 |
| Nominal, 0.40 A | 2 | 207.716 | 208.185 | 301.184 |
| Nominal, 0.40 A | 5 | 208.552 | **208.985** | 302.935 |
| Higher hypothesis, 0.40 A | 0 | **185.124** | **185.770** | 300.000 |
| Higher hypothesis, 0.40 A | 2 | 185.550 | 186.190 | 301.192 |
| Higher hypothesis, 0.40 A | 5 | 186.203 | **186.813** | 302.958 |

These numbers are not a measured performance or manufacturing-tolerance envelope. A physically unknown thermal resistance larger than 5 K/W, radiative/gas exchange, 3D ceramic temperature gradients, parasitic interstage pad conduction, source metal contacts and real P/N properties can all change the result significantly. The sources do not establish the actual cooler's safe terminal current.

## 4. Heat-load and power budget implications

The reconstructed Au detector wires deliver a conduction heat leak
\[
Q_{\mathrm{Au}} = (G_{\mathrm{bond7}}+G_{\mathrm{bond8}})(300\,\mathrm K-T_{\rm die}),
\]
using original source CAD wire path lengths and constant representative Au k. Under nominal 0.40 A and (R_\theta=5) K/W, this equals **1.5075 mW**. The reduced cold TEC therefore lifts roughly **3.5075 mW**: the imposed 2 mW die heat **plus** Au bond-wire heat. Wires OFF require only 2 mW on the cold stage. Despite the roughly **75% increase in cold-stage heat load**, the die temperature shift due to wires alone is **0.4328 K** at that same sink/current, because the TEC's nonlinear response redistributes its stage temperatures.

For nominal 0.40 A, 5 K/W with CAD wires ON, the calculated TEC terminal power is **0.60201 W**; the reduced model's effective hot-side sink rejection raises hot ceramic from 300 to **302.935 K**. That heating must **not** be estimated from terminal (IV) alone without independent signed lead and sink energy accounting. The source code retains the existing validated wire Joule partition and pin-reservoir heat paths, which are approximate and uncalibrated physically.

An *important diagnostic* emerged: adding positive Cu wire resistance does not guarantee a larger total **thermoelectric terminal voltage** at the same current if stage temperature gradients change simultaneously; at the higher-material/0.40 A/5 K/W point the calculated wire-ON voltage is slightly **lower** than wire-OFF. We did not reject mathematically valid cases solely for that unjustified monotonicity assumption. Independently verified current-power and energy balances are the acceptance criterion.

## 5. Numerical acceptance and qualification status

- **18/18** prospective cases numerically accepted; **6** use research transport within its actual measured 40–300 K interval and **12** explicitly use an engineering assumed continuation above 300 K.
- **0** rejected, **0** not run. Full original preregistered registration and **seven original input-file SHA-256** digests are saved; source original CAD and archival prior ideal-R3 outputs remain identical.
- Recomputed the original **three wire-OFF, 0 K/W controls** and reproduced the archived earlier R3 die temperatures; both-sided Au/Cu wire heat/current sinks, node/energy residuals and (P=IV) passed per-condition checks.
- Heat/current gate thresholds remain **node and global (<10^{-8}) W** and **each stage (<10^{-9}) W**, within source nonlinear model applicability. The available energy balances prove *internal numerical self-consistency*, not manufacturer-calibrated physical heat flow.

**Engineering decision:** A nonzero hot sink and the actual-source lead/bond geometry modestly degrade the optimistic reference results under these **narrow, selected assumptions**. This is substantive sensitivity information, but does **not** close the dominant unknowns: unmeasured (R_\theta), finite interfaces/contacts, ceramic spreading, optical/cavity exchange and production-grade thermoelectric transport. Do **not** keep stacking arbitrary scenario sweeps. The next high-value deliverable should obtain an independently documented *heat-sink mounted (T_h-T_{amb}) and (Q_{sink})*, measured detector/TEC IV and cold-side temperature, or evidence-backed finite-interface resistance to constrain these assumptions.

**Original R3 electrical Gate B FAIL/STOP; P2 prospective STOP; thermal C/D NOT RUN. Actual manufactured detector operating temperature is NOT QUALIFIED.** No 3D PDE, CAD/mesh changes, OEM fitting or Codex usage.
