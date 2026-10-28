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

## Phase 1a additions
- Read docs/geometry_sensitivity.md and tecooledmct/geometry_sweep.py and pellet_fvm.py.
- Do not say that changing a STEP assembly automatically runs a multiphysics analysis.
- geometry_sweep reruns a lumped network with dimensional R and K changes; pellet_fvm spatially solves one leg only.
- Peltier and Seebeck effects are still reduced to effective junction terms; no full 3D electrical field across the package.
- Run `pytest -q` and `python -m tecooledmct.geometry_demo --out outputs/pellet-study`.
- When reporting efficiency, compare *minimum input power at a fixed detector target temperature*, not only electrical power at a fixed current.
- Treat 28/12/4 stage pair split and effective R/K/S as uncertain.

## Phase 1b source-backed materials
- See docs/materials_and_provenance.md, tecooledmct/materials.py, and material_transport.py.
- OEM-calibrated and literature-derived P/N profiles are separate. The default solver MUST remain unchanged unless requested.
- Sourced properties carry material grade, measured temperature, source URI, and uncertainty status.
- Bi-Te hot-extruded OEM composition and S(T),sigma(T),k(T) are unpublished; literature example P/N values are not product claims.
- Kovar header composition, purity and actual plating need verification per actual package; Sn95Sb5 is only a proxy for unspecified OEM Sn-Sb solder.
- Bulk alumina, Kovar, solder and gold do NOT yet determine the main four-node model's stage temperatures; 1-D resistance estimates are diagnostic only.
- Run pytest -q and source-backed material profile tests; keep baseline regression passing.

## Current scope priority, 2026-10-28
Do NOT modify, invoke, import or integrate Kajin-0/mct-refactor/LSDDTS. Treat old coupling contract as dormant speculative documentation only. Build and validate Elmer/Gmsh TEC/package FEM first. Model MCT with sourced thermal properties and optional simple bias-dependent thermal load; no device carrier-transport PDE. OpenFOAM should be reserved for relevant gas convection/CHT cases after a conduction-only baseline and Rayleigh/Knudsen screening. The later G1/G2a/G2b sections record implemented solid thermoelectric FEM; package CFD remains unimplemented.

## Verified G1 checkpoint, 2026-10-28

- Read docs/PHASE1_G1_RESULT.md and docs/FEM_G1_REPRODUCIBILITY.md first.
- Genuine Gmsh/OpenCascade tetrahedral P/N + Cu + alumina coupled FEM is in
  tecooledmct/fem_g1.py, fem_g1_run.py and fem_g1_post.py. It invokes Elmer's
  actual ThermoElectricSolver for both T and phi; do not replace it with HeatSolve
  or a prescribed reduced-order temperature field.
- Isolated headless installation: fem/bootstrap.sh; runtime: fem/run.sh. Elmer
  release 26.2.1 source is pinned at a19504ac53ec222e3355e182b08f2ff280c2203a;
  Gmsh 4.13.1. Host Ubuntu 25.10 sudo needs a password; no PPA was installed.
- Source and project work remain in /home/User/TE_Cooled_MCT, using the existing
  sim session. Do not create another session or alter model/settings.
- Run `./fem/run.sh env TE_FEM_SMOKE=1 pytest -q` (21 tests at this checkpoint),
  the existing CLI quick check, geometry_demo, and the full FEM runner for physics
  changes. No solver means optional smoke is skipped; never fabricate results.
- Full benchmark: `./fem/run.sh python -m tecooledmct.fem_g1_run --out outputs/fem-g1`.
  `--postprocess-only` recomputes diagnostics from existing actual fields; it does
  not run the PDE again. Preserve the distinction in validation reports.
- Positive I enters N hot pad, crosses cold bridge and returns via P hot pad;
  300 K bottom bath, actual 2 mW top heat flux in loaded sweep. All contacts ideal.
  Alumina uses sigma=1e-12 S/m; 100-fold lower conductivity sensitivity passes.
- 666/1441/4223 nodes, 2029/5094/17046 tets; +0.3 A finest Tc=258.757514 K;
  finest Tc change 0.008813 K. Constants are mixed literature verification inputs,
  not manufacturer-specific or physical curves valid from 250 to 439 K.
