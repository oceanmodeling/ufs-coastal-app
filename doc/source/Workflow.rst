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
   conda install udunits2
   conda install fiona
   pip install pyschism
   
   conda install -c conda-forge xarray dask netCDF4 bottleneck
   conda install -c conda-forge esmpy
   conda install -c conda-forge herbie-data

.. note::
   ``udunits2`` and ``fiona`` Python modules are required by ``pyschism``.

In this case, `pyschism <https://github.com/schism-dev/pyschism>`_ is used to process SCHISM ocean model related input files while `Herbie <https://herbie.readthedocs.io/en/stable/index.html>`_ Python module is used to retrieve forcing files (i.e. `HRRR <https://rapidrefresh.noaa.gov/hrrr/>`_) that will be used by CDEPS Data Atmosphere to force the ocean model component. The rest of the Python modules are used to process forcing files to create `ESMF Mesh file <http://earthsystemmodeling.org/docs/nightly/develop/ESMF_refdoc/node3.html#SECTION03040000000000000000>`_, which is required by the CDEPS data component.

======================
Components of Workflow
======================

The workflow related files are found in two different directories under main source directory; ``templates/`` and ``ush/``. In this case, the template files are using `Jinja <https://jinja.palletsprojects.com/en/stable/>`_ format to define component specific namelist files. The ``ush/`` directory includes UFS Coastal application specific scripts and configuration files that are used by the ``uwtools`` workflow environment.

The current version of the workflow is leveraging a simple ``uwtools`` provided workflow engine called as `iotaa - It's One Thing After Another <https://github.com/maddenp/iotaa>`_ but there is a plan to support `ecFlow <https://confluence.ecmwf.int/display/ECFLOW>`_ workflow manager as a part of the UFS Coastal Application when it is supported by ``uwtools``.

.. note::
   The initial version of workflow only supports DATM-SCHISM configuration but it will be improved to cover other UFS Coastal specific configurations in the near future.

Main configuration file ``config.yaml``
---------------------------------------

This section includes detailed information about the main configuration file (``config.yaml`` that is found under ``ush/`` directory) and the parameters used in each section. The YAML formatted file includes multiple sections to define entire end-to-end workflow. Each supported configuration has its own template ``config.yaml`` file. To run a configuration through the workflow, the user needs to copy one of the template file as ``config.yaml`` and customize it based on selected configuration.

The following tables mainly describes the options that can be used in the ``config.yaml``. Some of those options are configuration specific. For example, ``schism`` section is only required when configuration includes SCHISM ocean model component but ``coastal`` or ``platform`` sections are required for all the configurations.

.. list-table:: Section ``coastal`` (required)
   :widths: 10 25
   :header-rows: 1

   * - Option
     - Description
   * - execution
     - Sub-section for the job submission script
       It might include ``batchargs``, ``envcmds``, ``executable``, ``mpiargs`` and ``mpicmd``
   * - links
     - List of the files that will be copied to run directory. It is given as destination, source pairs.
   * - rundir
     - Path for run directory

.. list-table:: Section ``driver`` (required)
   :widths: 10 25
   :header-rows: 1

   * - Option
     - Description
   * - componentList
     - List of model components that will be active in the configuration
   * - runSequence
     - Coupling run sequence. The names used in here needs to be consistent with name of active model components
   * - attributes
     - Driver level ESMF/NUOPC attributes such as ``Verbosity`` level
   * - allcomp/attributes
     - Attributes that will be shared across model components
   * - med
     - Mediator specific attributes such as model name, PET range etc.
   * - atm
     - Atmospheric model specific attributes such as model name, PET range etc.
   * - ocn
     - Ocean model specific attributes such as model name, PET range etc.

.. note::
   Model specific sections can be optional. If the desired configuration does not have ocean component, then ``ocn`` section can be skipped.   
.. list-table:: Section ``platform`` (required)
   :widths: 10 25
   :header-rows: 1

   * - Option
     - Description
   * - account
     - Account used in the job submission script
   * - scheduler
     - Type of job scheduler. Supported options are ``slurm``, ``pbs``, and ``lsf``

.. list-table:: Section ``cdeps`` (optional)
   :widths: 10 25
   :header-rows: 1

   * - Option
     - Description
   * - cdeps/atm_in/update_values/datm_nml
     - Data atmosphere specific configuration options used in ``datm_in``
   * - cdeps/atm_streams/streams/stream[NN]
     - Data atmosphere specific configuration options used in ``datm.streams``

