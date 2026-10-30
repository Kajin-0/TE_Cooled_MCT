"""Normal refinement changes owner depth, not interface geometry or remote cells."""
import numpy as np
import pytest
from tecooledmct.cold_layer_benchmark import geometry
from tecooledmct.fem_g2a import mesh_adjacency
from tecooledmct.cold_interface_audit import affine
from tecooledmct.gate_refinement import normal_edges,refine_edges


def test_normal_edge_star_halves_owner_height_and_keeps_far_domain_exact():
    p,c,b=geometry(2,[1,1,1]);adj=mesh_adjacency(c);f=[];tags=[]
    for face,owners in adj.items():
        if len(owners)==1 or b[owners[0]]!=b[owners[1]]:
            f.append(face);tags.append(12 if len(owners)==2 and sorted(b[owners])==[1,2] else 999)
    f=np.array(f);tags=np.array(tags);interface=f[tags==12];edges=normal_edges(c,b,interface,adj)
    pp,cc,bb,ff,tt=refine_edges(p,c,b,f,tags,edges);newadj=mesh_adjacency(cc)
    np.testing.assert_array_equal(ff[tt==12],interface)
    np.testing.assert_array_equal(cc[bb==3],c[b==3])
    v,_=affine(p,c,np.zeros(len(p)));vv,_=affine(pp,cc,np.zeros(len(pp)))
    for face in interface:
        old=adj[tuple(sorted(face))];new=newadj[tuple(sorted(face))]
        for bid in (1,2):
            a=next(i for i in old if b[i]==bid);z=next(i for i in new if bb[i]==bid)
            assert vv[z]==pytest.approx(v[a]/2,rel=1e-11)
    for bid in (1,2,3):assert vv[bb==bid].sum()==pytest.approx(v[b==bid].sum(),rel=1e-12)


def test_region_comparison_allows_node_renumbering_but_rejects_changed_tetrahedra():
    from tecooledmct.gate_refinement_study import same_region
    p,c,b=geometry(2,[1,1,1]);a={'points':p,'cells':c,'bodies':b}
    permutation=np.arange(len(p))[::-1];inverse=np.argsort(permutation)
    z={'points':p[permutation],'cells':inverse[c[:,::-1]],'bodies':b.copy()}
    assert same_region(a,z,[1,2,3])
    bad={k:v.copy() for k,v in z.items()};bad['cells'][0]=bad['cells'][1]
    assert not same_region(a,bad,[1])
    bad={k:v.copy() for k,v in z.items()};bad['bodies'][bad['bodies']==2]=3
    assert not same_region(a,bad,[2])
