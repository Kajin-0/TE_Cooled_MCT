# Custom-height TEC: mapped package operators and matched-power experiment

## Physical and numerical contract

The nominal 0.50 mm and constructed 0.60 mm assemblies retain 29/11/4 couples, 0.40 mm square P/N legs and the original bottom/header datum. This is a **conditional reduced-metal package model**: 88 separate nonlinear axial P/N legs couple to four original spatial 3D TET4 ceramic plates, CAD-derived Cu-tab multiports, two terminal leads, detector Au wires, header/sink and reduced cavity exchange. It is not a 430-domain coupled metal/semiconductor/gas PDE, manufactured cooler, rated device or OEM validation. The detector is a prescribed 2 mW thermal load. The historical native net88 3D electrical gate remains FAIL/STOP.

Before a coupled run, the [registered contract](../data/tec_height_coupling_20261110/solver_contract.json) fixed a maximum of two attempted matched-power cases (nominal, then candidate only after nominal independent audit), each <=300 s, <=8 CPUs and <=12 GiB; I is an actual unknown bounded to 0.25–0.55 A, constrained by `I*V = 0.5956680349614825 W`, not interpolated across rejected states. Both models use 300 K ambient, 100 Pa krypton and the unchanged Zhang research P/N laws with the unmeasured quarter-tangent continuation above 300 K. The original 0.4 A V3.11 run remains an archive reference, not an exact comparison because both present cases include the newly declared interstage gas proxy and correct a net88 electrical bookkeeping term.

## Mapping and physical changes

Candidate CAD and the independently imported 923 contact witnesses establish unchanged ceramic shapes, pad footprints and physical skin ownership under four rigid z translations 0/0.10/0.20/0.30 mm. The mapping preserves 95 original TRI3 face tags as **lineage keys**, not as newly assigned candidate CAD face tags, and traces 176 P/N end faces via solder to the verified candidate solids. Independent readback translates all actual source triangle vertices and verifies each centroid against its candidate physical Ti skin and verifies source mesh-face area: 3,334 triangles, max relative face-area difference <2e-15. All four original TET4 sets, 4,936/4,085/1,986/784 cells, are translated; a separate analytic P1 tetrahedron stiffness control confirms invariance under rigid translation. A new full candidate conformal 3D mesh has not been generated.

The source-derived copper 58/80/88 multiport is rebuilt from the actual saved candidate line/arc centerlines and seven solder-foot positions. It retains all seven thermal ports, including the net88 middle thermal-only foot; its spurious middle **electrical series** contact in the historical V3.11 approximation is removed in both new cases. This is a paired model correction, not a reclassification of the failed 3D electrical gate. The hot terminal Cu wire geometries stay fixed; both Au detector-bond conductances are recalculated from their reformed paths. The source Cu materials, 176 P/N solder joints and 352 interface resistance hypotheses are unchanged and not measured as a real cooler.

For the additional interstage gas sensitivity, each neighboring ceramic pair is approximated by one rarefied-gas parallel channel: area = smaller ceramic projected area minus the P/N solid footprints, and length = substrate separation minus two 15 µm metallization films. The three areas are 17.76, 10.92 and 4.48 mm²; gas lengths are 0.57 mm nominal and 0.67 mm custom. The existing krypton conductivity and temperature-jump expression uses the mean stage boundary temperature and accommodation 0.8. Each interstage link removes the same Q from its hot plate as it adds to its cold plate; its load is distributed onto native pad bases, an explicit approximation.

The previous **external** gas-to-reservoir 3 mm effective gap and diffuse-gray view factors are retained unchanged as fixed proxies, not represented as candidate-exact cavity geometry. These external and interstage proxies could overlap in actual cavity volume; spatial flow, lateral access, accommodation and any double counting are unqualified. At the archived fixed temperatures alone, changing the external gap to 1.5/3/6 mm yields 6.319/3.420/1.783 mW external gas heating; these are fixed-field sensitivities, not coupled temperature uncertainties. A real connected-gas domain and surface transfer calculation remain future work.

The explicit independent preflight passes 95 candidate skin/mesh-face registrations and 176 leg mappings. The reduced Cu operator reproduces the original nominal V3.11 operator when its historical net88 electrical approximation is intentionally enabled; the corrected operator conserves `sum(Q_ports)=I²R`, and its zero-current thermal matrix is reciprocal, positive semidefinite and zero-row-sum. Analytical tests cover gas direction reversal and zero controls, P1 translation invariance, altered material domains and missing/misaligned geometry. Mapping, operator specs, input hashes, source snapshot/solver contract, per-case logs and actual gas results are retained under `data/tec_height_coupling_20261110/`.

An initial fixed-field external sensitivity and extra gas check used the wrong recorded temperature-node indices; the failed artifact is retained and superseded by the corrected stage1-hot/stage2-hot/carrier/die control. The corrected 3 mm total exactly reproduces the archived V3.11 gas value. This did not alter the actual coupled solver or its registered external operator.

## Accepted conditional matched-power comparison

Both registered 3D-ceramic/88-leg package cases completed and passed their separate independent stage, gas, lead, Cu, die, sink and global-balance reconstructions. The current is solved together with temperatures, not read from the frozen-pad screen. Each model includes the same fixed external cavity proxies and the same new geometry-derived interstage gas model.

