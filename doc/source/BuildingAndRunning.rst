.. _BuildingAndRunning:

************************************
Building and Running the UFS Coastal
************************************

=================================
Supported Platforms and Compilers
=================================

Since the UFS Coastal is developed as a fork of the UFS Weather Model, the same platforms supported by the UFS Weather Model (`see list of suported platforms <https://ufs-weather-model.readthedocs.io/en/latest/CodeOverview.html#supported-platforms-and-compilers-for-running-the-ufs-weather-model>`_) is also used by the UFS Coastal. 

The prerequisite software libraries for building the UFS Coastal already exist in a centralized location on Level 1/pre configured systems, so users may skip dependency installation steps. On other systems, users will need to build the prerequisite libraries using `spack-stack <https://github.com/JCSDA/spack-stack>`_. The extensive documentation about installing dependencies through the spack-stack can be found in `here <https://spack-stack.readthedocs.io/en/latest/>`_.

=====================
Unsupported Platforms
=====================

For a complete walkthrough of Containerized EPIC Spack-Stack 1.6.0 for UFS Coastal on local and unsupported clusters (e.g., TACC Stampede3), see :ref:`Running UFS Coastal on HPCs with Spack-Stack <container_hpc_section>` for full instructions.


========
Get Data
========

The ROMS input files for pre-configured cases can be downloaded from the `ROMS Test <https://github.com/myroms/roms_test/tree/main/IRENE>`_ GitHub repository.

.. todo::
   Need to place UFS Coastal specific data to cloud or common place along with some level of versioning.

=================================
Downloading the UFS Coastal Model
=================================

To clone the main branch of the ``ufs-weather-model`` repository that includes UFS Coastal specific model component and update its submodules, execute the following commands:

.. code-block:: console

   git clone --recursive https://github.com/oceanmodeling/ufs-weather-model
   cd ufs-weather-model

Compiling the model will take place within the ``ufs-weather-model`` directory created by this command.

========================
Building the UFS Coastal
========================

----------------------------
Loading the Required Modules
----------------------------

The process for loading modules is fairly straightforward on Level 1 `supported platforms <https://ufs-weather-model.readthedocs.io/en/latest/BuildingAndRunning.html#supported-platforms-compilers>`_. Users may need to make adjustments when running on other systems.

On NOAA Level 1 & 2 Systems
---------------------------

Modulefiles for preconfigured platforms are located in ``modulefiles/ufs_<platform>.<compiler>``. For example, to load the modules from the ``ufs-weather-model`` directory on MSU's Hercules:

.. code-block:: console

   cd ufs-weather-model
   module use modulefiles
   module load ufs_hercules.intel

On Other Systems
----------------

If you are not running on one of the pre-configured platforms, you will need to install dependencies using spack-stack. The more detailed information about usage of spack-stack and dependency installation can be found in :ref:`porting section <PortingModel>`.

------------------------------------------------
Setting the ``CMAKE_FLAGS`` Environment Variable
------------------------------------------------

The UFS Coastal can be built in one of several configurations (see :numref:`Table %s <UFS-Coastal-configurations>` for common options). Also note that these configurations are specific to UFS Coastal and the wide range of supported configurations through the UFS Weather Model can be found in UFS Weather Model documentation `Configurations section <https://ufs-weather-model.readthedocs.io/en/latest/Configurations.html>`_.

DATM+OCN Configurations
-----------------------

**ADCIRC**

.. code-block:: console

   export CMAKE_FLAGS="-DAPP=CSTLA -DADCIRC_CONFIG=PADCIRC -DCOUPLED=ON"

.. note::
   The ``-DBUILD_ADCPREP`` option can be also provided to build ADCIRC pre-processing tools like ``adcprep`` command that allows the creation of input files. 
   The ``-DBUILD_UTILITIES`` option can be also provided to build ADCIRC specific utility tools.

**FVCOM**

.. code-block:: console

   export CMAKE_FLAGS="-DAPP=CSTLF -DCOORDINATE_TYPE=SPHERICAL -DWET_DRY=ON"

.. note::
   The ``-DAIR_PRESSURE`` option can also be provided to use surface air pressure as addtional forcing.

**ROMS**

.. code-block:: console

   export CMAKE_FLAGS="-DAPP=CSTLR -DMY_CPP_FLAGS=BULK_FLUXES"

.. note::
   The ROMS ocean model builds the ``IRANE`` application by default. ``-DROMS_APP`` and ``ROMS_APP_DIR`` can be provided to build custom configurations. Mode information about the ``IRANE`` configuration (CDEPS data atmosphere coupled with ROMS) can be found in `ROMS Test repository <https://github.com/myroms/roms_test/tree/main/IRENE/Coupling/roms_data_cmeps>`_.

**SCHISM**

