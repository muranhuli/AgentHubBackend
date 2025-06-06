FROM codesandbox-env-base AS builder

RUN /opt/env_sh/sandbox.sh \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

CMD ["/bin/bash"]
