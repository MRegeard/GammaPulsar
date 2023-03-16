import os
from pathlib import Path
import yaml
from yaml.loader import SafeLoader

__all__ = ["FermiConfig", "FermiSerializedConfig"]


class FermiConfig:
    def __init__(self, config_file):

        self._config_file = config_file
        with open(config_file, "r") as stream:
            config = yaml.safe_load(stream)
            self._dict = config
            stream.close()

    @property
    def selection(self):

        return self._dict["selection"]

    @property
    def data(self):

        return self._dict["data"]

    @property
    def binning(self):

        return self._dict["binning"]

    @property
    def gtlike(self):

        return self._dict["gtlike"]

    @property
    def model(self):

        return self._dict["model"]

    @property
    def config_file(self):

        return self._config_file

    def add_entry(self, primary_dict, entry, value):

        self._dict[primary_dict][entry] = value

    def to_dict(self):

        return self._dict

    def write(self, filename, **kwargs):

        if isinstance(filename, str):
            filename = Path(filename)

        if filename.name[-5:] != ".yaml":
            filename = Path(filename.name + "yaml")

        with open(filename, "w") as outfile:
            yaml.dump(self._dict, outfile, sort_keys=False, **kwargs)
            outfile.close()

    def make_phase_binned_directory(self, phase_axis, dir_path=None):

        if dir_path is None:
            base_path = Path("./")
        else:
            base_path = Path(dir_path)
        for edge_min, edge_max in zip(
            phase_axis.edges_min.value, phase_axis.edges_max.value
        ):
            dir_name = Path("phase_" + str(edge_min) + "-" + str(edge_max))
            out_dir = Path(os.path.join(base_path, dir_name))
            out_dir.mkdir(parents=True, exist_ok=True)
            self.add_entry(
                primary_dict="selection", entry="phasemin", value=float(edge_min)
            )
            self.add_entry(
                primary_dict="selection", entry="phasemax", value=float(edge_max)
            )
            outfile = Path("config_" + str(edge_min) + "-" + str(edge_max) + ".yaml")
            full_path = Path(os.path.join(out_dir, outfile))
            self.write(full_path)


class FermiSerializedConfig:
    def __init__(
        self,
        config_file,
    ):

        self.config_file = config_file
        with open(config_file, "r") as stream:
            config = yaml.load(stream, Loader=SafeLoader)
            self.to_dict = config
            stream.close()

    @property
    def source_name(self):

        return self.to_dict["source_name"]

    @property
    def free_sources_distance(self):

        return self.to_dict["free_sources"]["distance"]

    @property
    def free_sources_param(self):

        return self.to_dict["free_sources"]["pars"]

    @property
    def free_isodiff(self):

        return self.to_dict["free_diff"]["isodiff"]

    @property
    def free_galdiff(self):

        return self.to_dict["free_diff"]["galdiff"]

    @property
    def free_source(self):

        return self.to_dict["free_source"]

    @property
    def write_roi(self):

        return self.to_dict["roi"]["write"]

    @property
    def roi_filename(self):

        if self.write_roi:
            return self.to_dict["roi"]["filename"]
        else:
            return None

    @property
    def default_spectral(self):

        return self.to_dict["spectral"]["default"]

    @property
    def spectrum_type(self):

        if self.default_spectral:
            return "Default"
        else:
            return self.to_dict["spectral"]["spectrum_type"]

    @property
    def index(self):

        if self.default_spectral:
            return "Default"
        else:
            return self.to_dict["spectral"]["index"]

    @property
    def prefactor(self):

        if self.default_spectral:
            return "Default"
        else:
            return self.to_dict["spectral"]["index"]

    @property
    def scale(self):

        if self.default_spectral:
            return "Default"
        else:
            return self.to_dict["spectral"]["index"]

    @property
    def sed_type(self):

        return self.to_dict["sed"]["sed_type"]
