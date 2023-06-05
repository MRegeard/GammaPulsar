import logging as log
import os
import numpy as np
from astropy.io import fits
from astropy.time import Time
import pint
from gammapy.utils.scripts import make_path
from pint import models, toa
from pint.fermi_toas import load_Fermi_TOAs
from pint.observatory.satellite_obs import get_satellite_observatory
from GammaPulsar.fermi import FermiObservation
from GammaPulsar.utils import EphemerisKeyNotFound

__all__ = ["FermiPhaseMaker"]


class FermiPhaseMaker:
    """
    Class that compute of the pulsar phase of Fermi-LAT data.

    Once the pulsar phase is computed, it can be written in the original Fermi-LAT events file or in a copy
    of the original Fermi-lAT phase in a new column named "PULSE_PHASE" by default.

    Parameters
    ----------
    observation : `GammaPulsar.fermi.FermiObservation`
        The Fermi-LAT observation (events file and spacecraft file) to use.
    ephemeris_file : str
        Path to the ephemeris file to use for the pulsar phase computation
    ephem : str
        The name of the solar system ephemeris to use; defaults to "DE421".
    include_bipm : bool or None
        Whether to apply the BIPM clock correction. Defaults to False.
    include_gps : bool or None
        Whether to include the GPS clock correction. Defaults to False.
    planets : boor or None
        Whether to apply Shapiro delays based on planet positions.
    weightcolumn : str
        Specifies the FITS column name to read the photon weights from.
        The special value 'CALC' causes the weights to be computed
        empirically as in Philippe Bruel's SearchPulsation code.
    targetcoord : astropy.coordinates.SkyCoord
        Source coordinate for weight computation if weightcolumn=='CALC'
    """

    def __init__(
        self,
        observation,
        ephemeris_file,
        ephem="DE421",
        include_bipm=False,
        include_gps=False,
        planets=False,
        weightcolumn=None,
        targetcoord=None,
    ):

        if not isinstance(observation, FermiObservation):
            raise TypeError("observation must be instance of FermiObservation")
        ephemeris_file_path = make_path(ephemeris_file)
        if os.path.isfile(ephemeris_file_path):
            self.ephemeris_file = ephemeris_file_path
        else:
            raise FileNotFoundError(f"{ephemeris_file} is not a path to a file.")
        self.observation = observation
        self.model = models.get_model(ephemeris_file_path)
        self.ephem = ephem
        self.include_bipm = include_bipm
        self.include_gps = include_gps
        self.planets = planets
        self.phases = None
        self.weightcolumn = weightcolumn
        self.targetcoord = targetcoord

    def compute_phase(self, **kwargs):
        """
        Compute the pulsar phase.

        Parameters
        ----------
        **kwargs : dict
            Keyword arguments to pass to `pint.fermi_toas.load_Fermi_TOAs` .
        """

        get_satellite_observatory(
            "Fermi", self.observation.fermi_spacecraft.filename, overwrite=True
        )

        toa_list = load_Fermi_TOAs(
            ft1name=self.observation.fermi_events.filename,
            weightcolumn=self.weightcolumn,
            targetcoord=self.targetcoord,
            **kwargs,
        )

        ts = toa.get_TOAs_list(
            toa_list=toa_list,
            ephem=self.ephem,
            include_bipm=self.include_bipm,
            include_gps=self.include_gps,
            planets=self.planets,
        )

        phases = self.model.phase(toas=ts, abs_phase=True)[1]
        self.phases = np.where(phases < 0.0, phases + 1.0, phases)

    def write_column_and_meta(
        self, filename=None, column_name="PULSE_PHASE", overwrite=True
    ):
        """
        Write the pulsar phase as a new column in the original Fermi-LAT events file or in a copy of it.
        Write some metadata related to the phase computation in the header of the original Fermi-LAT events
        file or in a copy of it.

        Parameters
        ----------
        filename : str or None
            The path to the filename to write the column phase to. Default is None.
            If it is set to None, the column will be written in the original fermi-LAT events file.
        column_name : str
            The name of the column created to write the pulsar phase. Default is PULSE_PHASE, to match the
            standard of Fermi-LAT analysis.
        overwrite : bool
            Whether to overwrite the column if a column with the same name already exist in the file.
        """
        if filename is None:
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

        if filename is None:
            hdulist.flush(verbose=True, output_verify="warn")
        else:
            hdulist.writeto(
                filename, overwrite=True, checksum=True, output_verify="warn"
            )

    @staticmethod
    def _make_meta(ephemeris_file, model, column_name="PULSE_PHASE", offset=None):
        """
        Make the metadata string to put in the header of the Fermi-LAT events file.

        Parameters
        ----------
        ephemeris_file : str
            Path to the ephemeris file that was used for the pulsar phase computation.
        model : `pint.models.TimingModel`
            The PINT model for the epheremis file.
        column_name : str
            The name of the column on which the pulsar phase has been written. Default is PULSE_PHASE.
        offset : float or None
            The offset that was applied to the pulsar phase. Default is None.
        Returns
        -------
        str(meta_dict) : str
            The string of the dictionary that is build from the different metadata gather for the pulsar phase
            computation?
        """

        key_model = [
            "PSR",
            "START",
            "FINISH",
            "TZRMJD",
            "TZRSITE",
            "TZRFREQ",
            "EPHEM",
            "RAJ",
            "DECJ",
        ]

        meta_dict = dict()
        meta_dict["COLUMN_NAME"] = column_name
        meta_dict["EPHEMERIS_FILE"] = ephemeris_file
        meta_dict["PINT_VERS"] = pint.__version__

        for key in key_model:
            try:
                meta_dict[key] = getattr(model, key).value
            except AttributeError:
                print(
                    EphemerisKeyNotFound(key=key, ephemeris_file=ephemeris_file).message
                )
                meta_dict[key] = None

        meta_dict["PHASE_OFFSET"] = offset
        meta_dict["DATA"] = Time.now().mjd

        return str(meta_dict)

    @staticmethod
    def _check_column_name(event_hdu, column_name, overwrite):
        """
        Check the if a column name named as the `column_name` parameter exist in the `event_hdu` , and whether
        it is compatible with the overwrite parameter.

        Parameters
        ----------
        event_hdu : `astropy.io.fits.hdu.table.BinTableHDU`
            The FITS table to check for.
        column_name : str
            The name of the column to check.
        overwrite : bool
            Whether the column can be overwritten or not.

        Returns
        -------
        check : bool
            Whether the check passed.
        """
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
