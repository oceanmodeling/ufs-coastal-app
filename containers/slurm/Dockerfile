# syntax=docker/dockerfile:1

# base package
FROM --platform=linux/amd64 ubuntu:22.04 as base
MAINTAINER Ufuk Turuncoglu <turuncu@ucar.edu> 

# non interactive mode
ENV DEBIAN_FRONTEND=noninteractive

# container arguments
ARG USERNAME=ufs
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG GOSU_VERSION=1.17

# install core packages
RUN apt-get -yqq update && \
    apt-get -yqq upgrade && \
    apt install --no-install-recommends -yqq \
    slurmd \ 
    slurmctld \
    slurmdbd \
    munge \
    libfreeipmi-dev \
    libhwloc-dev \
    freeipmi \
    libmunge-dev \
    mysql-server \
    gnupg \
    wget && \
    rm -rf /var/lib/apt/lists/*

# install gosu
RUN set -ex && \
    wget --no-check-certificate -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-amd64" && \
    wget --no-check-certificate -O /usr/local/bin/gosu.asc "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-amd64.asc" && \
    export GNUPGHOME="$(mktemp -d)" && \
    # See https://github.com/tianon/gosu/issues/17#issuecomment-348464529
    ( gpg --keyserver ha.pool.sks-keyservers.net --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4 \
      || gpg --keyserver pgp.mit.edu --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4 \
      || gpg --keyserver keyserver.pgp.com --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4 \
      || gpg --keyserver keyserver.ubuntu.com --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4 \
    ) && \
    gpg --batch --verify /usr/local/bin/gosu.asc /usr/local/bin/gosu && \
    rm -rf "${GNUPGHOME}" /usr/local/bin/gosu.asc && \
    chmod +x /usr/local/bin/gosu && \
    gosu nobody true

# copy slurm configuration templates
COPY slurm.conf /etc/slurm/slurm.conf
COPY slurmdbd.conf /etc/slurm/slurmdbd.conf

# get entrypoint script
COPY ./entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]

# set default user
USER root
