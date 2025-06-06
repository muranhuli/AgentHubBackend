# Code Sandbox Docker Images

Each script in `env_sh/` has a matching Dockerfile under `env_docker/`.
Build these images first and then build the runtime image that assembles
them.  Each environment image contains all required versions (e.g. the
Python image includes 3.12 and 3.13).

Example build sequence:
```bash
# build common base
docker build -f env_docker/base.Dockerfile -t codesandbox-env-base env_docker

# build language environments (each builds all versions at once)
docker build -f env_docker/python.Dockerfile  -t codesandbox-env-python  env_docker
docker build -f env_docker/pypy.Dockerfile    -t codesandbox-env-pypy    env_docker
docker build -f env_docker/gcc.Dockerfile     -t codesandbox-env-gcc     env_docker
docker build -f env_docker/rust.Dockerfile    -t codesandbox-env-rust    env_docker
docker build -f env_docker/sandbox.Dockerfile -t codesandbox-env-sandbox env_docker

# finally build the runtime image
docker build -t code-sandbox .
```
