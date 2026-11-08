#!/usr/bin/env python3
"""Fail-closed grade-matched OEM thermoelectric source-data intake gate.

This is DATA VALIDATION ONLY. It does not change any working solver or
accept unverifiable labels as measurement evidence. A qualified candidate
needs both P and N property curves S/rho/k across registered working 88
source leg boundary temperatures 209.901..304.615 K, finite SI values,
uncertainty, evidence citations, supplier ID and source pairing status.
Even a passing candidate is eligible for *engineering review*, never
automatically changes V3.2 or establishes detector prediction accuracy.
"""
from pathlib import Path
import argparse,json,math,hashlib
ROOT=Path(__file__).resolve().parents[1]
OPER=ROOT/'data/v3_2_material_readiness_20261107/attempt01/material_contract.json'
REQUIRED={'S':'V/K','rho':'ohm m','k':'W/(m K)'}
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(data):
 required_main=('source_description','manufacturer','module_model_number',
 'module_source_document','material_grade_pairing_evidence',
 'curves','measurement_condition','raw_curve_traceability')
 problems=[]
 for key in required_main:
  if key not in data:problems.append(f'MISSING_FIELD {key}')
 for key in ('manufacturer','module_model_number','module_source_document',
              'material_grade_pairing_evidence','raw_curve_traceability'):
  val=data.get(key)
  if not isinstance(val,str) or len(val.strip())<10:
   problems.append('MISSING_GROUNDED_EVIDENCE '+key)
 require=read(OPER)
 req_lo,req_hi=require['working_V3_2_temperature_extrema_K']
 c=data.get('curves')
 valid=[]
 if not isinstance(c,dict):problems.append('MISSING_P_N_PROPERTIES')
 else:
  for polarity in ('P','N'):
   pc=c.get(polarity)
   if not isinstance(pc,dict):
    problems.append('MISSING_POLARITY '+polarity);continue
   for prop,unit in REQUIRED.items():
    item=pc.get(prop)
    if not isinstance(item,dict):
     problems.append('MISSING_CURVE '+polarity+'/'+prop);continue
    if item.get('unit')!=unit:problems.append('INVALID_UNIT '+polarity+'/'+prop)
    rows=item.get('measurements')
    if not isinstance(rows,list) or len(rows)<3:
     problems.append('MISSING_AT_LEAST_3_MEASURED_VALUES '+polarity+'/'+prop);continue
    good=True;temp=[]
    for i,row in enumerate(rows):
     if not isinstance(row,dict):good=False;break
     values=(row.get('temperature_K'),row.get('value_SI'),row.get('absolute_uncertainty_SI'))
     if not all(isinstance(z,(int,float)) and math.isfinite(z) for z in values):
      good=False;break
     t,x,err=values
     if err<=0 or (prop!='S' and x<=0) or (
       prop=='S' and x*(1 if polarity=='P' else -1)<=0):
      good=False;break
     if not isinstance(row.get('evidence_reference'),str) or len(row['evidence_reference'].strip())<6:
      good=False;break
     temp.append(t)
    if not good or any(b<=a for a,b in zip(temp,temp[1:])):
     problems.append('INVALID_MEASUREMENT_OR_UNCERTAINTY_OR_SOURCE '+polarity+'/'+prop)
     continue
    if temp[0]>req_lo or temp[-1]<req_hi:
     problems.append('INSUFFICIENT_T_RANGE '+polarity+'/'+prop+
       f' [{temp[0]:.3f},{temp[-1]:.3f}] vs required [{req_lo:.3f},{req_hi:.3f}]K')
     continue
    valid.append(polarity+'/'+prop)
 # Exact source batch/matched supplier cannot be authenticated by
 # declarative text alone. Force a separate scientific signoff after
 # all input curve conditions pass.
 enough=len(valid)==6 and not problems
 return {
  'status':'DATA_SCHEMA_INCOMPLETE' if problems else
      'SCHEMA_COMPLETE_PENDING_INDEPENDENT_GRADE_AND_MEASUREMENT_REVIEW',
  'all_six_curves_and_temp_coverage_claimed':enough,
  'missing_or_invalid_evidence':problems,
  'included_curve_keys':valid,
  'required_source_working_T_K':[req_lo,req_hi],
  'independent_actual_module_grade_identity_verified':False,
  'source_measurement_credibility_independently_verified':False,
  'auto_update_existing_V3_2':False,
  'OEM_grade_physical_material_release':False,
  'original_P1_Gate_B':'FAIL/STOP','full_430_C_D':'NOT RUN',
 }
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--candidate',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--verify-only',action='store_true')
 a=p.parse_args();d=read(a.candidate)
 result=validate(d)
 result['candidate_sha256']=sha(a.candidate)
 result['validator_sha256']=sha(Path(__file__))
 result['source_requirement_sha256']=sha(OPER)
 if a.verify_only:assert result==read(a.output)
 else:
  assert not a.output.exists()
  a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('OEM_PN_GRADE_INPUT_CONTRACT',result['status'],
  'issues',len(result['missing_or_invalid_evidence']))
if __name__=='__main__':main()
