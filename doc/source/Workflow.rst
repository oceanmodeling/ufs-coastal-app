.. _Workflow:

**************
Using Workflow
**************

The UFS Coastal Application uses Python based `Unified Workflow Tools (uwtools) <https://uwtools.readthedocs.io/en/stable/>`_ as a workflow environment. The tools that are provided by ``uwtools`` are accessible from both a command-line interface (CLI) and a Python API.

============
Dependencies
============

Following base tools are needed to use the workflow provided by the UFS Coastal Application.

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

The UFS Coastal executable (``ufs_model``) that will be used by the workflow are created using top level build script ``build.sh``.

.. note::
   Currently, building UFS Coastal model is not part of the application level workflow.

========================
Building The Application
========================

The application level build script (``build.sh``) mainly leverages build infrastructure and environment modules that are provided by the UFS WM (UFS Weather Model, ``sorc/ufs-weather-model``). The options that can be used in ``build.sh`` can be seen in the following code block,

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
     --cmake-settings=CMAKE_SETTINGS
         Additional CMake settings provided by user
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

.. note::
  The most up-to-date list of the available options can be seen using ``./build.sh -h`` command.

The DATM-SCHISM configuration (incl. CDEPS, `CMEPS <https://github.com/ESCOMP/CMEPS>`_ and `SCHISM <https://github.com/schism-dev/schism>`_ model components) can be build on MSU Hercules using following command,

.. code-block:: console

   ./build.sh --platform=hercules --app=CSTLS --compiler=intel

The shown command will install all the executables (incl. SCHISM pre- and post-processing tools) and copy them to ``install/bin`` directory on the UFS Coastal Application source tree (i.e. under `ufs-coastal-app/` directory). The default installation directory can be overwritten by using ``--install-dir`` command line argument. By this way, the installation files and executables can be placed in any user defined custom directory.

=======================================
Creating Conda Environment for Workflow
=======================================

To use `Unified Workflow Tools <https://uwtools.readthedocs.io/en/stable/>`_ and run UFS Coastal specific model comfigurations, a Python environment that includes dependencies needs to be created. The following section aims to give brief information about creating such working environment.

.. note::
   At this point, the UFS Coastal workflow is only tested on MSU Hercules and it is still active development. The new issues related with the workflow can be created in `UFS Coastal Application repository issue page <https://github.com/oceanmodeling/ufs-coastal-app/issues>`_. 

MSU Hercules
------------

This section includes step-by-step information to install workflow and its dependencies using `Conda <https://docs.conda.io/en/latest/#>`_ and `pip <https://packaging.python.org/en/latest/tutorials/installing-packages/>`_ Python package managers on MSU's Hercules platform. The following commands can be used to create new Conda environment named as ``myenv`` under UFS Coastal Application source directory that includes ``uwtools`` module. More information about installing ``uwtools`` can be found in the following `link <https://uwtools.readthedocs.io/en/stable/sections/user_guide/installation.html>`_.

* Install UWTools
  
.. code-block:: console

   cd ufs-coastal-app
   module load miniconda3/24.3.0
   conda create --prefix $PWD/python/envs/myenv
   conda activate $PWD/python/envs/myenv
   conda install -y -c conda-forge --override-channels conda-build conda-verify
   cd sorc/uwtools/
   make package
   conda install -c $CONDA_PREFIX/conda-bld -c conda-forge --override-channels uwtools=2.5.1

.. note::
   ``conda search -c $CONDA_PREFIX/conda-bld --override-channels uwtools`` command can be used to verify local availability of the newly built package. More information about building uwtools locally can be found in its `user guide <https://uwtools.readthedocs.io/en/stable/sections/user_guide/installation.html#build-the-uwtools-package-locally>`_. 

* Install Other Python Dependencies

Additional Python modules that is required by the workflow can be installed with following commands,

.. code-block:: console
   
   conda install -c conda-forge xarray dask netCDF4 bottleneck esmpy herbie-data boto3 pip udunits2 fiona
   pip install pyschism

.. note::
   ``udunits2`` and ``fiona`` Python modules are required by ``pyschism``.

The `pyschism <https://github.com/schism-dev/pyschism>`_ is used to pre-process SCHISM ocean model related input files while `Herbie <https://herbie.readthedocs.io/en/stable/index.html>`_ Python module is used to retrieve forcing files (i.e. `HRRR <https://rapidrefresh.noaa.gov/hrrr/>`_) that will be used by CDEPS Data Atmosphere to force the ocean model component. The rest of the Python modules are used to process forcing files to create `ESMF Mesh file <http://earthsystemmodeling.org/docs/nightly/develop/ESMF_refdoc/node3.html#SECTION03040000000000000000>`_, which is required by the CDEPS data component.

