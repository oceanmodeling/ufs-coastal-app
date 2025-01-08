"""
A driver for the Coastal App coupled executable.
"""

import os, sys
import logging
from pathlib import Path
from iotaa import asset, task, tasks
from uwtools.api.driver import DriverCycleBased
from uwtools.api.cdeps import CDEPS
from uwtools.api.schism import SCHISM
from uwtools.api.fs import link
from uwtools.api.logging import use_uwtools_logger
from uwtools.utils.tasks import file
from uwtools.api.template import render

# append paths of custom modules
sys.path.append(os.path.join(os.getcwd(), 'utils/schism'))
sys.path.append(os.path.join(os.getcwd(), 'utils/data'))

# load custom modules
import gen_bnd
import gen_gr3
import gen_bctides
import utils
import get_hrrr
import create_esmf_mesh

# setup logger
use_uwtools_logger()

# global variable to store config for modification
config = {}

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
        # copy config that is provided by the yaml file
        global config
        config = self.config_full
        yield self.taskname("Provisioned run directory")
        self._schism_config()
        self.data_retrieve()
        self.create_mesh()
        cdeps = CDEPS(config=config, cycle=self.cycle, controller=[self.driver_name()])
        schism = SCHISM(config=config, cycle=self.cycle, controller=[self.driver_name()], schema_file="utils/schism/schism.jsonschema")
        yield [
                self._model_configure(),
                self._ufs_configure(),
                cdeps.atm_nml(),
                cdeps.atm_stream(),
                self.schism_bnd_inputs(),
                self.schism_gr3_inputs(),
                self.schism_tidal_inputs(),
                schism.namelist_file(),
                self.linked_files(),
                self.restart_dir(),
                self.runscript(),
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
        schism = self.config_full["schism"]
        yield self.taskname("SCHSIM gr3 input files")
        _files = gen_gr3.execute(schism, output_dir=self.rundir)
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
        # get bounding box from grid
        if cfg['subset']:
            bbox = utils.bounding_rectangle_2d(hgrid)
        else:
            bbox = None
        # retrive files
        yield self.taskname("Prepare input forcing")
        _files = get_hrrr.download(cfg, self.cycle, bbox, combine=True, output_dir=self.rundir)
        yield [asset(path(fn), path(fn).is_file) for fn in _files]
        yield None

    @task
    def create_mesh(self):
        """
        Creates ESMF mesh file
        """
        path = lambda fn: self.rundir / fn
        yield self.taskname("Create ESMF mesh file")
        # create mesh file
        _res = create_esmf_mesh.gen_grid_def(os.path.join(self.rundir, 'combined.nc'), ff='mesh', output_dir=self.rundir)
        # update cdeps config such as name of the mesh file and domain dimensions
        global config
        if 'cdeps' in config.keys():
            if 'atm_in' in config['cdeps'].keys():
                if 'datm_nml' in config['cdeps']['atm_in']['update_values'].keys():
                    config['cdeps']['atm_in']['update_values']['datm_nml']['nx_global'] = _res['shape'][0] 
                    config['cdeps']['atm_in']['update_values']['datm_nml']['ny_global'] = _res['shape'][1]
                    config['cdeps']['atm_in']['update_values']['datm_nml']['model_maskfile'] = _res['output_file']
                    config['cdeps']['atm_in']['update_values']['datm_nml']['model_meshfile'] = _res['output_file']
            if 'atm_streams' in config['cdeps'].keys():
                # TODO: we could have multiple streams that might use different dataset
                if 'stream01' in config['cdeps']['atm_streams']['streams'].keys():
                    config['cdeps']['atm_streams']['streams']['stream01']['stream_mesh_file'] = _res['output_file']
        yield [asset(path(fn), path(fn).is_file) for fn in _res['output_file']]
        yield None

    @task
    def _schism_config(self):
        yield self.taskname("Update SCHISM configuration")
        if 'schism' in config.keys():
            if 'namelist' in config['schism'].keys():
                if 'template_values' in config['schism']['namelist'].keys():
                    config['schism']['namelist']['template_values']['start_year'] = self.cycle.year
                    config['schism']['namelist']['template_values']['start_month'] = self.cycle.month
                    config['schism']['namelist']['template_values']['start_day'] = self.cycle.day
                    config['schism']['namelist']['template_values']['start_hour'] = self.cycle.hour
                    config['schism']['namelist']['template_values']['utc_start'] = 0
        yield None        
        yield None

    @task
    def _model_configure(self):
        fn = "model_configure"
        yield self.taskname(f"main configuration file {fn}")
        path = self.rundir / fn
        yield asset(path, path.is_file)
        template_file = '../templates/model_configure'
        yield file(path=Path(template_file))
        # TODO: nhours_fcst is fixed to 24 to find better solution
        render(
            input_file=template_file,
            output_file=path,
            overrides={'start_year' : self.cycle.year,
                       'start_month': self.cycle.month,
                       'start_day'  : self.cycle.day,
                       'start_hour' : self.cycle.hour,
                       'nhours_fcst': 24,
                       },
            )

    @task
    def _ufs_configure(self):
        fn = "ufs.configure"
        yield self.taskname(f"main driver configuration file {fn}")
        path = self.rundir / fn
        yield asset(path, path.is_file)
        template_file = '../templates/ufs.configure'
        yield file(path=Path(template_file))
        # Populate dictionary to process template
        _dict = {}
        _dict['driver'] = config['driver']
        comps = config['driver']['componentList']
        for comp in comps:
            _dict[comp.lower()] = config[comp.lower()]
        render(
            input_file=template_file,
            output_file=path,
            overrides={'config': _dict},
            )

    def driver_name(self):
        return "coastal"
