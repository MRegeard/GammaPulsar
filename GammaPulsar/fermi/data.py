import collections.abc
import logging as log

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
    event_file : str
        Path to the event file
    """

    def __init__(self, event_file):
        self._event_file = event_file

    @property
    def event_file(self):
        """Path to the event file"""
        return self._event_file


class FermiSpacecraft:
    """
    Class for Fermi-LAT spacecraft file

    Parameters
    ----------
    spacecraft_file : str
        Path to the spacecraft file
    """

    def __init__(self, spacecraft_file):
        self._spacecraft_file = spacecraft_file

    @property
    def spacecraft_file(self):
        """Path to the spacecraft file"""
        return self._spacecraft_file


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
