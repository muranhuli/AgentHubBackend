#!/usr/bin/env bash
set -euo pipefail

# List of all images installed by the build script
IMAGES=(
  codesandbox-env-base
  codesandbox-env-python
  codesandbox-env-pypy
  codesandbox-env-gcc
  codesandbox-env-rust
  codesandbox-env-sandbox
  code-sandbox
)

for TAG in "${IMAGES[@]}"; do
  if docker image inspect "$TAG" >/dev/null 2>&1; then
    echo ">>> Removing image '$TAG'"
    docker rmi "$TAG"
  else
    echo ">>> Image '$TAG' not found — skipping"
  fi
done

echo "All specified images processed."
