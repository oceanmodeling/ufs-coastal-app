## Spack-stack Docker Container

The [Spack-stack](https://github.com/JCSDA/spack-stack) container is a self consistent [Docker](https://www.docker.com) container that includes dependencies to run [UFS Coastal](https://github.com/oceanmodeling/ufs-coastal) and/or any other UFS Model. 

The container leverages from `build_deps.sh` script to install required dependencies and tools. To run the UFS Coastal provided Regression Tests (RTs), it uses Slurm docker container as a base container. It is also possible to build the container by using Ubuntu as a base container without Slurm Workload Manager.

To build and run the container, docker commands need to be available. [Docker Desktop](https://www.docker.com/products/docker-desktop/) can be used for this purpose.

The container can be built using following commands,

```shell
$ cd ufs-coastal-app/containers/spack-stack
$ docker build -t spack-stack:latest .
```

Once the container is built, the following command can be use to run it.

```shell
$ docker run --platform linux/amd64 --hostname=linux -it spack-stack:latest bash
```

In this case, the installed tools (i.e. lmod, spack-stack) are found under `/root` directory.
