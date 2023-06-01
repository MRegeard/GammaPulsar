import logging as log
import numpy as np
from astropy.io import fits
from astropy.time import Time
import pint
from pint import models, toa
from pint.fermi_toas import load_Fermi_TOAs
from pint.observatory.satellite_obs import get_satellite_observatory
from GammaPulsar.fermi import FermiObservation
from GammaPulsar.utils import EphemerisKeyNotFound

__all__ = ["FermiPhaseMaker"]


class FermiPhaseMaker:
    """ """

    def __init__(
        self,
        observation,
        ephemeris_file,
        ephem="DE421",
        include_bipm=False,
        include_gps=False,
        planets=False,
    ):

        if not isinstance(observation, FermiObservation):
            raise TypeError("observation must be instance of FermiObservation")
        self.ephemeris_file = ephemeris_file
        self.observation = observation
        self.model = models.get_model(ephemeris_file)
        self.ephem = ephem
        self.include_bipm = include_bipm
        self.include_gps = include_gps
        self.planets = planets
        self.phases = None

    def compute_phase(self, **kwargs):

        get_satellite_observatory(
            "Fermi", self.observation.fermi_spacecraft, overwrite=True
        )

        toa_list = load_Fermi_TOAs(ft1name=self.observation.fermi_events, **kwargs)

        ts = toa.get_TOAs_list(
            toa_list=toa_list,
            ephem=self.ephem,
            include_bipm=self.include_bipm,
            include_gps=self.include_gps,
            planets=self.planets,
        )

        phases = self.model.phase(toas=ts, abs_phase=True)[1]
        self.phases = np.where(phases < 0.0, phases + 1.0, phases)

    def open_file(self, mode):
        hdulist = fits.open(self.observation.fermi_events.filename)
        return hdulist

    def write_column_and_meta(
        self, filename, column_name="PULSE_PHASE", overwrite=True
    ):

        if filename == self.observation.fermi_events.filename:
            hdulist = fits.open(self.observation.fermi_events.filename, mode="update")
        else:
            hdulist = fits.open(self.observation.fermi_events.filename)

        event_hdu = hdulist[1]
        event_header = event_hdu.header
        event_data = event_hdu

        if self._check_column_name(
            event_hdu=event_hdu, column_name=column_name, overwrite=overwrite
        ):
            event_data[column_name] = self.phases

        phasecol = fits.ColDefs(
            [fits.Column(name=column_name, format="D", array=self.phases)]
        )
        event_header["PHSE_LOG"] = self._make_meta(
            self.ephemeris_file, self.model, column_name=column_name
        )
        bin_table = fits.BinTableHDU.from_columns(
            event_hdu.columns + phasecol, header=event_header, name=event_hdu.name
        )

        hdulist[1] = bin_table

        if filename == self.observation.fermi_events.filename:
            hdulist.flush(verbose=True, output_verify="warn")
        else:
            hdulist.writeto(
                filename, overwrite=True, checksum=True, output_verify="warn"
            )

    @staticmethod
    def _make_meta(ephemeris_file, model, column_name="PULSE_PHASE", offset=None):
        meta_dict = dict
        meta_dict["COLUMN_NAME"] = column_name
        meta_dict["EPHEMERIS_FILE"] = ephemeris_file
        meta_dict["PINT_VERS"] = pint.__version__
        try:
            meta_dict["PSRJ"] = model.PSR.value
        except EphemerisKeyNotFound(key="PSR", ephemeris_file=ephemeris_file):
            pass
        try:
            meta_dict["START"] = model.START.value
        except EphemerisKeyNotFound(key="START", ephemeris_file=ephemeris_file):
            pass
        try:
            meta_dict["FINISH"] = model.FINISH.value
        except EphemerisKeyNotFound(key="FINISH", ephemeris_file=ephemeris_file):
            pass
        try:
            meta_dict["TZRMJD"] = model.TZRMJD.value
        except EphemerisKeyNotFound(key="TZRMJD", ephemeris_file=ephemeris_file):
            pass
        try:
            meta_dict["TZRSITE"] = model.TZRSITE.value
        except EphemerisKeyNotFound(key="TZRSITE", ephemeris_file=ephemeris_file):
            pass
        try:
            meta_dict["TZRFREQ"] = model.TZRFREQ.value
        except EphemerisKeyNotFound(key="TZRFREQ", ephemeris_file=ephemeris_file):
            pass
        try:
            meta_dict["EPHEM"] = model.EPHEM.value
        except EphemerisKeyNotFound(key="EPHEM", ephemeris_file=ephemeris_file):
            pass
        try:
            meta_dict["EPHEM_RA"] = model.RAJ.value
        except EphemerisKeyNotFound(key="RAJ", ephemeris_file=ephemeris_file):
            pass
        try:
            meta_dict["EPHEM_DEC"] = model.DECJ.value
        except EphemerisKeyNotFound(key="DECJ", ephemeris_file=ephemeris_file):
            pass
        meta_dict["PHASE_OFFSET"] = offset
        meta_dict["DATA"] = Time.now().mjd

        return str(meta_dict)

    @staticmethod
    def _check_column_name(event_hdu, column_name, overwrite):
        if column_name not in event_hdu.columns.names:
            log.info(f"Writing {column_name} to events file")
            return True
        if column_name in event_hdu.columns.names and overwrite is True:
            log.info(
                f"Column named {column_name} found in events file, overwriting it !"
            )
            return True
        if column_name in event_hdu.columns.names and overwrite is False:
            log.info(
                f"Column named {column_name} found in events file, overwrite is set to {overwrite} ! Cannot overwrite it"
            )
            return False
