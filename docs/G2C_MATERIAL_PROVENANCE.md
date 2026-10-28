# G2c source qualification

The opt-in library `material_profiles.py` leaves prior constant properties unchanged.
Its default v1 profile ingests six red-marker values at 200, 220, 240, 260, 280, 300 K for rho, S and k
on **N-HE-1** and **P-HE** in Zhang et al., Chinese Physics Letters 42 (2025) 056304,
[original paper](https://cpl.iphy.ac.cn/en/article/id/eff94ac0-79aa-4d9d-b706-fcf56e7577e6).
These are distinct commercial hot-extruded samples. Within each sample the three
properties were measured on the same specimen; the P/N pair is not identified as
a matched cooler pair or the OEM grade. Suppliers/grade details in the unavailable
supplement are not claimed. The main PDF and its plots were inspected directly.

`data/g2c/zhang2025_he_v1.json` stores SI values, original PDF SHA256, figure/page,
axis calibration, marker centres and conservative +/-0.5 PDF point reading bounds.
The plotted units are micro-ohm metre, microvolt/K and W/(m K). Resistivity is
interpolated linearly, sigma=1/rho. No conductivity-to-Seebeck/thermal inference.
The v1 interval is strictly **200–300 K**; the wider published range is not ingested.
Python rejects unsupported T; compiled Elmer functions also fail at runtime.
Reading bounds exclude specimen scatter and systematic measurement uncertainty.
The paper's uncertainty analysis is not an empirical confidence interval for this TEC.

Goldsmid Table 1 is partial: conductivity values at fixed thermopower do not
establish a complete same-specimen S/sigma/k trajectory. Cai Appendix A1 is
quarantined because the original PDF fetch/unit glyph verification failed; its
reported 288 K lower limit would exclude the previous ~262 K solution anyway.
Exact statuses/units/source URLs are in `source_registry.json` and retrieval hashes
in `retrieval.json`. No source table is fabricated from a search snippet.

The [specific 2019 OEM datasheet](https://www.tec-microsystems.com/Download/Datasheets/Thermoelectric%20Coolers/MC04%20Series/3MC04-044-05_Datasheet_2019.pdf)
was downloaded and its original page-2 vectors inspected. `oem2019_curves_v1.json`
contains 160 numeric readings on all four panels, with printed loads and separate
environment metadata. Currents .2/.6/1.0 A are calibration-reserved;
.1/.4/.8 A are validation holdouts. No fitting has occurred. Readings have a
conservative +/-1 PDF point bound (including rounded chart-grid placement),
not a manufacturer measurement tolerance. The nominal 300 K vacuum Qmax is
0.51 W; the rounded front-page 0.5 W is not silently substituted. Extrema are
not simultaneous conditions. Dry-N2 curves cannot validate a vacuum-only solid FEM.

`scripts/digitize_g2c.py` reproduces marker/polyline extraction using isolated
PyMuPDF 1.26.7 from `outputs/g2c-source-tools`, without a host install or image change.
Original copyrighted PDFs remain untracked in `outputs/g2c-sources`; derived
numerical data, source URLs and hashes are tracked. Curves in material/OEM files
are source readings, not simulated fields.

`g2c_qualification.Contact` checks SI area-specific R_e and R_th and computes
candidate thin-layer coefficients. These are assumed parameters, not measured
Sn-Sb chemistry/contact data. The pure parameter object reports **NOT EXECUTED**; a
parameter table must never be described as a meshed contact solve. Separate
`fem_g2c_contact` runs explicitly mesh and verify an assumed resistive transition
law, as recorded in the final numerical result; this does not assign an OEM
solder composition or measured interface resistance. The selected
pinned solver assumes shared-node continuity; a jump law requires independent
trace DOFs or an independently verified explicit layer construction.


An additive opt-in **v2, 40–300 K** profile now ingests fourteen red markers per
property from the same original figures. `zhang2025_he_40_300_v2.json` and
`low_temperature_extension_registry.json` retain all original provenance and
bounds. The v1 six-point subset is verified bit-for-bit unchanged; its default
interval and all earlier executions retain their meaning. Neither profile
silently extrapolates. Below-40 K readings are excluded. The published uncertainty
analysis does not supply an empirical confidence interval for this OEM module.
The model uses scalar sample properties; extrusion orientation and OEM tensor
properties remain unqualified. A separate actual 200/190 K fixed-face Elmer
check exercises v2 below 200 K, without asserting a predicted cold temperature.
Reproduce extraction with `scripts/digitize_g2c_low_temperature.py` and the
same isolated PDF tool. No speculative 190 K curve was invented.


Prepublication erratum: final visual review caught an inverted origin in the
negative N-type Seebeck panel. The bottom is -240 microV/K and the top is zero;
its negative axis cannot use the positive-panel zero-at-bottom mapping. Corrected
profiles have IDs **v1r1 / v2r1** and explicit axis-end values. A 300 K N Seebeck
anchor and the independently plotted N/P power-factor panels now cross-check the
extraction. Every affected source-profile FEM run was quarantined and rerun;
none is accepted source-qualified evidence. The constant G1-profile contact
executions did not consume that source data; their actual fields and constant
material callbacks were independently reverified with precise dependency records.
The original overbroad development manifests are retained for audit.
