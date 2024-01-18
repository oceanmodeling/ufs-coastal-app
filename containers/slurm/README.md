## Slurm Workload Manager Docker Container

The Slurm container is a self consistent [Docker](https://www.docker.com) container that allows to use/practice Slurm commands under Ubuntu 22.04.

To build and run the container, docker commands need to be available. [Docker Desktop](https://www.docker.com/products/docker-desktop/) can be used for this purpose.

The container can be built using following commands,

```shell
$ cd ufs-coastal-app/containers/slurm
$ docker build -t slurm:latest .
```

Once the container is built, the following command can be use to run it.

```shell
$ docker run --platform linux/amd64 --hostname=linux -it slurm:latest bash
```
