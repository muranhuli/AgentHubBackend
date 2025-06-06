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

# Java runtimes
COPY --from=eclipse-temurin:8  /opt/java/openjdk /opt/java/openjdk8
COPY --from=eclipse-temurin:17 /opt/java/openjdk /opt/java/openjdk17
COPY --from=eclipse-temurin:21 /opt/java/openjdk /opt/java/openjdk21

# Conda base (from prebuilt base image)
COPY --from=codesandbox-env-base:latest /opt/conda /opt/conda

# Language environments built separately
COPY --from=codesandbox-env-gcc:latest      /opt/gcc          /opt/gcc
COPY --from=codesandbox-env-rust:latest     /opt/rust         /opt/rust
COPY --from=codesandbox-env-python:latest   /opt/python       /opt/python
COPY --from=codesandbox-env-pypy:latest     /opt/pypy         /opt/pypy
COPY --from=codesandbox-env-sandbox:latest  /opt/sduoj-sandbox /opt/sduoj-sandbox

RUN set -eux; \
    ln -s /opt/sduoj-sandbox/bin/sandbox /usr/bin/sandbox; \
    ln -s /opt/python/3.12/bin/python /usr/bin/python3

CMD ["/bin/bash"]
