"""Reproducible static engineering figures from scenario CSV; not FEM plots."""
from pathlib import Path
import argparse
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def records(path):
    with Path(path).open(newline='') as f:
        return list(csv.DictReader(f))


def render(folder):
    folder=Path(folder)
    sweep=records(folder/'sweep.csv')
    sensitivity=records(folder/'sensitivity.csv')
    names=[
        ('vacuum_low_parasitic','Low-parasitic vacuum'),
        ('nominal_krypton','Nominal Kr cavity'),
        ('nitrogen_high_parasitic','High-parasitic N2 cavity'),
    ]
    fig,ax=plt.subplots(figsize=(8.4,5.5))
    for name,title in names:
        valid={round(float(r['current_a']),2):float(r['detector_k'])
               for r in sweep if r['scenario']==name}
        currents=[i/20 for i in range(21)]
        # Disconnected source-domain failures must NOT be bridged by a line.
        ax.plot(currents,[valid.get(round(i,2),float('nan')) for i in currents],
                marker='o',label=title)
    ax.axhline(300,linestyle=':',linewidth=1,label='Ambient: 300 K')
    ax.set(xlabel='TEC series current (A)',ylabel='HgCdTe die temperature (K)',
           title='Corrected-geometry thermal reference: scenario screening')
    ax.grid(alpha=.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(folder/'die_temperature_vs_current.png',dpi=190)
    plt.close(fig)

    # Do not imply magnitude comparable across factors with arbitrary interval widths.
    ordered=list(reversed(sensitivity))
    fig,ax=plt.subplots(figsize=(9.4,6.8))
    names=[r['factor'] for r in ordered]
    spans=[float(r['endpoint_span_abs_k']) for r in ordered]
    ax.barh(range(len(spans)),spans)
    ax.set_yticks(range(len(names)),labels=names)
    ax.set(xlabel='Absolute endpoint temperature difference (K)',
           title='One-at-a-time engineering spans (not statistical uncertainty)')
    ax.grid(axis='x',alpha=.25)
    fig.subplots_adjust(left=.36,right=.96,bottom=.13,top=.89)
    fig.savefig(folder/'sensitivity_spans.png',dpi=190)
    plt.close(fig)
    return [str(folder/'die_temperature_vs_current.png'),
            str(folder/'sensitivity_spans.png')]


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--from-dir',dest='folder',required=True)
    a=ap.parse_args()
    print('\n'.join(render(a.folder)))
