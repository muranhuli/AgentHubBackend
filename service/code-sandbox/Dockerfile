# ------------------------------------------------------------
# Dockerfile (Ubuntu 22.04) – 单层构建
# ------------------------------------------------------------
FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 TZ=Asia/Shanghai PYTHONDONTWRITEBYTECODE=1 \
    PATH=/opt/conda/bin:$PATH

RUN set -eux; \
    apt-get update -qq; \
    apt-get install -y -qq --no-install-recommends ca-certificates wget

COPY --from=eclipse-temurin:8  /opt/java/openjdk /opt/java/openjdk8
COPY --from=eclipse-temurin:17 /opt/java/openjdk /opt/java/openjdk17
COPY --from=eclipse-temurin:21 /opt/java/openjdk /opt/java/openjdk21

# 把静态文件先拷贝到镜像中
COPY mirrors/sources.list                 /etc/apt/sources.list
COPY mirrors/adoptium.list                /etc/apt/sources.list.d/adoptium.list
COPY mirrors/miniconda.txt                /tmp/miniconda.txt
COPY mirrors/gcc.txt                      /tmp/gcc.txt
COPY mirrors/.condarc                     /root/.condarc
COPY requirements.txt                     /opt/requirements.txt
COPY install_env.sh                       /opt/install_env.sh
COPY env_sh/                              /opt/env_sh/

RUN set -eux; \
    mkdir -p /etc/apt/keyrings; \
    wget -qO /etc/apt/keyrings/adoptium.asc \
         https://packages.adoptium.net/artifactory/api/gpg/key/public; \
    chmod +x /opt/install_env.sh /opt/env_sh/*.sh; \
    apt-get update -qq; \
    apt-get install -y -qq --no-install-recommends \
        gnupg curl bzip2 git unzip libseccomp-dev \
        build-essential libssl-dev libffi-dev software-properties-common \
        apt-transport-https dirmngr lsb-release cmake make dos2unix vim; \
    apt-get install -y -qq --no-install-recommends \
        temurin-8-jdk temurin-17-jdk temurin-21-jdk; \
    PREFIX=$(tr -d '\n' < /tmp/miniconda.txt); \
    wget -qO /tmp/miniconda.sh "${PREFIX}/Miniconda3-latest-Linux-x86_64.sh"; \
    bash /tmp/miniconda.sh -b -p /opt/conda; \
    /opt/conda/bin/conda update -y -q conda; \
    rm -f /tmp/miniconda.sh /tmp/miniconda.txt; \
    /opt/install_env.sh; \
    ln -s /opt/sduoj-sandbox/bin/sandbox /usr/bin/sandbox; \
    ln -s /opt/python/3.12/bin/python    /usr/bin/python3; \
    /opt/conda/bin/conda clean -afy; \
    rm -rf /root/.cache/pip; \
    apt-get autoremove -y; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*; \
    rm -rf /opt/env_sh gcc.txt /opt/install_env.sh /opt/requirements.txt

CMD ["/bin/bash"]
