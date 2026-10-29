"""Independent enclosure/radiation/gas physical limits and immutable predecessors."""
import math
import numpy as np
import pytest
from tecooledmct.fem_g3b_data import registry,preserve
from tecooledmct.fem_g3b_exchange import SIGMA,GASES,radiation_matrix,balanced_view_factors,gas_properties,gas_conductances,gas_power,rayleigh_screen
from tecooledmct.fem_g3b_rays import first_hits


def test_two_gray_parallel_plates_match_analytic_multiple_reflection_solution():
    a=np.array([2.,2.]);f=np.array([[0.,1.],[1.,0.]]);t=np.array([300.,250.]);e=np.array([.8,.4]);l=radiation_matrix(a,f,e);q=l@t**4
    expected=2*SIGMA*(300**4-250**4)/(1/.8+1/.4-1)
    assert q==pytest.approx([expected,-expected],rel=1e-12)
    assert np.all(radiation_matrix(a,f,0.)==0)
    assert np.max(abs(l@np.full(2,280.)**4))<1e-12
    assert np.sum(-q/t)>0


def test_reciprocal_closure_preserves_blocked_direct_views():
    # An enclosure graph with an exactly blocked opposite pair.
    raw=np.ones((4,4));np.fill_diagonal(raw,0);raw[0,2]=raw[2,0]=0;areas=np.array([1.,1.2,.9,1.1]);f,audit=balanced_view_factors(raw,areas)
    assert np.max(abs(f.sum(axis=1)-1))<1e-9
    assert np.max(abs(areas[:,None]*f-(areas[:,None]*f).T))<1e-12
    assert f[0,2]==f[2,0]==0 and audit['visibility_zeros_preserved']
    with pytest.raises(ValueError):radiation_matrix(areas,f,1.01)


def test_analytic_first_hit_occludes_roof_without_invented_escape_surface():
    m={'cavity':{'radius_m':1.,'floor_z_m':0.,'ceiling_z_m':2.,'cap_body':10,'window_body':11,'header_body':12},'package_registry':{'cap':{'window_radius_m':.3},'feedthroughs':{'centers_xy_m':[],'pin_radius_m':.02,'glass_radius_m':.05}},'pin_tops':[],'bodies':[]}
    origin=np.array([[0.,0.,.1],[0.,0.,1.]]);direction=np.array([[0.,0.,1.],[1.,0.,0.]])
    hit,bid,n=first_hits(origin,direction,m,np.array([12,12]));assert bid.tolist()==[11,10];assert hit[:,2]==pytest.approx([2.,1.]);assert hit[1,0]==pytest.approx(1.)
    m['bodies']=[{'id':99,'boxes_m':[[-.5,-.5,.8,1.,1.,.1]]}]
    hit,bid,n=first_hits(origin[:1],direction[:1],m,np.array([12]));assert bid[0]==99 and hit[0,2]==pytest.approx(.8)


@pytest.mark.parametrize('gas',list(GASES))
def test_gas_matches_continuum_and_independent_kennard_free_molecular_limit(gas):
    t=np.array([300.,260.]);area=1e-6;w=np.array([[0.,area],[area,0.]]);gap=np.ones((2,2))*.003;alpha=.8
    assert np.all(gas_conductances(w,gap,t,gas,0.)==0)
    previous=0.
    for pressure in (1e-8,1.,100.,100000.):
        g=gas_conductances(w,gap,t,gas,pressure,alpha);assert np.all(g>=0) and np.allclose(g,g.T);assert g[0,1]>previous;previous=g[0,1]
        q=gas_power(g,t);assert abs(q.sum())<1e-12;assert np.sum(q/t)>=0
    p=gas_properties(gas,280.,100000.);assert previous==pytest.approx(float(p['k'])*area/.003,rel=1e-3)
    low=gas_conductances(w,gap,t,gas,1e-8,alpha)[0,1]/1e-8;r=GASES[gas]
    kennard=alpha/(2-alpha)*(r['gamma']+1)/(r['gamma']-1)*area*math.sqrt(r['R']/(8*math.pi*280))
    assert low==pytest.approx(kennard,rel=1e-8)
    for temp in (199.99,400.01,float('nan')):
        with pytest.raises(ValueError):gas_properties(gas,temp,100.)
    with pytest.raises(ValueError):gas_conductances(w,gap,t,gas,-1.)


