# Pellet transport screen at frozen source-pad temperatures

## Preregistered question and scope

For the source 29/11/4-couple TEC at 0.4 A, 300 K reservoir, 100 Pa Kr and 2 mW imposed die heat, assess the local effect of a common P/N pellet height or cross-section change on axial-leg heat and terminal electrical input. A second comparison solves current against the same **0.595668034961 W** reference terminal input, within a preregistered 0.25--0.55 A bracket. These are research scenarios, not allowable current ratings, experimental hardware measurements or a global optimum.

The independent source 0.4 A state has top-ceramic 218.806728 K and mounting proxy 218.900024 K. **All 88 individual saved hot/cold pad temperatures and non-leg series resistances are frozen** here. Neither is re-solved for any changed pellet. Reported cooling rates at those fixed boundary temperatures are not new detector/top-ceramic temperature predictions and do not establish a coupled-device thermal balance.

| Factor | Registered hypotheses | Source/CAD interpretation |
|---|---|---|
| Common axial height | 0.40, 0.50, 0.60 mm at 0.40 mm square | Positive transport-only lengths; all changed heights break source landing/foil z alignment. |
| Common cross-section | 0.36, 0.40, 0.44 mm square at 0.50 mm height | 0.1296, 0.1600, 0.1936 mm². At 0.58 mm pitch nominal edge gaps are 0.22, 0.18, 0.14 mm; 0.44 mm footprint exceeds nominal 0.40 mm lands and no fully covered interface is shown. |
| Current / power | 0.4 A fixed; solve for fixed 0.595668034961 W in [0.25,0.55] A | Axial temperature profiles are recomputed; boundary temperatures and parasitic series resistance remain fixed. Bracket endpoints are modeled only, not inferred device ratings. |
| Stages | 29/11/4 couples; 58/22/8 individual P/N legs | Stage split, polarity, source face tags and material models remain fixed. No optimization of allocation. |

## Parameter-dependency audit

| Parameter | Actual implementation / limited safe control | Required for a physical geometry variant |
|---|---|---|
| P/N area and length | `leg()` uses current density `I/A`, actual L and source temperature-dependent S, rho, k; endpoint powers are multiplied by A. V3.11 uses common A=0.16 mm², L=0.5 mm for all 88. At fixed source pad temperatures, A/L can be perturbed *only as a transport hypothesis*. | Rebuild every leg and all 176 solder/joint footprints and 352 interfaces; refit and verify all source pad contacts. |
| Stage allocation and polarity | 29/11/4 derived from native 88-leg series ordering and face ownership; P and N are distinct source specimens. | Reassign native legs, routes, pads, circuit graph and 3D source mesh; no stage-only geometry here. |
| Ceramics and pads | Four source finite-element plates, 11,791 TET4, native 95 pad load/temperature responses; ceramic k=30 W/(m K) proxy. | Regenerate plate/face ownership and spatial thermal operators after any pad/leg displacement or footprint change. |
| Solder and interfaces | 35 µm nominal SnSb, 0.16 mm² area; 176 joint contributions and 352 electrical contacts; thermal jumps/contact Peltier omitted. Fixed resistance in this screen. | Revise footprint, resistance, heat deposition, possible spreading and real joining/clearances. |
| Copper and external leads | Source formed Cu 58/80/88 multiport, including three-foot thermal return and frozen-temperature electrical resistance; source Cu leads pin1/9. Net88 historical 3D raw electrical qualification remains FAIL/STOP. | Redesign bridge steps, feet, bends, insulation, access and electrical/thermal contact after dimensional changes; do not claim this reduced network is a qualified 3D metal field. |
| Gas/radiation | Kr100 Pa: four effective 3 mm gap branches, source-footprint ring areas and gray reservoir; source-pad-weighted heat mapping. Frozen at archived case only. | Recompute actual void/exposed side areas, narrow interleg gaps, view/occlusion and corresponding gas-regime closure; no native gas PDE is solved here. |
| Hot mount and detector load | 300 K reservoir, source-derived conditional sink and leads; die load fixed 2 mW. | Re-solve whole coupled thermal/electrical system at the new source geometry and same applied boundary. |

