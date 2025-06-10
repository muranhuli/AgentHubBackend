#!/bin/bash
set -euo pipefail

# Define images and their Dockerfiles
declare -A IMAGES=(
  [codesandbox-env-base]=base.Dockerfile
  [codesandbox-env-python]=python.Dockerfile
  [codesandbox-env-pypy]=pypy.Dockerfile
  [codesandbox-env-gcc]=gcc.Dockerfile
  [codesandbox-env-rust]=rust.Dockerfile
  [codesandbox-env-sandbox]=sandbox.Dockerfile
)

# For each image: if it’s not present locally, build it
for TAG in "${!IMAGES[@]}"; do
  DOCKERFILE="${IMAGES[$TAG]}"
  if ! docker image inspect "$TAG" >/dev/null 2>&1; then
    echo ">>> Image '$TAG' not found locally — building using $DOCKERFILE"
    docker build -f "$DOCKERFILE" -t "$TAG" .
  else
    echo ">>> Image '$TAG' already exists — skipping"
  fi
done

# Finally, build the runtime image if needed
RUNTIME_TAG="code-sandbox"
if ! docker image inspect "$RUNTIME_TAG" >/dev/null 2>&1; then
  echo ">>> Runtime image '$RUNTIME_TAG' not found — building"
  docker build -t "$RUNTIME_TAG" .
else
  echo ">>> Runtime image '$RUNTIME_TAG' already exists — skipping"
fi
