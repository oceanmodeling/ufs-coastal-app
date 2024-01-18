# syntax=docker/dockerfile:1

# base package
FROM --platform=linux/amd64 slurm:latest as bootstrap

# container arguments
# note ARGs dissapears after FROM. So, put them after FROM.
ARG SPACK_STACK_VERSION=1.5.1
ARG COMPILER_VERSION=11.4.0
ARG MPI_VERSION=4.1.6

# non interactive mode
ENV DEBIAN_FRONTEND=noninteractive

# additional environment variables for spack
ENV SPACK_ROOT=/opt/spack-stack/spack \
    CURRENTLY_BUILDING_DOCKER_IMAGE=1 \
    container=docker

# labels
LABEL description="Build Image for UFS Weather Model" \
  version="${SPACK_STACK_VERSION}"

# copy install script
COPY ../../build_deps.sh /opt/.

# change default shell to bash
SHELL ["/bin/bash", "-c"]

# checkout and configure spack
RUN cd /opt && \
  ./build_deps.sh --compiler=gcc@${COMPILER_VERSION} --mpi=openmpi@${MPI_VERSION} --install-lmod --install-core-pkgs -v

# clean unused files to reduce container size
RUN cd /root/ufs.local/gcc/${COMPILER_VERSION} && \
  rm -rf crtm*/share/crtm/src/fix && \
  rm -rf crtm*/share/crtm/src/.git && \
  rm -rf crtm*/fix && \
  rm -rf crtm*/share/crtm-fix

# set default user
USER root