.. code-block:: console

   export CMAKE_FLAGS="-DAPP=CSTLS -DUSE_ATMOS=ON -DNO_PARMETIS=OFF -DOLDIO=ON"

.. note::
   The ``-DBUILD_UTILS=ON`` option can be also provided to build SCHISM specific pre- and post-processing tools.
   The ``-DUSE_WW3=ON``  option can be also provided to couple with WW3 wave model.

DATM+WAV Configurations
-----------------------

**WW3**

.. code-block:: console

   export CMAKE_FLAGS="-DAPP=CSTLW -DPDLIB=ON"

.. note::
   The same options can be used both for standalone WW3 configuration (``standalone = true`` option needs to be provided in ``WAV_attributes`` section of ``ufs.configuration`` namelist file) and also the one coupled with CDEPS data atmosphere.


DATM+OCN+WAV Configurations
---------------------------

**SCHISM**

.. code-block:: console

   export CMAKE_FLAGS="-DAPP=CSTLSW -DUSE_ATMOS=ON -DUSE_WW3=ON -DNO_PARMETIS=OFF -DOLDIO=ON -DPDLIB=ON"

.. note::
   The ``-DBUILD_UTILS=ON`` option can be also provided to build SCHISM specific pre- and post-processing tools.

------------------
Building the Model
------------------

The UFS Weather Model uses the CMake build system. There is a build script called ``build.sh`` in the top-level directory of the UFS Coastal repository that configures the build environment and runs the ``make`` command. This script also checks that all necessary environment variables have been set.

The UFS Coastal can be built by running the following command from the ``ufs-weather-model`` directory once ``CMAKE_FLAGS`` is set:

.. code-block:: console

   ./build.sh

Once ``build.sh`` is finished, users should see the executable, named ``ufs_model``, in the ``ufs-weather-model/build/`` directory. If users prefer to build in a different directory, specify the ``BUILD_DIR`` environment variable. For example: ``export BUILD_DIR=test_cpld`` will build in the ``ufs-weather-model/test_cpld`` directory instead.

Expert help is available through `GitHub Discussions <https://github.com/oceanmodeling/ufs-weather-model/discussions/categories/q-a>`_. Users may post questions there for help with difficulties related to the UFS Coastal.

=================
Running the Model
=================

----------------------------
User Provided Configurations
----------------------------

Since the UFS Coastal does not have workflow capability in the application layer (`UFS Coastal Application <https://github.com/oceanmodeling/ufs-coastal-app>`_) yet, users need to populate namelist and input files manually. At this point, the best practice is to run UFS Coastal with a custom configuration/application is to run the similar configuration using UFS Coastal Regression Testing (RT) framework  and populate the run directory. Then, the run directory can be used as a base to build custom configuration by replacing model and component specific configuration and input files. The more information about running UFS Coastal specific RTs can be found in the following section.

--------------------------------------------------------------
Pre-configured Configurations Using the Regression Test Script
--------------------------------------------------------------

Users can run a number of preconfigured UFS Coastal specific regression test cases from the ``rt_coastal.conf`` file (``rt.conf`` includes RTs supported by UFS Weather Model) using the regression test script ``rt.sh`` in the ``tests`` directory. ``rt.sh`` is the top-level script that calls lower-level scripts to build specified UFS Coastal and UFS Weather Model configurations, set up environments, and run tests. This section aims to give brief information about running specific model configurations under UFS Coastal through the use of Regression Testing (RT) framework.

.. _rt_coastal.conf:

The ``rt_coastal.conf`` File
----------------------------

Each line in the PSV (Pipe-separated values) file, ``rt_coastal.conf``, contains information to build and run the specific model configuration. The file includes two lines for each model configuration starting as ``COMPILE`` and ``RUN``. The similar configurations could have a single ``COMPILE`` line but multiple ``RUN`` lines. In this case, a single compile step can be used to run multiple similar configurations. 

**COMPILE**

.. list-table:: Description of Compile Section of ``rt_coastal.conf``
   :widths: 10 70
   :header-rows: 1

   * - Column
     - Description
   * - 1
     - ``COMPILE``, It specifies the following information is to be used in setting up a compile job
   * - 2
     - It specifies the compile number. This is used as a reference for compile failures
   * - 3
     - Relates to the compiler to use in build (intel or gnu)
   * - 4
     - It specifies ``CMAKE`` options for the build. This is very similar to setting ``CMAKE_FLAGS`` to build model executable outside of the RT framework
   * - 5
     - Machines to run on (``-`` is used to ignore specified machines, ``+`` is used to only run on specified machines)
   * - 6
     - Relates to the control of the compile job only if FV3 was present, previously used to run a test w/o compiling code. It can be set to ``fv3`` in all the cases.

**RUN**

