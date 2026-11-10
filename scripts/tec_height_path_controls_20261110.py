#!/usr/bin/env python3
"""Apply source fillet construction to proposed tabs and detector bonds; no CAD."""
from pathlib import Path
import json,hashlib
from tecooledmct.tec_assembly_v3 import fillet
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/tec_height_geometry_20261110'
def main():
 d=json.loads((ROOT/'data/synthetic_v3_assembly_20261102/source_final/design.json').read_text())
 bodies={b['name']:b for b in d['bodies']}; rows=[]
 for n in (58,80,88):
  b=bodies[f'formed_tab{n}'];pts=[v[:] for v in b['points']]; orig=[v[1] for v in pts]
  levels=sorted(set(round(z,9) for z in orig)); assert len(levels)==(3 if n==88 else 2)
  for p in pts:p[1]+=(.1 if n==80 else 0.)+.1*min(range(len(levels)),key=lambda i:abs(p[1]-levels[i]))
  parts=fillet(pts,.075);length=sum(x['length'] for x in parts)
  source=sum(x['length'] for x in b['parts']);assert abs(length-source-(.2 if n==88 else .1))<1e-9
  rows.append(dict(name=b['name'],original_mm=source,proposed_mm=length,points=pts,source_fillets_succeed=True,clearance_contact_and_cad='NOT CHECKED'))
 bonds=[]
 for n in (7,8):
  b=bodies[f'detector_bond{n}'];old=[v[:] for v in b['points']];bad=[v[:] for v in old];bad[0][2]+=.3
  try:fillet(bad,.15);raise AssertionError('Unchanged apex should fail')
  except ValueError as e: reason=str(e)
  new=[v[:] for v in old];new[0][2]+=.3;new[1][2]+=.3;new[2][2]+=.3
  parts=fillet(new,.15);bonds.append(dict(name=b['name'],naive_preserved_apex='FAIL: '+reason,proposed_apex_mm=new[1][2],points=new,length_mm=sum(x['length'] for x in parts),clearance_contact_and_cad='NOT CHECKED'))
 out={'scope':'source analytic fillet/path proposal only; no CAD/contact, collisions, native gas, thermal mapping or solved device','tabs':rows,'detector_bonds':bonds,'status':'SOURCE PATH CONSTRUCTIBLE; ASSEMBLY NOT QUALIFIED'}
 p=DATA/'formed_paths_proposal.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
