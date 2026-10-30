"""Physical material domains and analytic conservative wire-power regressions."""
import json
import numpy as np
import pytest
from tecooledmct.corrected_thermal import material,link_powers
from tecooledmct.fem_g2a import PROPERTIES


def test_reference_materials_preserve_seebeck_and_passive_sigma_policy():
    for name in ('P','N','Cu'):
        actual=np.array(material(name,np.array([250.,300.])))
        np.testing.assert_allclose(actual,np.repeat(np.array(PROPERTIES[name][:3])[:,None],2,axis=1))
    for name in ('Alumina','Kovar','Pin','Glass','Presolder','Attach','Au','MCT'):
        k,sigma,S=material(name,np.array([299.,301.]),sigma=1e-14)
        assert np.all(k>0);np.testing.assert_allclose(sigma,1e-14,rtol=1e-15,atol=0)
        np.testing.assert_array_equal(S,0)


def test_material_temperature_interpolation_and_unknown_grade_fail_closed():
    np.testing.assert_allclose(material('MCT',np.array([90.,148.,298.,400.]))[0],[2.41,1.61,.973,.790])
    assert material('MCT',223.)[0]==pytest.approx((1.61+.973)/2)
    for name,T in (('MCT',89.99),('MCT',400.01),('Presolder',289.),('Presolder',321.),('Kovar',float('nan'))):
        with pytest.raises(ValueError):material(name,np.array([T]))
    with pytest.raises(ValueError):material('undocumented_alloy',300.)


def test_analytic_two_end_wire_conduction_joule_and_off_control(tmp_path):
    # Independent two-terminal rod law: G=2W/K, R=.3ohm, I=.1A.
    row={'pin':1,'material':'Cu','pin_body':501,'target_body':190,'pin_face_tag':6001,'target_face_tag':103,
         'length_m':1.,'G_W_K':2.,'R_ohm':.3}
    (tmp_path/'wire_routes.json').write_text(json.dumps({'wires':[row]}))
    ep={'6001':{'indices':[0,1],'weights':[.25,.75]},'103':{'indices':[2,3],'weights':[.5,.5]}}
    t=np.array([300.,304.,300.,302.]);meta={'current_a':.1,'cu_leads_on':True,'au_bonds_on':False}
    node,rows,mechanisms=link_powers(tmp_path,t,meta,ep)
    # Tpin303,Tpad301: exactly4W flows pin->pad, plus3mW wire Joule.
    np.testing.assert_allclose(node,[-3.9985*.25,-3.9985*.75,4.0015*.5,4.0015*.5],atol=1e-14)
    assert node.sum()==pytest.approx(.003)
    assert mechanisms['wire_conduction'].sum()==pytest.approx(0.,abs=1e-14)
    assert rows[0]['conduction_into_pad_w']==pytest.approx(4.)
    # Reversing electrical current reverses no Joule heating; thermal direction
    # comes from endpoint temperatures, not from arbitrary lead names.
    meta['current_a']=-.1
    np.testing.assert_allclose(link_powers(tmp_path,t,meta,ep)[0],node)
    meta['cu_leads_on']=False
    np.testing.assert_array_equal(link_powers(tmp_path,t,meta,ep)[0],0.)
