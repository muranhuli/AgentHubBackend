FROM codesandbox-env-base AS builder

# Install multiple CPython versions inside a single image. By default we
# build 3.12 and 3.13 to match the previous behaviour.
ARG PY_VERSIONS="3.12 3.13"

RUN set -eux; \
    for v in $PY_VERSIONS; do \
        /opt/env_sh/python.sh "$v"; \
    done; \
    /opt/conda/bin/conda clean -afy; \
    rm -rf /root/.cache/pip /var/lib/apt/lists/* /tmp/* /var/tmp/*

CMD ["/bin/bash"]
