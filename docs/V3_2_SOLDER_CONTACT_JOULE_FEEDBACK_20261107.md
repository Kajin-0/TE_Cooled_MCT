# V3.2 — Original SnSb solder and finite electrical-contact Joule losses in the running TEC system

**Date:** November 7, 2026. **Parent working baseline:** V3.1 at commit \`0afbcb4\`. **Source base:** current original R3.9 original-CAD 29/11/4 assembly.

**Verdict: ONE complete 0.4 A conditional V3.2 end-to-end nonlinear + original four 3D ceramic model converged and conserves charge/energy according to its declared circuit model. NOT matched OEM solder, not physically qualified real contact, not full 430-domain spatial TE PDE.** Historical original P1 electrical Gate B **FAIL/STOP**, first actual 3D pair raw-gradient current **FAIL 8/8**, prospective P2 **STOP** and full 430-domain C/D **NOT RUN**, unchanged.

## Deliverables

- [One V3.1-derived source-CAD V3.2 whole-system solver](../scripts/v3_2_joint_loss_feedback.py)
- [Exact pre-registered single operating point, contact hypothesis and all source hashes](../data/v3_2_joint_loss_feedback_20261107/attempt01/registration.json)
- [Complete TEC/detector/88-leg/4-ceramic nonlinear energy and 3D-field result](../data/v3_2_joint_loss_feedback_20261107/attempt01/result.json)
- [Four original-source 3D ceramic absolute temperature fields](../data/v3_2_joint_loss_feedback_20261107/attempt01/source_native_ceramics_V3_2.npz)
- [Independent no-PDE source face and electrical-work balance](../data/v3_2_joint_loss_feedback_20261107/attempt01/read_only_acceptance.json)
- [Read-only acceptance driver](../scripts/v3_2_read_only_audit.py)
- [Source SHA and archived-result manifest](../data/v3_2_joint_loss_feedback_20261107/attempt01/manifest.json)

## Scope and minimal added physics

**Unchanged:** one original-source CAD 29/11/4 circuit with 88 individually resolved nonlinear P/N legs, 32 axial intervals each, 11,791 original tetrahedra in the four 3D ceramic thermal spreading fields, actual native 91 ceramic-pad contact tags, source Cu power and Au detector wires, die attach, header/TIM, recommended radiator, 0.4 A, 300 K environment and 2 mW detector heat. Research-material P/N coefficients, thermal k30 alumina and all existing V3.1 source temperature boundaries unchanged. No global remesh and no Codex.

**New:** the exact original source series circuit has 176 SnSb solder body regions and 352 physical solder-side electrical interfaces (one leg/solder and one solder/metal contact for every solder). Use the previous **unqualified hypothetical** room-temperature SnSb bulk electrical resistivity \(\rho_s=1.7\times10^{-7}\,\Omega\,\mathrm m\); each source solder is 35 µm long and 0.16 mm² cross-sectional area. Use a **hypothetical**, unmeasured common electrical specific contact resistivity \(r_e=10^{-11}\,\Omega\,\mathrm m^2\) on all 352 interfaces. No fitted or manufactured specific resistivity is claimed.

\[
R_s^\mathrm{all\,176}=176\frac{\rho_s L_s}{A_s}=0.006545\ \Omega,
\quad
R_c^\mathrm{all\,352}=352\frac{r_e}{A_s}=0.022000\ \Omega.
\]
\[
R_\mathrm{added}=0.028545\ \Omega,\quad
\Delta V_\mathrm{series}=I R_\mathrm{added}=11.418\ \mathrm{mV},\quad
P_\mathrm{added}=I^2R_\mathrm{added}=4.5672\ \mathrm{mW}.
\]

At **each** original SnSb joint, add \(I^2(\rho_s L_s/A_s+2r_e/A_s)=25.95\) µW of electrical Joule heat to its **adjacent original ceramic native source metal-pad face**. Each of the 88 TE legs has two joints (hot and cold); this adds one identical positive thermal source to each of its hot/cold original CAD pads. The source Cu power-lead correction remains on real ceramic0 face36, underside sink on face6, and detector on ceramic3 face119.

The original 3D ceramic P1 Neumann fields are re-solved through their previously factored source matrices and reintegrated into the **same** 88-leg nonlinear TE model. The important new interstage thermal balances contain the original two facing stage-joint heat sources, not just a single added terminal resistance:

\[
Q_{c,0}-Q_{h,1}=(58+22)P_j,\qquad
Q_{c,1}-Q_{h,2}=(22+8)P_j,\qquad
Q_{c,2}-Q_{\mathrm{die\,attach}}=8P_j.
\]

All initial source P/N and 3D source-ceramic temperature states are inherited from V3.1; V3.2 converges to its own heat-feedback field.

**Thermal partition is an explicit coarse assumption, not a microscale contact model.** All solder/interface Joule heat is deposited directly into the attached ceramic, with **zero explicit solder thermal resistance, no contact temperature jump, no interfacial Peltier coefficient, and no solder or multilayer metal current-crowding solution**. Solder and metal thermal pathways and actual joint thermopower need future refinement only if whole-system sensitivity justifies them. This increment **does not include independent bulk metallization electrical series resistance**. The source P/N property curves above 300 K retain an explicitly unmeasured continuation.

## Same 0.40 A full-system comparison

| Metric | V3.1 reference | V3.2 with hypothetical original solder and electrical contact loss | Delta |
| --- | ---: | ---: | ---: |
| Calculated detector temperature | 209.803293 K | **209.987981 K** | **+0.184688 K** |
| Terminal voltage | 1.51329665 V | **1.52407083 V** | **+0.01077418 V** |
| Electrical power | 0.60531866 W | **0.60962833 W** | **+0.00430967 W** |
| Bath heat rejected | 0.58617370 W | **0.59032260 W** | **+0.00414891 W** |

The **direct** 11.418 mV series voltage from the new joints differs from the **net** 10.774 mV whole-device voltage shift because the hot/cold temperatures and nonlinear P/N thermoelectric stage voltages also change. Similarly, the incremental terminal electrical power differs from \(4.5672\) mW due to thermal feedback. The die temperature shift is an explicitly **conditional model difference**, neither numerical uncertainty nor a physical prediction error.

V3.2 mean ceramic/detector equivalent temperatures:

| Model junction | Temperature |
| --- | ---: |
| Stage0 hot | 303.63362 K |
| Stage0 cold | 265.74024 K |
| Stage1 hot | 266.16916 K |
| Stage1 cold | 235.60946 K |
| Stage2 hot | 235.75230 K |
| Stage2 cold | 209.90193 K |
| Detector carrier | 209.91816 K |
| **HgCdTe detector die** | **209.98798 K** |

Original source ceramic heating from new joints alone (not total through-plate heat) is **1.50510, 2.07600, 0.77850 and 0.20760 mW** for ceramic0 through ceramic3. Their sum is **4.56720 mW**, exactly the new electrical Joule heat. All native source face thermal loads and original source Cu/die terms remain explicitly separate.

## Numerical results and independent verification

- One registered operating point with **12 outer iterations**; last maximum original pad/plate temperature update **\(1.2194\times10^{-7}\) K**, below \(2\times10^{-7}\) K acceptance.
- Global electricity/detector/wires/TEC/sink energy residual **\(1.3789\times10^{-10}\) W**, maximum stage heat mismatch **\(1.2578\times10^{-10}\) W**, maximum native ceramic net heat imbalance **\(1.16\times10^{-15}\) W** and individual-leg energy residual **\(1.49\times10^{-13}\) W**.
- Independent [read-only acceptance](../data/v3_2_joint_loss_feedback_20261107/attempt01/read_only_acceptance.json) reconstructs the original 176 SnSb / 352 electrical-contact resistances, their \(I^2R\) budget, sums all 88 original-source leg electrical power and heat contributions, independently verifies stage joint-energy balances and each ceramic source face, without re-solving the PDE.
- The final saved ceramic field differs from the final recomputed nonlinear leg pad loads by as much as **\(1.0431\times10^{-10}\) W**, reflecting the *finite* final spatial fixed-point tolerance. This is below the registered residual budget, but is explicitly **not zero** or proof of exact local convergence. No evidence was overwritten or silently corrected.
- The original CAD, accepted mesh, V1/V2/V3/V3.1 baselines and canonical Rev3 are preserved.

## Next decision

V3.2 is a meaningful new **working-system** refinement: a directly traceable physical loss mechanism alters terminal electrical power, distributed ceramic heat and detector temperature while the original native spatial and nonlinear models remain connected. Further detailed modeling of each micro-contact on the old original raw-flux-failing P1 mesh would be churn. The high-value next uncertainty is likely the **real** P/N transport grade, \(\rho_c(T)\), solder/contact thermal resistance and actual heat-sink/thermal environment. Before increasing 3D electric mesh fidelity, prioritize a bounded whole-system sensitivity or getting source-specific experimental inputs. Full 430-domain 3D C/D, original electrical gate and as-built qualification remain unmet.
