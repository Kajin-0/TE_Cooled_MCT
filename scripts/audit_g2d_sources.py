#!/usr/bin/env python3
"""Audit preserved readings against original vector paths; never change a split."""
import json
import numpy as np
from tecooledmct.g2d_data import ROOT,DATA,sha,dump,preserve


def main():
    preserve();source=ROOT/'data/g2c/oem2019_curves_v1.json';paths=ROOT/'data/g2c/oem2019_vector_paths.json'
    d=json.loads(source.read_text());v=json.loads(paths.read_text());panels={p['id']:p for p in d['panels']};rows=[]
    for r in d['points']:
        p=panels[r['panel']];poly=next(q for q in v if all(q[k]==r[k] for k in ('panel','load_w','field')))
        xy=np.asarray(poly['pdf_path_xy_pt']);x=p['x0']+r['current_a']*160.1575;y=float(np.interp(x,xy[:,0],xy[:,1]));origin=p['y0'] if r['field']=='delta_t_k' else p['vy0'];scale=p['dy'] if r['field']=='delta_t_k' else p['vdy']
        value=(origin-y)/scale
        if abs(value-r['value'])>1e-10:raise ValueError('Vector / reading mismatch')
        rows.append({'id':r['id'],'split':r['split'],'panel':r['panel'],'curve_color_index':r['curve_color_index'],
            'pdf_page_index':1,'x_pdf_pt':x,'y_pdf_pt':y,'axis_x0_pdf_pt':p['x0'],'axis_y0_pdf_pt':origin,
            'x_pdf_pt_per_amp':160.1575,'y_pdf_pt_per_unit':scale,'coordinate_reading_bound_pdf_pt':1.,'recomputed_value':value,'value':r['value'],'field':r['field']})
    extension=json.loads((DATA/'material_extension_review.json').read_text());anchors={}
    for polarity,s in extension['samples'].items():
        r=s['rows'][0];a=s['independent_298K_anchor'];pf=r['S_v_k']**2*r['sigma_s_m']*1e3;zt=pf*.001*r['temperature_k']/r['k_w_mk']
        # Propagate printed last-digit rounding, not experimental uncertainty.
        sv=abs(r['S_v_k']);sig=r['sigma_s_m'];kk=r['k_w_mk']
        pf_bounds=[(sv-.005e-6)**2*(sig-.5)*1e3,(sv+.005e-6)**2*(sig+.5)*1e3]
        zt_bounds=[pf_bounds[0]*.001*r['temperature_k']/(kk+.00005),pf_bounds[1]*.001*r['temperature_k']/(kk-.00005)]
        if not (pf_bounds[0]-.00005<=a['source_pf_mw_mk2']<=pf_bounds[1]+.00005 and zt_bounds[0]-.00005<=a['source_zt']<=zt_bounds[1]+.00005):raise ValueError('Independent PF/ZT anchor mismatch')
        if s['same_physical_specimen_for_all_three_properties']:raise ValueError('Unsupported specimen matching')
        if any(np.sign(r['S_v_k'])!=(1 if polarity=='P' else -1) or abs(r['rho_ohm_m']*r['sigma_s_m']-1)>1e-12 for r in s['rows']):raise ValueError('Sign / reciprocal rho mismatch')
        anchors[polarity]={'pf_mw_mk2':pf,'zt':zt,'pf_input_rounding_bounds':pf_bounds,'zt_input_rounding_bounds':zt_bounds,'pass':True}
    out={'passed':True,'OEM_points':len(rows),'panels':d['panels'],'rows':rows,'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [source,paths,DATA/'material_extension_review.json',DATA/'oem_source_review.json',ROOT/'scripts/audit_g2d_sources.py']},
        'extension_independent_anchors':anchors,'extension_used_in_fit_or_pde':False,'note':'Original-vector cross-check, not a new OEM measurement or independent uncertainty estimate. Split retained exactly. Extension candidate is composition/process/direction matched, separate physical cuts, with derived total k.'}
    dump(ROOT/'outputs/g2d-source-audit.json',out);print('Audited',len(rows),'OEM readings and independent P/N table PF/ZT anchors')

if __name__=='__main__':main()
