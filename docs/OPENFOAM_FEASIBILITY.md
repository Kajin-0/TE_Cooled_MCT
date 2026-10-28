# OpenFOAM feasibility for sealed TO-66 detector packages

STATUS: Engineering evaluation; no OpenFOAM case is currently implemented.

## Solver responsibilities
- Elmer ThermoElectricSolver: electrically and thermally coupled P/N Bi-Te, metals, ceramics, solder, MCT die and electrical contacts.
- OpenFOAM: optional inert-gas transport, gravity-driven natural circulation, conjugate solid/fluid heat transfer. Stock multi-region thermal solvers do NOT inherently implement Seebeck, Peltier and Thomson electrical transport.
- Foundation v13: modular foamMultiRun with separate fluid/solid regions; OpenCFD releases: chtMultiRegionFoam, chtMultiRegionSimpleFoam. Pick one distribution and pin exact version.

## Approximate Rayleigh screen, not CFD
Ra = g beta DeltaT L^3/(nu alpha), beta ~ 1/T. At 250 K average, 100 K difference, 1 atm and 3 mm gap, illustrative 250 K properties yield Ra ~616 for N2, ~733 for Ar, ~2578 for Kr. At 1 mm, these numbers shrink by 27. Gas properties and geometry have not been calibrated for the actual cap. Classical Ra ~1708 onset is for a specific ideal horizontal layer heated from below, not a universal TO-66 threshold.
Result: for small gaps, gas conduction may dominate; at larger gaps Krypton can have nonnegligible buoyancy despite its lower conductivity. Do not assume Kr is always optimal for the real package.

## Decision gate before CFD
1. Extract and validate an actual watertight internal gas volume from the CAD. Define orientations and operating pressures.
2. Solve conduction-only gas domain plus cap-to-stage radiation with Elmer/package model; measure baseline Qgas and Tc.
3. For representative gas/pressure/geometry, run an independent OpenFOAM laminar buoyant CHT comparison using matched boundary temperatures.
4. Compute effective Nu=Q_CFD/Q_conduction and resulting DeltaTc. Use proposed screen of |Nu-1|<0.02 and |DeltaTc|<0.2 K to justify omitting full CFD in similar conditions; these thresholds are engineering goals, not established evidence.
5. If convection matters, conservatively couple FEM surface temperatures and OpenFOAM heat flux and verify interface/global energy balances, grid convergence and iterative convergence.
6. Evaluate Knudsen number at low pressure. Standard continuum OpenFOAM without temperature-jump/free molecular treatment is not suitable when Kn is material.

## Sources
https://openfoam.org/release/13/
https://github.com/OpenFOAM/OpenFOAM-13/blob/master/applications/solvers/foamMultiRun/foamMultiRun.C
https://www.openfoam.com/documentation/user-guide/a-reference/a.1-standard-solvers
https://github.com/ElmerCSC/elmerfem/blob/devel/fem/src/modules/ThermoElectricSolver.F90
