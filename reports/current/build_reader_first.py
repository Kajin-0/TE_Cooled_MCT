#!/usr/bin/env python3
"""Reader-first editorial permutation of the existing cumulative TEC/TO monograph.

The original text of each major section is copied without rewriting its body.
Original PDFs/source remain preserved. All source section hashes are emitted.
Inputs V3.8-V3.13 retain their own separately maintained scientific bodies.
"""
from pathlib import Path
import hashlib,json,re
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'cumulative_report.tex'
TARGET=HERE/'reader_first_report.tex'
DOC=SOURCE.read_text()
PAT=re.compile(r'^\\section\{([^}]+)\}',re.M)
HEADINGS=list(PAT.finditer(DOC[:DOC.index('\\appendix')]))
PRE=DOC[:HEADINGS[0].start()]
SECTIONS={}
for i,m in enumerate(HEADINGS):
  nxt=HEADINGS[i+1].start() if i+1<len(HEADINGS) else DOC.index('\\appendix')
  title=m.group(1)
  assert title not in SECTIONS,title
  SECTIONS[title]=DOC[m.start():nxt]
APP=DOC[DOC.index('\\appendix'):]
assert APP.startswith('\\appendix')
# The earlier cumulative version inserted additive science after V3.6. Extract
# those standalone inputs from the old layout without changing a body paragraph.
CURRENT='Current versus cooling performance: an operating envelope (V3.6)'
ADD=['expanded_tec_to_studies_20261109.tex','v312_contact_mounting_section.tex']
for f in ADD:
 marker='\\input{'+f+'}\n'
 assert SECTIONS[CURRENT].count(marker)==1,(f,SECTIONS[CURRENT].count(marker))
 SECTIONS[CURRENT]=SECTIONS[CURRENT].replace(marker,'',1)
ORDER=[
 'Device construction and thermal architecture',
 'Cooler layout and supported interstage connections',
 'Thermoelectric material behavior and heat pumping',
 'Heat spreading through ceramic substrates',
 'Electrical routing and interstage heat leakage',
 'Electrical contacts, solder joints and dissipative heating',
 'Package parasitic heat loads and thermal rejection',
 'Terminal wires, soldered TO pins, and thermal uncertainty',
 'Original V3.4 copper-bridge result and its physical explanation',
 CURRENT,
 '@expanded_tec_to_studies_20261109.tex',
 '@v312_contact_mounting_section.tex',
 '@v313_port_qualification_section.tex',
 'Geometric fidelity and remaining discretization risk',
 'Predicted detector temperature under enclosure loading',
 'Historical V3.3 stage temperatures, heat flow, and electrical input',
 'Historical V3.3 energy conservation and numerical credibility',
 'Device engineering implications and next experiment',
 'Model provenance and numerical evidence hierarchy',
 'Physical assumptions and reproducibility specification',
 'Scientific and engineering references',
]
expected=[x for x in ORDER if not x.startswith('@')]
assert set(expected)==set(SECTIONS),(set(expected)-set(SECTIONS),set(SECTIONS)-set(expected))
assert len(expected)==len(SECTIONS)==len(HEADINGS)
# One pagination-only edit prevents the pinout figure from monopolizing a page.
construct='Device construction and thermal architecture'
assert SECTIONS[construct].endswith('\\clearpage\n\n')
SECTIONS[construct]=SECTIONS[construct][:-len('\\clearpage\n\n')]+'\n'
# Allow independent preservation checks without relying on PDF page counts.
manifest={'input_source':str(SOURCE.relative_to(HERE.parent.parent)),
 'original_section_SHA256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in SECTIONS.items()},
 'original_preamble_sha256':hashlib.sha256(PRE.encode()).hexdigest(),
 'original_appendix_sha256':hashlib.sha256(APP.encode()).hexdigest(),
 'new_section_order':ORDER,
 'content_policy':'Every original scientific paragraph, figure and appendix retained; one forced page break after construction removed for pagination; two additive inputs reinserted and reader-navigation paragraph added.',
 'added_inputs':ADD+['v313_port_qualification_section.tex']}
NAV='''\\noindent\\textbf{Reader navigation.} The main assessment follows the physical device: construction and governing transport, interconnects and TO thermal paths, accepted operating conditions and sensitivity studies, then historical baseline comparisons, numerical verification and reproduction details. Historic simulations are retained as distinct source-model generations; the latest contact and material studies have explicit qualification limits.\\par\\medskip
'''
assert PRE.count('\\tableofcontents')==1
pieces=[PRE,NAV]
for key in ORDER:
 if key.startswith('@'):
  fname=key[1:];assert (HERE/fname).is_file()
  pieces.append('\\input{'+fname+'}\n')
 else:
  pieces.append(SECTIONS[key])
pieces.append(APP)
NEW=''.join(pieces)
assert NEW.count('\\appendix')==1
assert all(NEW.count('\\section{'+k+'}')==1 for k in SECTIONS)
assert NEW.count('\\input{expanded_tec_to_studies_20261109.tex}')==1
assert NEW.count('\\input{v312_contact_mounting_section.tex}')==1
assert NEW.count('\\input{v313_port_qualification_section.tex}')==1
TARGET.write_text(NEW)
manifest['new_tex_sha256']=hashlib.sha256(NEW.encode()).hexdigest()
(HERE/'reader_first_organization_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('SECTIONS_RETAINED',len(SECTIONS),'APPENDIX_BYTES',len(APP),'OUTPUT',TARGET,'SOURCE_BYTES',len(DOC),'OUTPUT_BYTES',len(NEW))
