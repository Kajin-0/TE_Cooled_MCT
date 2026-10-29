"""Preregistered data access, source integrity and deterministic OEM residuals."""
from pathlib import Path
import hashlib,json
from .fem_g2c import intact_checkpoints
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/g2d'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')

def preserve():
    old=intact_checkpoints();archive=ROOT/'fem/results/g2c_20261028';index=json.loads((archive/'checksums.json').read_text())
    for name,h in index['source_sha256'].items():
        if sha(ROOT/name)!=h:raise ValueError(f'Protected G2c source changed: {name}')
    for name,h in index['verification_test_source_sha256'].items():
        if sha(ROOT/name)!=h:raise ValueError(f'Protected earlier test changed: {name}')
    for name,h in index['artifacts_sha256'].items():
        if sha(archive/name)!=h:raise ValueError(f'Protected G2c artifact changed: {name}')
    return {**old,'g2c_unchanged':True,'g2c_artifacts':len(index['artifacts_sha256'])}


def preregister():
    source=ROOT/'data/g2c/oem2019_curves_v1.json';data=json.loads(source.read_text());groups={'calibration_reserved':[],'validation_holdout':[]}
    for row in data['points']:
        r=dict(row);r.update(source_file_sha256=sha(source),source_pdf_sha256=data['original_pdf_sha256'],
            comparable_to_solid_model=r['ambient']=='vacuum' and r['hot_k']==300,
            excluded_reason=None if r['ambient']=='vacuum' and r['hot_k']==300 else 'dry N2 / hot-T and missing environment physics')
        # Horizontal reading error propagated with a same-curve source slope.
        family=[q for q in data['points'] if q['panel']==r['panel'] and q['field']==r['field'] and q['load_w']==r['load_w'] and q['id']!=r['id']]
        q=min(family,key=lambda q:abs(q['current_a']-r['current_a']))
        slope=(q['value']-r['value'])/(q['current_a']-r['current_a'])
        r['combined_reading_bound']=r['value_reading_bound']+abs(slope)*r['current_reading_bound_a'];r['unit']='K' if r['field']=='delta_t_k' else 'V'
        groups[r['split']].append(r)
    files={}
    for split,rows in groups.items():
        p=DATA/(split+'.json');dump(p,{'schema_version':1,'split':split,'points':rows,'source_json_sha256':sha(source)});files[p.name]=sha(p)
    registration={'schema_version':1,'files_sha256':files,'protected_checkpoint':'122a4172ff7661d5f3595e2ae9372afa5ddf7474',
        'split_preserved_from_g2c':True,'fit_reads_only':'calibration_reserved.json',
        'holdout_unlock':'only after frozen_fit.json and its SHA256 are written',
        'pde_directions_preregistered':[{'id':'baseline','seebeck_scale':1.,'k_scale':1.,'current_a':.2},
            {'id':'seebeck_minus10','seebeck_scale':.9,'k_scale':1.,'current_a':.2},
            {'id':'k_plus10','seebeck_scale':1.,'k_scale':1.1,'current_a':.2}],
        'pde_point_conditions':{'hot_k':300,'load_w':0,'ambient':'vacuum','profile':'original constant-law diagnostic; not measured T-dependent OEM grade'},
        'source_domain_probe':{'hot_k':300,'current_a':.1,'load_w':0,'profile':'audited G2c v2r1; strict 40..300 K guard'},
        'fit_interpretation':'Reduced-network diagnostic effective coefficients, never FEM or manufacturer-grade identification',
        'definitions':{'delta_t_k':'actual hot bath minus cold ceramic mean','current_a':'total module series current','load_w':'inward cold-face thermal load','extrema':'DeltaTmax at Qc=0; Qmax at DeltaT=0, not simultaneous'},
        'measurement_uncertainty':'Not supplied by OEM. Bounds are chart-reading limits, not standard deviations or confidence intervals.'}
    dump(DATA/'preregistration.json',registration);return registration


def points(split):
    if split not in ('calibration_reserved','validation_holdout'):raise ValueError('Explicit split required')
    registration=json.loads((DATA/'preregistration.json').read_text());p=DATA/(split+'.json')
    if sha(p)!=registration['files_sha256'][p.name]:raise ValueError('Preregistered data changed')
    return [r for r in json.loads(p.read_text())['points'] if r['comparable_to_solid_model']]


def residual(observed,prediction):
    if prediction['hot_k']!=observed['hot_k'] or prediction['ambient']!=observed['ambient'] or prediction['current_a']!=observed['current_a'] or prediction['load_w']!=observed['load_w']:raise ValueError('Mismatched operating conditions')
    value=prediction[observed['field']];difference=value-observed['value'];bound=observed['combined_reading_bound'];threshold=.1 if observed['field']=='delta_t_k' else .05
    return {'point_id':observed['id'],'field':observed['field'],'unit':observed['unit'],'split':observed['split'],
        'observed':observed['value'],'predicted':value,'signed_residual':difference,'absolute_residual':abs(difference),
        'relative_residual':difference/observed['value'] if observed['value'] else None,'reading_bound':bound,
        'normalized_to_reading_bound':difference/bound,'direction':'over' if difference>0 else 'under' if difference<0 else 'equal',
        'within_nominal_plus_reading_bound':abs(difference)<=threshold*abs(observed['value'])+bound,'device_accuracy_proven':False}

if __name__=='__main__':preserve();print(json.dumps(preregister(),indent=2))
