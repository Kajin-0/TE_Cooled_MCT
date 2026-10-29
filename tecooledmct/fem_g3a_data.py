"""G3a source hypotheses and immutable predecessor integrity."""
import json
from .g2d_data import ROOT,sha,dump,preserve as earlier


def preserve():
    r=earlier();p=ROOT/'fem/results/g2d_20261029';d=json.loads((p/'checksums.json').read_text())
    for n,h in d['source_sha256'].items():
        if sha(ROOT/n)!=h:raise ValueError('Protected G2d source changed: '+n)
    for n,h in d['artifact_sha256'].items():
        if sha(p/n)!=h:raise ValueError('Protected G2d evidence changed: '+n)
    return {**r,'g2d_unchanged':True,'g2d_artifacts':len(d['artifact_sha256'])}


def registry():
    return {'geometry_status':'assumed solver construction, not OEM tooling; actual G2b TEC retained',
      'header':{'ellipse_semiaxes_m':[.01575,.00875],'thickness_m':.0011,'mount_hole_centers_x_m':[-.0122,.0122],'mount_hole_radius_m':.00185,'material':'Kovar proxy','k_w_mk':17.3},
      'feedthroughs':{'illustrated_pin_count':9,'actually_meshed_pin_count':2,'centers_x_m':[-.0054,.0054],'glass_radius_m':.00055,'pin_radius_m':.00022,'pin_above_header_m':.0009,'pin_below_header_m':.002,'pin_k_w_mk':17.3,'glass_k_w_mk':1.,'status':'assumed Kovar pins/glass proxy; remaining seven seals/holes/pins omitted, no fixed pin temperatures'},
      'hot_mount':{'thickness_m':50e-6,'k_w_mk':2.,'status':'assumed insulating thermal joint; no asserted solder grade'},
      'die_attach':{'width_m':.00125,'thickness_m':80e-6,'k_w_mk':1.,'status':'assumed insulating epoxy-equivalent; no chemistry claim'},
      'mct':{'width_m':.001,'thickness_m':.00012,'x':.29,'temperature_k':[90,148,298,400],'k_w_mk':[2.41,1.61,.973,.790],'cp_j_kgk':[130,146,176,194],'density_kg_m3':6830,'doi':'10.1364/AO.47.000578','url':'https://opg.optica.org/ao/abstract.cfm?uri=ao-47-4-578','source':'Heckman/Gonzalez/Guha (2008), original Table2, x=.29; k derived from measured density/Cp/diffusivity','source_relative_uncertainty_ranges':{'density':[.01,.04],'cp':[.05,.10],'diffusivity':[.05,.10],'k':[.07,.14]},'policy':'piecewise linear in local nodal T; reject outside90..400 K; no x interpolation; no transient calculation'},
      'wires':{'type':'hybrid massless 1D Fourier conductance between area-weighted 3D endpoint patches','number':2,'diameter_m':25e-6,'length_m':.007,'k_w_mk':315.,'pad_width_m':.00015,'pad_thickness_m':20e-6,'pad_centers_x_m':[-.0003,.0003],'source_url':'https://www.inseto.com/wp-content/uploads/2022/08/Gold-Wire-Data-Sheet.pdf','status':'vendor Au bulk proxy, chosen bond length/diameter; no resolved 3D wire arc, no detector electric current/Joule path'},
      'electrical_package_policy':'S=0 and computational sigma=1e-12 S/m on non-TEC domains, for a connected passive potential extension. This is not physical Au/Kovar conductivity. Fourier thermal model; bound parasitic current/Joule and test100x lower sigma.',
      'boundaries':'300 K on header underside only; all other external faces insulated except equal/opposite hybrid wire endpoint fluxes; no pin-top clamp',
      'heating':'uniform actual MCT volume source=(one bias-power representation + absorbed optical thermal power)/volume',
      'sources':{'geometry':'geometry/reference_cad.py and revision6 assumptions, visual dimensions rebuilt independently','kovar':'https://www.ametekinterconnect.com/-/media/ametek-ecp/v2/files/cw_datasheets_sds_cfsi/datasheets/kovar.pdf?la=en','TEC':'protected G2b constant verification properties; no measured wide-T or OEM-grade accuracy'},
      'missing':['seven feedthroughs','cap/window','gas','radiation','thermistor','TEC supply lead heat leakage','actual contact chemistry/tensors','carrier transport','transients']}


def wire_conductance(number=2,diameter=25e-6,length=.007,k=315.):
    import math
    if number<0 or int(number)!=number or min(diameter,length,k)<=0:raise ValueError('Invalid wire geometry')
    return number*k*math.pi*diameter**2/(4*length)
