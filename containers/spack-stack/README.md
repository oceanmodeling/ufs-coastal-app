## Spack-stack Docker Container

The [Spack-stack](https://github.com/JCSDA/spack-stack) container is a self consistent [Docker](https://www.docker.com) container that includes dependencies to run [UFS Coastal](https://github.com/oceanmodeling/ufs-coastal) and/or any other UFS Model. 

The container leverages from `build_deps.sh` script to install required dependencies and tools. To run the UFS Coastal provided Regression Tests (RTs), it uses Slurm docker container as a base container. More information to build Slurm container can be found in [here](https://github.com/oceanmodeling/ufs-coastal-app/blob/main/containers/slurm/README.md).

To build and run the container, docker commands need to be available. [Docker Desktop](https://www.docker.com/products/docker-desktop/) can be used for this purpose.

The container can be built using following commands,

```shell
$ cd ufs-coastal-app
$ docker build -f containers/spack-stack/Dockerfile -t spack-stack:latest .
```

Once the container is built, the following command can be use to run it.

```shell
$ docker run --platform linux/amd64 --hostname=linux -it spack-stack:latest bash
```

In this case, the installed tools (i.e. lmod, spack-stack) are found under `/root` directory.
