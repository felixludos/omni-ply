from omnibelt import unspecified_argument, InitWall
# import torch
# from torch.nn import functional as F
# import torch.distributions as distrib
# from torch.distributions.utils import lazy_property
# from torch.distributions import constraints

from ..util.tensors import WrappedTensor
from ..features import Device
from ..persistent import Fingerprinted

from .operations import Sampler


# TODO: make exportable
# TODO: add warnings for non-seeded functions like rsample()
class Distribution(Sampler, Fingerprinted, ):#distrib.Distribution): # TODO: saving and loading distributions
	def __init__(self, params=None, apply_constraints=False, constraints=None, soft_constraints=False, **kwargs):
		if params is None:
			params = {key: kwargs[key] for key in self.arg_constraints if key in kwargs}
		if constraints is None:
			constraints = self.arg_constraints
		kwargs.update(self._constrain_params(params, constraints, soft_constraints=soft_constraints)
		              if apply_constraints else params)
		super().__init__(**kwargs)
		self._param_keys = set(key for key in params if params[key] is not None)


	def _constrain_params(self, params, constraints, **kwargs):
		return {key: self.constrain_value(constraints.get(key), val, **kwargs) for key, val in params.items()}


	# def sample(self, sample_shape=torch.Size()):
	# 	if isinstance(sample_shape, int):
	# 		sample_shape = sample_shape,
	# 	return super().sample(sample_shape)


	def best(self):
		'''
		Get the best sample (by default, the mean, but possibly also the mode)
		:return:
		'''
		return self.mean


	def iterate_parameters(self):
		for key in self._param_keys:
			val = getattr(self, key)
			if val is not None:
				yield (key, val)


	def _fingerprint_data(self):
		params = {key: self.fingerprint_obj(getattr(self, key)) for key in self._param_keys if hasattr(self, key)}
		return {'params': params, **super()._fingerprint_data()}


	def copy(self, **kwargs):
		for param in self._param_keys:
			if param not in kwargs:
				kwargs[param] = getattr(self, param)
		return self.__class__(**kwargs)


	def to(self, device):
		params = {}
		for key in self._param_keys:
			param = getattr(self, key)
			if isinstance(param, (torch.Tensor, Device)):
				param = param.to(device)
			params[key] = param
		return self.copy(**params)


	@staticmethod
	def constrain_value(constraint, value, eps=1e-12, soft_constraints=False):
		if value is None:
			return value

		if constraint == constraints.simplex:
			return F.normalize(value, p=1, dim=1, eps=eps).abs()

		if isinstance(constraint,
		              (constraints.greater_than, constraints.greater_than_eq)) and constraint.lower_bound == 0:
			return F.softplus(value) if soft_constraints else value.exp()

		if isinstance(constraint, constraints.interval):
			mn, mx = constraint.lower_bound, constraint.upper_bound
			# assert mn == 0 and mx == 1, f'{constraint}: {mn} {mx}'
			value = value.sigmoid()
			if mn != 0 or mx != 1:
				value = value.mul(mx - mn) + mn
			return value

		if constraint == constraints.positive_definite:
			raise NotImplementedError  # TODO
			if len(real.shape) == 1:
				N = int(np.sqrt(len(real)))
				real = value.reshape(N, N) + ep
				s * torch.eye(N, device=real.device)
			return real.t() @ real

		return value



class NormalDistribution(Distribution, ):#distrib.Normal):
	def __init__(self, loc, scale, **kwargs):
		super().__init__(loc=loc, scale=scale, **kwargs)


	def _sample(self, shape):
		shape = self._extended_shape(shape)
		noise = torch.randn(*shape, generator=self.rng)
		return noise.mul(self.scale) + self.loc



class CategoricalDistribution(Distribution, ):#distrib.Categorical):
	def __init__(self, probs=None, logits=None, **kwargs):
		super().__init__(probs=probs, logits=logits, **kwargs)

	def best(self):
		return self._param.argmax(-1)


	def _sample(self, shape):
		probs_2d = self.probs.reshape(-1, self._num_events)
		samples_2d = torch.multinomial(probs_2d, shape.numel(), True, generator=self.rng).T
		return samples_2d.reshape(self._extended_shape(shape))



class DistributionTensor(Fingerprinted, WrappedTensor):

	_base_distribution = None
	@classmethod
	def _create_distribution(cls, **kwargs):
		return cls._base_distribution(**kwargs)


	@staticmethod
	def __new__(cls, dis=None, value=None, use_best=True, **kwargs):

		if dis is None:
			dis = cls._create_distribution(**kwargs)

		if value is None:
			value = dis.best() if use_best else dis.generate()

		obj = super().__new__(cls, value.float())
		obj._distribution = dis
		return obj


	def _fingerprint_data(self):
		return {'distribution': self.fingerprint_obj(self._distribution), **super()._fingerprint_data()}


	# def __repr__(self):
	# 	return repr(self.distribution)

	def copy(self):
		params = dict(self.distribution.iterate_parameters())
		copy = self.__class__.__new__(self.__class__, value=self, **params)
		copy.__dict__.update(self.__dict__)
		copy.data = self.data
		return copy


	@property
	def distribution(self):
		return self._distribution


	def to(self, *args, **kwargs):
		try:
			new = super().to(*args, **kwargs)
		except RuntimeError:
			print('Cannot change the dtype of distributions (only devices)') # TODO
			return self
		else:
			new._distribution = self.distribution.to(*args, **kwargs)
			return new


	# def __getattr__(self, item):
	# 	value = getattr(self.distribution, item, unspecified_argument)
	# 	if value is unspecified_argument:
	# 		raise AttributeError(item)
	# 	return value



class Normal(DistributionTensor):
	_base_distribution = NormalDistribution

	@staticmethod
	def __new__(cls, loc, scale, **kwargs):
		return super().__new__(cls, loc=loc, scale=scale, **kwargs)



class Categorical(DistributionTensor):
	_base_distribution = CategoricalDistribution

	@staticmethod
	def __new__(cls, probs=None, logits=None, apply_constraints=False, soft_constraints=False,
	            gen=unspecified_argument, seed=unspecified_argument, **kwargs):
		return super().__new__(cls, probs=probs, logits=logits, **kwargs)



