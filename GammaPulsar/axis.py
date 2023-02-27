import numpy as np

__all__ = ["PhaseAxis"]

class PhaseAxis:

    def __init__(
        self,
        edges_min,
        edges_max,
        reference_phase,
        norm=1,
        name="phase",
    ):

        self._edges_min = edges_min
        self._edges_max = edges_max
        self._reference_phase = reference_phase
        self._norm = norm
        self._name = name

        delta = edges_min[1:] - edges_max[:1]
        if np.any(delta < 0):
            raise ValueError("Time intervals must not overlap.")

    @property
    def is_contiguous(self):

        return np.all(self.edges_min[1:] == self.edges_max[:-1])

    @property
    def nbin(self):

        return len(self.edges_min.flatten())

    @property
    def reference_phase(self):

        return self._reference_phase

    @property
    def edges(self):

        if not self.is_contiguous:
            raise ValueError("Time axis is not contiguous")

        return edges_from_lo_hi(self.edges_min, self.edges_max)

    @property
    def phase_min(self):

        return self.edges_min + self.reference_phase

    @property
    def phase_max(self):

        return self.edges_max + self.reference_phase

    @property
    def phase_edges(self):

        return self.reference_phase + self.edges

    @property
    def phase_delta(self):

        return self.phase_max - self.phase_min

    @property
    def name(self):

        return self._name

    @property
    def norm(self):

        return self._norm

    @property
    def edges_min(self):

        return self._edges_min

    @property
    def edges_max(self):

        return self._edges_max

    @property
    def center(self):

        return self.edges_min + 0.5 * self.bin_width

    @property
    def bin_width(self):

        return self.phase_delta

    @classmethod
    def from_phase_edges(cls, phase_min, phase_max, norm=1, name="phase"):

        reference_phase = phase_min[0]
        edges_min = phase_min - reference_phase
        edges_max = phase_max - reference_phase

        return cls(
            edges_min=edges_min,
            edges_max=edges_max,
            reference_phase=reference_phase,
            norm=norm,
            name=name,
        )

    @classmethod
    def from_phase_bounds(cls, phase_min, phase_max, nbin, norm=1, name="phase"):

        delta = phase_max - phase_min
        phase_edges = phase_min + delta * np.linspace(0, 1, nbin +1)
        return cls.from_phase_edges(
            phase_min=phase_edges[:-1],
            phase_max=phase_edges[1:],
            norm=norm,
            name=name,
        )


def edges_from_lo_hi(edges_lo, edges_hi):
    if np.isscalar(edges_lo) and np.isscalar(edges_hi):
        return [edges_lo, edges_hi]

    edges = edges_lo.copy()
    try:
        edges = edges.insert(len(edges), edges_hi[-1])
    except AttributeError:
        edges = np.insert(edges, len(edges), edges_hi[-1])
    return edges