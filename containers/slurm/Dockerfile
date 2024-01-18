# syntax=docker/dockerfile:1

# base package
FROM --platform=linux/amd64 ubuntu:22.04 as base
MAINTAINER Ufuk Turuncoglu <turuncu@ucar.edu> 

# non interactive mode
ENV DEBIAN_FRONTEND=noninteractive

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

# copy slurm configuration templates
COPY slurm.conf /etc/slurm/slurm.conf
COPY slurmdbd.conf /etc/slurm/slurmdbd.conf

# enable colored bash terminal prompt
RUN sed -i -e 's/#force_color_prompt=yes/force_color_prompt=yes/' /root/.bashrc

# get entrypoint script
COPY ./entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]

# set default user
USER root
