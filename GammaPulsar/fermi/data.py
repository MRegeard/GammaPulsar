import collections.abc

__all__ = [
    "FermiFiles",
    "FermiEvents",
    "FermiSpacecraft",
    "FermiObservation",
    "FermiObservations",
]


class FermiFiles:
    """
    Fermi files container

    Parameters
    __________
    events_files : list of str
        List of path to events files
    spacecraft_file : str
        Path to spacecraft file
    """

    def __init__(self, events_files, spacecraft_file):
        self._events_files = events_files
        self._spacecraft_file = spacecraft_file

    @property
    def event_files(self):
        """Return the list of events files path"""
        return self._events_files

    @property
    def spacecraft_file(self):
        """Return the path to spacecraft file"""
        return self._spacecraft_file

    def to_fermi_events(self):
        fermi_events_list = []
        for ev in self.event_files:
            fermi_events_list.append()


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
