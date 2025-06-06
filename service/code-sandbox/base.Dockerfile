FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 TZ=Asia/Shanghai PYTHONDONTWRITEBYTECODE=1 \
    PATH=/opt/conda/bin:$PATH

RUN set -eux; \
    apt-get update -qq; \
    apt-get install -y -qq --no-install-recommends ca-certificates wget; \
    rm -rf /var/lib/apt/lists/*

# copy mirror configs and scripts
COPY mirrors/sources.list      /etc/apt/sources.list
COPY mirrors/adoptium.list     /etc/apt/sources.list.d/adoptium.list
COPY mirrors/miniconda.txt     /opt/miniconda.txt
COPY mirrors/gcc.txt           /opt/gcc.txt
COPY mirrors/.condarc          /root/.condarc
COPY requirements.txt          /opt/requirements.txt
COPY env_sh/                   /opt/env_sh/

RUN set -eux; \
    mkdir -p /etc/apt/keyrings; \
    wget -qO /etc/apt/keyrings/adoptium.asc \
         https://packages.adoptium.net/artifactory/api/gpg/key/public; \
    chmod +x /opt/env_sh/*.sh; \
    apt-get update -qq; \
    apt-get install -y -qq --no-install-recommends \
        gnupg curl bzip2 git unzip libseccomp-dev \
        build-essential libssl-dev libffi-dev software-properties-common \
        apt-transport-https dirmngr lsb-release cmake make vim; \
    PREFIX=$(tr -d '\n' < /opt/miniconda.txt); \
    wget -qO /tmp/miniconda.sh "${PREFIX}/Miniconda3-latest-Linux-x86_64.sh"; \
    bash /tmp/miniconda.sh -b -p /opt/conda; \
    /opt/conda/bin/conda update -y -q conda; \
    rm -f /tmp/miniconda.sh /opt/miniconda.txt

RUN apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
