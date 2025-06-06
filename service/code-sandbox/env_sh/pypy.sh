#!/bin/bash
set -eux

# =============================================================================
# env_sh/pypy.sh
#   - 安装 PyPy v7.3.19（3.10 或 3.11）到 /opt/pypy/<版本>
#   - 无任何哈希校验
#
# 用法：
#   bash env_sh/pypy.sh <PYPY_VERSION>
# 示例：
#   bash env_sh/pypy.sh 3.10-v7.3.19
#   bash env_sh/pypy.sh 3.11-v7.3.19
# =============================================================================

if [ $# -ne 1 ]; then
  echo "Usage: $0 <PYPY_VERSION>"
  echo "支持：3.10-v7.3.19 或 3.11-v7.3.19"
  exit 1
fi

PYPY_VERSION="$1"
PYTHON_VERSION="${PYPY_VERSION%%-*}"    # “3.10” 或 “3.11”
DPKG_ARCH="$(dpkg --print-architecture)"

# 根据架构决定下载文件名
case "$PYPY_VERSION" in
  "3.10-v7.3.19")
    case "${DPKG_ARCH##*-}" in
      "amd64") FILE="pypy3.10-v7.3.19-linux64.tar.bz2";;
      "arm64") FILE="pypy3.10-v7.3.19-aarch64.tar.bz2";;
      *) echo "不支持架构：$DPKG_ARCH"; exit 1;;
    esac
    ;;
  "3.11-v7.3.19")
    case "${DPKG_ARCH##*-}" in
      "amd64") FILE="pypy3.11-v7.3.19-linux64.tar.bz2";;
      "arm64") FILE="pypy3.11-v7.3.19-aarch64.tar.bz2";;
      *) echo "不支持架构：$DPKG_ARCH"; exit 1;;
    esac
    ;;
  *)
    echo "不支持的 PYPY_VERSION：$PYPY_VERSION"
    exit 1
    ;;
esac

PREFIX="/opt/pypy/${PYTHON_VERSION}"
mkdir -p "$PREFIX"
cd "$PREFIX"

# 下载并解压，不做任何校验
curl -fsSL "https://downloads.python.org/pypy/${FILE}" -o "pypy.tar.bz2"
tar -xjf pypy.tar.bz2 --strip-components=1
rm pypy.tar.bz2

echo "PyPy ${PYPY_VERSION} 安装至 ${PREFIX}"
