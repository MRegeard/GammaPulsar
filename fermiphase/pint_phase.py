import logging
from pint import toa
from pint import models
from pint.fermi_toas import load_Fermi_TOAs
import numpy as np
import astropy.units as u
from gammapy.data import EventList

log = logging.getLogger(__name__)

__all__ = ["ComputePintPhase", "PintPhaseFermi"]

class ComputePintPhase:

    def __init__(
        self,
        events,
        ephemeris_file,
        error,
        obs,
        event_file = None,
        ephem="DE421",
        include_bipm=True,
        include_gps=True,
        planets=True,
    ):

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

    def run(self, collum_name="PHASE", overwrite=True, meta_entry="PHS_LOG"):

        self.compute_phase()
        self.add_collumn(column_name=collum_name, overwrite=overwrite)
        self.add_meta(meta_entry=meta_entry)

        return EventList(self.events.table)

    def compute_phase(self):

        toa_list = list(toa.TOA(MJD=t, error=self.error*u.microsecond, obs=self.obs) for t in self.times)
        ts = toa.get_TOAs_list(toa_list=toa_list,
                               ephem=self.ephem,
                               include_bipm=self.include_bipm,
                               include_gps=self.include_gps,
                               planets=self.planets)
        phase = self.model.phase(toas=ts, abs_phase=True)[1]
        self.phase = np.where(phase < 0.0, phase + 1.0, phase)


    def add_collumn(self, column_name="PHASE", overwrite=True):

        if overwrite:
            self.events.table[column_name] = self.phase
        else:
            if self._check_column(column_name=column_name, overwrite=overwrite):
                self.events.table[column_name] = self.phase
            else:
                self._check_column(column_name=column_name, overwrite=overwrite)

    def add_meta(self, meta_entry="PHSE_LOG"):

        self.events.table.meta[meta_entry] = phase_log


    def _check_column(self, column_name, overwrite):

        if self.events.table[column_name]:
            log.debug(f"Passing {column_name} with overwrite : {overwrite}. Column name {column_name} already exist."
                      f"Aborting add_column")
            return 0
        else: return 1

class PintPhaseFermi(ComputePintPhase):

    def _check_event_file(self):
        if self.event_file is None:
            raise AttributeError(f"No event_file given to pass to 'load_fermi_TOAs'.")

    def compute_phase(self):
        self._check_event_file()
        toa_list = load_Fermi_TOAs(ft1name=self.event_file)
        ts = toa.get_TOAs_list(toa_list=toa_list,
                               ephem=self.ephem,
                               include_bipm=self.include_bipm,
                               include_gps=self.include_gps,
                               planets=self.planets)
        phase = self.model.phase(toas=ts, abs_phase=True)[1]
        self.phase = np.where(phase < 0.0, phase + 1.0, phase)












