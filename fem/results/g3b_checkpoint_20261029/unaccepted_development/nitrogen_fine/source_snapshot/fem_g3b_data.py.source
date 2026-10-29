"""G3b geometry hypotheses and immutable G1..G3a checkpoints."""
import math,json,copy
from .g2d_data import ROOT,sha,dump
from .fem_g3a_data import preserve as previous,registry as baseline


def preserve():
    r=previous();p=ROOT/'fem/results/g3a_20261029';d=json.loads((p/'checksums.json').read_text())
    for n,h in d['source_sha256'].items():
        if sha(ROOT/n)!=h:raise ValueError('Protected G3a source changed: '+n)
    for n,h in d['artifact_sha256'].items():
        if sha(p/n)!=h:raise ValueError('Protected G3a artifact changed: '+n)
    return {**r,'g3a_unchanged':True,'g3a_artifacts':len(d['artifact_sha256'])}


def registry():
    p=copy.deepcopy(baseline());p['feedthroughs']['centers_xy_m']=[[-.0054,0.],[.0054,0.]]+[[.0054*math.cos(math.radians(a)),.0054*math.sin(math.radians(a))] for a in (36,72,108,144,216,252,288)]
    p['feedthroughs'].update(actually_meshed_pin_count=9,status='unnumbered nine-instance construction; first two retain G3a positions, added seven on10.8mm PCD; not OEM pinout')
    p['cap']={'outer_radius_m':.0076,'inner_radius_m':.0071,'height_m':.0086,'roof_m':.00045,'window_radius_m':.00295,'k_w_mk':15.,'status':'assumed stainless-steel-like constant thermal proxy; cap roof/side thicknesses not OEM verified'}
    p['window']={'material':'ZnSe candidate','k_w_mk':18.,'reference_temperature_k':298.,'source_url':'https://www.crystran.co.uk/optical-materials/zinc-selenide-znse/','status':'vendor conductivity proxy; no actual coatings or spectral emissivity/transmission qualification','thermal_radiation_policy':'opaque diffuse gray hypotheses; do not equate optical transmission with thermal IR absorption'}
    p['supply_leads']={'count':2,'diameter_m':.000202,'length_m':.008,'k_w_mk':400.,'rho_ohm_m':1.72e-8,'endpoint_pins':[2,3],'status':'two hybrid thermal Cu leads, assumed8mm length/AWG32 diameter; generic warm pin positions, not product pinout; include I^2R split equally at endpoints','source':'OEM AWG32 designation inherited; Cu constants protected generic reference'}
    p['missing']=['thermistor','actual product pinout/contacts/grades','carrier/absorber parts','spectral window transmission and external enclosure exchange','gas CFD','carrier transport','transients']
    return p
