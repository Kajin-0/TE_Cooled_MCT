#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=/home/User/TE_Cooled_MCT
W=/var/tmp/v3_r38_global_tetgen_20261105/attempt01
SOURCE="$ROOT/data/v3_r37_plc_preflight_20261105/seed_refined_01/R37_430_domains_surface_seed_refined.poly"
TETGEN=/var/tmp/r35_tetgen_plc_20261105/tetgen
IMAGE=tecooledmct-fem:26.2.1-recovered-20261105
EXPECTED_INPUT=f36eb5efc49318058f176d4661caa9e1029f5238fe3f43806d6cc911ca1deeb3
EXPECTED_BINARY=361f99ea481c3bf2ce630a181fdc883a564f0e6698bb8654bdf60ee07712d08f
EXPECTED_IMAGE=sha256:97526dcefe0324c06197ce2a2dc632840ddd27a06493c6220002a85fb7a9ef14
STATUS=pending
PHASE=preflight
RC=99
CG_KILL=none
START=$(date -u +%FT%TZ)
export W
write_result(){
  local oldrc=$?
  python3 - "$W/supervisor_result.json" "$STATUS" "$PHASE" "$RC" "$CG_KILL" <<'PY'
import sys,json,datetime,pathlib
p=pathlib.Path(sys.argv[1]);d={
'status':sys.argv[2],'phase':sys.argv[3],'exit_code':int(sys.argv[4]),
'stop_reason':sys.argv[5],'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
'tetrahedralization':'RUN ONCE; consult TetGen files','PDE':'NOT RUN'}
tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2)+'\n');tmp.replace(p)
PY
}
trap write_result EXIT
exec >"$W/supervisor.log" 2>&1
echo "START $START"
echo "SOURCE $(sha256sum "$SOURCE")"
echo "TETGEN $(sha256sum "$TETGEN")"
echo "IMAGE $(docker image inspect "$IMAGE" --format '{{.Id}}')"
test "$(sha256sum "$SOURCE" | cut -d' ' -f1)" = "$EXPECTED_INPUT"
test "$(sha256sum "$TETGEN" | cut -d' ' -f1)" = "$EXPECTED_BINARY"
test "$(docker image inspect "$IMAGE" --format '{{.Id}}')" = "$EXPECTED_IMAGE"
python3 - "$ROOT" <<'PY'
from pathlib import Path
import json,hashlib,sys
root=Path(sys.argv[1]);m=json.loads((root/'data/v3_r37_plc_preflight_20261105/manifest.json').read_text())
r=json.loads((root/'data/v3_r37_plc_preflight_20261105/seed_refined_01/independent_plc_readback.json').read_text())
assert r['status']=='PASS PLC SERIALIZATION AND CAD REGION SEED CLEARANCE'
assert (r['input_vertices'],r['facet_count'],r['face_markers'],r['regions'])==(156599,320522,2440,430)
assert r['seed_clearance_min_mm']>=.0005 and r['duplicate_triplets']==0 and r['volume_edge_incidence_not_equal_two']==0
assert m['finite_contact_witnesses']==378
assert m['final_PLC_sha256']==r['file_sha256']
assert json.loads((root/'data/v3_r33_surface_20261105/attempt_01/run/result.json').read_text())['status']=='FAIL GLOBAL SURFACE GATE; NO RETRY'
print('INDEPENDENT_REGISTRATION_VALIDATED',flush=True)
PY
test ! -e "$W/trial_started"
test ! -e "$W/work"
mkdir "$W/work"
cp --reflink=auto -- "$SOURCE" "$W/work/R38_430_domains.poly"
test "$(sha256sum "$W/work/R38_430_domains.poly" | cut -d' ' -f1)" = "$EXPECTED_INPUT"
printf 'ONE_ATTEMPT %s\n' "$(date -u +%FT%TZ)" >"$W/trial_started"
PHASE=global_tetgen_PLC
STATUS=RUNNING
RC=98
echo "ONE_TETGEN_ATTEMPT -pYYAC -V; 4CPU 8GiB 900sec, network none"
# Containerized TetGen writes only to /trial; source repository is never mounted for write.
cidfile="$W/container.cid"
set +e
timeout --signal=TERM --kill-after=12s 900s \
docker run --rm --init --network=none \
 --cidfile "$cidfile" --cpus=4 --memory=8g --memory-swap=8g --pids-limit=256 \
 --user 1001:1001 --mount type=bind,src="$W/work",dst=/trial \
 --mount type=bind,src="$TETGEN",dst=/usr/local/bin/r38-tetgen,readonly \
 --workdir /trial "$IMAGE" \
 /usr/local/bin/r38-tetgen -pYYAC -V R38_430_domains.poly >"$W/tetgen_stdout.log" 2>&1 &
P=$!
echo "DOCKER_PROCESS_PID=$P"
while kill -0 "$P" 2>/dev/null; do
 if [ -s "$cidfile" ]; then
   cid=$(cat "$cidfile")
   mem=$(docker stats --no-stream --format '{{.MemUsage}}' "$cid" 2>/dev/null | head -1)
   echo "$(date -u +%FT%TZ) mem=$mem output=$(du -sm "$W/work" | cut -f1)MiB" >>"$W/resource_samples.log"
   # Directly read memory.current in this process's cgroup to avoid parsing unit strings.
   mc=$(docker exec "$cid" sh -c 'cat /sys/fs/cgroup/memory.current 2>/dev/null || echo 0' 2>/dev/null | head -1)
   case "$mc" in ''|*[!0-9]*) mc=0;; esac
   if [ "$mc" -gt 8053063680 ];then
     echo "STOP GUARD: resident cgroup memory exceeded 7.5GiB ($mc bytes)"
     CG_KILL=memory_guard_7p5GiB
     docker kill "$cid" >/dev/null 2>&1 || true
     break
   fi
 fi
 used=$(du -sm "$W/work" | cut -f1)
 if [ "$used" -gt 6144 ];then
   echo "STOP GUARD: output above 6GiB: $used MiB"
   CG_KILL=output_guard_6GiB
   if [ -s "$cidfile" ];then docker kill "$(cat "$cidfile")" >/dev/null 2>&1 || true;fi
   break
 fi
 sleep 6
done
wait "$P"
RC=$?
set -e
echo "TetGen returned RC=$RC STOP_REASON=$CG_KILL $(date -u +%FT%TZ)"
if [ "$RC" -ne 0 ];then
 STATUS=STOP
 echo "STOP: failed attempt archived, no retry"
 exit "$RC"
fi
PHASE=mesh_generated_pending_independent_audit
STATUS=MESH_GENERATED_UNQUALIFIED
if [ ! -s "$W/work/R38_430_domains.1.ele" ];then STATUS=STOP;RC=95;echo 'No tetrahedra output';exit 95;fi
if [ ! -s "$W/work/R38_430_domains.1.node" ];then STATUS=STOP;RC=94;echo 'No node output';exit 94;fi
if [ ! -s "$W/work/R38_430_domains.1.face" ];then STATUS=STOP;RC=93;echo 'No face output';exit 93;fi
echo "SUCCESS: saved mesh pending independent quality/ownership audit"
RC=0
