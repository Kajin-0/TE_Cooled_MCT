"""Re-encode the exact archived corrected mesh; no CAD remeshing or old package."""
import argparse,json,shutil
from pathlib import Path
import numpy as np
from .geometry_rebaseline import ROOT,sha,write
from .fem_g1_run import execute
from .fem_g2c_mesh import verify_elmer_tetra_mapping


def prepare(out):
    import meshio
    if out.exists():raise ValueError('Choose a new mesh reconstruction label')
    src=ROOT/'fem/results/geometry_complete_checkpoint_20261030';ledger=json.loads((src/'checksums.json').read_text())
    out.mkdir(parents=True)
    for name in ('mesh.npz','manifest.json','wire_routes.json'):
        if sha(src/name)!=ledger['artifact_sha256'][name]:raise ValueError('Protected corrected geometry changed')
        shutil.copy2(src/name,out/name)
    d=np.load(out/'mesh.npz');p,c,b,f,tags=[d[n] for n in ('points','cells','bodies','faces','boundaries')]
    meshio.write(out/'connected.msh',meshio.Mesh(p,[('triangle',f),('tetra',c)],cell_data={'gmsh:physical':[tags,b],'gmsh:geometrical':[tags,b]}),file_format='gmsh22',binary=False)
    status,_=execute(['ElmerGrid','14','2','connected.msh','-out','elmer'],out,'grid')
    proof=verify_elmer_tetra_mapping(out);proof.update(mesh_sha256=sha(out/'mesh.npz'),source_sha256=sha(Path(__file__)),
                       basis='exact protected NPZ arrays re-encoded; actual Elmer nodes/tetrahedra/body labels checked; new node order permitted')
    write(out/'mapping_audit.json',proof);print('Exact corrected mesh reconstructed:',proof,flush=True)
    return proof


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);prepare(p.parse_args().out.resolve())