- Distinguish conservative terminal reactions, interior cut currents and raw
  element-gradient terminal fluxes. The last still have corner discretization
  errors (~8%/5.4% at +0.3 A); do not claim local flux convergence from global
  balance. Fine interior driven-cut error is <0.04%, bath-gradient energy error
  <0.17%, weak global energy/current checks pass. Zero current uses an absolute
  section-current gate of 1 microamp, since percentage of zero is undefined.
- Representative actual meshes, plots, fields, logs, lock versions and checksums
  are tracked under fem/results/g1_20261028; complete raw run is outputs/fem-g1.
- G2 is next: verified 88-leg series netlist, three stages, realistic material
  curves and contact sensitivity, then withheld OEM curves. Stage split 28/12/4
  remains inferred. Full TO-66 package, MCT die and gas/radiation are later gates.
- Preserve all Phase 0/1a/1b behavior and tests; no changes to other repositories.

## G2a multi-couple checkpoint

- Read docs/PHASE1_G2A_RESULT.md and docs/G2A_REPRODUCIBILITY.md. G1 files and
  all 128 published evidence hashes are unchanged; fem_g2a_run.g1_integrity checks
  them. Never rewrite G1 source/evidence to make G2 pass.
- New modules: fem_g2a.py (parametric snake, graph/geometry/mesh audit, SIF),
  fem_g2a_post.py (actual-field component currents/heat/Joule and weak residuals),
  fem_g2a_run.py (real coupled runs and 29 gates). The existing pinned image is
  sufficient; do not reinstall or change shared Docker/bootstrap settings.
- Four couples: 8 legs, 7 alternating hot/cold Cu links, 2 external hot terminal
  pads and 2 alumina plates. Actual mesh must prove a unique path with 17 conductor
  vertices and 16 edges, no illegal overlaps or point/edge shorts. Contacts ideal.
- Run `./fem/run.sh python -m tecooledmct.fem_g2a_run --out outputs/fem-g2a`
  and `./fem/run.sh env TE_FEM_SMOKE=1 pytest -q` (30 passed). Existing CLI and
  geometry_demo must also pass. Changing source during a run invalidates it.
- Actual fine run: 17,651 nodes, 74,552 tets; 300 K bath and 8 mW cold-face load.
  +0.15 A gives Tc=277.559043 K and V=79.480673 mV. Finest mean-T change
  0.003191 K = 0.01422% of lift; fine worst leg current <0.00089%, bridge <0.089%,
  direct bath energy mismatch <0.161%. Raw terminal-corner flux peaks remain
  unconverged; do not substitute them for conservative/interior-cut currents.
- `fem/archive_g2a.py` only accepts verified full runs with matching source and
  SIF/VTU hashes. Tracked evidence: fem/results/g2a_20261028; full raw outputs
  remain outputs/fem-g2a. Keep BCs and material assumptions explicit.
- G2b must first be a geometry/netlist/mesh feasibility proof, after the verified
  G2a commit. 28/12/4 is still inferred. No full-TEC nonlinear solution is claimed
  by generating 88 legs. G2c independent OEM/device calibration remains later.

## G2b geometry-only follow-up

- G2a passed and was committed/pushed first at f43d07835c5c58a336f661054b42023eeb5a50d5.
  Read docs/PHASE1_G2B_FEASIBILITY.md before continuing the full TEC.
- fem_g2b_geometry.py constructs 88 legs, 85 Cu bridges, six stage pads and four
  shared ceramic plates, with assumed 28/12/4 couples and 3.8 mm stack height.
- Actual 0.20 mm mesh: 14,666 nodes / 47,667 tets / 183 domains / 267 contacts.
  Graph, volumes, contacts and point/edge-short checks pass; ElmerGrid exits zero.
- This is THREE SEPARATE stage circuits with SIX internal feasibility ports.
  No module-level two-terminal interstage routing or coupled G2b solve exists.
  geometry_only.vtu has body IDs only; do not invent temperature/current fields.
- Reproduce with `./fem/run.sh python -m tecooledmct.fem_g2b_geometry`;
  combined `TE_FEM_SMOKE=1 pytest -q` passes 32 tests, including actual G1/G2a
  solver and G2b mesh. Published G1/G2a code/evidence are unchanged.
