# TE_Cooled_MCT

**[Master Engineering Report — Revision 3](reports/generated/HgCdTe_Engineering_Assessment_Rev3_REVIEW_DRAFT.pdf)**

This single, continuously maintained standalone report is the current externally
facing scientific assessment. It distinguishes genuine corrected-geometry 3D
solid fields from the nonlinear reduced package and preliminary cavity proxy.
The legacy download filename is retained for compatibility; the document itself
is the Revision 3 engineering master. Historical PDF bytes remain sealed evidence.
The current master has 38 pages; all pages were visually reviewed and the PDF
and source-derived figures reproduce exactly. It includes the frozen 181-case
material screening, conditional 200 K target, rejected coverage and candid
manufacturer lift/voltage discrepancy. It now derives the nonlinear geometry/material
ambiguity and distinguishes a reduced residual improvement from failed native-pad
realization. A matched-200 K finite-sink study quantifies nominal input rising
from 0.548425 to 0.622176 W between ideal and 10 K/W sink, conditional on assumed
continuation. Original numerical failures remain explicit.

A reproducible engineering model of a **plausible synthetic** three-stage
TEC-cooled HgCdTe detector in a nine-pin, two-ear TO-66 package. The objective
is useful thermal budgets and sensitivity, not reconstruction of a proprietary
assembly. [Modeling policy](docs/PLAUSIBLE_REFERENCE_MODEL_POLICY_20261030.md).

## Internal implementation and reproduction notes

Development starts with the authoritative [CURRENT PROJECT CONTRACT](AGENTS.md).
The guides below support implementation and reproduction; they are internal
methods documents, not alternative standalone scientific reports. Earlier
milestone instructions have been relocated to historical context.

