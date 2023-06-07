import collections.abc
import logging as log
import os
from astropy.io import fits
from astropy.table import Table
from gammapy.utils.scripts import make_path

__all__ = [
    "FermiEvents",
    "FermiSpacecraft",
    "FermiObservation",
    "FermiObservations",
]


class FermiEvents:
    """
    Class for Fermi-LAT event file

    Parameters
    ----------
    filename : str
        Path to the event file
    """

    def __init__(self, filename):
        filename_path = make_path(filename)
        if os.path.isfile(filename_path):
            self._filename = filename_path
        else:
            raise FileNotFoundError(f"{filename} is not a path to a file.")
        self._table = None
        self._primary_hdu = None

    @property
    def filename(self):
        """Path to the event file"""
        return self._filename

    @property
    def table(self):
        """Load events table"""
        if self._table is None:
            self._table = self._load_file(self.filename, hdu_type="events")
        return self._table

    @property
    def primary_hdu(self):
        """Load PrimaryHDU"""
        if self._primary_hdu is None:
            self._primary_hdu = self._load_file(self.filename, hdu_type="primary")
        return self._primary_hdu

    @staticmethod
    def _load_file(filename, hdu_type="events", **kwargs):
        """
        Static method that load events and primary hdu from a fits file

        Parameters
        ----------
        filename : str
            Path to the fits file
        hdu_type : str
            HDU to open. Either "events" or "primary"
        **kwargs : dict
            Keyword arguments to pass to either events hdu or primary hdu depending on `hdu_type`

        Returns
        -------
        table or primary_hdu : `astropy.table.Table` or `astropy.io.fits.PrimaryHDU`
            Events table or PrimaryHDU depending on `hdu_type` .
        """
        kwargs.setdefault("hdu", "EVENTS")
        if hdu_type == "events":
            return Table.read(filename, **kwargs)
        if hdu_type == "primary":
            return fits.PrimaryHDU.readfrom(filename, **kwargs)


class FermiSpacecraft:
    """
    Class for Fermi-LAT spacecraft file

    Parameters
    ----------
    filename : str
        Path to the spacecraft file
    """

    def __init__(self, filename):
        filename_path = make_path(filename)
        if os.path.isfile(filename_path):
            self._filename = filename_path
        else:
            raise FileNotFoundError(f"{filename} is not a path to a file.")

    @property
    def filename(self):
        """Path to the spacecraft file"""
        return self._filename


class FermiObservation:
    """
    Class that bundle together a Fermi-LAT event file and a spacecraft file

    Parameters
    ----------
    fermi_events : `~GammaPulsar.fermi.FermiEvents`
        Event file
    fermi_spacecraft : `~GammaPulsar.fermi.FermiSpacecraft`
        Spacecraft file
    """

    def __init__(self, fermi_events, fermi_spacecraft):
        if not isinstance(fermi_events, FermiEvents):
            raise TypeError(
                f"parameter fermi_events must be an instance of {FermiEvents.__name__}, given {type(fermi_events)}"
            )
        if not isinstance(fermi_spacecraft, FermiSpacecraft):
            raise TypeError(
                f"parameter fermi_spacecraft must be an instance of {FermiSpacecraft.__name__}, given {type(fermi_spacecraft)}"
            )
        self._fermi_events = fermi_events
        self._fermi_spacecraft = fermi_spacecraft

    @property
    def fermi_events(self):
        """Return `FermiEvents` object"""
        return self._fermi_events

    @property
    def fermi_spacecraft(self):
        """Return `FermiSpacecraft`object"""
        return self._fermi_spacecraft


class FermiObservations(collections.abc.MutableSequence):
    """
    Class container for `~GammaPulsar.fermi.FermiObservation`

    Parameters
    ----------
    observations : `~GammaPulsar.fermi.FermiObservation`
        Fermi-LAT observation
    """

    def __init__(self, observations=None):
        self._observations = observations or []

    def insert(self, idx, obs):
        if isinstance(obs, FermiObservation):
            self._observations.insert(idx, obs)
        else:
            raise TypeError(f"Invalid type: {type(obs)!r}")

    def __getitem__(self, key):
        return self._observations[self.index(key)]

    def __setitem__(self, key, obs):
        if isinstance(obs, FermiObservation):
            self._observations[self.index(key)] = obs
        else:
            raise TypeError(f"Invalid type: {type(obs)!r}")

    def __delitem__(self, key):
        del self._observations[self.index(key)]

    def __len__(self):
        return len(self._observations)

    def index(self, key):
        if isinstance(key, (int, slice)):
            return key
        elif isinstance(key, FermiObservation):
            return self._observations.index(key)
        else:
            raise TypeError(f"Invalid type: {type(key)!r}")

    @classmethod
    def from_files(cls, events_files, spacecrafts_files):
        """Create a FermiObservations object from a list of events files and spacecraft files

        Parameters
        ----------
        events_files : list of str
            List of path to events files
        spacecrafts_files : str or list of str
            Path or list of path to spacecrafts files. If a list is given it must either be of length one
            or of the same length as events_files. If the length of the list is one (or if spacecraft is a string),
            the same spacecraft file will be applied to each events file. If the length of the list matches the
            length of events_files, each spacecraft file in the list will be associated with the corresponding
            events file in events_files
        """

        observations = []
        if isinstance(spacecrafts_files, str):
            spacecrafts_files = [spacecrafts_files]
        if isinstance(events_files, str):
            events_files = [events_files]

        if len(events_files) == len(spacecrafts_files):
            pass
        elif len(spacecrafts_files) == 1:
            spacecrafts_files = spacecrafts_files * len(events_files)
            log.info(
                f"Using {spacecrafts_files} of every events files in {events_files}"
            )
        else:
            raise ValueError(
                "spacecraft_files must be either a list of the same length as events_file or of length one"
            )

        for ev_file, sp_file in zip(events_files, spacecrafts_files):
            events = FermiEvents(ev_file)
            spacecraft = FermiSpacecraft(sp_file)
            observations.append(
                FermiObservation(fermi_events=events, fermi_spacecraft=spacecraft)
            )

        return FermiObservations(observations=observations)
