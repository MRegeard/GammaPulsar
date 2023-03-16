import collections.abc
import glob
import os
from fermipy.gtanalysis import GTAnalysis
from GammaPulsar.config import FermiConfig, FermiSerializedConfig

__all__ = ["FermiAnalysis", "FermiAnalysisList", "FermiAnalysisSerialize"]


class FermiAnalysis(GTAnalysis):
    def __init__(
        self,
        config,
        dir_path=None,
    ):

        self._fermi_config = FermiConfig(config)
        self._dir_path = dir_path
        super().__init__(config, logging={"verbosity": 3})

    @property
    def view_config(self):

        return self._fermi_config._dict

    @property
    def dir_path(self):

        return self._dir_path

    def run_fit(
        self,
        source_name,
        free_source=True,
        free_distance=3.0,
        free_param="norm",
        free_diff=True,
    ):

        self.free_sources(distance=free_distance, pars=free_param)
        if free_diff:
            self.free_source("galdiff")
            self.free_source("isodiff")
        if free_source:
            self.free_source(source_name)
        fit_results = self.fit()
        print(f'Fit Quality : {fit_results["fit_quality"]}')

    def compute_flux_points(self, source_name):

        return self.sed(source_name)


class FermiAnalysisList(collections.abc.MutableSequence):
    def __init__(self, analysis=None):
        self._analysis = analysis or []

    def __getitem__(self, key):
        return self._analysis[self.index(key)]

    def __delitem__(self, key):
        del self._analysis[self.index(key)]

    def __setitem__(self, key, ana):
        if isinstance(ana, FermiAnalysis):
            self._analysis[self.index(key)] = ana
        else:
            raise TypeError(f"Invalid type: {type(ana)!r}")

    def __len__(self):
        return len(self._analysis)

    def insert(self, idx, ana):
        if isinstance(ana, FermiAnalysis):
            self._analysis.insert(idx, ana)
        else:
            raise TypeError(f"Invalid type: {type(ana)!r}")

    def index(self, key):
        if isinstance(key, (int, slice)):
            return key
        elif isinstance(key, FermiAnalysis):
            return self._analysis.index(key)
        else:
            raise TypeError(f"Invalid type: {type(key)!r}")

    @classmethod
    def from_file(cls, configs, dir_paths=None):

        fermi_ana = []
        if dir_paths is None:
            dir_paths = [None] * len(configs)
        for config, dir_path in zip(configs, dir_paths):

            fermi_ana.append(FermiAnalysis(config=config, dir_path=dir_path))

        return FermiAnalysisList(analysis=fermi_ana)


class FermiAnalysisSerialize:
    def __init__(
        self,
        analysis_config,
        dir_prefix,
        config_prefix="config*.yaml",
    ):

        self._dir_prefix = dir_prefix
        self._config_prefix = config_prefix
        self._analysis_config = FermiSerializedConfig(analysis_config)
        self._fermi_analysis = FermiAnalysisList.from_file(
            configs=self.list_config, dir_paths=self.list_dir
        )

    @property
    def analysis_config(self):

        return self._analysis_config

    @property
    def config_prefix(self):

        return self._config_prefix

    @property
    def dir_prefix(self):

        return self._dir_prefix

    @property
    def list_dir(self):

        return glob.glob(self.dir_prefix + "*")

    @property
    def list_config(self):

        config_list = []
        for directory in self.list_dir:
            config_list.append(glob.glob(directory + "/" + self.config_prefix)[0])
        return config_list

    @property
    def fermi_analysis(self):

        return self._fermi_analysis

    def run_analysis(self):

        roi_prefit = []
        roi_postfit = []
        fit_results = []
        sed = []
        work_dir = os.getcwd()
        for ana in self.fermi_analysis:

            os.chdir(work_dir + ana.dir_path)

            ana.setup()

            roi = ana.roi[self.analysis_config.source_name]
            if not self.analysis_config.default_spectral:
                roi.spectral_pars["Index"] = self.analysis_config.index
                roi.spectral_pars["Prefactor"] = self.analysis_config.prefactor
                roi.spectral_pars["Scale"] = self.analysis_config.scale

            ana.free_sources(
                distance=self.analysis_config.free_sources_distance,
                pars=self.analysis_config.free_sources_param,
            )
            if self.analysis_config.free_galdiff:
                ana.free_source("galdiff")
            if self.analysis_config.free_isodiff:
                ana.free_source("isodiff")
            if self.analysis_config.free_source:
                ana.free_source(self.analysis_config.source_name)
            roi = ana.roi[self.analysis_config.source_name]
            roi_prefit.append(roi)

            fit_res = ana.fit()
            fit_results.append(fit_res)

            roi = ana.roi[self.analysis_config.source_name]
            roi_postfit.append(roi)

            if self.analysis_config.write_roi:
                ana.write_roi(self.analysis_config.roi_filename)

            sed.append(ana.sed(self.analysis_config.source_name))

        setattr(self, "roi_prefit", roi_prefit)
        setattr(self, "roi_postfit", roi_postfit)
        setattr(self, "fit_results", fit_results)
        setattr(self, "flux_point", sed)