.. list-table:: Description of Run Section of ``rt_coastal.conf``
   :widths: 10 70
   :header-rows: 1

   * - Column
     - Description
   * - 1
     - ``RUN``, It specifies following information is to be used in setting up a model run
   * - 2
     - Test name. The test in the tests/tests directory should be sourced
   * - 3
     - Machines to run on (- is used to ignore specified machines, + is used to only run on specified machines)
   * - 4
     - Controls whether the run creates its own baseline or it uses the baseline from a different (control) test
   * - 5
     - Test name to compare baselines with if not itself

The order of lines in ``rt_coastal.conf`` matters since ``rt.sh`` processes them sequentially; a ``RUN`` line should be preceded by a ``COMPILE`` line that builds the model used in the test. The following
``rt_coastal.conf`` file builds the ROMS ocean model coupled with CDEPS data atmosphere: 

.. code-block:: console

   COMPILE | 16 | intel | -DAPP=CSTLR -DMY_CPP_FLAGS=BULK_FLUXES | | fv3 |
   RUN | coastal_irene_atm2roms | | baseline |

The ``rt_coastal.conf`` file includes a large number of tests. If the user wants to run only specific tests, ``-n`` argument can be used. The ``-l rt_coastal.conf`` option can be used to run only UFS Coastal specific RTs. The ``rt.sh`` uses the ``rt.conf`` file by default.

.. _rt.sh:

The ``rt.sh`` File
------------------

This section contains additional information on command line options and troubleshooting for the ``rt.sh`` file. 

To display detailed information on how to use ``rt.sh``, users can simply run ``./rt.sh``, which will output the following options: 

.. code-block:: console

   Usage: ./rt.sh -a <account> | -b <file> | -c | -d | -e | -h | -k | -l <file> | -m | -n <name> | -o | -r | -v | -w
   
     -a  <account> to use on for HPC queue
     -b  create new baselines only for tests listed in <file>
     -c  create new baseline results
     -d  delete run directories that are not used by other tests
     -e  use ecFlow workflow manager
     -h  display this help
     -k  keep run directory after rt.sh is completed
     -l  runs test specified in <file>
     -m  compare against new baseline results
     -n  run single test <name>
     -o  compile only, skip tests
     -r  use Rocoto workflow manager
     -v  verbose output
     -w  for weekly_test, skip comparing baseline results

When running a large number (10's or 100's) of tests, the ``-e`` or ``-r`` options can significantly decrease testing time by using a workflow manager (ecFlow or Rocoto, respectively) to queue the jobs 
according to dependencies and run them concurrently.

.. note::
   Workflow Engine `ecFlow <https://confluence.ecmwf.int/display/ECFLOW>`_ is used with ``-e`` argument and `Rocoto <https://github.com/christopherwharrop/rocoto>`_ is used with ``-r`` argument. The Workflow Engine needs to be installed to the system to use these options. The Tier-1 platforms might have those workflow engines but Tear-2 level supported systems and custom installations might not have them.

.. note::
   Since the UFS Coastal specific input files are not part of the UFS Weather Model input files, the location of the RT directory (defined by ``DISKNM`` variable) in ``rt.sh`` needs to be modified to run UFS Coastal specific RTs. To do that user needs to edit platform (i.e. Orion, Hercules) specific section of ``rt.sh`` and set ``DISKNM`` variable. For both ``Orion`` and ``Hercules`` platforms, ``/work2/noaa/nems/tufuk/RT`` directory is used to set ``DISKNM`` variable. 

To run ``rt.sh`` using a custom configuration file and the Rocoto workflow manager:

.. code-block:: console

   ./rt.sh -r -l rt_coastal.conf

To run a single test from custom configuration file:

.. code-block:: console

   Running with Intel compiler:
   ./rt.sh -l rt_coastal.conf -k -n "coastal_irene_atm2roms intel"

   Running with GNU compiler:
   ./rt.sh -l rt_coastal.conf -k -n "coastal_irene_atm2roms gnu"

.. note::
   ``-k`` argument is used to keep the run directory for further reference.

.. note::
   ``-a`` argument can be used to specify account to job scheduler

The up-to-date list of supported and tested (the RTs that is indicated as bold) RTs can be seen in `UFS Coastal specific UFS WM fork repository Wiki page <https://github.com/oceanmodeling/ufs-weather-model/wiki/Current-Status-of-UFS%E2%80%90Coastal-Implementation>`_.



.. _container_hpc_section:

Running UFS Coastal on HPCs with the Containerized EPIC Spack-Stack 1.6.0 Environment
=====================================================================================


This guide provides step-by-step instructions to compile and run the UFS Coastal Application on unsupported platforms (e.g., local machines, new HPC systems) using the EPIC Spack-Stack containerized environment (v1.6.0). It involves launching a container (via Apptainer or Singularity), building the UFS model, externalizing the executable, and running test cases outside the container.

Two workflow options are provided:

