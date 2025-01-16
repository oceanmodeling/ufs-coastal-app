"""
A driver for the Coastal App coupled executable.
"""

import logging
import sys
from contextlib import redirect_stdout
from pathlib import Path

from iotaa import asset, refs, task, tasks
from uwtools.api.cdeps import CDEPS
from uwtools.api.config import YAMLConfig
from uwtools.api.driver import DriverCycleBased
from uwtools.api.fs import link
from uwtools.api.logging import use_uwtools_logger
from uwtools.api.schism import SCHISM
from uwtools.api.template import render
from uwtools.utils.tasks import file

sys.path.append(str(Path(__file__).parent))

# pylint: disable=wrong-import-position

from utils.data.create_esmf_mesh import gen_grid_def
from utils.data.get_hrrr import download
from utils.schism import gen_bctides, gen_bnd, gen_gr3
from utils.schism.utils import bounding_rectangle_2d

use_uwtools_logger()

class Coastal(DriverCycleBased):
    """
    A driver for the Coastal App coupled executable.
    """

    @classmethod
    def driver_name(cls):
        return "coastal"

    @task
    def forcing_data(self):
        """
        Forcing data.
        """
        path = self.rundir / "combined.nc"
        yield self.taskname("Forcing data")
        yield asset(path, path.is_file)
        yield None
        config_fd = self.config["forcing_data"]
        hgrid = self.config_full["schism"]["hgrid"]
        bbox = bounding_rectangle_2d(hgrid) if config_fd["subset"] else None
        logging.debug("%s Using bounding box: %s", self.taskname(""), bbox)
        self.rundir.mkdir(parents=True, exist_ok=True)
        with open(self.rundir / "combined.log", "w", encoding="utf-8") as f:
            with redirect_stdout(f):
                logging.info("%s Downloading forcing data", self.taskname(""))
                download(config_fd, self.cycle, bbox, combine=True, output_dir=self.rundir)

    @task
    def linked_files(self):
        """
        Data files linked into the run directory.
        """
        path = lambda fn: self.rundir / fn
        links = self.config["links"]
        yield self.taskname("Linked files")
        yield [asset(path(fn), path(fn).is_file) for fn in links]
        yield None
        link(config=links, target_dir=self.rundir)

    @task
    def mesh_file(self):
        """
        The ESMF mesh file.
        """
        path_cdeps_config = self.rundir / "cdeps.yaml"
        path_mesh_file = self.rundir / "mesh.nc"
        yield self.taskname("ESMF mesh file")
        yield {
            "cdeps-config": asset(path_cdeps_config, path_cdeps_config.is_file),
            "mesh-file": asset(path_mesh_file, path_mesh_file.is_file),
        }
        forcing_data = self.forcing_data()
        yield forcing_data
        self.rundir.mkdir(parents=True, exist_ok=True)
        res = gen_grid_def(refs(forcing_data), ff="mesh", output_dir=self.rundir)
        outfile = res["output_file"]
        config = self.config_full
        config["cdeps"]["atm_in"]["update_values"]["datm_nml"].update(
            {
                "nx_global": res["shape"][0],
                "ny_global": res["shape"][1],
                "model_maskfile": outfile,
                "model_meshfile": outfile,
            }
        )
        # NB: We could have multiple streams that might use different dataset.
        config["cdeps"]["atm_streams"]["streams"]["stream01"]["stream_mesh_file"] = outfile
        YAMLConfig(config).dump(path_cdeps_config)

    @task
    def model_configure(self):
        """
        The model_configure file.
        """
        fn = "model_configure"
        yield self.taskname(f"Main configuration file {fn}")
        path = self.rundir / fn
        yield asset(path, path.is_file)
        template_file = "../templates/model_configure"
        yield file(path=Path(template_file))
        # NB: Set simulation lenght based on input until to find better solution
        nhours_fcst = 24
        if 'forcing_data' in self.config.keys():
            if 'length' in self.config['forcing_data'].keys():
                nhours_fcst = self.config['forcing_data']['length']
        render(
            input_file=template_file,
            output_file=path,
            overrides={
                "start_year": self.cycle.year,
                "start_month": self.cycle.month,
                "start_day": self.cycle.day,
                "start_hour": self.cycle.hour,
                "nhours_fcst": nhours_fcst,
            },
        )

    @task
    def ufs_configure(self):
        """
        The ufs.configure file.
        """
        fn = "ufs.configure"
        yield self.taskname(f"Main driver configuration file {fn}")
        path = self.rundir / fn
        yield asset(path, path.is_file)
        template_file = "../templates/ufs.configure"
        yield file(path=Path(template_file))
        config = self.config_full
        d = {"driver": config["driver"]}
        for component in config["driver"]["componentList"]:
            d[component.lower()] = config[component.lower()]
        render(input_file=template_file, output_file=path, overrides={"config": d})

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

    @tasks
    def provisioned_rundir(self):
        """
        The run directory provisioned with all required content.
        """
        yield self.taskname("Provisioned run directory")
        mesh_file = self.mesh_file()
        cdeps = CDEPS(
            config=refs(mesh_file)["cdeps-config"],
            controller=[self.driver_name()],
            cycle=self.cycle,
        )
        schism_cfg = self.schism_update_config() 
        schism = SCHISM(
            config=refs(schism_cfg)["schism-config"],
            controller=[self.driver_name()],
            cycle=self.cycle,
            schema_file="utils/schism/schism.jsonschema",
        )
        yield [
            self.schism_bnd_inputs(),
            self.schism_gr3_inputs(),
            self.schism_tidal_inputs(),
            cdeps.atm_nml(),
            cdeps.atm_stream(),
            schism.namelist_file(),
            self.linked_files(),
            self.model_configure(),
            self.restart_dir(),
            self.runscript(),
            self.ufs_configure(),
        ]

    @task
    def schism_update_config(self):
        """
        The SCHISM namelist file.
        """
        path_schism_config = self.rundir / "schism.yaml"
        yield self.taskname("SCHISM configuration")
        yield {
            "schism-config": asset(path_schism_config, path_schism_config.is_file)
        }
        config = self.config_full
        config["schism"]["namelist"]["template_values"].update(
            {
                "start_year": self.cycle.year,
                "start_month": self.cycle.month,
                "start_day": self.cycle.day,
                "start_hour": self.cycle.hour,
                "utc_start": 0
            }
        )
        YAMLConfig(config).dump(path_schism_config)
