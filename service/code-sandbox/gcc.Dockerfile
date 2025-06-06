FROM codesandbox-env-base AS builder

ARG GCC_VERSION=13.3.0

RUN /opt/env_sh/gcc.sh ${GCC_VERSION} \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

CMD ["/bin/bash"]