- **Option 1:** Build and run from inside the container.
- **Option 2:** Extract modulefiles and build/run externally.

Example commands are shown for Stampede3 (TACC), but they can be adapted to other systems.

Prerequisites
-------------

- Apptainer or Singularity installed
- HPC account with interactive compute access (`idev`, `srun`, etc.)
- Familiarity with Git and environment module systems

Download the Container Image
----------------------------

.. code-block:: bash

   wget https://epic-noaa.s3.us-east-1.amazonaws.com/ubuntu22.04-intel-ufs-env-v1.6.0.img
   export img=/path/to/ubuntu22.04-intel-ufs-env-v1.6.0.img

Start an Interactive HPC Session (Stampede3 Example)
----------------------------------------------------

.. code-block:: bash

   idev -m 120
   ml tacc-apptainer/1.3.3

Check Loaded Modules (Example Output)
-------------------------------------

.. code-block:: bash

   ml list
   # cmake/3.31.5, python/3.9.18, intel/24.0, netcdf/4.9.2, metis/5.1.0.3, tacc-apptainer/1.3.3, ...

Option 1: Build and Run Inside the Container
--------------------------------------------

1. **Enter the container**

   .. code-block:: bash

      singularity shell -e -s /bin/bash $img
      # Optional
      Apptainer> source /usr/lmod/lmod/init/bash

2. **Load UFS modules**

   .. code-block:: bash

      Apptainer> module use /opt/spack-stack/spack-stack-1.6.0/envs/unified-env/install/modulefiles/Core
      Apptainer> module load stack-intel 
      Apptainer> module load stack-intel-oneapi-mpi
      Apptainer> module load ufs-weather-model-env
      Apptainer> module list

3. **Clone and build UFS Coastal**

   .. code-block:: bash

      Apptainer> git clone --recursive https://github.com/oceanmodeling/ufs-weather-model
      Apptainer> cd ufs-weather-model
      Apptainer> mkdir build && cd build
      Apptainer> cmake -DAPP=CSTLS -DPDLIB=ON -DUSE_ATMOS=ON -DNO_PARMETIS=OFF -DOLDIO=ON -DUSE_WW3=OFF ..
      Apptainer> make -j 8

4. **Externalize the executable**

   .. code-block:: bash

      Apptainer> /opt/container-scripts/externalize.sh -e $PWD/extern $PWD/ufs_model
      # Result: build/extern/ufs_model (wrapper executable)

5. **Exit container and run externally**

   .. code-block:: bash

      Apptainer> exit
      cd /path/to/test-case
      ibrun -n 10 ../ufs-weather-model/build/extern/ufs_model
      # or use srun/mpirun

Option 2: Externalize Modulefiles and Build Outside the Container
------------------------------------------------------------------

1. **Create a modulefiles directory**

   .. code-block:: bash

      mkdir modulefiles
      cd modulefiles

2. **Extract modulefiles from the container**

   .. code-block:: bash

      singularity exec $img cp /opt/container-scripts/convert-modules.py .
      python3 ./convert-modules.py -i $img -o $PWD/spack-stack-1.6.0

3. **Load externalized modules**

   .. code-block:: bash

      module use /path/to/modulefiles/spack-stack-1.6.0/Core
      module load stack-intel
      module load stack-intel-oneapi-mpi
      module load ufs-weather-model-env sp crtm
      module list

4. **Build UFS Coastal externally**

   .. code-block:: bash

      git clone --recursive https://github.com/oceanmodeling/ufs-weather-model
      cd ufs-weather-model
      mkdir build_external && cd build_external
      cmake -DAPP=CSTLS -DPDLIB=ON -DUSE_ATMOS=ON -DNO_PARMETIS=OFF -DOLDIO=ON -DUSE_WW3=OFF ..
      make -j 8

5. **Create executable wrapper**

   .. code-block:: bash

      make-external ./ufs_model
      # Generates ufs_model (wrapper) and ufs_model.orig (original binary)

6. **Run test case externally**

   .. code-block:: bash

      cd /path/to/test-case
      ibrun -n 10 ../ufs-weather-model/build_external/ufs_model

Summary
-------

- **Option 1** builds inside the container and externalizes only the executable.
- **Option 2** extracts environment modules and builds entirely outside the container.
- Both approaches allow unsupported systems to run the UFS Coastal Application using the EPIC Spack-Stack container.

Notes
-----

- Adjust `ibrun -n` or `srun` based on your platform and test case.
- Replace `/path/to/test-case` with your actual directory.
- This setup is portable to other clusters using Apptainer/Singularity (e.g., university or institutional HPCs).

Acknowledgments
---------------

This workflow builds upon techniques shared during a NOAA workshop led by Mark Potts. It was adapted and extended to support UFS Coastal compilation and execution on Stampede3.

