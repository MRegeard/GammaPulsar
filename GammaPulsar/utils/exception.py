__all__ = ["EphemerisKeyNotFound"]


class EphemerisKeyNotFound(Exception):
    """
    Exception raised when a ephemeris file key is not found.

    Parameters
    ----------
    key : str
        Ephemeris key that is not found
    ephemeris_file : str
        Path or reference to the ephemeris file. Default is None
    """

    def __init__(self, key, ephemeris_file=None):
        self.key = key
        if ephemeris_file is None:
            self.message = f"{key} not found in ephemeris file !"
        else:
            self.message = f"{key} not found in ephemeris file {ephemeris_file} !"
        super(EphemerisKeyNotFound, self).__init__(self.key, self.message)
