#!/bin/bash
set -euo pipefail

# 将上层 requirements.txt 拷贝过来
cp ../../requirements.txt .

# 定义所有环境镜像及对应 Dockerfile
declare -A IMAGES=(
  [codesandbox-env-base]=base.Dockerfile
  [codesandbox-env-python]=python.Dockerfile
  [codesandbox-env-pypy]=pypy.Dockerfile
  [codesandbox-env-gcc]=gcc.Dockerfile
  [codesandbox-env-rust]=rust.Dockerfile
  [codesandbox-env-sandbox]=sandbox.Dockerfile
)

# 1. 构建 base 镜像
BASE_TAG="codesandbox-env-base"
if ! docker image inspect "$BASE_TAG" >/dev/null 2>&1; then
  echo ">>> Image '$BASE_TAG' not found — building with base.Dockerfile"
  docker build -f "${IMAGES[$BASE_TAG]}" -t "$BASE_TAG" .
else
  echo ">>> Image '$BASE_TAG' already exists — skipping"
fi

# 2. 并行构建其它环境镜像
PARALLEL_TAGS=(
  codesandbox-env-python
  codesandbox-env-pypy
  codesandbox-env-gcc
  codesandbox-env-rust
  codesandbox-env-sandbox
)

for TAG in "${PARALLEL_TAGS[@]}"; do
  (
    if ! docker image inspect "$TAG" >/dev/null 2>&1; then
      echo ">>> Image '$TAG' not found — building with ${IMAGES[$TAG]}"
      docker build -f "${IMAGES[$TAG]}" -t "$TAG" .
    else
      echo ">>> Image '$TAG' already exists — skipping"
    fi
  ) &
done

# 等待所有后台构建完成
wait

# 3. 构建运行时镜像
RUNTIME_TAG="code-sandbox"
if ! docker image inspect "$RUNTIME_TAG" >/dev/null 2>&1; then
  echo ">>> Runtime image '$RUNTIME_TAG' not found — building"
  docker build -t "$RUNTIME_TAG" .
else
  echo ">>> Runtime image '$RUNTIME_TAG' already exists — skipping"
fi
