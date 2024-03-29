import os
from pathlib import Path
import pytest
from numpy.testing import assert_allclose
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.time import Time
import pint
from gammapy.utils.scripts import make_path
from pint.models import TimingModel
from GammaPulsar.fermi import FermiObservation, FermiObservations, FermiPhaseMaker
from GammaPulsar.utils import disable_logging_library


@pytest.fixture(scope="class")
def fermi_observation():
    event = "$GAMMAPULSAR_DATA/fermi/vela_2days/vela_2days_events.fits"
    spacecraft = "$GAMMAPULSAR_DATA/fermi/vela_2days/vela_2days_spacecraft.fits"
    return FermiObservations.from_files(
        events_files=event, spacecrafts_files=spacecraft
    )


@pytest.fixture()
def ephemeris():
    return "$GAMMAPULSAR_DATA/ephemeris/vela/J0835-4510_tnfit_220401.par"


@pytest.fixture()
def targetcoord():
    return SkyCoord("128.83606354", "-45.17643181", unit="deg", frame="icrs")


def test_init_fermi_phase_maker(fermi_observation, ephemeris):
    obs = fermi_observation
    ephemeris = ephemeris
    with pytest.raises(TypeError):
        FermiPhaseMaker(obs, ephemeris)
    with pytest.raises(FileNotFoundError):
        FermiPhaseMaker(obs[0], "$GAMMAPULSAR_DATA/ephemeris/vela")

    maker = FermiPhaseMaker(obs[0], ephemeris)

    assert maker.ephemeris_file == make_path(
        os.path.join(
            make_path("$GAMMAPULSAR_DATA"),
            Path("ephemeris/vela/J0835-4510_tnfit_220401.par"),
        )
    )
    assert isinstance(maker.observation, FermiObservation)
    assert maker.phases is None
    assert isinstance(maker.model, TimingModel)


class TestFermiPhaseMaker:
    @pytest.fixture(autouse=True)
    def setup_class(self, fermi_observation, ephemeris, targetcoord):
        obs = fermi_observation[0]
        self.maker1 = FermiPhaseMaker(observation=obs, ephemeris_file=ephemeris)
        self.maker2 = FermiPhaseMaker(
            observation=obs,
            ephemeris_file=ephemeris,
            weightcolumn="CALC",
            targetcoord=targetcoord,
        )

    @disable_logging_library(name="pint")
    def test_compute_phase(self):

        self.maker1.compute_phase()

        assert self.maker1.phases is not None
        assert_allclose(self.maker1.phases.sum(), 2276.69356911)

        self.maker2.compute_phase()

        assert self.maker2.phases is not None
        assert_allclose(self.maker2.phases.sum(), 2276.69356911)

    def test_make_meta(self):

        meta_str = self.maker1._make_meta(self.maker1.ephemeris_file, self.maker1.model)

        assert isinstance(meta_str, str)

        meta_dict = eval(meta_str)

        check_dict = {
            "COLUMN_NAME": "PULSE_PHASE",
            "EPHEMERIS_FILE": str(self.maker1.ephemeris_file),
            "PINT_VERS": str(pint.__version__),
            "PSR": "J0835-4510",
            "START": 54682.71577,
            "FINISH": 59662.01623,
            "TZRMJD": 56623.15526603913,
            "TZRSITE": "coe",
            "TZRFREQ": None,
            "EPHEM": "DE421",
            "RAJ": 8.589058747222223,
            "DECJ": -45.17635419444444,
            "PHASE_OFFSET": None,
            "DATE": Time.now().mjd,
        }

        for k in {k: v for k, v in meta_dict.items() if k not in ["DATE"]}.keys():
            assert meta_dict[k] == check_dict[k]

    def test_check_column_name(self):

        hdulist = fits.open(self.maker1.observation.fermi_events.filename)
        event_hdu = hdulist[1]

        check_pulse_overwrite = self.maker1._check_column_name(
            event_hdu=event_hdu, column_name="PULSE_PHASE"
        )
        check_energy_overwrite = self.maker1._check_column_name(
            event_hdu=event_hdu, column_name="ENERGY"
        )

        assert check_pulse_overwrite is True
        assert check_energy_overwrite is False

    @disable_logging_library(name="pint")
    def test_write_column_and_meta(self, tmp_path):

        filename = tmp_path / "written_file_fermi_phase_maker.fits"

        if self.maker1.phases is None:
            self.maker1.compute_phase()

        self.maker1.write_column_and_meta(filename=filename)

        hdulist = fits.open(filename)

        event_hdu = hdulist[1]
        header = event_hdu.header

        assert_allclose(event_hdu.data["PULSE_PHASE"].sum(), 2276.69356911)
        assert eval(header["PHSE_LOG"])["COLUMN_NAME"] == "PULSE_PHASE"

        with pytest.raises(ValueError):
            self.maker1.write_column_and_meta(
                filename=filename, column_name="ENERGY", overwrite=False
            )