Source transport: separate Zhang research P/N samples, source-digitized 40--300 K, with active 180--390 K and unmeasured quarter-tangent continuation above 300 K. P/N sign conventions, Peltier/Fourier/Thomson/Joule terms and per-leg `Qh-Qc=IV` follow the unchanged 32-interval nonlinear source. Frozen current return and solder terms are not copper-field validation. No MCT electrical or optical physics is invoked.

Before analysis, `registration.json` fixes five cases, bounds, original data/code hashes, per-case 110 s wall, 4 CPUs/8 GiB, strict <1e-9 W leg/stage energy gates, <=1e-6 W matched-power error and <=14 bracket evaluations; source seal is written before the first solve. A candidate exceeding the limits or losing a bracket/domain is STOP, with diagnostics. The original independent V3.11 full-system audit remains archived; new independent checks re-sum every saved leg/stage and `P=IV` but **cannot assert full-package heat closure** at artificially frozen boundaries. No whole-device solve or geometry promotion is authorized within this screen. Prior V3.6 and V3.8 operating/mounting studies differ in assumptions and are context only, not new matched-power runs.

## Results

Five scenarios were attempted and independently accepted: **ten frozen-boundary states**, not ten coupled-device states. The source baseline replays within 6.77e-16 in recorded units; maximum independent leg and stage energy residuals are 1.81e-13 W and 1.025e-12 W. No whole-device solve, new device temperature or geometry-consistent candidate was run.

| Case | Width (mm) | Height (mm) | g | Fixed 0.4 A voltage (V) | Fixed 0.4 A power (W) | Fixed 0.4 A Qc3 (mW) | Matched current (A) | Matched voltage (V) | Matched Qc3 (mW) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.40 | 0.50 | 1.0000 | 1.489170 | 0.595668 | 4.9079 | 0.400000 | 1.489170 | 4.9079 |
| length_040 | 0.40 | 0.40 | 1.2500 | 1.299146 | 0.519658 | -18.7994 | 0.435432 | 1.367993 | -9.8233 |
| length_060 | 0.40 | 0.60 | 0.8333 | 1.680372 | 0.672149 | 19.8895 | 0.372366 | 1.599683 | 13.4403 |
| width_036 | 0.36 | 0.50 | 0.8100 | 1.713557 | 0.685423 | 21.9059 | 0.368174 | 1.617899 | 14.5311 |
| width_044 | 0.44 | 0.50 | 1.2100 | 1.324215 | 0.529686 | -14.9376 | 0.430163 | 1.384749 | -7.3376 |

All matched rows are actual bracketed axial solves at 0.595668 W within 1 µW, not interpolated temperatures. Negative Qc means net heat into the held cold boundary; it is not a balanced refrigerator at the archived load. At matched power, nominal Qc3 = 4.907928 mW; 0.60 mm length gives 13.440302 mW (+8.532374 mW), and 0.36 mm width gives 14.531062 mW (+9.623134 mW). The latter uses 0.368174 A instead of 0.400000 A; its pad/solder footprint remains unresolved. This is the best **sampled frozen-boundary heat-lift tradeoff**, not a prediction of a colder physical package.

Matched-power dQc3/dln(g) is -57.375 mW for length endpoints and -54.489 mW for width endpoints; normalized to nominal Qc3, the dimensionless finite-span sensitivities are -11.690 and -11.102. These are different-span secants, not local derivatives, confidence intervals, or device-temperature sensitivities.

Fixed reference means: hot ceramic 303.762295 K, top ceramic 218.806728 K and detector mount 218.900024 K. These are **inputs**, not predicted responses for changed pellets. Frozen auxiliary series resistance is 0.046167509 Ω; it includes the known net88 middle-contact bookkeeping caveat. Current changes do not update foil/joint temperatures in this proxy.

### Matched-power stage budgets

| Case | Stage | Qc (mW) | Qh (mW) | P/N voltage (V) |
|---|---:|---:|---:|---:|
| baseline | 1 | 289.4526 | 711.3290 | 1.054691 |
| baseline | 2 | 136.3874 | 260.6820 | 0.310737 |
| baseline | 3 | 4.9079 | 47.0182 | 0.105276 |
| length_040 | 1 | 201.5508 | 623.1286 | 0.968183 |
| length_040 | 2 | 117.5709 | 240.7821 | 0.282963 |
| length_040 | 3 | -9.8233 | 32.3023 | 0.096744 |
| length_060 | 1 | 335.0570 | 757.1136 | 1.133444 |
| length_060 | 2 | 144.6651 | 269.7853 | 0.336014 |
| length_060 | 3 | 13.4403 | 55.5302 | 0.113034 |
| width_036 | 1 | 340.3940 | 762.4740 | 1.146415 |
| width_036 | 2 | 145.4801 | 270.7240 | 0.340176 |
| width_036 | 3 | 14.5311 | 56.6172 | 0.114310 |
| width_044 | 1 | 216.9127 | 638.5397 | 0.980156 |
| width_044 | 2 | 121.0076 | 244.3817 | 0.286808 |
| width_044 | 3 | -7.3376 | 34.7865 | 0.097926 |

