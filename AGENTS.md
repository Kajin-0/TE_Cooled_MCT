# Agent continuation / engineering contract

## Mission
Build a truthful, testable multiphysics model of a three-stage TEC-cooled HgCdTe detector in a nine-pin TO-66 package. Physics verification, reproducibility, parameter provenance and quantified limits outrank visual fidelity.

## Read first
README.md; docs/physics_and_sources.md; docs/simulation_roadmap.md; docs/rev6_cad_audit.md.

## Current baseline
- tecooledmct/model.py: four-node steady-state thermal/electrical solver.
- tecooledmct/experiments.py: gas comparisons, uncertainty, transient dynamics.
- tecooledmct/cli.py: parameter sweeps, figures, JSON reports.
- tests/test_model.py: conservation, anchor, input and trend checks.
- geometry/revision6/engineering_assumptions.json: original visual-CAD specifications. **Not** validated solver geometry.

Manufacturer reference: TEC Microsystems 3MC04-044-05 (2019), hot 6.4 × 6.4 mm; cold 2.4 × 2.4 mm; height 3.8 ± 0.15 mm; 44 couples; ΔTmax ~113 K; Qmax ~0.5 W; AC resistance ~2.9 Ω. All maximum values occur at different conditions. Per-stage 28/12/4 allocation and intermediate geometry are **inferred**.

## Mandatory rules
1. Distinguish manufacturer-documented, fitted, assumed, and measured inputs. Track units, sources, temperature/pressure domain and uncertainty.
2. Preserve SI units internally. Conserve energy at each stage; Qh-Qc=I*V.
3. Fitting two manufacturer limits is **not** validation of loaded/temperature-dependent curves. Digitize additional data and reserve holdouts.
4. Do not claim Krypton or mixtures are optimal for *production* from thermal conductivity alone; purity, outgassing, sealing, spectral loss and reliability matter.
5. Monte Carlo percentile ranges from chosen priors are not empirical confidence intervals.
6. Do not use the visual Revision 6 STEP as a simulation mesh without repaired gaps/contact definitions and verified stage connectivity.
7. Never add exposed external TEC jumpers. The cooler has two heavier tinned leads and separate detector/thermistor bonds; interstage conductors belong inside validated on-ceramic metallization.
8. Run pytest -q and python -m tecooledmct.cli --quick --out outputs/check for each change.
9. Favor open NumPy/SciPy, and Gmsh/Elmer/FEniCSx/OpenFOAM where justified.
10. Report convergence, assumptions, and failure modes; do not claim accuracy from visual plausibility.

## Next checkpoints
- Manufacturer curve digitization (Q-I-ΔT, V-I), joint fit and holdout.
- True multi-surface radiation plus aperture shielding and cold-baffle conduction.
- Temperature-dependent MCT R(T,V), optical absorption and real thermistor calibration.
- Real package gas species/pressure model, kinetic regimes, and mixture transport.
- FEM-ready geometry, electrical connectivity, contact mesh and BC.
- Experimental hot/cold temperature and current/voltage correlation.
