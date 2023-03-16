import os
from pathlib import Path
import numpy as np
import astropy.units as u
from loguru import logger as log
from pint import models, toa
from pint.fermi_toas import load_Fermi_TOAs
from pint.observatory.satellite_obs import get_satellite_observatory
from GammaPulsar.data import FermiObservation
from gammapy.data import EventList

__all__ = ["PhaseMaker", "FermiPhaseMaker"]


class PhaseMaker:
    def __init__(
        self,
        events=None,
        ephemeris_file=None,
        error=None,
        obs=None,
        event_file=None,
        ephem="DE421",
        include_bipm=True,
        include_gps=True,
        planets=True,
    ):

        if events is None and event_file is None:
            raise Exception(
                f"Cannot initiate {self.__name__} with both events and event_file set to None."
            )
        if ephemeris_file is None:
            raise Exception(
                f"Cannot initiate {self.__name__} with ephemeris_file set to None"
            )
        self.events = events
        self.event_file = event_file
        if events is None and event_file is not None:
            self.events = EventList.read(filename=event_file)
        self.ephemeris_file = ephemeris_file
        self.phase = None
        self.error = error
        self.obs = obs
        self.model = models.get_model(ephemeris_file)
        self.times = events.times
        self.ephem = ephem
        self.include_bipm = include_bipm
        self.include_gps = include_gps
        self.planets = planets

    def run(self, column_name="PHASE", overwrite=True, meta_entry="PHS_LOG"):

        self.compute_phase()
        self.add_column(column_name=column_name, overwrite=overwrite)
        self.add_meta(meta_entry=meta_entry)

        return EventList(self.events.table)

    def compute_phase(self):

        toa_list = list(
            toa.TOA(MJD=t, error=self.error * u.microsecond, obs=self.obs)
            for t in self.times
        )
        ts = toa.get_TOAs_list(
            toa_list=toa_list,
            ephem=self.ephem,
            include_bipm=self.include_bipm,
            include_gps=self.include_gps,
            planets=self.planets,
        )
        phase = self.model.phase(toas=ts, abs_phase=True)[1]
        self.phase = np.where(phase < 0.0, phase + 1.0, phase)

    def add_column(self, column_name="PHASE", overwrite=True):

        if overwrite:
            self.events.table[column_name] = self.phase
        else:
            if self._check_column(column_name=column_name, overwrite=overwrite):
                self.events.table[column_name] = self.phase
            else:
                self._check_column(column_name=column_name, overwrite=overwrite)

    def add_meta(self, meta_entry="PHSE_LOG"):
        pass

    def _check_column(self, column_name, overwrite):

        if self.events.table[column_name]:
            log.debug(
                f"Passing {column_name} with overwrite : {overwrite}. Column name {column_name} already exist. Aborting add_column"
            )
            return 0
        else:
            return 1


class FermiPhaseMaker:
    def __init__(
        self,
        observation=None,
        ephemeris_file=None,
        weightcolumn=None,
        ephem="DE421",
        include_bipm=False,
        include_gps=False,
        planets=False,
    ):
        if not isinstance(observation, FermiObservation):
            raise TypeError("observation must be instance of FermiObservation")
        self.observation = observation.copy()
        self.model = models.get_model(ephemeris_file)
        self.ephem = ephem
        self.include_bipm = include_bipm
        self.include_gps = include_gps
        self.planets = planets
        self.weightcolumn = weightcolumn
        self.phase = None

    def compute_phase(self):

        get_satellite_observatory(
            "Fermi", self.observation.spacecraft.filename, overwrite=True
        )

        toa_list = load_Fermi_TOAs(
            ft1name=self.observation.events.filename,
            weightcolumn=self.weightcolumn,
            targetcoord=self.observation.events.center,
        )
        ts = toa.get_TOAs_list(
            toa_list=toa_list,
            ephem=self.ephem,
            include_bipm=self.include_bipm,
            include_gps=self.include_gps,
            planets=self.planets,
        )
        phase = self.model.phase(toas=ts, abs_phase=True)[1]
        self.phase = np.where(phase < 0.0, phase + 1.0, phase)

    def add_column(self, column_name="PHASE", overwrite=True):

        if overwrite:
            self.observation.events.table[column_name] = self.phase.astype("float64")
        else:
            if self._check_column(column_name=column_name, overwrite=overwrite):
                self.observation.events.table[column_name] = self.phase.astype(
                    "float64"
                )
            else:
                self._check_column(column_name=column_name, overwrite=overwrite)

    def add_meta(self, meta_entry="PHSE_LOG"):
        pass

    def run(self, column_name="PHASE", overwrite=True, meta_entry="PHS_LOG"):

        self.compute_phase()
        self.add_column(column_name=column_name, overwrite=overwrite)
        self.add_meta(meta_entry=meta_entry)

        return self.observation

    def _check_column(self, column_name, overwrite):

        if self.observation.events.table[column_name]:
            log.debug(
                f"Passing {column_name} with overwrite : {overwrite}. Column name {column_name} already exist."
                f"Aborting add_column"
            )
            return 0
        else:
            return 1


class FermiBinnedConfigMaker:
    def __init__(self, fermi_config, axis_name, map_axis):

        self.fermi_config = fermi_config
        self.axis_name = axis_name
        self.map_axis = map_axis

    @staticmethod
    def _make_base_path(self, base_dir=None):

        if base_dir is None:
            base_path = Path("./")
        else:
            if isinstance(base_dir, str):
                base_path = Path(base_dir)
            else:
                base_path = base_dir
        return base_path

    @staticmethod
    def _make_dir_name(name, value_min, value_max):

        if not isinstance(name, str):
            name = str(name)
        if not isinstance(value_min, str):
            value_min = str(value_min)
        if not isinstance(value_max, str):
            value_max = str(value_max)

        return Path(name + "_" + value_min + "-" + value_max)

    @staticmethod
    def _make_config_name(value_min, value_max, name="config"):

        if not isinstance(name, str):
            name = str(name)
        if not isinstance(value_min, str):
            value_min = str(value_min)
        if not isinstance(value_max, str):
            value_max = str(value_max)

        return Path(name + "_" + value_min + "-" + value_max + ".yaml")

    def run(self, base_dir=None):

        base_path = self._make_base_path(base_dir=base_dir)

        for edge_min, edge_max in zip(
            self.map_axis.edges_min.value, self.map_axis.edges_max.value
        ):

            dir_name = self._make_dir_name(
                name=self.axis_name, value_min=edge_min, value_max=edge_max
            )
            out_dir = Path(os.path.join(base_path, dir_name))
            out_dir.mkdir(parents=True, exist_ok=True)

            self.fermi_config.add_entry(
                primary_dict="selection", entry="phasemin", value=float(edge_min)
            )
            self.fermi_config.add_entry(
                primary_dict="selection", entry="phasemax", value=float(edge_max)
            )

            outfile = self._make_config_name(
                value_min=edge_min, value_max=edge_max, name=self.axis_name
            )
            full_path = Path(os.path.join(out_dir, outfile))
            self.fermi_config.write(full_path)
