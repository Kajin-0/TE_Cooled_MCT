"""Independent all-port sensitivity review of saved, fixed-model predictions.

The study's initial sharp-cut screen covers eight section powers only. This
review also checks every condensed port, including the P174 side contact; a
quiet sharp-cut screen cannot establish the registered general heat-path gate.
No coefficient, temperature or power is modified by this review.
"""
import argparse
from pathlib import Path

from .nonlocal_solid_network import read,sha,ROOT,PORT_NAMES
from .nonlocal_solid_study import write


def assess(result):
    coarse,fine=result['levels'][0],result['levels'][-1]
    powers=[]
    for name,a,b in zip(PORT_NAMES,coarse['network_into_ports_w'],fine['network_into_ports_w']):
        change=abs(a-b)/max(abs(b),1e-12)
        powers.append({'port':name,'coarse_w':a,'fine_w':b,'relative_change':change,'exceeds_5_percent':change>.05})
    cold=abs(coarse['temperatures_k'][3]-fine['temperatures_k'][3])
    sharp=any(r['coarse_fine_relative_power_change']>.05 for r in result['discretization']['path_changes'])
    port_flag=any(r['exceeds_5_percent'] for r in powers)
    return {'schema':'independent-all-port-review-v1','cold_coarse_fine_k':cold,'ports':powers,
        'sharp_cut_screen_exceeded':sharp,'all_port_screen_exceeded':port_flag,
        'registered_sensitivity_exceeded':cold>.1 or sharp or port_flag,
        'numerical_convergence_established':False,
        'physical_mean_to_contact_closure_qualified':False,'new_mesh_release':False,
        'decision':'Stop at registered levels. Retain all predictions as conditional diagnostics; no refined-grid chase, fitted K or report change.',
        'initial_screen_limit':'diagnostic.json discretization.unresolved_flag tests cold T and sharp cuts only; it excludes the side-contact port and is not an overall pass.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path,required=True);args=p.parse_args()
    folder=args.data;path=folder/'all_port_review.json'
    if path.exists():raise ValueError('Do not overwrite an existing review')
    result=assess(read(folder/'diagnostic.json'))
    result['input_sha256']={name:sha(folder/name) for name in ('diagnostic.json','frozen_operators.json')}
    result['source_sha256']={'tecooledmct/nonlocal_solid_review.py':sha(Path(__file__))}
    write(path,result)
    print(result['decision'])


if __name__=='__main__':main()
