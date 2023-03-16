import collections.abc
import copy
import re
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.table import Table
from regions import CircleSkyRegion
from gammapy.utils.scripts import make_path

__all__ = [
    "FermiEventList",
    "GTI",
    "FermiSpacecraft",
    "FermiObservation",
    "FermiObservations",
]


class FermiEventList:
    def __init__(self, table, filename=None):

        self.table = table
        self._filename = filename

    @property
    def filename(self):

        return make_path(self._filename)

    @property
    def region(self):

        meta = self.table.meta
        ds3 = [meta["DSTYP3"], meta["DSUNI3"], meta["DSVAL3"]]

        if ds3[0] == "POS(RA,DEC)" and ds3[1] == "deg":

            region_str = re.split(r"[(,)]", ds3[2])
            center = SkyCoord(region_str[1], region_str[2], unit=ds3[1], frame="icrs")
            return CircleSkyRegion(center, radius=float(region_str[3]) * u.deg)
        else:
            raise NotImplementedError

    @property
    def center(self):

        return self.region.center

    @property
    def energy(self):

        meta = self.table.meta
        DS5 = [meta["DSTYP5"], meta["DSUNI5"], meta["DSVAL5"]]
        energy = [float(_) for _ in DS5[2].split(":")]
        return energy * u.Unit(DS5[1])

    @property
    def time(self):
        pass

    def copy(self):

        return copy.deepcopy(self)

    @classmethod
    def read(cls, filename, **kwargs):

        filename = make_path(filename)
        kwargs.setdefault("hdu", "EVENTS")
        table = Table.read(filename, **kwargs)
        return cls(table=table, filename=filename)

    def to_table_hdu(self):

        return fits.BinTableHDU(self.table, name="EVENTS")

    def write(self, filename, gti=None, overwrite=False):

        filename = make_path(filename)

        primary_hdu = fits.PrimaryHDU()
        hdu_evt = self.to_table_hdu()
        hdu_all = fits.HDUList([primary_hdu, hdu_evt])

        if gti is not None:
            if not isinstance(gti, GTI):
                raise TypeError("gti must be an instance of GTI")
            hdu_gti = gti.to_table_hdu()
            hdu_all.append(hdu_gti)

        hdu_all.writeto(filename, overwrite=overwrite)


class GTI:
    def __init__(self, table):
        self.table = table

    def copy(self):
        return copy.deepcopy(self)

    @classmethod
    def read(cls, filename, hdu="GTI"):
        filename = make_path(filename)
        table = Table.read(filename, hdu=hdu)
        return cls(table)

    def to_table_hdu(self):
        return fits.BinTableHDU(self.table, name="GTI")

    def write(self, filename, **kwargs):
        hdu = self.to_table_hdu()
        hdulist = fits.HDUList([fits.PrimaryHDU(), hdu])
        hdulist.writeto(make_path(filename), **kwargs)


class FermiSpacecraft:
    def __init__(self, table, filename=None):
        self.table = table
        self._filename = filename

    @property
    def filename(self):
        return self._filename

    @classmethod
    def read(cls, filename, **kwargs):
        filename = make_path(filename)
        table = Table.read(filename, **kwargs)
        return cls(table, filename=filename)


class FermiObservation:
    def __init__(
        self,
        events=None,
        gti=None,
        spacecraft=None,
    ):
        self._events = events
        self._gti = gti
        self._spacecraft = spacecraft

    @property
    def events(self):
        return self._events

    @property
    def gti(self):
        return self._gti

    @property
    def spacecraft(self):
        return self._spacecraft

    def copy(self):

        return copy.deepcopy(self)

    def write(self):
        pass


class FermiObservations(collections.abc.MutableSequence):
    def __init__(self, observations=None):
        self._observations = observations or []

    def __getitem__(self, key):
        return self._observations[self.index(key)]

    def __delitem__(self, key):
        del self._observations[self.index(key)]

    def __setitem__(self, key, obs):
        if isinstance(obs, FermiObservation):
            self._observations[self.index(key)] = obs
        else:
            raise TypeError(f"Invalid type: {type(obs)!r}")

    def __len__(self):
        return len(self._observations)

    def insert(self, idx, obs):
        if isinstance(obs, FermiObservation):
            self._observations.insert(idx, obs)
        else:
            raise TypeError(f"Invalid type: {type(obs)!r}")

    def index(self, key):
        if isinstance(key, (int, slice)):
            return key
        elif isinstance(key, FermiObservation):
            return self._observations.index(key)
        else:
            raise TypeError(f"Invalid type: {type(key)!r}")

    def filenames_list(self):

        file_list = []
        for obs in self:
            file_list.append(obs.event_filename)
        return file_list

    @classmethod
    def from_files(cls, events_files, spacecraft, gti=True):

        observations = []
        if isinstance(spacecraft, list):
            raise TypeError(
                "a unique spacecraft file is allowed to create FermiObservations"
            )

        spacecraft = FermiSpacecraft.read(spacecraft)
        for file in events_files:
            events = FermiEventList.read(file)
            if gti:
                gti = GTI.read(file)
            else:
                gti = None
            observations.append(
                FermiObservation(events=events, gti=gti, spacecraft=spacecraft)
            )
        return FermiObservations(observations=observations)