.. note::
   In addtion to Herbie Python module to retrive required forcing data, the initial version of the wokflow also provide capability to use `Boto3 <https://boto3.amazonaws.com/v1/documentation/api/latest/index.html>`_ Python module to retrieve data from AWS S3 buckets and ``wget`` command to download data from ``http`` and ``https`` end points. The user needs to specify protocol in each CDEPS stream configuration to define the approach to download the forcing data that will be used in the simulation.

======================
Components of Workflow
======================

The initial version of UFS Coastal Application workflow is leveraging ``uwtools`` that uses workflow engine called as `iotaa - It's One Thing After Another <https://github.com/maddenp/iotaa>`_. There is also plan to support `ecFlow <https://confluence.ecmwf.int/display/ECFLOW>`_ and/or `Rocoto <https://github.com/christopherwharrop/rocoto/wiki/documentation>`_ as a workflow manager through the ``uwtools``.

The UFS Coastal specific workflow related files are found in following directories under main source directory; 

* `templates/ <https://github.com/oceanmodeling/ufs-coastal-app/tree/main/templates>`_. The `Jinja <https://jinja.palletsprojects.com/en/stable/>`_ formatted template files is used by the workflow to generate component specific namelist files.

* `ush/ <https://github.com/oceanmodeling/ufs-coastal-app/tree/main/ush>`_. It includes UFS Coastal workflow specific scripts and configuration files that are used by the ``uwtools`` workflow environment.

* `tests/ <https://github.com/oceanmodeling/ufs-coastal-app/tree/main/tests>`_. It includes application level test configurations.
  
.. note::
   The initial version of the workflow supports only DATM-SCHISM configuration but the workflow will be extended to cover also other UFS Coastal specific configurations such as DATM-SCHISM-WW3 and DATM-ROMS in the near future.

Main configuration file ``coastal.yaml``
----------------------------------------

This section includes detailed information about the main configuration file found under ``ush/`` directory (`coastal.yaml <https://github.com/oceanmodeling/ufs-coastal-app/blob/main/ush/coastal.yaml>`_). The YAML formatted file includes various sections to define entire end-to-end workflow and their sub-sections related with the desired model configuration. The ``tests/`` directory also includes example configurations such as ``coastal_ike_shinnecock_atm2sch.yaml`` for DATM-SCHISM configuration. To run a configuration through the workflow, the example configurations under ``tests/`` directory or the main configuration file (``coastal.yaml``) can be used and customized based on desired configuration.

* Platform specific definitions

.. code-block:: yaml

  dir:
    app: "{{ 'PWD' | env }}/.."
    run: run
  platform:
    account: nems
    scheduler: slurm
  coastal:
    execution:
      batchargs:
        cores: 6
        export: NONE
        jobname: myjob 
        stderr: err
        stdout: out
        partition: hercules
        queue: batch
        walltime: '00:30:00'
      envcmds:
        - module use {{ dir.app }}/sorc/ufs-weather-model/modulefiles
        - module load ufs_hercules.intel
        - export ESMF_RUNTIME_PROFILE=ON
        - export ESMF_RUNTIME_PROFILE_OUTPUT="SUMMARY"
      executable: "{{ dir.app }}/install/bin/ufs_model"
      mpiargs:
        - '--export=ALL'
      mpicmd: srun

This section includes platform specific definitions related with the job scheduler (``scheduler`` entry) and the parameters that would be passed to the scheduler (``batchargs``, ``envcmds``, ``mpiargs`` and ``mpicmd`` sections under ``coastal/execution`` entry).

* NUOPC driver specific definitions

The UFS Coastal model uses `ESMF/NUOPC <https://earthsystemmodeling.org/nuopc/>`_ as a coupling infrastructure to allow interaction among different model components. To define the active model components, their interactions and component specific options, The UFS Coastal model uses ``ufs.configure`` and ``model_configure`` namelist files (`ESMF Config format <https://earthsystemmodeling.org/docs/nightly/develop/ESMF_refdoc/node6.html#SECTION06090000000000000000>`_). The following sections from ``coastal.yaml`` shows NUOPC driver specific sections for DATM-SCHISM configuration.

