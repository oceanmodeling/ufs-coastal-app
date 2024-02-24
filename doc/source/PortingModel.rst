.. _PortingModel:

*************************
Porting UFS Coastal Model
*************************

Porting UFS Coastal Model to an unsupported platform involves multiple steps. Similar to the UFS Weather Model, the UFS Coastal Model also uses `spack-stack <https://github.com/JCSDA/spack-stack>`_ package manager to manage model level dependencies. In addition to the standard list of dependencies required by the UFS Weather Model, the UFS Coastal Model has extra dependencies like `ParMETIS <http://glaros.dtc.umn.edu/gkhome/metis/parmetis/overview>`_ and `PROJ <https://proj.org/en/5.1/>`_ libraries. The addtional components (i.e. ADCIRC, FVCOM) are able to install extra dependecies by their own build interface if the required libraries are not provided by the system or spack-stack installation.

The model dependencies are pre-configured and bult on `Tier 1 <https://spack-stack.readthedocs.io/en/latest/PreConfiguredSites.html#pre-configured-sites-tier-1>`_ systems, so users could run the model in those plaotforms. The Tier 1 & 2 systems (e.g., Hera, Orion, Hercules and Derecho) are generally restricted to those with access through NOAA and its affiliates. To that end, the UFS Coastal is ported to `TACC Frontera <https://tacc.utexas.edu/systems/frontera/>`_ system support coastal modeling community and users but it is still testing phase and experimental.

================================
Additionally Supported Platforms
================================

TACC Frontera
-------------

This platform is not fully supported yet and still in testing phase. It uses ``spack-stack`` version ``1.5.1`` and supports only Intel compiler (``19.1.1.217``) along with Intel MPI (``2020.4.304``). The module file `ufs_frontera.intel.lua <https://github.com/oceanmodeling/ufs-coastal/blob/feature/coastal_app/modulefiles/ufs_frontera.intel.lua>`_ is also included to the UFS Coastal code base along with update in RT framework to enable experimenting the new platform. There is a plan to update ``spack-stack`` version and also used compiler and MPI versions.

=======================
Installing Dependencies
=======================




Docker Container
----------------

A `Docker <https://www.docker.com/>`_ container image is a lightweight, standalone, executable package of software that includes everything needed to run an application: code, runtime, system tools, system libraries and settings. It enables creating development and testing environment that run on local resources.

The `Docker Desktop <https://www.docker.com/products/docker-desktop/>`_ is required to build and run the Docker containers.

The following instructions can be used to create a new Docker container from scratch but the pre-build container can be also used to run UFS Coastal. There is a plan to make available pre-configured Docker Containers for UFS Coastal through the `DockerHub <https://hub.docker.com>`_.

1. Run a new Docker container

.. code-block:: console

   docker run -it ubuntu:latest 

.. note::
   In this case, the command will create a Docker Container that uses Ubuntu OS.

.. note::
   The optional ``--rm`` argument can be used when the container needed to be deleted after the task for it is complete.
   The optional ``--platform`` argument can be used to emulate specific platform (i.e. linux/amd64). This needs to be used carefully since it could slow down the container.

2. Install base development environment with Ubuntu package manager (apt).

.. code-block:: console

   apt-get -yqq update
   apt-get -yqq upgrade
   apt-get install --no-install-recommends -yqq \
   gcc \
   g++ \
   gfortran \
   build-essential \
   libkrb5-dev \
   m4 \
   git \
   git-lfs \
   vim \
   bzip2 \
   unzip \
   tar \
   automake \
   xterm \
   texlive \
   libcurl4-openssl-dev \
   libssl-dev \
   meson \
   python3-dev  \
   python3-pip \
   wget  \
   rsync \
   tcl  \
   tcl-dev \
   openssh-client

3. Clone Spack-stack

In this case, ``/opt`` directory will be used to install the dependencies but there is no any restriction to use another directory for installation. Also, spack-stack 1.5.1 is used as an example.

.. code-block:: console

   cd /opt
   git clone --recurse-submodules https://github.com/jcsda/spack-stack.git
   cd spack-stack
   git checkout 1.5.1
   git submodule update --init --recursive
   export SPACK_ROOT=/opt/spack-stack/spack
   source setup.sh

4. Create spack environment and activate it

.. code-block:: console

   spack stack create env --site linux.default --template ufs-weather-model --name ufs.local --prefix /opt/ufs.local
   cd envs/ufs.local
   spack env activate .

.. note::
   ``spack stack create env -h`` shows the list of available environments.

5. Find external packages that are shipped through the OS and installed with ``apt`` package manager in Step (2).

.. code-block:: console

   cd /opt/spack-stack
   export SPACK_SYSTEM_CONFIG_PATH="/opt/spack-stack/envs/ufs.local/site"
   spack external find --scope system --exclude bison --exclude cmake --exclude curl --exclude openssl --exclude openssh
   spack external find --scope system perl
   spack external find --scope system wget
   spack external find --scope system texlive
   spack compiler find --scope system
   unset SPACK_SYSTEM_CONFIG_PATH

