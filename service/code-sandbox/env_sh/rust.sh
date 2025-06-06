#!/bin/bash
set -eux

# env_sh/rust.sh
#  - 独立安装指定版本 Rust 到 /opt/rust/<版本>
#  - 不做哈希校验，仅用于内部镜像构建

if [ $# -ne 1 ]; then
  echo "Usage: $0 <RUST_VERSION>"
  exit 1
fi

RUST_VERSION="$1"
PREFIX="/opt/rust/$RUST_VERSION"
DPKG_ARCH="$(dpkg --print-architecture)"

# 选择目标三元组
case "$RUST_VERSION" in
  "1.78.0"|"1.84.0")
    case "${DPKG_ARCH##*-}" in
      "amd64") TARGET="x86_64-unknown-linux-gnu" ;;
      "arm64") TARGET="aarch64-unknown-linux-gnu" ;;
      *) echo "Unsupported arch: $DPKG_ARCH"; exit 1 ;;
    esac ;;
  *)
    echo "Unsupported RUST_VERSION: $RUST_VERSION"
    exit 1 ;;
esac

# 如果已存在旧目录先删掉，避免残留
rm -rf "$PREFIX"
mkdir -p "$PREFIX"

# 使用临时目录进行解压与安装
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

curl -fsSL \
  "https://static.rust-lang.org/dist/rust-${RUST_VERSION}-${TARGET}.tar.xz" \
  -o "$WORK_DIR/rust.tar.xz"

tar -xJf "$WORK_DIR/rust.tar.xz" -C "$WORK_DIR"

cd "$WORK_DIR/rust-${RUST_VERSION}-${TARGET}"
./install.sh --prefix="$PREFIX" --disable-ldconfig

echo "Rust $RUST_VERSION installed to $PREFIX"