.. note::
   The ``cdeps/atm_streams/streams/`` section might include multiple section of streams named like ``stream01``, ``stream02`` etc.

.. note::
   More information about CDEPS related configuration options can be found in `CDEPS documentation <https://escomp.github.io/CDEPS/versions/master/html/index.html>`_.

.. list-table:: Section ``schism`` (optional)
   :widths: 10 25
   :header-rows: 1

   * - Option
     - Description
   * - hgrid
     - Location of SCHISM horizontal grid that will be used to create input files
   * - vgrid
     - Location of SCHISM vertical grid that will be used to create input files
   * - boundary_vars
     - Flags for boundary variables that would be created. The orders are ``elev2D``, ``TS``, and ``UV``.
   * - ocean_bnd_ids
     - Segment indices for ocean boundaries, starting from zero
   * - bctides
     - Subsection for tidal boundary conditions such as TPXO dataset location, constituents etc.
   * - gr3
     - Subsection for gr3 files
   * - namelist
     - Subsection for ``param.nml`` customizations such as ``rnday`` for total run time in days or ``dt`` for time step in sec.
       
.. note::
   The entries in `schism/namelist` section are used to customize SCHISM main configuration file (``param.nml``). The parameters that are used to define simulation start date (``start_year``, ``start_month``, ``start_day``, ``start_hour`` and ``utc_start``) is modified automatically by the workflow and there is no need to define them seperately in this section. The main template file can be seen under ``templates/param.nml`` directory.

.. list-table:: Section ``input`` (optional)
   :widths: 10 25
   :header-rows: 1

   * - Option
     - Description
   * - source
     - The data source. Both ``hrrr`` (High Resolution Rapid Refresh, default) and ``gfs`` (Global Forecast System) are supported.
   * - length
     - Lenght of required data in hours. Default is 24.
   * - fxx
     - Forecast lead time. Default is 0.
   * - subset
     - Option to subset data based on given grid file. Default is ``true``.
   * - overwrite
     - Option to overwrite all files. Default is ``false``.

.. note::
   The workflow uses Python Herbie module to retrieve data files and more information can be found in `Herbie documentation <https://herbie.readthedocs.io/en/stable/index.html>`_. HRRR Homepage (ESRL) can be found in `GSL webpage <https://rapidrefresh.noaa.gov/hrrr/>`_.

.. note::
   The forcing file used by data components can be also provided by user. In this case, the files can be copied to run directory using ``coastal/links`` section.

DATM-SCHISM Configuration
-------------------------

The model configuration includes two model components (CDEPS and SCHISM) and the mediator (CMEPS) to create uni-directional coupled application. In this case, CDEPS Data Atmosphere provides atmospheric forcing (components of the wind speed and also surface pressure) to the ocean model component but there is no feedback from the ocean to atmsopheric model component.

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
     - Generate open boundary input files using ``self.schism_bnd_inputs()``
     - schism
     - schism
   * - 8
     - Generate ``gr3`` formatted input files using ``self.schism_gr3_inputs()``
     - schism
     - schism/gr3
   * - 9
     - Generate tidal open boundary conditions using ``self.schism_tidal_inputs()``
     - schism
     - schism/bctides
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

.. note::
   To use GFS (Global Forecast System, 0.25 deg. global 6-hourly dataset) output as forcing, following changes need to be done in ``coastal.yaml`` workflow configuration file. (1) Set ``input/source`` to ``gfs``, and (2) set ``cdeps/atm_streams/streams/stream01/stream_data_variables`` to ``[u10 Sa_u10m, v10 Sa_v10m, prmsl Sa_pslv ]``.

Running Workflow
----------------

The run directory for the specified configuration (via ``coastal.yaml``) can be created using following command.

.. code-block:: console

   cd ufs-coastal-app/ush
   uw execute --module coastal.py --classname Coastal --task provisioned_rundir --config-file coastal.yaml --cycle 2024-08-05T12 --batch

Once ``uw execute`` command issued, it will create a run directory specified by ``dir/run`` entry in the ``coastal.yaml``. The run directory can be customized by point another diretory in the YAML configuration file. Then, the job can be submitted manually by using ``runscript.coastal`` SLURM job submisson script. The detailed information about runninf jobs on MSU's Hercules platform can be found in `here <https://docs.rdhpcs.noaa.gov/systems/MSU-HPC_user_guide.html>`_.

.. code-block:: console

   sbatch runscript.coastal
