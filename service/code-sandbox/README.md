# Code Sandbox Docker Images

Each script in `env_sh/` has a matching Dockerfile.
Build these images first and then build the runtime image that assembles
them. Each environment image contains all required versions (e.g. the
Python image includes 3.12 and 3.13).

Example build sequence:

```bash
# build common base
docker build -f base.Dockerfile -t codesandbox-env-base .

# build language environments (each builds all versions at once)
docker build -f python.Dockerfile  -t codesandbox-env-python .
docker build -f pypy.Dockerfile    -t codesandbox-env-pypy .
docker build -f gcc.Dockerfile     -t codesandbox-env-gcc .
docker build -f rust.Dockerfile    -t codesandbox-env-rust .  
docker build -f sandbox.Dockerfile -t codesandbox-env-sandbox .

# finally build the runtime image
docker build -t code-sandbox .
```
