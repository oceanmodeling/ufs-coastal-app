.. _PortingModel:

*************************
Porting UFS Coastal Model
*************************

Porting UFS Coastal Model to an unsupported platform involves multiple steps. Similar to the UFS Weather Model, the UFS Coastal Model also uses `spack-stack <https://github.com/JCSDA/spack-stack>`_ package manager to manage model dependencies. In addition to the standard list of dependencies required by the UFS Weather Model, the UFS Coastal Model has extra dependencies for the addtional model components like `ParMETIS <http://glaros.dtc.umn.edu/gkhome/metis/parmetis/overview>`_ and `PROJ <https://proj.org/en/5.1/>`_ libraries. The UFS Coastal Model component is able to install extra dependecies by theirself if they are not provided by the system or spack-stack.

The prerequisite software libraries for building the UFS Coastal Model already exist in a centralized location on `Tier 1 <https://spack-stack.readthedocs.io/en/latest/PreConfiguredSites.html#pre-configured-sites-tier-1>`_ (preconfigured) systems, so users could run the model in those plaotforms. The list of pre-configured Tier 1 & 2 systems are generally restricted to those with access through NOAA and its affiliates. These systems are named (e.g., Hera, Orion, Hercules and Derecho).

In addtion to the already supported systems, UFS Coastal is also ported to `TACC Frontera <https://tacc.utexas.edu/systems/frontera/>`_ system but this is still experimental.

================
Docker Container
================

1. Create new Docker container and install base development environment:

.. code-block:: console

   docker run -it ubuntu:latest

   apt-get update
   apt-get upgrade
   apt-get install -y gcc g++ gfortran gdb
   apt-get install -y build-essential
   apt-get install -y libkrb5-dev
   apt-get install -y m4
   apt-get install -y git
   apt-get install -y git-lfs
   apt-get install -y bzip2
   apt-get install -y unzip
   apt-get install -y automake
   apt-get install -y xterm
   apt-get install -y texlive
   apt-get install -y libcurl4-openssl-dev
   apt-get install -y libssl-dev
   apt-get install -y meson
   apt-get install -y mysql-server
   apt-get install -y libmysqlclient-dev
   apt-get install -y python3-dev python3-pip
   apt-get install -y openmpi-bin libopenmpi-dev

2. Log out and in to container (save hash of container)

.. code-block:: console

  exit
  docker exec -it [HASH_OF_DOCKER_CONTAINER] bash

3. Clone Spack-stack

In this case, ``/opt`` directory will be used to install the dependencies but there is no
any restriction to use another directory for it.

.. code-block:: console

  cd /opt
  git clone --recurse-submodules https://github.com/jcsda/spack-stack.git
  cd spack-stack
  git checkout 1.4.1
  git submodule update --init --recursive
  source setup.sh

.. note::
  The ``proj`` package has bug and creates issue in the installation. Until ``spack`` submodule is
  updated under ``spack-stack``, the following instructions can be used to fix the ``proj`` package.

  .. code-block:: console

    cd spack-stack/spack
    git remote add upstream https://github.com/spack/spack.git
    git fetch upstream
    git cherry-pick upsream 149d194 (and resolve conflicts)

4. Install core dependencies

.. code-block:: console

  cd spack-stack
  spack stack create env --site linux.default --template ufs-weather-model --name ufs.local --prefix /opt/ufs.local
  cd envs/ufs.local/
  spack env activate .

.. note::
  ``spack stack create env -h`` shows the list of available environments.

5. Find external packages/compilers

.. code-block:: console

  cd spack-stack
  export SPACK_SYSTEM_CONFIG_PATH="$PWD/envs/ufs.local/site"
  find --scope system --exclude bison --exclude cmake --exclude curl --exclude openssl --exclude openssh
  spack external find --scope system perl
  spack external find --scope system wget
  spack external find --scope system mysql
  spack external find --scope system texlive
  spack compiler find --scope system
  unset SPACK_SYSTEM_CONFIG_PATH

6. Set default compiler and MPI library

The user need to check compiler and openmpi versions.

