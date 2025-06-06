#!/bin/bash
set -eux

# =============================================================================
# env_sh/gcc.sh
#   - 从源码编译并安装 GCC 到 /opt/gcc/<版本>
#   - 无任何哈希校验
#
# 用法：
#   bash env_sh/gcc.sh <GCC_VERSION>
# 示例：
#   bash env_sh/gcc.sh 13.3.0
# =============================================================================

if [ $# -ne 1 ]; then
  echo "Usage: $0 <GCC_VERSION>"
  exit 1
fi

GCC_VERSION="$1"
PREFIX="/opt/gcc/$GCC_VERSION"
TEMP_DIR="/tmp/gcc-build"
BUILD_ARCH="$(dpkg-architecture --query DEB_BUILD_GNU_TYPE)"

# 检查镜像配置文件
MIRROR_BASE="https://ftp.gnu.org"
if [ -f "/opt/gcc.txt" ]; then
  MIRROR_BASE=$(head -n 1 /opt/gcc.txt | tr -d '\n')
  echo "使用镜像源: $MIRROR_BASE"
fi

# 创建临时目录并下载源码
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

curl -fsSL "${MIRROR_BASE}/gnu/gcc/gcc-${GCC_VERSION}/gcc-${GCC_VERSION}.tar.gz" \
  -o gcc.tar.gz
tar -xzf gcc.tar.gz
cd "gcc-${GCC_VERSION}"

# 设置下载依赖包时使用的镜像源
export BASE_URL="$MIRROR_BASE"
./contrib/download_prerequisites

# 在单独目录里编译
mkdir -p build && cd build
../configure \
  --build="$BUILD_ARCH" \
  --prefix="$PREFIX" \
  --disable-multilib \
  --enable-languages=c,c++

make -j"$(nproc)"
make install-strip

# 清理临时目录
cd /
rm -rf "$TEMP_DIR"

echo "GCC ${GCC_VERSION} 安装至 ${PREFIX}"