| Quantity | 0.50 mm nominal | 0.60 mm custom |
|---|---:|---:|
| Current (A) | 0.400298 | 0.370631 |
| Terminal voltage (V) | 1.488062 | 1.607175 |
| Electrical input (W) | 0.595668 | 0.595668 |
| Hot ceramic (K) | 303.761291 | 303.764120 |
| Top ceramic (K) | 219.297688 | 215.591806 |
| Die mount (K) | 219.368939 | 215.663617 |
| Cold-stage P/N Qc before parasitics (mW) | 6.099082 | 6.051364 |
| Heat rejected at sink (W) | 0.592285 | 0.592474 |
| Cu tab electrical dissipation (mW) | 2.060049 | 1.852711 |
| P/N solder/contact electrical dissipation (mW) | 4.574002 | 3.921141 |
| Lead conduction into ceramic (mW; negative = outward) | -10.311436 | -10.362365 |
| External gas / gray radiation (mW) | 3.401815 / 0.560315 | 3.549955 / 0.579929 |
| Interstage gas hot→cold, stages 1/2/3 (mW) | 6.347763 / 2.588255 / 1.205127 | 5.958504 / 2.348298 / 1.116628 |
| Outer iterations / wall seconds | 18 / 191.01 | 16 / 179.22 |

Under these **specific conditional proxies**, the taller case gives ΔTdie = **-3.705321 K**, ΔTtop = **-3.705882 K**, and requires 0.029667 A less current at the matched input. These are model comparisons, not an experimental result, global optimum, manufacturer rating, or proof that native interleg gas reduces temperature by that amount. The Qc row is the P/N leg cold-end heat before interstage gas and other parasitics; its small difference does not mean the package balance is unchanged.

Stage budgets, W `(Qhot, Qcold, V, Joule W)`:

| Case | Stage 1 | Stage 2 | Stage 3 |
|---|---|---|---|
| 0.50 mm | 0.717058, 0.295305, 1.053599, 0.266300 | 0.262929, 0.138533, 0.310758, 0.085632 | 0.048246, 0.006099, 0.105289, 0.026385 |
| 0.60 mm | 0.717007, 0.293265, 1.143301, 0.272976 | 0.259221, 0.135573, 0.333615, 0.087117 | 0.047922, 0.006051, 0.112972, 0.026630 |

Both independent audits pass: max stage boundary imbalance 1.204e-9 W, max global energy error 1.044e-9 W, maximum individual leg error 1.478e-13 W; the final spatial iterations changed by 1.963e-7/1.307e-7 K. Source-law actual leg extrema are 219.268–305.278 K / 215.563–305.303 K, and 58/57 hot-stage legs invoke the assumed continuation above 300 K. Both saved compressed field archives contain the **actual solved four ceramic temperature arrays with corresponding translated source node coordinates**, not a full 3D metal or gas field.

The original source 3D electrical contact FAIL/STOP, original bath/cold flux gates, native gas raw-flux failure and all archive identities remain unchanged. Two cases were solved, no failed numerical cases were hidden and no third or fourth full-system solve was launched. Compare the external 3 mm sensitivity above only as an algebraic fixed-temperature range; it does not establish the uncertainty or robustness of the -3.705 K difference. Next, validate the actual interleg gas geometry/transport and source-consistent metal/contact thermal losses, and perform a matched-power controlled variation of those physical paths before treating the direction as a robust design recommendation.

## Reproduction

The solver and its exact generated derivative are separately source-sealed in `solver_contract.json`. `scripts/build_tec_height_v320_solver.py <new-output-path>` reconstructs the executed derivative byte-for-byte from the frozen V3.11 source; it refuses to overwrite an existing output. `scripts/tec_height_v320_mapping_audit.py` uses the pre-existing source mesh and writes translated coordinates only to a fresh evidence directory. The recovered runtime image identity is recorded in the preceding CAD record; it is not the missing original image digest. The 27-test focused command is recorded in `focused_tests_final_release.log`; it runs on the saved results and does not invoke a full package solve.

The executed solver expects the original mesh files at `/var/tmp/mct_r3_header_3d_20261107` inside its container. If the host's temporary copy is unavailable, the two frozen archives contain the required files and can be unpacked to a **new** host directory, then mounted read-only at that container path:

```sh
mkdir -p outputs/v320-restored-mesh
tar --zstd -xf data/v3_r38_global_tetgen_20261105/attempt01/saved_tetra_mesh.tar.zst -C outputs/v320-restored-mesh R38_430_domains.1.node R38_430_domains.1.face
tar --zstd -xf data/v3_r39_quality_20261105/attempt01/candidate_mesh_and_flips.tar.zst -C outputs/v320-restored-mesh R39_430_domains.1.ele
```

Verify the three SHA-256 values against `registration.json` before running. A future repetition should use a fresh output directory, the recorded offline container with <=4 CPUs/8 GiB, and the same 300 s per-case bound. Re-run both separate recorded-result and gas/port audits against the new outputs. No prior source, mesh, output or PDF needs to be overwritten.
