.. _Workflow:

**************
Using Workflow
**************

============
Dependencies
============


=======================================
Downloading the UFS Coastal Application
=======================================

To clone the main branch of the ``ufs-coastal-app`` repository including its submodules, execute the following commands:

.. code-block:: console

   git clone --recursive https://github.com/oceanmodeling/ufs-coastal-app
   cd ufs-coastal-app

Compiling the executable that will be used by workflow will be done with top level build script ``build.sh``.

========================
Building the Application
========================

The application level build script (``build.sh``) mainly leverages build infrastructure and environment modules that are provided by the model (``sorc/ufs-weather-model``). The options that can be used in ``build.sh`` can be seen as following,

.. code-block:: console

   Usage: ./build.sh --platform=PLATFORM [OPTIONS] ... [TARGETS]
   
   OPTIONS
     -a, --app=APPLICATION
         weather model application to build; for example, CSTLS for DATM+SCHISM
     --bin-dir=BIN_DIR
         installation binary directory name ("bin" by default; any name is available)
     -b, --build-dir=BUILD_DIR
         build directory
     --build-jobs=BUILD_JOBS
         number of build jobs; defaults to 4
     --build-type=BUILD_TYPE
         build type; defaults to RELEASE
         (e.g. DEBUG | RELEASE | RELWITHDEBINFO)
     --clean
         does a "make clean"
     -c, --compiler=COMPILER
         compiler to use; default depends on platform
         (e.g. intel | gnu)
     -h, --help
         show this help guide
     -i, --install-dir=INSTALL_DIR
         installation prefix
     -p, --platform=PLATFORM
         name of machine you are building on
         (e.g. cheyenne | hera | jet | orion | wcoss2)
     --remove
         removes existing build
     -v, --verbose
         build with verbose output
   
   NOTE: See User's Guide for detailed build instructions

To build DATM-SCHISM configuration (incl. CDEPS, CMEPS and SCHISM components) can be build on MSU Hercules using following command,

.. code-block:: console

   ./build.sh --platform=hercules --app=CSTLS --compiler=intel

This will install all executables (incl. SCHISM tools) under ``install/bin`` directory on the UFS Coastal Application source tree. The default installation directory can be overwritten using ``--install-dir`` command line argument. By this way, the installation can be done in any custom directory.

=======================================
Creating Conda Environment for Workflow
=======================================

MSU Hercules:

.. code-block:: console

   module load miniconda3/24.3.0
   cd ufs-coastal-app
   conda create --prefix $PWD/python/envs/myenv
   conda activate $PWD/python/envs/myenv
   conda install -c conda-forge --override-channels conda-build conda-verify
   cd sorc/uwtools/
   conda build recipe -c conda-forge --override-channels
   conda install -c ../../python/envs/myenv/conda-bld uwtools




