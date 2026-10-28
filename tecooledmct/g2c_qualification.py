"""OEM holdout comparisons and auditable contact parameters; never a fitted claim."""
from dataclasses import dataclass,asdict
import json,math
from .material_profiles import DATA

@dataclass(frozen=True)
class Contact:
    electrical_ohm_m2: float=0.
    thermal_m2_k_w: float=0.
    thickness_m: float=10e-6
    material_status: str='assumed interface; no OEM measurement'

    def __post_init__(self):
        if not all(math.isfinite(v) for v in (self.electrical_ohm_m2,self.thermal_m2_k_w,self.thickness_m)) or min(self.electrical_ohm_m2,self.thermal_m2_k_w)<0 or self.thickness_m<=0:
            raise ValueError('Nonnegative finite contact resistances and positive thickness required')

    def layer_parameters(self,area_m2):
        if not math.isfinite(area_m2) or area_m2<=0:raise ValueError('Positive finite area required')
        return {**asdict(self),'electrical_resistance_ohm':self.electrical_ohm_m2/area_m2,
            'thermal_resistance_k_w':self.thermal_m2_k_w/area_m2,
            'layer_sigma_s_m':None if not self.electrical_ohm_m2 else self.thickness_m/self.electrical_ohm_m2,
            'layer_k_w_mk':None if not self.thermal_m2_k_w else self.thickness_m/self.thermal_m2_k_w,
            'zero_limit':'null means ideal continuity, not zero conductivity',
            'joule_location':'I^2 R must be dissipated inside explicitly meshed contact domains',
            'solver_gate':'NOT EXECUTED; parameters alone are not an interface PDE'}


def holdout_compare(predictions,split='validation_holdout'):
    source=json.loads((DATA/'oem2019_curves_v1.json').read_text());out=[]
    for p in predictions:
        hot=p.get('hot_k',300);ambient=p.get('ambient','vacuum')
        if ambient!='vacuum' and not p.get('environment_physics_qualified',False):
            raise ValueError('Non-vacuum comparison requires explicitly represented environmental physics')
        for r in source['points']:
            if r['split']!=split or r['ambient']!=ambient or r['hot_k']!=hot:continue
            if abs(p['current_a']-r['current_a'])>1e-10 or abs(p['load_w']-r['load_w'])>1e-10:continue
            value=p[r['field']];delta=value-r['value'];relative=delta/r['value'] if abs(r['value'])>1e-12 else None
            threshold=.05 if r['field']=='voltage_v' else .10
            # Bound includes horizontal reading error times source local slope;
            # model error and manufactured-device uncertainty remain unknown.
            family=sorted([v for v in source['points'] if v['panel']==r['panel'] and v['load_w']==r['load_w'] and v['field']==r['field']],key=lambda x:x['current_a'])
            neighbor=min((v for v in family if v['id']!=r['id']),key=lambda x:abs(x['current_a']-r['current_a']))
            slope=(neighbor['value']-r['value'])/(neighbor['current_a']-r['current_a'])
            bound=r['value_reading_bound']+abs(slope)*r['current_reading_bound_a']
            out.append({'source_point_id':r['id'],'split':split,'field':r['field'],'current_a':r['current_a'],'load_w':r['load_w'],
                'source_value':r['value'],'fem_value':value,'residual':delta,'relative_residual':relative,'source_reading_bound':bound,
                'nominal_error_gate':threshold,'within_nominal_gate':abs(delta)<=threshold*abs(r['value'])+bound,
                'qualification_status':'diagnostic comparison only; gas/radiation/mounting omitted, inferred geometry, unmatched material grade',
                'fem_origin':p['origin']})
    return {'fit_performed':False,'calibration_points_used':0,'split':split,'comparisons':out,
        'device_validation_passed':False,'reason':'No independent grade/geometry/contact/environment qualification or calibrated family; diagnostic discrepancies do not identify unique parameters.'}


def family_objective(predictions,split='calibration_reserved'):
    """Declared full I-V-DeltaT/load-family score; reading bounds are not sigmas.

    No optimization is performed here. Incomplete families cannot claim calibrated
    or held-out device validation. Environmental mismatches are rejected upstream.
    """
    result=holdout_compare(predictions,split)
    rows=result['comparisons']
    source=json.loads((DATA/'oem2019_curves_v1.json').read_text())
    expected={r['id'] for r in source['points'] if r['split']==split}
    observed={r['source_point_id'] for r in rows}
    return {'split':split,'observations':len(rows),'score_sum_squared_reading_bound_residual':sum((r['residual']/r['source_reading_bound'])**2 for r in rows),
        'statistical_likelihood':False,'fit_performed':False,
        'identifiability':{'status':'NOT IDENTIFIED; FEM parameter Jacobian not computed',
            'unknown_groups':['P/N grade property curves','individual stage dimensions/counts','contact electrical/thermal resistance','interstage routing','environment/lead/mounting heat paths'],
            'structural_ambiguity':'R scales as L/(sigma A), K as k A/L and alpha as couple count times P/N thermopower; multiple geometry/property/contact choices can reproduce similar terminal curves.'},
        'full_family_coverage_established':expected.issubset(observed)}
