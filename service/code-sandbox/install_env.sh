#!/bin/bash
set -eux

# =============================================================================
# install_env.sh (Ubuntu 22.04，已使用 mirrors/ 下的镜像源)
#   - 安装 Temurin JDK 并将其移动到 /opt/java 下
#   - 安装 GCC 13.3.0、Rust 1.78.0 & 1.84.0
#   - 安装 PyPy 3.10-v7.3.19 & 3.11-v7.3.19
#   - 安装 Conda-Python 3.12 & 3.13（pip + conda 都走中科大）
# =============================================================================

# 确保以 root 身份运行
if [ "$(id -u)" -ne 0 ]; then
  echo "请以 root 或 sudo 身份运行"
  exit 1
fi

# 在 /opt 下创建所需目录
mkdir -p /opt/gcc \
         /opt/rust \
         /opt/pypy \
         /opt/python \
         /opt/sduoj-sandbox

# 确保 conda 在 PATH 中
export PATH="/opt/conda/bin:$PATH"

# -------------------------------------------------------------------
# 6) 安装 SDUOJ 沙箱环境
# -------------------------------------------------------------------
bash /opt/env_sh/sandbox.sh

# -------------------------------------------------------------------
# 3) 安装 Rust 1.78.0 与 1.84.0
# -------------------------------------------------------------------
bash /opt/env_sh/rust.sh 1.78.0
bash /opt/env_sh/rust.sh 1.84.0

# -------------------------------------------------------------------
# 4) 安装 PyPy 3.10-v7.3.19 & 3.11-v7.3.19
# -------------------------------------------------------------------
bash /opt/env_sh/pypy.sh 3.10-v7.3.19
bash /opt/env_sh/pypy.sh 3.11-v7.3.19

# -------------------------------------------------------------------
# 5) 安装 Conda-Python 3.12 & 3.13
#    - pip.conf 已指向中科大镜像，pip install 会自动走中科大
#    - requirements.txt 已复制到 /opt/requirements.txt
# -------------------------------------------------------------------
bash /opt/env_sh/python.sh 3.12
bash /opt/env_sh/python.sh 3.13

# -------------------------------------------------------------------
# 2) 安装 GCC 13.3.0
# -------------------------------------------------------------------
bash /opt/env_sh/gcc.sh 13.3.0

echo "=== 所有环境已安装，位于 /opt 下 ==="
