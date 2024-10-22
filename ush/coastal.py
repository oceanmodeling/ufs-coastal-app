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
sys.path.append(os.path.join(os.getcwd(), 'utils/schism'))
sys.path.append(os.path.join(os.getcwd(), 'utils/data'))

# load custom modules
import gen_bnd
import gen_gr3
import gen_bctides
import utils
import get_hrrr

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
        schism = SCHISM(config=self.config_full, cycle=self.cycle, controller=[self.driver_name()], schema_file="utils/schism/schism.jsonschema")
        yield self.taskname("Provisioned run directory")
        yield [
                self.data_retrieve(),
                #cdeps.atm_nml(),
                #cdeps.atm_stream(),
                #self.schism_bnd_inputs(),
                #self.schism_gr3_inputs(),
                #self.schism_tidal_inputs(),
                #schism.namelist_file(),
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
        Generate boundary files
        """
        path = lambda fn: self.rundir / fn
        hgrid = self.config_full["schism"]["hgrid"]
        vgrid = self.config_full["schism"]["vgrid"]
        ocean_bnd_ids = self.config_full["schism"]["ocean_bnd_ids"]
        bnd_vars = self.config_full["schism"]["boundary_vars"]
        yield self.taskname("SCHSIM boundary input files")
        _files = gen_bnd.execute(hgrid, vgrid, self.cycle, 1, ocean_bnd_ids=ocean_bnd_ids, output_dir=self.rundir, output_vars=bnd_vars)
        yield [asset(path(fn), path(fn).is_file) for fn in _files]
        yield None

    @task
    def schism_gr3_inputs(self):
        """
        Generate gr3 input files
        """
        path = lambda fn: self.rundir / fn
        hgrid = self.config_full["schism"]["hgrid"]
        yield self.taskname("SCHSIM gr3 input files")
        _files = gen_gr3.execute(hgrid, "description", output_dir=self.rundir)
        yield [asset(path(fn), path(fn).is_file) for fn in _files]
        yield None

    @task
    def schism_tidal_inputs(self):
        """
        Generate tidal boundary condition input files
        """
        path = lambda fn: self.rundir / fn
        schism = self.config_full["schism"]
        yield self.taskname("SCHSIM tidal input files")
        _files = gen_bctides.execute(schism, self.cycle, 1, output_dir=self.rundir) 
        yield [asset(path(fn), path(fn).is_file) for fn in _files]
        yield None

    @task
    def data_retrieve(self):
        """
        Download and process forcing data
        """
        path = lambda fn: self.rundir / fn
        cfg = self.config_full["input"]
        hgrid = self.config_full["schism"]["hgrid"]
        bbox = utils.bounding_rectangle_2d(hgrid)
        yield self.taskname("Prepare input forcing")
        if cfg['forcing'].lower() == 'hrrr':
            _files = get_hrrr.download(cfg, self.cycle, bbox, output_dir=self.rundir)
        yield [asset(path(fn), path(fn).is_file) for fn in _files]
        yield None

    def driver_name(self):
        return "coastal"