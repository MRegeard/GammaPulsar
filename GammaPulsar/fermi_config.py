class FermiConfig:

    def __init__(
            self,
    ):

    # self._config_filename = config_filename
    #        with open(config_filename, 'r') as f:
    #            conf = yaml.safe_load(f)
    #            self._to_dict = FermiConfigDictionnary(conf)

    @property
    def config_filename(self):
        return self._config_filename

    @property
    def selection(self):
        return self.to_dict()._selection

    @property
    def emin(self, unit='MeV'):

    @property
    def emin(self):
        return self.config._selection._emin

    def to_dict(self):
        return self._to_dict


class FermiConfigDictionnary(dict):

    def __init__(self, dic):
        super().__init__(dic)
        for key, value in dic.items():
            if isinstance(value, dict):
                setattr(self, '_' + key, FermiConfigDictionnary(value))
            else:
                setattr(self, '_' + key, value)