.. code-block:: console

  gcc --version
  spack config add "packages:all:compiler:[gcc@YOUR-VERSION]"
  # Example
  spack config add "packages:all:compiler:[gcc@11.4.0]"

  # Example for Red Hat 8 following the above instructions
  spack config add "packages:all:providers:mpi:[openmpi@4.1.5]"

  # Example for Ubuntu 20.04 or 22.04 following the above instructions
  spack config add "packages:all:providers:mpi:[mpich@4.1.1]"  

7. Set few more package variants

.. code-block:: console

  spack config add "packages:fontconfig:variants:+pic"
  spack config add "packages:pixman:variants:+pic"
  spack config add "packages:cairo:variants:+pic"
  spack config add "packages:libffi:version:[3.3]"
  spack config add "packages:flex:version:[2.6.4]"

8. Add additional dependencies for UFS Coastal Model

.. code-block:: console

  spack add parmetis@4.0.3~shared ^metis~shared
  spack add proj@4.9.2~shared~tiff

.. note::
  Since ``parmetis`` package depends on ``metis``, it will also install `metis@5.1.0` spack package.
  Also note that ``metis@5.1.0`` is not compatible with ADCIRC and throw error like
  ``undefined reference to metis_estimatememory_``.

9. Install packages

.. code-block:: console

  spack concretize 2>&1 | tee log.concretize
  spack install --source 2>&1 | tee log.install

10. Create modules

.. code-block:: console

  spack module tcl refresh
  spack stack setup-meta-modules

11. Testing modules (Optional)

.. code-block:: console

  . /etc/profile.d/modules.sh
  module use /opt/ufs.local/modulefiles/Core
  module load stack-gcc/11.4.0
  module load stack-python/3.10.8
  module load stack-openmpi/4.1.5

12. Clone UFS Coastal Model and create new module file

.. code-block:: console

  cd /opt
  git clone -b feature/coastal_app --recursive https://github.com/oceanmodeling/ufs-coastal.git
  cd ufs-coastal/modulefiles
  vi ufs_local.gnu

Content of ``ufs_local.gnu`` module file:

.. code-block:: console 

  #%Module
  
  proc ModulesHelp {} {
    puts stderr "\tcit - loads modules required for building and running UFS Model on Linux/GNU"
  }
  
  module-whatis "loads UFS Model prerequisites for Linux/GNU"
  
  module use /opt/ufs.local/modulefiles/Core
  
  module load stack-gcc/11.4.0
  module load stack-python/3.10.8
  module load stack-openmpi/4.1.5
  
  module load jasper/2.0.32
  module load zlib/1.2.13
  module load libpng/1.6.37
  module load hdf5/1.14.0
  module load netcdf-c/4.9.2
  module load netcdf-fortran/4.6.0
  module load parallelio/2.5.9
  module load esmf/8.4.2
  module load fms/2023.01
  module load bacio/2.4.1
  module load crtm/2.4.0
  module load g2/3.4.5
  module load g2tmpl/1.10.2
  module load ip/3.3.3
  module load sp/2.3.3
  module load w3emc/2.9.2
  module load gftl-shared/1.5.0
  module load mapl/2.35.2-esmf-8.4.2
  module load scotch/7.0.3
  
  module load metis/5.1.0
  module load parmetis/4.0.3
  module load proj/4.9.2
  
  setenv METIS_ROOT $env(metis_ROOT)
  setenv PARMETIS_ROOT $env(parmetis_ROOT)
  setenv PROJ_ROOT $env(proj_ROOT)
  
  setenv CC  mpicc
  setenv CXX mpicxx
  setenv F77 mpif77
  setenv F90 mpif90
  setenv FC  mpif90
  setenv CMAKE_Platform linux.gnu

13. Building UFS Coastal Model specific configurations  

.. code-block:: console

  cd ufs-coastal/tests

  # ADCIRC (it is not compatible with metis 5.x at this point)
  ./compile.sh "local" "-DAPP=CSTLA -DBUILD_ADCPREP=ON -DADCIRC_CONFIG=PADCIRC -DCOUPLED=ON" coastal gnu NO NO

  # FVCOM 
  ./compile.sh "local" "-DAPP=CSTLF -DCOORDINATE_TYPE=SPHERICAL -DWET_DRY=ON" coastal gnu NO NO

  # SCHISM
  ./compile.sh "local" "-DAPP=CSTLS -DUSE_ATMOS=ON -DNO_PARMETIS=OFF -DOLDIO=ON" coastal gnu NO NO
