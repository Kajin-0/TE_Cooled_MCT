"""Protect every earlier accepted/rejected checkpoint and the standalone report."""
from .g2d_data import ROOT,sha
from .flux_presolder_common import guard as older
import json


def preserve():
    result=older();base=ROOT/'fem/results/flux_presolder_checkpoint_20261030'
    ledger=json.loads((base/'checksums.json').read_text())
    for group,parent in [('source_sha256',ROOT),('artifact_sha256',base)]:
        for name,digest in ledger[group].items():
            if sha(parent/name)!=digest:raise ValueError('Protected flux/presolder checkpoint changed: '+name)
    return {**result,'flux_presolder_sources':len(ledger['source_sha256']),'flux_presolder_artifacts':len(ledger['artifact_sha256']),'previous_checkpoint_sha256':sha(base/'checksums.json')}
