# ------------------------------------------------------------
# Runtime Dockerfile (Ubuntu 22.04)
#   - Assumes individual environment images are prebuilt
# ------------------------------------------------------------

FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 TZ=Asia/Shanghai PYTHONDONTWRITEBYTECODE=1 \
    PATH=/opt/conda/bin:$PATH

RUN set -eux; \
    apt-get update -qq; \
    apt-get install -y -qq --no-install-recommends ca-certificates wget; \
    rm -rf /var/lib/apt/lists/*

COPY mirrors/sources.list      /etc/apt/sources.list

RUN set -eux; \
    apt-get update -qq; \
    apt-get install -y -qq --no-install-recommends  \
    ca-certificates tzdata libseccomp-dev \
    sudo git unzip wget curl host dos2unix vim \
    make cmake build-essential dosbox; \
    apt-get clean autoclean; \
    apt-get autoremove -y; \
    rm -rf /var/lib/apt/lists/*; \
    rm -f /var/cache/apt/archives/*.deb

# Java runtimes
COPY --from=eclipse-temurin:8  /opt/java/openjdk /opt/java/openjdk8
COPY --from=eclipse-temurin:17 /opt/java/openjdk /opt/java/openjdk17
COPY --from=eclipse-temurin:21 /opt/java/openjdk /opt/java/openjdk21
COPY --from=codesandbox-env-base:latest /opt/conda /opt/conda
COPY --from=codesandbox-env-gcc:latest      /opt/gcc          /opt/gcc
COPY --from=codesandbox-env-rust:latest     /opt/rust         /opt/rust
COPY --from=codesandbox-env-python:latest   /opt/python       /opt/python
COPY --from=codesandbox-env-pypy:latest     /opt/pypy         /opt/pypy
COPY --from=codesandbox-env-sandbox:latest  /opt/sduoj-sandbox /opt/sduoj-sandbox

COPY requirements.txt /opt/requirements.txt
RUN set -eux; \
    ENV_PREFIX="/opt/python/agent"; \
    CONDA_BIN="/opt/conda/bin/conda"; \
    REQ_FILE="/opt/requirements.txt"; \
    export PATH="/opt/conda/bin:$PATH"; \
    "$CONDA_BIN" create --prefix "$ENV_PREFIX" --yes --quiet python="3.12"; \
    . /opt/conda/bin/activate "$ENV_PREFIX"; \
    python -m pip install --upgrade pip setuptools wheel; \
    python -m pip install --no-cache-dir -r "$REQ_FILE"; \
    conda deactivate; \
    "$CONDA_BIN" clean -ay -q; \
    rm -f "$REQ_FILE"; \
    ln -s -f /opt/python/agent/bin/python /usr/bin/python3; \
    ln -s -f /opt/sduoj-sandbox/bin/sandbox /usr/bin/sandbox; \
    echo "Agent environment created at $ENV_PREFIX"

CMD ["/bin/bash"]
