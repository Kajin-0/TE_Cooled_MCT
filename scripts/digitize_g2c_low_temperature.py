#!/usr/bin/env python3
"""Additive v2 extraction: original HE markers from 40--300 K, preserving v1."""
from pathlib import Path
import hashlib,json
import fitz
ROOT=Path(__file__).resolve().parents[1]

def main():
    original=ROOT/'outputs/g2c-sources/zhang2025.pdf';doc=fitz.open(original)
    data=json.loads((ROOT/'data/g2c/zhang2025_he_v1.json').read_text())
    if hashlib.sha256(original.read_bytes()).hexdigest()!=data['original_pdf_sha256']:raise ValueError('Original PDF changed')
    for sample in data['specimens'].values():
        for prop,curve in sample['curves'].items():
            x0,y0,x1,y1=curve['axes_pt'];lower,upper=curve['axis_y_range_si'];scale=upper-lower;rows=[]
            for d in doc[curve['pdf_page_index']].get_drawings():
                if d['fill']!=(1.,0.,0.) or d['color']!=(1.,0.,0.):continue
                r=d['rect'];x,y=(r.x0+r.x1)/2,(r.y0+r.y1)/2
                if not(x0<x<x1 and y1<y<y0):continue
                raw=325*(x-x0)/(x1-x0);nominal=round(raw/20)*20
                if nominal<40 or nominal>300 or abs(raw-nominal)>1:continue
                rows.append({'temperature_k':nominal,'value_si':lower+scale*(y0-y)/(y0-y1),'vector_center_pt':[x,y],'axis_temperature_k':raw,
                    'temperature_reading_bound_k':325*.5/(x1-x0),'value_reading_bound_si':abs(scale)*.5/(y0-y1)})
            rows.sort(key=lambda r:r['temperature_k'])
            if [r['temperature_k'] for r in rows]!=list(range(40,301,20)):raise ValueError((sample['sample_id'],prop,rows))
            # The v1 subset is bit-for-bit the same source measurement reading.
            if [r for r in rows if r['temperature_k']>=200]!=curve['points']:raise ValueError('v1 subset changed')
            curve['points']=rows
    data.update(id='zhang2025_he_digitized_40_300_v2r1',valid_temperature_k=[40,300],
        coverage_note='Additive v2: fourteen published markers per property at 40..300 K. Below-40 K points excluded. v1 remains unchanged; only v1 used by earlier 295 K stack runs.',
        measurement_uncertainty='Published uncertainty analysis covers 40..300 K; reading bounds stored here exclude measurement/systematic/specimen uncertainty and are not device confidence intervals.')
    out=ROOT/'data/g2c/zhang2025_he_40_300_v2.json';out.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    registry={'schema_version':1,'id':data['id'],'source_url':data['source_url'],'doi':data['doi'],'original_pdf_sha256':data['original_pdf_sha256'],
        'profile_file':out.name,'ingested_temperature_k':[40,300],'status':'Original source red markers digitized; same-specimen triple within polarity, unmatched N/P pair and OEM grade',
        'supersession':'Additive opt-in profile. Default v1 and all earlier executions/evidence retain their exact meaning.',
        'extrapolation_policy':'reject','below_40k':'not ingested or qualified'}
    (ROOT/'data/g2c/low_temperature_extension_registry.json').write_text(json.dumps(registry,indent=2)+'\n')

if __name__=='__main__':main()
