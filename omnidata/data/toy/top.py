import numpy as np

from ...parameters import hparam, inherit_hparams
from ...structure import spaces

from ..flavors import BuildableDataset, SyntheticDataset
from .manifolds import SwissRollDatasetBase, HelixDatasetBase



class ToyDataset(BuildableDataset, SyntheticDataset):
	n_samples = hparam(100, space=spaces.Naturals())



@inherit_hparams('n_samples')
class SwissRollDataset(SwissRollDatasetBase, ToyDataset):
	_name = 'swiss-roll'

	noise_std = hparam(0., space=spaces.Bound(min=0.))

	target_theta = hparam(False, space=spaces.Binary())

	Ax = hparam(np.pi/2, space=spaces.Bound(min=0.))
	Ay = hparam(21., space=spaces.Bound(min=0.))
	Az = hparam(np.pi/2, space=spaces.Bound(min=0.))

	freq = hparam(0.5, space=spaces.Bound(min=0.))
	tmin = hparam(3., space=spaces.Bound(min=0.))
	tmax = hparam(9., space=spaces.Bound(min=0.))



@inherit_hparams('n_samples')
class HelixDataset(HelixDatasetBase, ToyDataset):
	_name = 'helix'

	n_helix = hparam(2, space=spaces.Naturals())
	noise_std = hparam(0., space=spaces.HalfBound(min=0.))

	target_theta = hparam(True, space=spaces.Binary())
	periodic_strand = hparam(False, space=spaces.Binary())

	Rx = hparam(1., space=spaces.Bound(min=0.))
	Ry = hparam(1., space=spaces.Bound(min=0.))
	Rz = hparam(1., space=spaces.Bound(min=0.))

	w = hparam(1., space=spaces.Bound(min=0.))