.. code-block:: yaml

  nuopc:
    driver:
      componentList: [ATM, OCN, MED]
      runSequence: |
        @3600
          ATM -> MED :remapMethod=redist
          MED med_phases_post_atm
          OCN -> MED :remapMethod=redist
          MED med_phases_post_ocn
          MED med_phases_prep_atm
          MED med_phases_prep_ocn_accum
          MED med_phases_prep_ocn_avg
          MED -> ATM :remapMethod=redist
          MED -> OCN :remapMethod=redist
          ATM
          OCN
          MED med_phases_history_write
          MED med_phases_restart_write
        @
      attributes:
        Verbosity: low  
      allcomp:
        attributes:
          ScalarFieldCount: 3
          ScalarFieldIdxGridNX: 1
          ScalarFieldIdxGridNY: 2
          ScalarFieldIdxNextSwCday: 3
          ScalarFieldName: cpl_scalars
          start_type: startup
          restart_dir: RESTART/
          case_name: ufs.cpld
          restart_n: 12
          restart_option: nhours
          restart_ymd: -999
          orb_eccen: 1.e36
          orb_iyear: 2000
          orb_iyear_align: 2000
          orb_mode: fixed_year
          orb_mvelp: 1.e36
          orb_obliq: 1.e36
          stop_n: 24
          stop_option: nhours
          stop_ymd: -999
    med:
      model: cmeps
      petlist_bounds: 0-2
      omp_num_threads: 1
      attributes:
        history_n: 1
        history_option: nsteps
        history_ymd: -999
        coupling_mode: coastal
    atm:
      model: datm
      petlist_bounds: 0-2
      omp_num_threads: 1
      attributes:
        Verbosity: 0
        DumpFields: false
        ProfileMemory: false
        OverwriteSlice: true
    ocn:
      model: schism
      petlist_bounds: 3-5
      omp_num_threads: 1
      attributes:
        Verbosity: 0
        DumpFields: false
        ProfileMemory: false
        OverwriteSlice: true
        meshloc: element
        CouplingConfig: none

The following table aims to describe the desction used in the YAML file.

.. list-table:: Section ``driver`` (required)
   :widths: 10 25
   :header-rows: 1

   * - Option
     - Description
   * - componentList
     - List of model components that will be active in the configuration such as ATM for atmospheric model component, OCN for ocean model and MED for mediator component (``CMEPS``) 
   * - runSequence
     - Coupling run sequence that defined interaction among components and coupling interval. The names used in here needs to be consistent with name of active model components
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

* CDEPS data components specific definitions

The Community Data Models for Earth Predictive Systems (CDEPS) contains a set of NUOPC-compliant data components along with ESMF-based share code that enables new capabilities in selectively removing feedbacks in coupled model systems. The following YAML block is used to activate CDEPS data atmosphere component that provides single stream. 

.. code-block:: yaml

  cdeps:
    datm:
      update_values:
        datm_nml:
          datamode: ATMMESH
          export_all: true
          factorfn_data: 'null'
          factorfn_mesh: 'null'
          flds_co2: false
          flds_presaero: false
          flds_wiso: false
          iradsw: 1
          restfilm: 'null'
      streams:
        stream01:
          taxmode: limit
          mapalgo: redist
          tinterpalgo: linear
          readmode: single
          dtlimit: 1.5
          stream_offset: 0
          stream_vectors: 'null'
          stream_lev_dimname: 'null'
          stream_data_variables: [ u10 Sa_u10m, v10 Sa_v10m, mslma Sa_pslv ]
          data:
            protocol: herbie
            source: hrrr
            length: 24 
            fxx: 0
            subset: true
            combine: false
            target_directory: 'INPUT'
    template_file: ../templates/cdeps.streams

In this case, ``cdeps/datm/update_values/datm_nml`` section provides configuration options related with data atmosphere component while ``cdeps/datm/streams/stream01`` includes stream specific configuration options. 

.. note::
   The ``cdeps/datm/streams`` section might include multiple streams named as ``stream01``, ``stream02``, ... and each one might provide different information to the parent data component (``datm`` in this example). The ``cdeps`` section could also have multiple data components such as ``datm`` and ``docn``. More information about CDEPS related configuration options can be found in the `CDEPS documentation <https://escomp.github.io/CDEPS/versions/master/html/index.html>`_.

The existing workflow implementation also allows to assign defaults for CDEPS configuration options. The following table includes the list of options and their default values if there is.

