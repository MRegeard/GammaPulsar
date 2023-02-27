import logging
from pint import toa
from pint import models
from pint.fermi_toas import load_Fermi_TOAs
import numpy as np
import astropy.units as u
from astropy.io import fits
from gammapy.data import EventList
from GammaPulsar.data import FermiObservation

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
            raise Exception(f"Cannot initiate {self.__name__} with both events and event_file set to None.")
        if ephemeris_file is None:
            raise Exception(f"Cannot initiate {self.__name__} with ephemeris_file set to None")
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

        toa_list = list(toa.TOA(MJD=t, error=self.error * u.microsecond, obs=self.obs) for t in self.times)
        ts = toa.get_TOAs_list(toa_list=toa_list,
                               ephem=self.ephem,
                               include_bipm=self.include_bipm,
                               include_gps=self.include_gps,
                               planets=self.planets)
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
                f"Passing {column_name} with overwrite : {overwrite}. Column name {column_name} already exist."
                f"Aborting add_column")
            return 0
        else:
            return 1

class FermiPhaseMaker:

    def __init__(
        self,
        observation=None,
        ephemeris_file=None,
        ephem="DE421",
        include_bipm=True,
        include_gps=True,
        planets=True,
    ):
        if not isinstance(observation, FermiObservation):
            raise TypeError(f"observation must be instance of FermiObservation")
        self.observation = observation.copy()
        self.model = models.get_model(ephemeris_file)
        self.ephem = ephem
        self.include_bipm = include_bipm
        self.include_gps = include_gps
        self.planets = planets


    def compute_phase(self):
        toa_list = load_Fermi_TOAs(ft1name=self.observation.events.filename)
        ts = toa.get_TOAs_list(toa_list=toa_list,
                               ephem=self.ephem,
                               include_bipm=self.include_bipm,
                               include_gps=self.include_gps,
                               planets=self.planets)
        phase = self.model.phase(toas=ts, abs_phase=True)[1]
        self.phase = np.where(phase < 0.0, phase + 1.0, phase)

    def add_column(self, column_name="PHASE", overwrite=True):

        if overwrite:
            self.observation.events.table[column_name] = self.phase.astype('float64')
        else:
            if self._check_column(column_name=column_name, overwrite=overwrite):
                self.observation.events.table[column_name] = self.phase.astype('float64')
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
                f"Aborting add_column")
            return 0
        else:
            return 1


