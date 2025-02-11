import os
import sys
import logging
from datetime import timedelta
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

from utils.data.esmf import create_grid_definition 
from utils.data.get_input import download
from utils.data.shared import get_time_range 
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
    def cdeps_data(self):
        """
        CDEPS forcing data.
        """
        config_fd = {}
        config = self.config_full
        # List of arguments that need to be checked for consistency
        arg_list = [
            "nx_global",
            "ny_global",
            "model_maskfile",
            "model_meshfile"
        ]
        # Loop over each cdeps sub-component
        for comp in config["cdeps"].keys():
            if comp == "template_file":
                continue
            # Check if streams section exists (atm_streams, ocn_streams, etc.)
            if "streams" in config["cdeps"][comp].keys():
                for key, val in config["cdeps"][comp]["streams"].items():
                    # Check data section for stream to retrive
                    if "data" in val.keys():
                        if not comp in config_fd.keys():
                            config_fd[comp] = {}
                        config_fd[comp][key] = val
                        # Check for combine option 
                        combine = False
                        if "herbie" in val["data"]["protocol"]:
                            logging.info("Data protocol is set to 'herbie' for {}/{}. Set combine as True".format(comp, key))
                            combine = True
                        else:
                            if "combine" in val["data"].keys():
                                combine = val["data"]["combine"]
                        # Check for target directory
                        target_dir = "INPUT"
                        if "target_directory" in val["data"].keys():
                            target_dir = val["data"]["target_directory"]
                        if not os.path.abspath(target_dir) or not os.path.isdir(target_dir):
                            target_dir = os.path.join(self.rundir, target_dir)
                        config_fd[comp][key]["data"]["target_directory"] = target_dir
                        # Check for stream data files
                        if not "stream_data_files" in val.keys() and combine:
                            fn = "combined_{}_stream{}.nc".format(comp, key[6:9])
                            config_fd[comp][key]["stream_data_files"] = [ os.path.join(target_dir, fn) ]
                        else:
                            config_fd[comp][key]["stream_data_files"] = []
                            for fn in val["data"]["files"]:
                                config_fd[comp][key]["stream_data_files"].append(os.path.join(target_dir, os.path.basename(fn)))
                        # Check for mesh file
                        if not "stream_mesh_file" in val.keys():
                            fn = "mesh_{}_stream{}.nc".format(comp, key[6:9])
                            config_fd[comp][key]["stream_mesh_file"] = os.path.join(target_dir, fn)
        # Create run directory if it is not done before
        self.rundir.mkdir(parents=True, exist_ok=True)
        # Get bounding box to subset data if it is requested
        bbox = self._bounding_box()
        # Retrieve data for each stream and component if it is requested
        files = []
        with open(self.rundir / "cdeps.log", "w", encoding="utf-8") as f:
            with redirect_stdout(f):
                for comp in config_fd.keys():
                    for key, cfg in config_fd[comp].items():
                        logging.info("%s Downloading forcing data for %s and %s", self.taskname(""), comp, key)
                        # Check subset option
                        subset = False
                        if "subset" in config_fd[comp][key]["data"].keys():
                            subset = config_fd[comp][key]["data"]["subset"]
                        # Retrieve data for stream
                        output_file = config_fd[comp][key]["stream_data_files"][0]
                        if subset:
                            download(cfg, self.cycle, bbox=bbox)
                        else:
                            download(cfg, self.cycle, bbox=None)
                        files.append(Path(output_file))
                        # Create ESMF mesh
                        input_file = output_file
                        output_file = config_fd[comp][key]["stream_mesh_file"]
                        out = create_grid_definition(input_file, output_file=output_file, ff='mesh', output_dir=self.rundir)
                        files.append(Path(output_file))
                        # Update configuration
                        if not "nx_global" in config["cdeps"][comp]["update_values"]["{}_nml".format(comp)].keys():
                            config["cdeps"][comp]["update_values"]["{}_nml".format(comp)].update(
                                {
                                    "nx_global": out['shape'][0],
                                    "ny_global": out['shape'][1],
                                    "model_maskfile": out['output_file'],
                                    "model_meshfile": out['output_file']
                                }
                            )
        # Additional check for cdeps data component 
        for comp in config["cdeps"].keys():
            if comp == "template_file":
                continue
            if "{}_nml".format(comp) in config["cdeps"][comp]["update_values"].keys():
                force_to_exit = False
                for item in arg_list:
                    if not item in config["cdeps"][comp]["update_values"]["{}_nml".format(comp)].keys():
                        logging.error("Missing {} in {}/update_values/{}_nml section!".format(item, comp, comp))
                        force_to_exit = True
                if force_to_exit:
                    sys.exit(1)
        # Find out year align, first and last to update cdeps stream configurations
        for comp in config["cdeps"].keys():
            if comp == "template_file":
                continue
            for key, cfg in config["cdeps"][comp]["streams"].items():
                date_first, date_last = get_time_range(cfg["stream_data_files"], self.rundir)
                year_first = date_first.year
                year_last = date_last.year
                # Update configuration
                config["cdeps"][comp]["streams"][key].update(
                    {
                        "yearAlign": year_first,
                        "yearFirst": year_first,
                        "yearLast" : year_last
                    }
                )
        # Create file that has modified CDEPS configuration
        path_cdeps_config = self.rundir / "cdeps.yaml"
        YAMLConfig(config).dump(path_cdeps_config)
        # Task related definitions
        yield self.taskname("CDEPS forcing data")
        yield {
            "cdeps-config": asset(path_cdeps_config, path_cdeps_config.is_file),
            "cdeps-files": [asset(fn, fn.is_file) for fn in files],
        }
        yield None

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
    def _model_configure(self, run_duration):
        """
        The model_configure file.
        """
        fn = "model_configure"
        yield self.taskname(f"Main configuration file {fn}")
        path = self.rundir / fn
        yield asset(path, path.is_file)
        template_file = "../templates/model_configure"
        yield file(path=Path(template_file))
        render(
            input_file=template_file,
            output_file=path,
            overrides={
                "start_year": self.cycle.year,
                "start_month": self.cycle.month,
                "start_day": self.cycle.day,
                "start_hour": self.cycle.hour,
                "nhours_fcst": run_duration,
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
        d = {"driver": config["nuopc"]["driver"]}
        for component in config["nuopc"]["driver"]["componentList"]:
            d[component.lower()] = config["nuopc"][component.lower()]
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
        yield self.taskname("SCHSIM boundary input files")
        if "boundary" in self.config_full["schism"].keys():
            hgrid = self.config_full["schism"]["hgrid"]
            vgrid = self.config_full["schism"]["vgrid"]
            ocean_bnd_ids = self.config_full["schism"]["boundary"]["ids"]
            bnd_vars = self.config_full["schism"]["boundary"]["vars"]
            _files = gen_bnd.execute(hgrid, vgrid, self.cycle, 1, ocean_bnd_ids=ocean_bnd_ids, output_dir=self.rundir, output_vars=bnd_vars)
            yield [asset(path(fn), path(fn).is_file) for fn in _files]
        else:
            yield None
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
        if "bctides" in self.config_full["schism"].keys():
            _files = gen_bctides.execute(schism, self.cycle, 1, output_dir=self.rundir)
            yield [asset(path(fn), path(fn).is_file) for fn in _files]
        else:
            yield None
        yield None

    @tasks
    def provisioned_rundir(self):
        """
        The run directory provisioned with all required content.
        """
        yield self.taskname("Provisioned run directory")
        run_duration = self._run_duration()
        self.linked_files()
        cdeps_cfg = self.cdeps_data()
        cdeps = CDEPS(
            config=refs(cdeps_cfg["cdeps-config"]),
            controller=[self.driver_name()],
            cycle=self.cycle,
            schema_file="utils/cdeps/cdeps.jsonschema",
        )
        schism_cfg = self._schism_update_config(run_duration) 
        schism = SCHISM(
            config=refs(schism_cfg)["schism-config"],
            controller=[self.driver_name()],
            cycle=self.cycle,
            schema_file="utils/schism/schism.jsonschema",
        )
        yield [
            cdeps.atm_nml(),
            cdeps.atm_stream(),
            self.schism_bnd_inputs(),
            self.schism_gr3_inputs(),
            self.schism_tidal_inputs(),
            schism.namelist_file(),
            self._model_configure(run_duration),
            self.ufs_configure(),
            self.restart_dir(),
            self.runscript(),
        ]

    @task
    def _schism_update_config(self, run_duration):
        """
        The SCHISM namelist file.
        """
        path_schism_config = self.rundir / "schism.yaml"
        yield self.taskname("SCHISM configuration")
        yield {
            "schism-config": asset(path_schism_config, path_schism_config.is_file)
        }
        yield None
        config = self.config_full
        config["schism"]["namelist"]["template_values"].update(
            {
                "start_year": self.cycle.year,
                "start_month": self.cycle.month,
                "start_day": self.cycle.day,
                "start_hour": self.cycle.hour,
                "utc_start": 0, 
                "rnday": run_duration / 24.0
            }
        )
        YAMLConfig(config).dump(path_schism_config)

    # Private helper methods

    def _bounding_box(self):
        """
        Returns bounding box based on used component and its mesh
        Return value: [minlon, minlat, maxlon, maxlat]
        """
        bbox = None
        if "schism" in self.config_full:
            hgrid = self.config_full["schism"]["hgrid"]
            bbox = bounding_rectangle_2d(hgrid)
        return bbox

    def _run_duration(self):
        """
        Returns run duration for the simulation.
        """
        config = self.config_full
        run_duration = 6 
        # Find out run duration
        if "nuopc" in config.keys():
            if "driver" in config["nuopc"].keys():
                if "allcomp" in config["nuopc"]["driver"].keys():
                    if "attributes" in config["nuopc"]["driver"]["allcomp"].keys():
                         unit = config["nuopc"]["driver"]["allcomp"]["attributes"]["stop_option"]
                         if unit == 'nhours':
                             run_duration = config["nuopc"]["driver"]["allcomp"]["attributes"]["stop_n"]
                         elif unit == 'ndays':
                             run_duration = config["nuopc"]["driver"]["allcomp"]["attributes"]["stop_n"]*24
                         else:
                             logging.error("stop_option option can only be nhours or ndays!")
                             sys.exit(1)
                elif "med" in config["nuopc"]["driver"].keys():
                    if "attributes" in config["nuopc"]["driver"]["med"].keys():
                         unit = config["nuopc"]["driver"]["med"]["attributes"]["stop_option"]
                         if unit == 'nhours':
                             run_duration = config["nuopc"]["driver"]["med"]["attributes"]["stop_n"]
                         elif unit == 'ndays':
                             run_duration = config["nuopc"]["driver"]["med"]["attributes"]["stop_n"]*24
                         else:
                             logging.error("stop_option option can only be nhours or ndays!")
                             sys.exit(1)
                else:
                    logging.info("no way to determine run duration.")
        return run_duration
