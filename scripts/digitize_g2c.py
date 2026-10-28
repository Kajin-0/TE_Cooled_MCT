#!/usr/bin/env python3
"""Extract factual vector markers/curves from downloaded original PDFs.

Requires isolated PyMuPDF tool, not a runtime dependency. PDF coordinates are
points, origin upper left. Axes were checked against the rendered original.
Numerical precision is NOT experimental precision; bounds below are conservative
plot-reading bounds, not statistical confidence intervals.
"""
from pathlib import Path
import hashlib,json
import fitz
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/g2c'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,data):(OUT/name).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')

def materials():
    pdf=ROOT/'outputs/g2c-sources/zhang2025.pdf';doc=fitz.open(pdf)
    # x axis extends to 325 K, labelled major ticks through 300 K. Each
    # tuple: page, figure-panel, x0,y0(bottom),x1,y1(top), vertical full scale.
    axes={'N':{'rho':(2,'2a',159.824,589.128,284.468,488.652,12e-6),
               'S':(2,'2b',336.139,589.191,461.273,488.356,-240e-6),
               'k':(2,'2d',336.133,715.541,460.786,615.167,10.)},
          'P':{'rho':(3,'3a',158.873,580.271,286.243,477.597,14e-6),
               'S':(3,'3b',332.376,580.303,459.769,477.664,240e-6),
               'k':(3,'3d',332.492,710.336,459.840,607.674,8.)}}
    specimens={}
    for polarity,properties in axes.items():
        curves={}
        for prop,(page,panel,x0,y0,x1,y1,scale) in properties.items():
            rows=[]
            for d in doc[page].get_drawings():
                if d['fill']!=(1.,0.,0.) or d['color']!=(1.,0.,0.):continue
                r=d['rect'];x,y=(r.x0+r.x1)/2,(r.y0+r.y1)/2
                if not (x0<x<x1 and y1<y<y0):continue
                raw_t=325*(x-x0)/(x1-x0);nominal=round(raw_t/20)*20
                if nominal<200 or nominal>300 or abs(raw_t-nominal)>1:continue
                lower,upper=(-240e-6,0.) if polarity=='N' and prop=='S' else (0.,scale)
                value=lower+(upper-lower)*(y0-y)/(y0-y1)
                rows.append({'temperature_k':nominal,'value_si':value,
                    'vector_center_pt':[x,y],'axis_temperature_k':raw_t,
                    'temperature_reading_bound_k':325*.5/(x1-x0),
                    'value_reading_bound_si':abs(scale)*.5/(y0-y1)})
            rows.sort(key=lambda r:r['temperature_k'])
            assert [r['temperature_k'] for r in rows]==list(range(200,301,20)),(polarity,prop,rows)
            curves[prop]={'unit':{'rho':'ohm m','S':'V/K','k':'W/(m K)'}[prop],
                'pdf_page_index':page,'figure_panel':panel,
                'axes_pt':[x0,y0,x1,y1],'axis_x_range_k':[0,325],
                'axis_y_range_si':[-240e-6,0.] if polarity=='N' and prop=='S' else [0,scale],'points':rows}
        specimens[polarity]={'sample_id':'N-HE-1' if polarity=='N' else 'P-HE',
            'composition':'Bi2(Te,Se)3' if polarity=='N' else '(Bi,Sb)2Te3',
            'process':'hot extrusion','supplier_grade':'not named in main paper; supplement unavailable',
            'same_specimen_triple_properties':True,'curves':curves}
    save('zhang2025_he_v1.json',{'schema_version':1,'id':'zhang2025_he_digitized_v1r1',
        'status':'published_sample_plot_digitization','source_url':'https://cpl.iphy.ac.cn/en/article/id/eff94ac0-79aa-4d9d-b706-fcf56e7577e6',
        'doi':'10.1088/0256-307X/42/5/056304','original_pdf_sha256':sha(pdf),
        'valid_temperature_k':[200,300],'specimens':specimens,'oem_grade_matched':False,
        'paired_module_specimens':False,'extrapolation_policy':'reject',
        'interpolation':'piecewise linear rho, S and k; sigma=1/rho',
        'measurement_uncertainty':'Paper reports low-temperature uncertainty analysis; plot-reading bounds here exclude specimen variability and systematic measurement uncertainty. No empirical device confidence interval.',
        'digitization':'red marker centres, original PDF vector paths; +/-0.5 PDF point axis/centre reading bound; no guide-to-eye lines used',
        'prepublication_correction':'N Seebeck axis is -240 microV/K at bottom and zero at top; corrected offset and trend, all affected prior runs quarantined.',
        'coverage_note':'Only six markers 200..300 K per property ingested. Published wider-range figures are not implicitly qualified.'})

