"""Bounded independent imported STEP contact and curved overlap audit."""
from pathlib import Path
import signal
from tecooledmct.tec_assembly_v3_step_audit import main
R=Path(__file__).resolve().parents[1];B=R/'data/tec_height_060_cad_20261110'
def alarm(*_):raise TimeoutError('Registered 155 second contact audit budget')
if __name__=='__main__':
 signal.signal(signal.SIGALRM,alarm);signal.alarm(155)
 main(B/'cad_attempt01',B/'source_candidate',B/'imported_contact_audit_attempt01.json')