.. list-table:: CDEPS related configuration options
   :widths: 10 25 50 50 50
   :header-rows: 1

   * - Section in YAML
     - Name
     - Description
     - Default value
     - Valid values
   * - stream0[1-9]
     - taxmode
     - It specifies how to handle data outside the specified stream time axis
     - limit
     - extend, cycle, limit
   * - stream0[1-9]
     - mapalgo
     - Specifies spatial interpolation algorithm to map stream data on stream mesh to stream data on model mesh
     - redist
     - redist, nn, bilinear, consd, consf
   * - stream0[1-9]
     - tinterpalgo
     - Specifies time interpolation algorithm option
     - linear
     - lower, upper, nearest, linear, coszen
   * - stream0[1-9]
     - readmode
     - Specifies data stream read mode
     - single
     - single, full_file
   * - stream0[1-9]
     - dtlimit
     - Specifies delta time ratio limits placed on the time interpolation associated with the array of streams
     - 1.5
     - The limit might need to be set to a value greater than 1.0 due to the round-off arithmetic
   * - stream0[1-9]
     - stream_offset
     - The offset allows a user to shift the time axis of a data stream by a fixed and constant number of seconds. 
     - 0
     - Any valid number. Note that a positive offset advances the input data time axis forward by that number of seconds
   * - stream0[1-9]
     - stream_vectors
     - Specifies paired vector field names that will be rotated to make them relative to earth coordinates using source mesh coordinates
     - null
     - Value pair like "Sa_u:Sa_v"
   * - stream0[1-9]
     - stream_lev_dimname
     - Specifies name of vertical dimension in stream
     - null
     - Only required for 3d fields

Each stream (like ``stream01``) might include section like ``data`` to specify data specific configuration options. In this example, the data will be retrieved vy using Herbie Python module which could able to access and download different data sets. In the initial implementation of the workflow the ``source`` of the dataset for Herbie can be defined as ``hrrr`` or ``gfs``. The ``length`` is used to define lenght of the data that will be retrieved from the defined source endpoint while ``fxx`` is used to define forecast lead time of the selected data set in hours. More information about Herbie module can be found in its `documentation <https://herbie.readthedocs.io/en/stable/index.html>`_. Since selected dataset might cover bigger area than the actual simulation domain, the workflow provides a way to subset the data spatially to reduce the file sizes. The ``subset`` option can be used for this purpose and workflow trim the dataset based on given SCHISM grid file and combines them to a single file if ``combine`` option is set to true. The ``target_directory`` defined the local folder under run directory to place the forcing files.

.. note::
   HRRR Homepage (ESRL) can be found in `GSL webpage <https://rapidrefresh.noaa.gov/hrrr/>`_.

.. note::
   In addition to the ``herbie`` given as a ``protocol`` entry. The workflow also allow to define ``protocol`` as ``wget`` and ``s3``.

In case of defining ``protocol`` as ``wget`` and ``s3``, the ``data`` section can be defined as following,

.. code-block:: yaml

  data:
    protocol: wget
    end_point: 'https://downloads.psl.noaa.gov'
    files:
      - /Datasets/noaa.oisst.v2.highres/sst.day.mean.1982.nc
      - /Datasets/noaa.oisst.v2.highres/sst.day.mean.1983.nc
    combine: combine
    subset: true
    target_directory: 'INPUT'

.. code-block:: yaml

  data:
    protocol: s3
    end_point: 'noaa-ufs-regtests-pds'
    files:
      - input-data-20221101/FV3_fix_tiled/C96/C96.maximum_snow_albedo.tile1.nc
    target_directory: 'INPUT'

.. note::
   The ``data`` section under strem definition is optional and user might copy the forcing file from another location of the file system rather than accessing through the web. In this case, user need to specify ``model_maskfile``, ``model_meshfile``, ``nx_global`` and ``ny_global`` entries for the data component section such as ``cdeps/datm/update_values/datm_nml`` and ``stream_data_variables``, ``stream_mesh_file`` and ``stream_data_files`` entries under stream specific section. An example workflow configuration can be seen in `coastal_ike_shinnecock_atm2sch.yaml <https://github.com/oceanmodeling/ufs-coastal-app/blob/main/tests/coastal_ike_shinnecock_atm2sch.yaml>` configuration file.

* SCHISM specific definitions

The UFS Coastal application level workflow, provides set of tools to generate namelist and input files for SCHISM model component. The user only needs to provide horizontal (``hgrid.gr3`` and ``hgrid.ll`` files) and vertical grid (``vgrid.in``) files along with the ``hgrid`` and ``vgrid`` configuration entriies under ``schism`` section. The options found under ``boundary``, ``gr3`` and ``bctides`` sections are mainly used to define configuration specific parameters and open boundary conditions. The following example is used to provide required options to generate input files and stage them in the run directory.