6. Set compiler and MPI library that will be used to install dependencies. In this example, GNU compiler and OpenMPI are used. The compiler and MPI library versions could change based on the version of the used OS. To that end, user needs to check compiler and MPI versions carefully. Following commands give some exmaple to find out the versions and addind them to the spack-stack configuration.

.. code-block:: console

   gcc --version
   spack config add "packages:all:compiler:[gcc@YOUR-VERSION]"
   # Example
   spack config add "packages:all:compiler:[gcc@11.4.0]"

   # Example for Red Hat 8 following the above instructions
   spack config add "packages:all:providers:mpi:[openmpi@4.1.6]"

   # Example for Ubuntu 20.04 or 22.04 following the above instructions
   spack config add "packages:all:providers:mpi:[mpich@4.1.1]"

7. Set few more package variants

.. code-block:: console

   spack config add "packages:fontconfig:variants:+pic"
   spack config add "packages:pixman:variants:+pic"
   spack config add "packages:cairo:variants:+pic"
   spack config add "packages:libffi:version:[3.3]"

8. Add additional dependencies to newly created spack environment for UFS Coastal

.. code-block:: console

   spack add parmetis@4.0.3~shared ^metis~shared
   spack add proj@4.9.2~shared~tiff

.. note::
   Since ``parmetis`` package depends on ``metis``, it will also install `metis@5.1.0` spack package. Also note that ``metis@5.1.0`` is not compatible with ADCIRC and throw error like ``undefined reference to metis_estimatememory_``.

.. note::
   The ``proj`` package had bug in spack-stack ``1.4.1`` version. This is fixed in recent version of the spack-stack (``>= 1.5.1```) but ``spack`` submodule can be updated under ``spack-stack`` for older versions with the following instructions. Again, this is not needed for newer versions of spack-stack.

   .. code-block:: console

      cd spack-stack/spack
      git remote add upstream https://github.com/spack/spack.git
      git fetch upstream
      git cherry-pick upsream 149d194 (and resolve conflicts)

9. Install packages and clean unneccecary files

.. code-block:: console

   spack concretize 2>&1 | tee log.concretize
   spack install --source 2>&1 | tee log.install
   spack gc -y  2>&1 | tee log.clean

10. (Optional) To create module files for the dependencies, `lmod <https://lmod.readthedocs.io/en/latest/>`_ and ``lua`` needs to be installed. Following commands can be used to install them.

To install ``lua```:

.. code-block:: console

   cd /opt
   export LUA_VERSION=5.1.4.9
   wget -c https://sourceforge.net/projects/lmod/files/lua-${LUA_VERSION}.tar.bz2
   tar -xvf lua-${LUA_VERSION}.tar.bz2
   cd lua-${LUA_VERSION}
   ./configure --prefix=/opt/lua
   make
   make install

To install ``lmod```:

.. code-block:: console

   cd /opt
   export LMOD_VERSION=8.7
   wget -c https://sourceforge.net/projects/lmod/files/Lmod-${LMOD_VERSION}.tar.bz2
   tar -xvf Lmod-${LMOD_VERSION}.tar.bz2
   cd Lmod-${LMOD_VERSION}
   ./configure --prefix=/opt/lmod --with-lua=/opt/lua/bin/lua --with-luac=/opt/lua/bin/luac --with-lua_include=/opt/lua/include
   make
   make install

Then, ``lmod`` can be activated with following commands:

.. code-block:: console

   source /opt/lmod/lmod/${LMOD_VERSION}/init/profile
   ln -sf /opt/lmod/lmod/${LMOD_VERSION}/init/profile /etc/profile.d/lmod.sh

After instaling ``lmod`` successfully, the module files for dependencies, which are installed by spack-stack can be created with following command,

.. code-block:: console

   spack module tcl refresh -y
   spack stack setup-meta-modules

11. (Optional) Testing module files that are created in Step (10)

.. code-block:: console

   . /etc/profile.d/modules.sh
   module use /opt/ufs.local/modulefiles/Core
   module load stack-gcc/11.4.0
   module load stack-python/3.10.8
   module load stack-openmpi/4.1.6

.. note::
   Module names can be different if different versions of GNU compiler, MPI library and Python are installed.

12. Clone UFS Coastal Model and create new module file to support custom Docker installation

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
   module load stack-openmpi/4.1.6
   
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

13. Testing build of UFS Coastal specific configurations  

.. code-block:: console

   cd ufs-coastal/tests

   # ADCIRC (DATM+OCN, ADCIRC is not compatible with Metis 5.x at this point)
   ./compile.sh "local" "-DAPP=CSTLA -DBUILD_ADCPREP=ON -DADCIRC_CONFIG=PADCIRC -DCOUPLED=ON" coastal gnu NO NO

   # FVCOM (DATM+OCN)
   ./compile.sh "local" "-DAPP=CSTLF -DCOORDINATE_TYPE=SPHERICAL -DWET_DRY=ON" coastal gnu NO NO

   # SCHISM (DATM+OCN)
   ./compile.sh "local" "-DAPP=CSTLS -DUSE_ATMOS=ON -DNO_PARMETIS=OFF -DOLDIO=ON" coastal gnu NO NO

.. note::
   In addition to the steps that are explained above, the UFS Coastal RT system needs to be adjusted to support running RT under Docker container. This part is not covered by the documentation.
