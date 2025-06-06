FROM codesandbox-env-base AS builder

# Install Rust 1.78.0 and 1.84.0 in a single build.
ARG RUST_VERSIONS="1.78.0 1.84.0"

RUN set -eux; \
    for v in $RUST_VERSIONS; do \
        /opt/env_sh/rust.sh "$v"; \
    done; \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

CMD ["/bin/bash"]