def oem():
    pdf=ROOT/'outputs/g2c-sources/oem2019.pdf';p=fitz.open(pdf)[1]
    colors=[(.979,.289,.071),(.209,.49,.642),(.087,.341,.47),(0.,.473,.259),(.481,.104,.48)]
    panels=[{'id':'300K_vacuum','hot_k':300,'ambient':'vacuum','qmax_w':.51,'loads_w':[0,.10,.20,.31,.41],'x0':91.654243,'y0':309.38977,'dy':132/120,'vy0':359.3898,'vdy':10},
            {'id':'323K_dry_n2','hot_k':323,'ambient':'dry_N2','qmax_w':.58,'loads_w':[0,.12,.23,.35,.46],'x0':335.103088,'y0':309.38977,'dy':132/120,'vy0':359.3898,'vdy':10},
            {'id':'348K_dry_n2','hot_k':348,'ambient':'dry_N2','qmax_w':.63,'loads_w':[0,.13,.25,.38,.50],'x0':91.528252,'y0':627.38977,'dy':132/140,'vy0':679.3898,'vdy':7.5},
            {'id':'358K_dry_n2','hot_k':358,'ambient':'dry_N2','qmax_w':.65,'loads_w':[0,.13,.26,.39,.52],'x0':335.103088,'y0':627.38977,'dy':132/140,'vy0':679.3898,'vdy':7.5}]
    rows=[];curves=[]
    for pi,panel in enumerate(panels):
        for ci,color in enumerate(colors):
            matches=[d for d in p.get_drawings() if d['color'] and max(abs(a-b) for a,b in zip(d['color'],color))<.025 and len(d['items'])>50]
            matches=[d for d in matches if (d['rect'].x0<300)==(pi in (0,2)) and (d['rect'].y0<450)==(pi<2)]
            assert len(matches)==2,(pi,ci,len(matches))
            for d in matches:
                field='delta_t_k' if d['rect'].y1<panel['y0']+2 else 'voltage_v'
                y0=panel['y0'] if field=='delta_t_k' else panel['vy0'];dy=panel['dy'] if field=='delta_t_k' else panel['vdy']
                pts=[d['items'][0][1],*[item[2] for item in d['items']]]
                assert all(it[0]=='l' for it in d['items'])
                xv=np.array([(v.x-panel['x0'])/160.1575 for v in pts]);yv=np.array([(y0-v.y)/dy for v in pts])
                curves.append({'panel':panel['id'],'load_w':panel['loads_w'][ci],'field':field,'pdf_path_xy_pt':[[v.x,v.y] for v in pts]})
                for current in (.1,.2,.4,.6,.8,1.):
                    if xv.min()<=current<=xv.max():
                        value=float(np.interp(current,xv,yv))
                        if field=='delta_t_k' and value<0:continue
                        rows.append({'id':f'{pi}-{ci}-{field}-{current}', 'panel':panel['id'],'hot_k':panel['hot_k'],'ambient':panel['ambient'],
                            'load_w':panel['loads_w'][ci],'load_fraction_label':ci*.2,'current_a':current,'field':field,'value':value,
                            'current_reading_bound_a':1/160.1575,'value_reading_bound':1/dy,
                            'split':'calibration_reserved' if current in (.2,.6,1.) else 'validation_holdout',
                            'source_pdf_page_index':1,'curve_color_index':ci,'measurement_uncertainty':'not supplied by manufacturer'})
    save('oem2019_curves_v1.json',{'schema_version':1,'id':'3MC04-044-05_2019_vectors_v1','source_url':'https://www.tec-microsystems.com/Download/Datasheets/Thermoelectric%20Coolers/MC04%20Series/3MC04-044-05_Datasheet_2019.pdf',
        'original_pdf_sha256':sha(pdf),'panels':panels,'points':rows,
        'digitization':'Original PDF colored polylines, axis calibration visually checked; conservative +/-1 PDF point reading bound, not manufacturer measurement uncertainty',
        'curve_status':'DIGITIZED','fit_status':'NOT FITTED; split reserved before any comparison',
        'split_rule':'currents .2,.6,1.0 A reserved calibration; .1,.4,.8 A withheld; all loads/panels retain split',
        'limits':{'delta_t_max_k':113,'qmax_300k_vacuum_w':.51,'imax_a':1.,'umax_v':3.5,'acr_300k_ohm':2.9,'simultaneous_conditions':False},
        'axes_note':'Chart grid is rounded to integer PDF points; reading bounds include that offset. Loads use printed W values, not silently recomputed percentages.'})
    save('oem2019_vector_paths.json',curves)

if __name__=='__main__':materials();oem()
