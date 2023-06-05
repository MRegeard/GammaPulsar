import os
from pathlib import Path
import pytest
from astropy.io import fits
from astropy.table import Table
from gammapy.utils.scripts import make_path
from GammaPulsar.fermi import (
    FermiEvents,
    FermiObservation,
    FermiObservations,
    FermiSpacecraft,
)


def test_read_not_file():
    with pytest.raises(FileNotFoundError):
        FermiEvents(filename="$GAMMAPULSAR_DATA/fermi")


class TestFermiEvents:
    def setup_class(self):
        self.events = FermiEvents(
            filename="$GAMMAPULSAR_DATA/fermi/vela_2days/vela_2days_events.fits"
        )

    def test_filename(self):
        assert self.events.filename == make_path(
            os.path.join(
                make_path("$GAMMAPULSAR_DATA"),
                Path("fermi/vela_2days/vela_2days_events.fits"),
            )
        )

    def test_load_file(self):
        hdu_events = self.events._load_file(self.events.filename, hdu_type="events")
        hdu_primary = self.events._load_file(self.events.filename, hdu_type="primary")

        assert isinstance(hdu_events, Table)
        assert isinstance(hdu_primary, fits.PrimaryHDU)

    def test_table(self):

        assert isinstance(self.events.table, Table)
        assert self.events.table is not None

    def test_primary(self):

        assert isinstance(self.events.primary_hdu, fits.PrimaryHDU)
        assert self.events.primary_hdu is not None


class TestFermiSpacecraft:
    def setup_class(self):
        self.spacecraft = FermiSpacecraft(
            filename="$GAMMAPULSAR_DATA/fermi/vela_2days/vela_2days_spacecraft.fits"
        )

    def test_filename(self):
        assert self.spacecraft.filename == make_path(
            os.path.join(
                make_path("$GAMMAPULSAR_DATA"),
                Path("fermi/vela_2days/vela_2days_spacecraft.fits"),
            )
        )


class TestFermiObservation:
    def setup_class(self):
        fermi_events = FermiEvents(
            filename="$GAMMAPULSAR_DATA/fermi/vela_2days/vela_2days_events.fits"
        )
        fermi_spacecraft = FermiSpacecraft(
            filename="$GAMMAPULSAR_DATA/fermi/vela_2days/vela_2days_spacecraft.fits"
        )
        self.obs = FermiObservation(
            fermi_events=fermi_events, fermi_spacecraft=fermi_spacecraft
        )

    def test_fermi_events(self):
        assert isinstance(self.obs.fermi_events, FermiEvents)

    def test_fermi_spacecraft(self):
        assert isinstance(self.obs.fermi_spacecraft, FermiSpacecraft)


def test_observations_from_files():

    event = "$GAMMAPULSAR_DATA/fermi/vela_2days/vela_2days_events.fits"
    spacecraft = "$GAMMAPULSAR_DATA/fermi/vela_2days/vela_2days_spacecraft.fits"

    obs_str_both = FermiObservations.from_files(
        events_files=event, spacecrafts_files=spacecraft
    )
    obs_list_both_size = FermiObservations.from_files(
        events_files=[event, event], spacecrafts_files=[spacecraft, spacecraft]
    )
    obs_list_only_ev = FermiObservations.from_files(
        events_files=[event, event], spacecrafts_files=spacecraft
    )
    with pytest.raises(ValueError):
        FermiObservations.from_files(
            events_files=event, spacecrafts_files=[spacecraft, spacecraft]
        )

    assert isinstance(obs_list_only_ev, FermiObservations)
    assert isinstance(obs_list_both_size, FermiObservations)
    assert isinstance(obs_str_both, FermiObservations)

    assert len(obs_str_both) == 1
    assert len(obs_list_both_size) == 2
    assert len(obs_list_only_ev) == 2

    assert isinstance(obs_str_both[0], FermiObservation)
    assert isinstance(obs_str_both[0].fermi_events, FermiEvents)
