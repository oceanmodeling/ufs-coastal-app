.. _Workflow:

**************
Using Workflow
**************

The UFS Coastal Application uses Python based `Unified Workflow Tools (uwtools) <https://uwtools.readthedocs.io/en/stable/>`_ as a workflow environment. The tools that are provided by ``uwtools`` are accessible from both a command-line interface (CLI) and a Python API.

============
Dependencies
============

Following tools are needed to use workflow provided by the UFS Coastal Application.

- Python
- Conda (e.g., Miniforge, Miniconda, Anaconda) - install ``uwtools`` into an existing or new conda environment
- Pip

=======================================
Downloading the UFS Coastal Application
=======================================

To clone the main branch of the ``ufs-coastal-app`` repository including its submodules, execute the following commands:

.. code-block:: console

   git clone --recursive https://github.com/oceanmodeling/ufs-coastal-app
   cd ufs-coastal-app

Compiling the executable that will be used by workflow will be done with top level build script ``build.sh``.

.. note::
   Building model is not part of the workflow.

========================
Building The Application
========================

The application level build script (``build.sh``) mainly leverages build infrastructure and environment modules that are provided by the UFS WM (UFS Weather Model, ``sorc/ufs-weather-model``). The options that can be used in ``build.sh`` can be seen as following,

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

For example, DATM-SCHISM configuration (incl. `CDEPS <https://github.com/ESCOMP/CDEPS>`_, `CMEPS <https://github.com/ESCOMP/CMEPS>`_ and `SCHISM <https://github.com/schism-dev/schism>`_ model components) can be build on MSU Hercules using following command,

.. code-block:: console

   ./build.sh --platform=hercules --app=CSTLS --compiler=intel

The given command will install all executables (incl. SCHISM pre- and post-processing tools) and copy them under ``install/bin`` directory on the UFS Coastal Application source tree (i.e. under `ufs-coastal-app/` directory). The default installation directory (same with the `./build.sh` script) can be overwritten by using ``--install-dir`` command line argument. By this way, the installation file can be placed in any user defined custom directory.

=======================================
Creating Conda Environment for Workflow
=======================================

To use `Unified Workflow Tools <https://uwtools.readthedocs.io/en/stable/>`_, a Python environment needs to be created. The following section aims to give brief information to create such environment.

MSU Hercules
------------

This section includes step-by-step guidence to install workflow and its dependencies using `Conda <https://docs.conda.io/en/latest/#>`_ Python environment and package manager on MSU's Hercules platform. The following commands can be used to create new Conda environment named as ``myenv`` under UFS Coastal Application source directory that includes ``uwtools`` module. More information about installing ``uwtools`` can be found in the following `link <https://uwtools.readthedocs.io/en/stable/sections/user_guide/installation.html>`_.

.. code-block:: console

   cd ufs-coastal-app
   module load miniconda3/24.3.0
   conda create --prefix $PWD/python/envs/myenv
   conda activate $PWD/python/envs/myenv
   conda install -c conda-forge --override-channels conda-build conda-verify
   cd sorc/uwtools/
   conda build recipe -c conda-forge --override-channels
   conda install -c ../../python/envs/myenv/conda-bld uwtools

Then, additional Python modules that is required by the workflow can be installed with following commands,

.. code-block:: console
   
   conda install pip
   pip install pyschism
   
   conda install -c conda-forge xarray dask netCDF4 bottleneck
   conda install -c conda-forge esmpy
   conda install -c conda-forge herbie-data

In this case, `pyschism <https://github.com/schism-dev/pyschism>`_ is used to process SCHISM ocean model related input files while `Herbie <https://herbie.readthedocs.io/en/stable/index.html>`_ Python module is used to retrieve forcing files (i.e. `HRRR <https://rapidrefresh.noaa.gov/hrrr/>`_) that will be used by CDEPS Data Atmosphere to force the ocean model component. The rest of the Python modules are used to process forcing files to create `ESMF Mesh file <http://earthsystemmodeling.org/docs/nightly/develop/ESMF_refdoc/node3.html#SECTION03040000000000000000>`_, which is required by the CDEPS data component.

