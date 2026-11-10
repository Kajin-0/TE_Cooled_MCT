"""Create additive report text and internal result tables from the audited summary."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
D=R/'data/tec_height_robustness_20261110'; H=R/'reports/current'
s=json.loads((D/'summary.json').read_text())
labels={'v320_control':'V3.20 reference','interstage_off':'Interstage gas off','outer_gap_1p5mm':'Outer gas gap 1.5 mm','sink_plus5':'Sink resistance +5 K/W'}
rows=s['pairs']
tex=r'''\subsection{Matched-power robustness of the height comparison}
The following paired comparisons vary one uncertain heat path at a time while preserving the 29/11/4 thermocouple layout and solving the actual 88 nonlinear legs and four source ceramic temperature fields at $IV=0.595668$ W, 300 K ambient and 2 mW imposed detector heat. Both geometries receive the same change. The exterior gas path is a lumped proxy, not a resolved native cavity, and may overlap the interstage approximation; its nominal 3 mm effective distance is compared with 1.5 mm. A separate gas case suppresses all three interstage links, while the sink case adds 5 K/W to the original external sink resistance. These are engineering hypotheses, not measured tolerances.

\begin{center}\small\begin{tabular}{lrrr}\toprule
Case & 0.50 mm die (K) & 0.60 mm die (K) & Difference (K) \\ \midrule
'''
for p in rows:
 tex+=f"{labels[p['scenario']]} & {p['nominal']['die_K']:.3f} & {p['custom_060']['die_K']:.3f} & {p['delta_die_K']:.3f} " + r'\\'+'\n'
tex+=r'''\bottomrule\end{tabular}\end{center}
'''
if s['all_sampled_custom_colder']:
 tex+='The taller candidate remains colder at the mount in each displayed paired scenario. '
else:
 tex+='The paired scenarios do not all retain the same ranking. '
tex+=f"The sampled difference ranges from {s['min_delta_die_K']:.3f} to {s['max_delta_die_K']:.3f} K; this is a set of model scenarios, not a statistical interval or a guarantee for a manufactured part. "
tex+=r'''All new cases meet the registered matched-power and independently reconstructed stage and whole-package energy gates. A separate fixed-field copper contact-resistance exercise changes the predicted metal heat paths; it is not an additional coupled temperature prediction. Net88's middle foot is a thermal port, not a series electrical contact. The historical spatial electrical-contact gate remains failed, the gas approximations are not validated native-void solutions, the research P/N specimens are not a matched commercial grade, and continuation above 300 K is assumed.

\begin{figure}[htbp]\centering\includegraphics[width=.96\linewidth]{figures/v321_height_robustness.pdf}\caption{Actual matched-power package solutions for the nominal and custom leg heights. Differences are conditional on the specified gas and mounting models, with no interpolation across uncomputed scenarios. The reference pair is the previously archived result; other pairs are new independently audited solutions.}\end{figure}
'''
(H/'v321_height_robustness_section.tex').write_text(tex)
p=H/'reader_first_height_coupled_20261110.tex'; t=p.read_text(); marker='\\input{v320_height_coupled_section.tex}\n';assert t.count(marker)==1
(H/'reader_first_height_robustness_20261110.tex').write_text(t.replace(marker,marker+'\\input{v321_height_robustness_section.tex}\n'))
doc_path=R/'docs/TEC_HEIGHT_ROBUSTNESS_20261110.md'
existing=doc_path.read_text()
marker='\n## Independently audited results\n'
if marker in existing: doc_path.write_text(existing.split(marker,1)[0])
with doc_path.open('a') as f:
 f.write('\n## Independently audited results\n\n')
 f.write('| Case | 0.50 mm die K | 0.60 mm die K | Δ die K | Δ top ceramic K |\n|---|---:|---:|---:|---:|\n')
 for p in rows:f.write(f"| {labels[p['scenario']]} | {p['nominal']['die_K']:.6f} | {p['custom_060']['die_K']:.6f} | {p['delta_die_K']:.6f} | {p['delta_top_K']:.6f} |\n")
 f.write('\n| Case | Height mm | I A | V V | Input W | Hot ceramic K | Sink W | Cold-leg Qc mW | Outer gas mW | Internal gas mW | Cu Joule mW | Max stage residual W | Global residual W |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n')
 for p in rows:
  for key,h in [('nominal',.5),('custom_060',.6)]:
   r=p[key];f.write(f"| {labels[p['scenario']]} | {h} | {r['current_A']:.6f} | {r['voltage_V']:.6f} | {r['power_W']:.9f} | {r['hot_K']:.6f} | {r['sink_W']:.6f} | {1000*r['cold_leg_Qc_W']:.6f} | {1000*r['gas_external_W']:.6f} | {1000*sum(r['gas_internal_W']):.6f} | {1000*r['Cu_joule_W']:.6f} | {r['stage_residual_W']:.3g} | {r['global_residual_W']:.3g} |\n")
 f.write(f"\n**Result:** {s['new_full_system_solves_with_audit']} new independently audited solves, {s['new_paired_scenarios']} paired scenarios. The sampled die difference spans {s['min_delta_die_K']:.6f} to {s['max_delta_die_K']:.6f} K. ")
 f.write('The custom design is colder in all sampled cases. ' if s['all_sampled_custom_colder'] else 'The direction is not preserved in every sampled case. ')
 f.write('This is conditional on the listed model paths and not an uncertainty interval or empirical proof. Detailed individual copper-stage, lead, gas and radiation terms, iterations, timestamps, input hashes and audit residuals are in the machine-readable summary and per-case records.\n')
 f.write('\n## Separate fixed-field copper sensitivity\n\nWith the original V3.20 face temperatures and currents held fixed, contact area resistances of $10^{-6}$, $10^{-5}$ and $10^{-4}$ m² K/W give Cu C2 heat of 86.714, 62.614 and 17.532 mW for 0.50 mm and 84.288, 61.899 and 17.832 mW for 0.60 mm. An independent incidence-matrix calculation passes; these are transport-only calculations, not coupled die-temperature results or measured contact properties.\n')
 if s['incomplete']:f.write('\n**Incomplete / not run:** '+str(s['incomplete'])+'\n')