Frozen pad temperatures make stage-to-stage heat gaps intentionally unbalanced when geometry changes; individual `Qh-Qc=IV` checks do not close the externally constrained package. The archived source case passes its own prior full-system audit.

### Selected source P/N properties

Exact digitized source-law values, not matched-grade measurements. S is µV/K, resistivity is µΩ m and k is W/(m K).

| T (K) | S(P) | rho(P) | k(P) | S(N) | rho(N) | k(N) |
|---:|---:|---:|---:|---:|---:|---:|
| 220 | 179.3214 | 7.0733 | 1.33216 | -156.2313 | 4.9321 | 1.65388 |
| 260 | 199.2199 | 9.3511 | 1.19408 | -174.5683 | 6.2326 | 1.50673 |
| 300 | 212.4625 | 12.0806 | 1.09901 | -189.5752 | 7.5433 | 1.39923 |

All five matched cases use the assumed >300 K continuation in 58 hot-stage legs. The 88 per-leg heat/voltage outputs and extrema are retained. Source curves, guards and source fields are unchanged.

## Geometry promotion and next experiment

All four changed-size variants are **NOT geometry-consistent**, even where pitch spacing is positive. Height changes displace physical top contacts, foil bends and stack envelope; width changes alter overlapping pad/solder/interface areas, current crowding and exposed gas gaps. No physically consistent 2--4-case promotion or new detector-temperature result follows. The source full-system reference took about 160 s, exceeding the new 120 s per-solve cap; no full-system run was attempted.

Next: build a separately versioned, geometry-consistent 0.60 mm-height candidate with aligned solder, foil feet, pad contacts and gas areas, then attempt a bounded matched-power coupled solve with independent stage/global balance. The 0.36 mm-width candidate requires its own pad/solder footprint study; neither is a proven optimum or manufacturable design. The first figure-only invocation omitted the project import path and stopped; the corrected `python -m` invocation used the same saved results, with no numerical scenario rerun.

Reproduce from the sealed registration and source hashes, per-case result/independent-audit records and source-reproduction manifest; no original archived source or PDF was replaced.

## Reproduction and verification

The saved case writer refuses to overwrite an existing case directory; reproduce numerical cases in an isolated copy of the repository and preserve the registered inputs and source hashes. The successful bounded regression used the recovered, separately identified runtime (not the missing original image):

```sh
docker run --rm --network none --cpus=2 --memory=4g \
  -e GIT_CONFIG_COUNT=1 -e GIT_CONFIG_KEY_0=safe.directory \
  -e GIT_CONFIG_VALUE_0=/workspace -v "$PWD:/workspace" -w /workspace \
  tecooledmct-fem:26.2.1-recovered-20261105 python -m pytest -q \
  tests/test_tec_pellet_screen_20261110.py tests/test_v3_11_backfill_source.py \
  tests/test_v3_6_operating_envelope.py tests/test_v3_8_transport_sink_transfer.py
/home/User/venvs/plotting/bin/python -B fem/archive_bath_spatial_device.py --verify
/home/User/venvs/plotting/bin/python scripts/tec_pellet_manifest_20261110.py
```

The successful run passed 22 tests. An initial repeated test invocation used a nonexistent V3.8 filename and executed no tests; a second invocation yielded 21 passes and one Git ownership setup failure, preserved in `targeted_regression_final.log.gz`. Passing `safe.directory` only to the disposable container as shown fixed that environment issue; no test or source criterion changed. The archival verifier passed with original raw failures preserved. Report-only builds were run twice in separate staging directories using `scripts/tec_pellet_report_build_20261110.py --out <new-directory>`; the resulting 44-page PDFs and rendered pages were byte-identical. All page contact sheets and the two added pages were visually inspected. No new 3D or package solve was performed.