================
Running Workflow
================

The workflow related files are found in two different directories under main source directory; ``templates/`` and ``ush/``. In this case, the template files are using `Jinja <https://jinja.palletsprojects.com/en/stable/>`_ format to define component specific namelist files. The ``ush/`` directory includes UFS Coastal application specific scripts and configuration files that are used by the ``uwtools`` workflow environment.

The current version of the workflow is leveraging a simple ``uwtools`` provided workflow engine called as `iotaa - It's One Thing After Another <https://github.com/maddenp/iotaa>`_ but there is a plan to support `ecFlow <https://confluence.ecmwf.int/display/ECFLOW>`_ workflow manager as a part of the UFS Coastal Application when it is supported by ``uwtools``.

.. note::
   The initial version of workflow only supports DATM-SCHISM configuration but it will be improved to cover other UFS Coastal specific configurations in the near future.

DATM-SCHISM
-----------

This model configuration has two model components (CDEPS and SCHISM) and the mediator (CMEPS) to create uni-directional coupled application. In this case, CDEPS Data Atmosphere provides atmospheric forcing (components of the wind speed and also surface pressure) to ocean model component but ocean model does not feedback to the atmsopheric model component.

The main workflow configuration file (``coastal.yaml``) for this specific configuration is found under ``ush/`` directory. The YAML formatted file includes multiple sections to define entire end-to-end workflow. The detailed information and steps about currently supported workflow can be seen in following table.

.. list-table:: Workflow tasks for DATM-SCHISM configuration
   :widths: 10 25 50 50
   :header-rows: 1

   * - #
     - Task
     - Related component
     - Sections in ``coastal.yaml``
   * - 1
     - Download forcing data using ``data_retrieve()``
     - cdeps, datm
     - input
   * - 2
     - Create ESMF mesh file using ``create_mesh()`` (uses ESMF provided ``ESMF_Scrip2Unstruct`` tool) 
     - cdeps, datm
     -
   * - 3
     - Generate ``model_configure`` using ``_model_configure()``
     - driver
     - driver
   * - 4
     - Generate ``ufs.configure`` using ``_ufs_configure()`` 
     - driver
     - driver, med, atm, ocn
   * - 5
     - Generate ``datm_in`` using ``cdeps.atm_nml()``
     - cdeps, datm
     - cdeps/atm_in/update_values/datm_nml
   * - 6
     - Generate ``datm.streams`` using ``cdeps.atm_stream()``
     - cdeps, datm
     - cdeps/atm_streams/streams/stream01
   * - 7
     -
     -
     -
   * - 8
     -
     -
     -
   * - 9
     -
     -
     -
   * - 10
     - Generate ``param.nml`` using ``schism.namelist_file()``
     - schism
     - schism/namelist
   * - 11
     - Copy files like ``fd_ufs.yaml`` from UFS WM source using ``self.linked_files()``
     - model
     - coastal/links
   * - 12
     - Create required directoryies such as ``RESTART`` under run directory using ``self.restart_dir()``
     - model    
     -
   * - 13
     - Create job submission script using ``self.runscript()``
     - model
     -

The following command is used to trigger each task to populate run directory required for the DATM-SCHISM configuration.

.. code-block:: console

   cd ufs-coastal-app/ush
   uw execute --module coastal.py --classname Coastal --task provisioned_rundir --config-file coastal.yaml --cycle 2024-08-05T12 --batch

Once ``uw execute`` command issued, it will create a run directory specified by ``dir/run`` entry in the ``coastal.yaml``. The run directory can be customized by point another diretory in the YAML configuration file. Then, the job can be submitted manually by using ``runscript.coastal`` SLURM job submisson script. The detailed information about runninf jobs on MSU's Hercules platform can be found in `here <https://docs.rdhpcs.noaa.gov/systems/MSU-HPC_user_guide.html>`_.

.. code-block:: console

   sbatch runscript.coastal
