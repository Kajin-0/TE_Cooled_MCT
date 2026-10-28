# Geometry-sensitive pellet simulation (Phase 1a)

## Direct answer to the methodology question

The original Phase 0 **was not a geometry-resolved multiphysics solver**. It uses fixed effective stage coefficients and a four-node energy network. It was insufficient to answer "what changes if I make the P/N legs thinner?" without modifying transport.

This update adds two distinct numerical tools:

- **Geometry-parameterized full three-stage TEC network.** Each stage can independently vary leg length L and cross-section A. The solver recalculates electrical resistance and thermal conductance from R~L/A and K~A/L; Seebeck coefficient is held constant, assuming unchanged materials and couple count. Its 4 thermal nodes are still lumped—not spatial FEM.
- **Actual 3D voxel finite-volume (FVM) solver of a single pellet.** It numerically solves the diffusion/Joule PDE on the pellet's physical dimensions and explicit sidewalls. The boundary temperatures are supplied separately by the TEC network. Peltier terms are computed at the pellet junctions after the spatial temperature solve. This is not full 3D coupled thermoelectric FEM of the detector assembly. The field solver verifies the assumed local pellet physics and can resolve geometry/sidewall changes missed by an algebraic-only calculation.

The **same TECGeometry parameter** also drives the separate CadQuery reference STEP generator. However, neither the STEP nor the complete 3D TO-66 geometry is ingested as a mesh by the network or FVM solver.

## Study definition

Baseline from TEC Microsystems 3MC04-044-05 OEM external envelope, **inferred** 28/12/4 P/N couple allocations, nominal [1.07, 0.82, 0.64] mm leg heights and 0.4 mm square legs. Phase 0 effective properties are calibrated to two OEM limit points and remain unvalidated for geometric optimization.

At fixed 0.65 A drive, 300 K ambient, Ar at 1 atm, original approximate cap loads, MCT 100 ohm @ 0.5 V:

| All-stage leg height relative to baseline | Detector temperature (K) | TEC input at 0.65 A (W) | Minimum TEC input at target 200 K (W) |
| --- | ---: | ---: | ---: |
| 0.70× | 206.85 | 1.221 | 1.695 |
| 1.00× | 195.49 | 1.620 | 1.232 |
| 1.30× | 192.49 | 1.975 | 0.998 |

The target comparison optimizes current over **0.2 to 1.05 A**, assuming a unimodal cold-temperature-versus-current curve on that interval. This is a *conditional* power ranking, not experimentally verified COP. Real parasitics, mechanical clearance, reliability and manufacturing limits have not been reoptimized.

**Physical reason:** thinner legs reduce R and Joule heating, but also increase thermal back-conduction K. For a fixed 200 K target, higher drive can be required; therefore lower fixed-current power is *not* synonymous with higher cooling efficiency.

## Spatial FVM equations

Each pellet uses a cell-centered Cartesian 3D mesh and solves

\[
-\nabla\cdot(k\nabla T)=\rho_e(I/A)^2
\]

with fixed T at end faces, effective gas heat transfer on four sidewalls, and volumetric Joule heating. Contact Peltier flux is applied analytically at junctions after solving; no spatial E-field or Seebeck coefficient gradient is yet solved. Stage-effective resistivity, conductivity and Seebeck are inherited from Phase 0's OEM-limit calibration.

Calculated energy-balance errors for illustrative 0.7×, 1.0× and 1.3× cases were below 3×10⁻¹⁴ W per pellet (numerical closure, **not predictive accuracy**). Adiabatic-wall FVM matches the corresponding lumped analytic limit, and a mesh refinement test verifies local heat extraction sensitivity below 10 µW per pellet.

## Important omissions

- OEM does not document exact 28/12/4 allocation, Seebeck, k(T) or sigma(T).
- Stage-scale FEM geometry, temperature-dependent p- and n-type transport, electrical continuity, copper pad/solder contacts and wire bonds not solved in 3D.
- The gas cavity is not meshed or solved by CFD; sidewall h is imposed as a boundary condition.
- The backfill load model in the network is **not recomputed from changing absolute stack height**, a potentially material cross-effect.
- Fabrication constraints and geometry clearance beyond the simple top-cap collision check are not optimized.
- A fitted baseline against two limiting points cannot substantiate quantitative accuracy of the geometry tradeoff.

## How to run

\`\`\`bash
python -m pip install -e '.[dev]'
pytest -q
python -m tecooledmct.geometry_demo --out outputs/pellet-study
python geometry/reference_cad.py --pellet-scale 0.7 --out outputs/CAD_70pct  # optional cadquery
python geometry/reference_cad.py --pellet-scale 1.3 --out outputs/CAD_130pct # optional cadquery
\`\`\`

See generated PNG/CSV/JSON; \`geometry_vs_electrical_power.png\` is the primary comparison.

## Next required for full CAD-geometry multiphysics

A genuine coupled 3D model should parse contact-clean STEP, tetrahedralize all electrical/thermal domains and solve (temperature-dependent) charge conservation and energy conservation together with Peltier/Seebeck/Joule, 3D conduction, interfacial conductances, multi-surface radiation and cavity gas. Gmsh + Elmer/FEniCSx or COMSOL are appropriate candidate stacks. Verify mesh convergence and withheld OEM data. Use a measured device to validate prediction of absolute detector temperature.

**Status: reproducible geometry-based sensitivity *plus a local spatial pellet PDE*, not a validated 3D full-package digital twin.**