- Before G2b physics: define stage drives/interstage routes, real BCs, solve and
  verify current/energy/mesh convergence. Contacts, stage allocation, material
  curves and OEM/device holdouts remain missing. G2c stays deferred.


## G2b two-terminal coupled checkpoint, 2026-10-28

- Read docs/PHASE1_G2B_TWO_TERMINAL_RESULT.md and
  docs/G2B_COUPLED_REPRODUCIBILITY.md. This supersedes the geometry-only next-step
  status above without changing the original six-port generator or its meaning.
- fem_g2b_connected.py adds two separate assumed buried Cu routes and four
  alumina supports/collars. Cu is cut from dielectric before fragmentation.
  Preserve the distinction between inferred construction and verified OEM artwork.
  These supports/routes create thermal shunts that must remain in the PDE.
- The actual mesh has 189 material domains and a unique 181-vertex / 180-edge
  conductor path through all 88 legs, exactly two degree-one external terminals.
  Orthogonal CSG, OCC and actual tetrahedra agree on volumes/contact areas.
  fem_g2b_connectivity.py additionally proves face-connected tetrahedra inside
  every body, and one conductor and one thermal tetrahedron component. A shared
  body tag alone cannot prove continuity; reject point/edge-only connections.
- New fem_g2b_physics.py, fem_g2b_post.py and fem_g2b_run.py execute actual coupled
  Elmer ThermoElectricSolver and independently verify actual T/phi/E/J/q/Joule.
  Run ./fem/run_g2b.sh python -m tecooledmct.fem_g2b_run, then the supplemental
  connectivity command in the reproduction guide. This wrapper reuses the pinned
  image with four CPU / 12 GiB limits; original fem/run.sh remains unchanged.
- Three actual meshes culminate in 91,538 nodes / 384,121 tetrahedra / 183,076
  DOFs. With 300 K bottom bath and 2 mW actual top load, +0.1 A gives cold mean
  262.056237 K / +0.56829253 V; -0.1 A gives 356.989385 K / -0.66503709 V and
  positive input power. Intermediate ceramic temperatures are solved unknowns.
- All 30 full checks and 41 tests passed. Regress with
  ./fem/run.sh env TE_FEM_SMOKE=1 pytest -q plus existing CLI and geometry_demo.
  Original G1/G2a and six-port source/evidence hashes must remain unchanged.
  Do not rewrite protected checkpoints to make a new gate pass.
- Every leg, local bridge and insert has an interior current cut (175 total).
  Fine driven cuts pass <0.5%, direct bath energy <1%, cold mean/max mesh change
  <1% of lift and voltage change <1%. Raw terminal-gradient currents and corner
  peaks remain separate and are not claimed resolved. Zero drive uses 1 microamp
  absolute current tolerance. Ceramic sigma reduction is independently tested.
- Stage heat budgets use P1 nodal control volumes through intermediate plates,
  including relevant routing/ceramic portions. Their conservative transfers are
  not raw sharp-face gradients or a textbook leg-only stage decomposition.
- --reuse-mesh re-audits real mesh inputs. --resume reuses only actual completed
  cases after BC/status/SIF/VTU checks and fresh field verification. Loaded-positive
  explicitly aliases the identical final convergence execution, not another solve.
  Warm starts use hashed actual solution.result initial states and still run PDEs.
- The final nonlinear stopping tolerance is 1e-9, the declared convergence gate.
  Stronger completed early solves retain their original SIFs/source snapshots.
  A roundoff plateau and stopped duplicate are incomplete attempts, never successes.
  Keep the .source archival suffixes to prevent pytest collecting old snapshots.
- Archive only verified evidence using fem/archive_g2b_coupled.py; it checks source,
  mesh and actual SIF/VTU hashes. Tracked data is fem/results/g2b_two_terminal_20261028;
  raw runs remain outputs/fem-g2b-two-terminal and outputs/fem-g2b-connected.
- All contacts ideal; room-temperature literature constants, inferred 28/12/4
  stages and manufactured routing remain assumptions. G2c OEM calibration,
  temperature-dependent grade-matched curves, contact/solder validation and G3
  package/gas/radiation are later gates. No 113 K / 0.5 W fitted validation claim.
- Continue in the existing sim session; do not touch LSDDTS or unrelated projects.
