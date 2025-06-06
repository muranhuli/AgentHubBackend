FROM codesandbox-env-base AS builder

# Build both supported PyPy versions in one image. Defaults correspond to the
# previous install_env.sh script.
ARG PYPY_VERSIONS="3.10-v7.3.19 3.11-v7.3.19"

RUN set -eux; \
    for v in $PYPY_VERSIONS; do \
        /opt/env_sh/pypy.sh "$v"; \
    done; \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

CMD ["/bin/bash"]
