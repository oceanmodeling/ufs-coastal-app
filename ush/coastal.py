"""
A driver for the Coastal App coupled executable.
"""

import os, sys
import logging
from iotaa import asset, task, tasks
from uwtools.api.cdeps import CDEPS
from uwtools.api.driver import DriverCycleBased
from uwtools.api.fs import link
from uwtools.api.logging import use_uwtools_logger
from uwtools.api.schism import SCHISM

# append paths of custom modules
sys.path.append(os.path.join(os.getcwd(), 'schism'))

# load custom modules
import gen_bnd

# setup logger
use_uwtools_logger()

class Coastal(DriverCycleBased):
    """
    A driver for the Coastal App coupled executable.
    """

    @task
    def linked_files(self):
        """
        Data files linked into the run directory.
        """
        links = self.config["links"]
        path = lambda fn: self.rundir / fn
        yield self.taskname("Linked files")
        yield [asset(path(fn), path(fn).is_file) for fn in links.keys()]
        yield None
        link(config=links, target_dir=self.rundir)

    @tasks
    def provisioned_rundir(self):
        """
        The run directory provisioned with all required content.
        """
        cdeps = CDEPS(config=self.config_full, cycle=self.cycle, controller=[self.driver_name()])
        schism = SCHISM(config=self.config_full, cycle=self.cycle, controller=[self.driver_name()], schema_file="schism/schism.jsonschema")
        yield self.taskname("Provisioned run directory")
        yield [
                cdeps.atm_nml(),
                cdeps.atm_stream(),
                self.schism_bnd_inputs(),
                schism.namelist_file(),
                #self.linked_files(),
                #self.restart_dir(),
                #self.runscript(),
                ]

    @task
    def restart_dir(self):
        """
        RESTART directory in run directory.
        """
        path = self.rundir / "RESTART"
        yield self.taskname("RESTART directory")
        yield asset(path, path.is_dir)
        yield None
        path.mkdir(parents=True)

    @task
    def schism_bnd_inputs(self):
        """
        Generate data files for SCHSIM
        """
        path = lambda fn: self.rundir / fn
        hgrid = self.config_full["schism"]["hgrid"]
        vgrid = self.config_full["schism"]["vgrid"]
        bnd_vars = self.config_full["schism"]["boundary_vars"]
        #bnd_vars = {'elev2D': e, 'TS': True, 'UV': True}
        #active_bnd_vars = [key for key,val in bnd_vars.items() if val]
        #_files = []
        #for bnd_var in active_bnd_vars:
        #    if bnd_var == 'elev2D':
        #        _files.append('elev2D.th.nc')
        #    elif bnd_var == 'TS':
        #        _files.append('SAL_3D.th.nc')
        #        _files.append('TEM_3D.th.nc')
        #    elif bnd_var == 'UV':
        #        _files.append('uv3D.th.nc')
        yield self.taskname("SCHSIM input files")
        gen_bnd.execute(hgrid, vgrid, self.cycle, 1, ocean_bnd_ids=[0], output_dir=self.rundir)
        yield [asset(path(fn), path(fn).is_file) for fn in _files]
        yield None




    def driver_name(self):
        return "coastal"
