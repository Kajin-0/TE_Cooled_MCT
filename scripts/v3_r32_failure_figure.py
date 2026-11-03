"""Actual saved phase/resource plot only; no mesh/field image is fabricated."""
from pathlib import Path
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/v3_r32_global_surface_20261103'


def main():
    out=DATA/'figures';out.mkdir(exist_ok=False)
    result=json.loads((DATA/'run/result.json').read_text())
    execution=json.loads((DATA/'execution_receipt.json').read_text())
    names=['Source import/checks','Native sizing','Shared1D mesh','Exact ten directional patches',
           'Native global2D fill','Seed-tag guard: STOP']
    phases=list(result['phases'].values())
    times=[q['wall_seconds'] for q in phases]
    fig,ax=plt.subplots(figsize=(10,4.7))
    ax.barh(range(len(names)),times,color=['#466f8b']*5+['#b24b45'])
    ax.set_yticks(range(len(names)),names);ax.invert_yaxis()
    ax.set_xscale('log');ax.set_xlim(.0001,10)
    for i,t in enumerate(times):ax.text(t*1.15,i,f'{t:.4f}s',va='center',fontsize=9)
    ax.set_xlabel('Measured phase wall time (seconds, log scale)')
    ax.grid(axis='x',alpha=.2)
    ax.set_title('R3.2 ONE trial: native meshing returned, qualification STOPPED before archive')
    fig.text(.5,.015,f"End-to-end {execution['wall_seconds']:.3f}s; CPU {execution['CPU_seconds']:.3f}s. No saved MSH / area or quality qualification.",
             ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.06,1,1));fig.savefig(out/'actual_phase_stop.png',dpi=180);plt.close(fig)
    (out/'provenance.json').write_text(json.dumps(dict(result_SHA256=hashlib.sha256((DATA/'run/result.json').read_bytes()).hexdigest(),
        execution_SHA256=hashlib.sha256((DATA/'execution_receipt.json').read_bytes()).hexdigest(),
        source_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        actual_mesh_or_field_visual='NOT AVAILABLE; not substituted',no_mesh_generation=True,no_PDE=True),indent=2)+'\n')


if __name__=='__main__':main()
