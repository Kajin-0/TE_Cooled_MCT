# LSDDTS ↔ TEC FEM coupling contract v1

This is a design contract, NOT a functioning direct bridge or a production LSDDTS export adapter.

Source: Kajin-0/mct-refactor, Python package lsddts. Supported HgCdTe solver is restricted to bounded same-surface photoconductor physics. Its material_profile may be metadata-only and its illuminated current/response is often diagnostic-only. Use effective configuration hash + exact git commit and preserve per-output authority flags.

Thermal side: TE_Cooled_MCT accepts an explicit physical net die heat flow in W at a source temperature in K. Device side consumes updated die temperature, composition, geometry, bias, optical context and source provenance.

Exchange schema: schemas/mct_thermal_exchange_v1.schema.json, synthetic example: examples/coupling/mct_thermal_exchange_example.json. The synthetic example contains NO LSDDTS solved data.

Scalar algorithm:
1. Initialize cold-die temperature T0 from TEC FEM for specified I, hot-side thermal BC and optical conditions.
2. Run a qualified LSDDTS case at T0 if its supported material/temperature range permits it.
3. Extract actual Vdet, terminal signed I and any properly defined optical absorbed HEAT power (not photons/sec); use passive sign for Pbias=Vdet*Idet, and count only thermally deposited optical energy.
4. Package q_die_total_W = Pbias + Poptical_thermalized + separately defined other nonduplicate heat terms. Flag per-field authority, resolution status, effective hash, source revision.
5. Apply q_die_total to a physical die region in 3D FEM: uniform volume source initially; later spatially mapped from detector discretization, conserving volume integral.
6. Update T from FEM. Relax T_next = T_old + omega*(T_FEM−T_old). Converge below 0.05 K and 0.5% relative power, or fail closed.
7. Preserve both source solver outputs and all iterations; do not claim authoritative combined results unless BOTH constituent outputs pass independent authority and mesh/uncertainty gates.

Do not double-count Pbias as both V*I and V^2/R. Do not assume spectral photocurrent equals optical heat. Do not force Tchip=200K into an LSDDTS profile verified only at 77K and claim validity. An authority flag is not changed by serialization.

Future v2 spatial exchange: source term q(x,y,z) for Joule/recombination and optics absorbed power, mesh transfer operators, heat conservation tolerance and die T(x,y,z) feedback.
