#!/usr/bin/env bash
set -euo pipefail
project_dir=$(cd "$(dirname "$0")/.." && pwd)
exec docker run --rm --interactive --network=none --cpus=4 --memory=12g \
  --user "$(id -u):$(id -g)" --env HOME=/tmp --env PYTHONPATH=/work \
  --mount "type=bind,src=$project_dir,dst=/work" --workdir /work \
  tecooledmct-fem:26.2.1 "$@"