.. code-block:: yaml

  schism:
    hgrid: '{{ dir.data }}/hgrid.gr3'
    vgrid: '{{ dir.data }}/vgrid.in'
    boundary:
      vars: [True, True, True]
      ids: [0]
    gr3:
      description: description
      albedo: 2.0e-1
      watertype: 4
      windrot_geo2proj: 0.0
      manning: 2.5e-2
    bctides:
      mode: tidal
      constituents: [ 'Q1','O1','P1','K1','N2','M2','S2','K2','Mm','Mf','M4','MN4','MS4','2N2','S1' ]  
      database: 'tpxo'
      earth_tidal_potential: true
      cutoff_depth: 40
      bc_type: 3
      tpxo_dir: /work/noaa/nosofs/mjisan/pyschism-main/PySCHISM_tutorial/data/TPXO
    namelist:
      template_file: ../templates/param.nml
      template_values:
        dt: 200

In this case, ``bctides`` and ``boundary`` sections are optional and not used for the configurations without open boundaries and tidal forcing. The ``namelist`` options can be updated by providing them with the ``template_values`` entries. 

.. note::
   The entries in `schism/namelist` section are used to customize SCHISM main configuration file (``param.nml``). The parameters that are used to define simulation start date (``start_year``, ``start_month``, ``start_day``, ``start_hour`` and ``utc_start``) is updated automatically by the workflow based on the given cycle date in the command line (e.g. ``--cycle 2024-08-05T12``). The ``rnday`` is also updated by the workflow with the value given in ``stop_n`` under ``nuopc/driver/allcomp/attributes`` or ``nuopc/driver/med/attributes`` sections. The main template file that is use to create model configuration file can be seen under ``templates/param.nml`` directory.

DATM-SCHISM Configuration
-------------------------

In this case, the model configuration includes two model components (CDEPS and SCHISM) and the mediator (CMEPS) to create uni-directional coupled application. The CDEPS Data Atmosphere provides atmospheric forcing (components of the wind speed and also surface pressure) to the SCHISM model but there is no feedback from the ocean to atmsopheric model component.

.. list-table:: Workflow tasks for DATM-SCHISM configuration
   :widths: 10 25 50 50
   :header-rows: 1

   * - #
     - Task
     - Related component
     - Sections in ``coastal.yaml``
   * - 1
     - Download forcing data using ``cdeps_data()``. This step also includes data retrieval through use of ``utils.data.get_input.download()`` function and ESMF mesh generation by ``utils.data.esmf.create_grid_definition()`` functions if it is requested by the user.
     - cdeps, datm
     - input
   * - 2
     - Generate ``model_configure`` using ``_model_configure()``
     - driver
     - driver
   * - 3
     - Generate ``ufs.configure`` using ``ufs_configure()`` 
     - driver
     - driver, med, atm, ocn
   * - 4
     - Generate ``datm_in`` using ``cdeps.atm_nml()``
     - cdeps, datm
     - cdeps/datm/update_values/datm_nml
   * - 5
     - Generate ``datm.streams`` using ``cdeps.atm_stream()``
     - cdeps, datm
     - cdeps/datm/streams/stream01
   * - 6
     - Generate open boundary input files using ``schism_bnd_inputs()``
     - schism
     - schism/boundary
   * - 7
     - Generate ``gr3`` formatted input files using ``schism_gr3_inputs()``
     - schism
     - schism/gr3
   * - 8
     - Generate tidal open boundary conditions using ``schism_tidal_inputs()``
     - schism
     - schism/bctides
   * - 9
     - Generate ``param.nml`` using ``namelist_file()``
     - schism
     - schism/namelist
   * - 10
     - Copy files like ``fd_ufs.yaml`` from UFS Coastal model source using ``linked_files()``
     - UFS Coastal model
     - coastal/links
   * - 11
     - Create required directoryies such as ``RESTART`` under run directory using ``self.restart_dir()``
     - UFS Coastal model
     -
   * - 12
     - Create job submission script using ``runscript()``
     - UFS Coastal model
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

Running UFS Coastal Application Tests
-------------------------------------

To run tests that are placed under ``tests/`` directory,

.. code-block:: console

   cd ufs-coastal-app/ush
   ./run_tests.sh

.. note::
  Since ``coastal_ike_shinnecock_atm2sch.yaml`` test is trying to reproduce the results of UFS Coastal Model level ``coastal_ike_shinnecock_atm2sch`` regression tests and requires forcing and ``bctides.in`` files from the regression test, it request to access prestaged test directory which is defined in ``data`` entry under ``dir`` section. This limitation will be removed once UFS Coastal Application level workflow is able to generate ``bctides.in`` using the same way used in the regression tests and the forcing files will be available throught the UFS Coastal specific AWS S3 bucket.   
