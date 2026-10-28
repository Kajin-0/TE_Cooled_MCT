#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs/bootstrap
df -h . | tee logs/bootstrap/disk-before.txt
available_kb=$(df -Pk . | awk 'NR==2 {print $4}')
if (( available_kb < 6000000 )); then
    echo 'Need at least 6 GB free for the bounded source build.' >&2
    exit 1
fi
docker build --progress=plain -f fem/Dockerfile -t tecooledmct-fem:26.2.1 . 2>&1 | tee logs/bootstrap/build.log
docker image inspect tecooledmct-fem:26.2.1 > logs/bootstrap/image.json
./fem/run.sh bash -ec 'cat /opt/elmer/provenance/commit; gmsh --version; ElmerSolver -v; cat /opt/apt-packages.lock; pip freeze' > logs/bootstrap/versions.txt 2>&1
df -h . | tee logs/bootstrap/disk-after.txt
