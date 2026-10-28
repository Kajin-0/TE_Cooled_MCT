# Compact HgCdTe thermal domain (no electrical PDE)

Inputs: MCT Cd fraction x, die area/thickness, density, Cp(T,x), thermal conductivity k(T,x), die attach/contact thermal resistance, bonds, surface radiative/optical absorption and fixed electrical dissipation.
Use P_bias = V*I, or V²/R(T,V) where a measured or declared lumped R model is available; NEVER add both for the same power. Add thermally deposited optical absorbed power; incident photons are not automatically all heat.

Source-supported 2008 Heckman/Gonzalez/Guha data for Hg0.71Cd0.29Te:
T=90 K: k=2.41 W/m/K, Cp=130 J/kg/K.
T=148 K: k=1.61 W/m/K, Cp=146 J/kg/K.
T=298 K: k=0.973 W/m/K, Cp=176 J/kg/K, density=6830 kg/m3.
T=400 K: k=0.790 W/m/K, Cp=194 J/kg/K.
For x=0.23 at 298 K, k=1.01 W/m/K; density=7330 kg/m3. These are measured alloy values, not necessarily the actual detector Cd fraction.
Use temperature interpolation only within supported samples, and include source uncertainties. Thermal conduction through a thin die may be small compared to unknown die attach contact resistance; measure/sweep both.

Required plots: MCT T_max and mean versus TEC current, bias power and absorbed optical power; thermal gradient at die attach; contact resistance sensitivity; cooldown and die-lag; heat budget.

This project must NOT invoke, modify or connect LSDDTS. Semiconductor band structure, drift-diffusion and microscopic recombination are outside active scope.

Source: https://opg.optica.org/ao/abstract.cfm?uri=ao-47-4-578