def test_convection_screen_distinguishes_low_pressure_from_atmospheric_krypton():
    r=rayleigh_screen();assert max(x['Ra'] for x in r if x['pressure_pa']==100)<1.
    assert next(x for x in r if x['gas']=='Kr' and x['pressure_pa']==101325 and x['gap_m']==.003)['convection_flag']
    for gas in GASES:
        assert gas_properties(gas,300.,100)['k']==pytest.approx(GASES[gas]['k'][1])


def test_nine_feedthroughs_and_old_evidence_are_explicit_and_intact():
    r=registry();assert len(r['feedthroughs']['centers_xy_m'])==9
    assert len(set(tuple(x) for x in r['feedthroughs']['centers_xy_m']))==9
    assert r['cap']['outer_radius_m']>r['cap']['inner_radius_m']>r['cap']['window_radius_m']
    assert r['supply_leads']['count']==2
    assert preserve()['g3a_unchanged']


@pytest.mark.parametrize('pressure',[0.,100.])
def test_genuine_elmer_compiled_exchange_does_not_stagnate_at_zero_initial_flux(tmp_path,pressure):
    import os,shutil
    if os.environ.get('TE_FEM_SMOKE')!='1' or not shutil.which('ElmerSolver'):
        pytest.skip('Opt-in actual Elmer nonlocal regression')
    pytest.importorskip('meshio')
    from tecooledmct.fem_g3b_plate_check import run
    result=run(tmp_path/'plates',pressure)
    assert result['passed'] and result['max_temperature_error_k']<1e-6
    assert abs(result['actual_conduction_balance_w'])<1e-9


def test_local_edge_bisection_preserves_conformal_interfaces_and_exact_p1_fields():
    from tecooledmct.fem_g3b_bath_refine import bisect_edges,prolong
    from tecooledmct.fem_g2a import mesh_adjacency
    from tecooledmct.fem_g1 import tetra_geometry
    p=np.array([[0.,0,0],[1.,0,0],[0.,1,0],[0.,0,1],[0.,0,-1]])
    c=np.array([[0,1,2,3],[0,2,1,4]]);b=np.array([190,194]);adj=mesh_adjacency(c);f=np.array(list(adj));tags=np.array([1001 if len(v)==2 else 105 for v in adj.values()])
    pp,cc,bb,ff,tt,mid=bisect_edges(p,c,b,f,tags,[(0,1),(0,2),(1,3)])
    vv,_=tetra_geometry(pp,cc)
    for bid in b:assert vv[bb==bid].sum()==pytest.approx(1/6,rel=1e-13)
    assert np.all(np.linalg.det(pp[cc[:,1:]]-pp[cc[:,:1]])>0)
    actual=mesh_adjacency(cc)
    assert all(len(actual[tuple(sorted(row))])==(2 if tag==1001 else 1) for row,tag in zip(ff,tt))
    assert {tuple(sorted(row)) for row,tag in zip(ff,tt) if tag==105}=={k for k,v in actual.items() if len(v)==1}
    interface=pp[ff[tt==1001]];area=np.linalg.norm(np.cross(interface[:,1]-interface[:,0],interface[:,2]-interface[:,0]),axis=1).sum()/2
    assert area==pytest.approx(.5,rel=1e-13)
    original=np.column_stack([280+p@[1.,2.,3.],.4+p@[.1,-.2,.3]])
    expected=np.column_stack([280+pp@[1.,2.,3.],.4+pp@[.1,-.2,.3]])
    np.testing.assert_allclose(prolong(original,mid),expected,atol=1e-13,rtol=0)