| Question | Read / run |
| --- | --- |
| What blocks geometry promotion and further physics now? | [Physical-source audit](docs/PHYSICAL_GEOMETRY_QUALIFICATION_20261102.md); independent review PENDING, [issue#2 OPEN](https://github.com/Kajin-0/TE_Cooled_MCT/issues/2). V2 CAD PASS cannot establish physical acceptance |
| How is the single master built and its historical evidence preserved? | [Internal report build/integrity guide](docs/MASTER_REPORT_REPRODUCIBILITY.md) |
| What does the current package model solve? | [Integrated model guide](docs/INTEGRATED_REFERENCE_THERMAL_20261030.md) |
| Which P/N laws and transport approximations are available? | [Transport and enclosure guide](docs/GRADED_TEC_AND_CORRECTED_ENCLOSURE_20261030.md) |
| Can admitted material assumptions reach 200 K, and resemble published module curves? | [Material-hypothesis study](docs/TEC_MATERIAL_PLAUSIBILITY_20261101.md): 141/181 admitted; nominal idealized 300 K/2 mW/wires-ON sample 186.484 K at 0.4 A; substantial joint datasheet mismatch and no full-device qualification |
| Can steady cooling/voltage identify leg dimensions rather than material changes? | [Registered identifiability diagnostic](docs/TEC_GEOMETRY_MATERIAL_IDENTIFIABILITY_20261101.md): 260/269 admitted; exact A/L–rho–k ambiguity, raw SVD caveat and failed unchanged native-pad realization; no OEM fitting |
| How much does finite hot-side resistance cost at a matched die target? | [Finite-sink study](docs/FINITE_SINK_MATCHED_TARGET_20261101.md): 203/288 grid states admitted; six actual nominal 200 K crossings; 10 K/W raises target input 13.4478%, with assumed >300 K transport and explicit wire/sink heat accounting |
| Which physical evidence would most improve temperature/power credibility? | [Input/path qualification program](docs/PHYSICAL_INPUT_QUALIFICATION_20261101.md): primary-source domains, matched-target local derivatives, independent measurement requests and explicit failed/NOT RUN paths |
| Does fresh source-constrained geometry yield a feasible datasheet-aligned candidate? | [Separate29/11/4 candidate](docs/SOURCE_CONSTRAINED_TEC_CANDIDATE_20261101.md): geometric361-solid STEP gates PASS; no-fit and explicitly authorized two-factor calibration FAIL full alignment. Loaded25.11K error and omitted Cu physics prevent a qualified candidate; original reference untouched |
| Is the candidate connector/Cu/calibration/sink sequence qualified? | [Separate compact v2 prototype](docs/COMPACT_TEC_V2_20261102.md): patterned face/edge metal plus short foil gaps; source circuit/clearance and359-solid STEP/SI gates PASS. Runtime recipe restored/verified; Cu FEM/calibration/sink NOT RUN. [Earlier long-post draft](docs/GATED_CANDIDATE_CU_20261102.md) is preserved but must not resume; all pending work retained uncommitted |
| What is documented, inferred or assumed? | Source matrices in those guides; [materials](docs/materials_and_provenance.md) |
| What is the corrected physical construction? | [Geometry specification](GEOMETRY_SOURCE_OF_TRUTH_SPEC.md), protected geometry manifest and wire routes |
| What is actually solved in 3D? | [Corrected solid-only thermal work](CORRECTED_GEOMETRY_COUPLED_THERMAL_WORK_ORDER.md), archived Elmer evidence |
| Why do reduced and corrected 3D temperatures differ? | [Matched audit](docs/MATCHED_SOLID_MODEL_DIAGNOSTIC_20261031.md) and [geometry-only nonlocal diagnostic](docs/NONLOCAL_PORT_NETWORK_20261031.md): 8.413 K predicted warming, 0.782 K residual; unresolved side-port sensitivity and ceramic spreading |
| Can the seven-port plate fixture isolate spreading? | [Native interface/admissibility audit](docs/PASSIVE_PLATE_PORT_AUDIT_20261031.md): stopped before solves; missing cut conditions and incompatible side/hot-foot traces; no causal heat attribution |
| Is there an independent native gas PDE baseline? | [Isolated cap/native gas control](docs/ISOLATED_CAP_AND_NATIVE_GAS_20261101.md): accepted SI derivative, audited connected native void, one 228,710-tet Elmer gas-only solve; **32.6274% raw balance fails 1%**. Analytic walls; no new device temperature or qualified gas budget |
| Why do raw gas flux and conservative reactions differ? | [Frozen-field forensic audit](docs/NATIVE_GAS_FLUX_FORENSICS_20261101.md): exact interior normal-flux jumps explain the net imbalance; shared-node splitting only redistributes local budgets. No new solve or cleared raw gate |
| What happened to the earlier bad STEP files? | [Original source-unit audit](docs/NATIVE_GAS_DOMAIN_AUDIT_20261101.md) and [quarantined first correction](docs/UNIT_CORRECT_CAP_AND_NATIVE_GAS_20261101.md) preserve both errors exactly; neither is used as current gas geometry |
| What must future development preserve? | [Current contract](AGENTS.md), sealed numerical evidence and original historical PDFs; continuously improve the live Rev3 |

## Current capabilities and their scope

| Implementation | Space / physics | Qualification limits |
| --- | --- | --- |
| `integrated_reference` + `g1_constant` | Five temperatures; three conservative TEC stages, attach, Cu/Au wires, sink, die heating and reservoir exchange | Constant verification properties; 63-point historical baseline |
| `zhang2025_analog` | Piecewise-integrated affine-temperature P/N legs | Opt-in research analog; high-current curvature omitted; historical 49 accepted / 14 rejected |
| **`zhang2025_nonlinear`** | Direct bounded nonlinear 1D P/N profiles, analytic banded Newton solve and exact-key cache; same five-node package | New opt-in option; 50 accepted / 13 rejected in the old reservoir scenarios |
| **`corrected_exchange`** | Gray radiosity and pressure-dependent gas chord network; corrected cap/window dimensions with an explicitly filled stepped core | Preliminary proxy visibility, not every native 88-leg/pin/wire surface; 52 accepted / 11 rejected when coupled to the nonlinear package |
| Archived corrected Elmer | Genuine coupled 3D solid Peltier/Joule/Fourier fields, 88 legs, header, explicit joints and die | No coupled solids/gas/radiation package field; historical raw bath/interface failures remain unresolved; separate gas-only control above is unqualified |

A result that conserves heat is not automatically an accurate device prediction.
The 300–390 K P/N continuation, contacts, emissivities, gas accommodation, core
closure and thermal reservoir conditions are engineering assumptions. The VIGO
housing drawing and TEC Microsystems reference do not identify a verified OEM
assembly. No optical transmission or detector carrier/noise model is solved.

## Run the current model

Use the existing pinned Docker environment; no installation or new session is
needed. It stays within four CPUs and the 12 GiB maximum. Use **new output
locations**, never sealed archives or previous versioned result folders.

```bash
# Existing baseline, or replace material with zhang2025_analog
./fem/run.sh python -m tecooledmct.integrated_reference   --material g1_constant --out outputs/reference-replay/baseline

# Direct nonlinear transport with the old effective reservoir exchange
./fem/run.sh python -m tecooledmct.integrated_reference   --material zhang2025_nonlinear --out outputs/reference-replay/nonlinear

# Build three bounded ray levels and independently audit native source faces
./fem/run.sh python -m tecooledmct.corrected_exchange   --out outputs/reference-replay/exchange

# Couple the preliminary closed proxy operator to the five-node package
./fem/run.sh python -m tecooledmct.integrated_reference   --material zhang2025_nonlinear   --exchange outputs/reference-replay/exchange/operator_65536.json   --out outputs/reference-replay/enclosed
./fem/run.sh python -m tecooledmct.integrated_reference_figures   --from-dir outputs/reference-replay/enclosed
```

`summary.json` records temperatures, stage/path budgets, electrical power,
provenance and full rejected-candidate diagnostics. `sweep.csv` contains accepted
points only; plots preserve failed intervals as gaps. Discrete grid minima are
not qualified continuous optima. The operator also records native face audits,
raw view factors, reciprocal closure corrections and mean geometric chords.

## Current evidence

New versioned results: [nonlinear transport and exchange](data/nonlinear_exchange_20261030).
At the measured-domain 0.7 A leg test, nonlinear32 vs independent BVP64 voltage
error is 0.00570%, compared with about 6.48% for the affine approximation.
At nominal 300 K, 0.15 A and 2 mW die heating, the coupled **proxy** predicts
232.209 K die temperature and 1.15193 V terminal voltage. These are reduced
synthetic-device predictions, not measured or 3D enclosed-package temperatures.

![Reduced nonlinear/proxy scenario sweep; failed intervals remain gaps](data/nonlinear_exchange_20261030/enclosed_scenarios/die_temperature_vs_current.png)

At fixed test temperatures, increasing rays per surface from 16,384 to 65,536
changes die gas heat by 0.88% and radiation by 0.14%. The largest view-factor
balancing correction is still 0.0404 absolute at the last level. This is a
preliminary operator, without a native-cavity accuracy or statistical error claim.

## Verify

```bash
./fem/run.sh python -m tecooledmct.nonlinear_tec_study   --out outputs/reference-replay/transport-checks
./fem/run.sh python -m pytest -q tests/test_nonlinear_tec.py   tests/test_corrected_exchange.py tests/test_graded_tec.py   tests/test_corrected_enclosure.py tests/test_integrated_reference.py
./fem/run.sh env TE_FEM_SMOKE=1 pytest -q --ignore=outputs
./fem/run.sh python fem/archive_bath_spatial_device.py --verify
./fem/run.sh python -m tecooledmct.cli --quick --out outputs/reference-replay/legacy-cli
./fem/run.sh python -m tecooledmct.geometry_demo --out outputs/reference-replay/legacy-geometry
```

Host-only development can use `python -m pip install -e '.[dev]'` and `pytest -q`;
native Gmsh and actual Elmer smoke require the existing FEM image. No new large
FEM production solve is needed for these reduced-model commands.

## Historical implementations and preserved reports

The original four-node `model.py`/`cli.py`, geometry sensitivity and pellet-FVM
work remain compatible demonstrations; they use different assumptions and some
OEM-anchored effective coefficients. They are not the current corrected package.
See [original physics](docs/physics_and_sources.md), [geometry study](docs/geometry_sensitivity.md),
[G1](docs/PHASE1_G1_RESULT.md), [G2a](docs/PHASE1_G2A_RESULT.md),
[G2b](docs/PHASE1_G2B_TWO_TERMINAL_RESULT.md), [G2c](docs/PHASE1_G2C_RESULT.md),
[G2d](docs/PHASE1_G2D_RESULT.md), [G3a](docs/PHASE1_G3A_RESULT.md) and
[G3b](docs/PHASE1_G3B_RESULT.md) for their original scope. Older G3b enclosure
geometry is not a source for the corrected operator.

The single master linked first is updated in place. Its original 15-page bytes
and Rev2 remain immutable historical evidence; they are not parallel current
scientific reports. See the internal [master build/integrity guide](docs/MASTER_REPORT_REPRODUCIBILITY.md). Raw bath <1% and cold interface <5% are
still requirements for a future numerical-release claim. Neither conservative
reduced budgets nor stable temperatures replace those criteria. See
[the preserved spatial-bath result](docs/BATH_SPATIAL_FLUX_AND_COMBINED_QUALIFICATION.md).

The [contract's ordered science milestones](AGENTS.md#ordered-next-science-milestones)
govern continuation. The bounded identifiability study is complete: geometry
and reciprocal material changes are transport-equivalent, with no identified
commercial dimensions or grade. The subsequently authorized finite-sink study is
also complete, preserving all old baseline outcomes and predecessor report bytes.
The [physical-input qualification program](docs/PHYSICAL_INPUT_QUALIFICATION_20261101.md)
now ranks independent dimensions/same-grade transport and matched calorimetry
requests, with a source/domain matrix and 102 bounded local reduced calls.
At a matched 200 K target / 2 K/W sink, equal-fraction power leverage is S, k,
then rho; this is conditional sensitivity, not empirical uncertainty or grade
identification. Native gas/nonlocal/contact impacts remain unqualified or NOT RUN.
The same 38-page Rev3 is unchanged; no next experiment/acquisition is authorized.
The subsequently authorized separate source-inspired candidate now reaches its
[registered STOP](docs/SOURCE_CONSTRAINED_TEC_CANDIDATE_20261101.md): a geometrically
consistent29/11/4,.5mm prototype substantially improves the intrinsic comparison,
but bounded calibration fails full loaded agreement. No fitted property enters
the original reference; Cu/contact/ceramic electrothermal behavior is unqualified.
Its proposed Cu electrical fixture is NOT RUN; no follow-on campaign is authorized.
The geometry-derived route/support comparison remains
conditional and its one plate-fixture follow-up stopped at the seven-port
admissibility gate. The later isolated writer/SI reader qualified a separate
cap derivative and actual native gas void, preserving both earlier unit failures.
The [gas-only control](docs/ISOLATED_CAP_AND_NATIVE_GAS_20261101.md) remains
**STOPPED: 32.6274% raw flux mismatch fails 1%**; its
[frozen-field forensics](docs/NATIVE_GAS_FLUX_FORENSICS_20261101.md) identify the
P1 normal-flux jumps without qualifying a gas budget. The proposed affine control
is neither authorized nor run. Further solid fitting/refinement is outside its stops.
Then native-surface visibility/exchange with actual
interleg/pin/wire geometry and paired mechanisms/contact/bypass/grade/
reservoir scenarios in the bounded nonlinear package. A later 3D qualification
experiment needs an engineering justification and all original gates; no OEM
calibration or large remesh is the next required milestone. Keep this README and
existing technical guides coherent with each increment; promote verified,
substantive scientific results into the same Rev3 master when warranted.
All development stays in the existing VPS sim:0.0 Codex session; LSDDTS is outside scope.
