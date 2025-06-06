#!/bin/bash
set -eux

# =============================================================================
# env_sh/python.sh
#   - 在 /opt/python/<版本> 创建 Conda 环境（走中科大镜像）
#   - 安装常见最新版包
#   - 再安装 /opt/requirements.txt 中的项目依赖
# =============================================================================

if [ $# -ne 1 ]; then
  echo "Usage: $0 <PYTHON_VERSION>"
  exit 1
fi

PYTHON_VERSION="$1"
ENV_PREFIX="/opt/python/$PYTHON_VERSION"
CONDA_BIN="/opt/conda/bin/conda"

# 确保 conda 在 PATH
export PATH="/opt/conda/bin:$PATH"

# 若已存在则跳过
if [ -d "$ENV_PREFIX" ]; then
  echo "Conda 环境 ${ENV_PREFIX} 已存在，跳过。"
  exit 0
fi

# 1) 创建基础 Conda 环境
"$CONDA_BIN" create \
  --prefix "$ENV_PREFIX" \
  --yes \
  --quiet \
  python="$PYTHON_VERSION"

# 2) 激活环境，安装常见最新版包
source /opt/conda/bin/activate "$ENV_PREFIX"
python -m pip install --upgrade pip setuptools wheel

python -m pip install \
  numpy \
  pandas \
  scipy \
  scikit-learn \
  matplotlib \
  jupyterlab \
  notebook \
  seaborn \
  sqlalchemy \
  requests \
  fastapi \
  uvicorn \
  pydantic \
  sqlalchemy-utils \
  alembic \
  loguru \
  python-dotenv \
  celery \
  redis

# 4) 清理 conda 缓存
"$CONDA_BIN" clean -ay -q
conda deactivate

echo "Conda 环境 Python ${PYTHON_VERSION} 已创建，路径：${ENV_PREFIX}"
