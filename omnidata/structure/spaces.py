from typing import Sequence as _Sequence
from omnibelt import Packable

# import math

import numpy as np
# import torch
# from torch.nn import functional as F

from ..util import angle_diff
from ..persistent import Fingerprinted

from .operations import Sampler
from .metrics import Measure, Lp, L2, L1


# TODO: include dtypes
# TODO: equality testing


class Dim(Packable, Measure, Sampler, Fingerprinted):
	def __init__(self, min=None, max=None, shape=(), dtype=None, **kwargs):
		super().__init__(**kwargs)
		self.shape = shape
		self.dtype = dtype
		self.min = min
		self.max = max


	def __str__(self):
		terms = ', '.join(map(str,self.shape))
		return f'{self.__class__.__name__}({terms})'


	def __repr__(self):
		return str(self)


	def compress(self, vals):
		return vals


	def expand(self, vals):
		return vals


	class InvalidValue(ValueError):
		pass


	def validate(self, value):
		if not isinstance(value, (int, float)):
			raise NotImplementedError
		if self.min is not None and value < self.min:
			raise self.InvalidValue(value)
		if self.max is not None and value > self.max:
			raise self.InvalidValue(value)

	@property
	def width(self): # for (default) neural representation
		return self.dof

	@property
	def dof(self): # minimal representation
		return len(self)


	@property
	def shape(self): # native representation
		return self._shape
	@shape.setter
	def shape(self, shape):
		if isinstance(shape, int):
			shape = (shape,)
		self._shape = shape# torch.Size(shape)


	@property
	def expanded_shape(self):
		return self.shape


	def __len__(self):  # compressed shape
		return self.shape.numel()


	def _fingerprint_data(self):
		return {
			'min': None if self.min is None else self.min.float().mean().item(),
			'max': None if self.max is None else self.max.float().mean().item(),
			'dtype': str(self.dtype),
			'shape': str(self.shape),
			**super()._fingerprint_data()
		}
	

	def sample(self, *shape, **kwargs):
		samples = super().sample(*shape, **kwargs)
		if self.dtype is not None:
			samples = samples.to(self.dtype)
		return samples


	def difference(self, x, y, standardize=None):  # x-y
		if standardize:
			x, y = self.standardize(x), self.standardize(y)
		return super().difference(x, y)


	def distance(self, x, y, standardize=None):
		if standardize:
			x, y = self.standardize(x), self.standardize(y)
		return super().distance(x, y)


	def measure(self, x, y, standardize=None):
		if standardize:
			x, y = self.standardize(x), self.standardize(y)
		return super().measure(x, y)


	def transform(self, vals, spec): # spec is current space of vals, self is the new
		return self.unstandardize(spec.standardize(vals))


	def standardize(self, vals):
		raise NotImplementedError


	def unstandardize(self, vals):
		raise NotImplementedError


	@property
	def min(self):
		return self._min
	@min.setter
	def min(self, val):
		self._min = val if val is None else val#torch.as_tensor(val)


	@property
	def max(self):
		return self._max
	@max.setter
	def max(self, val):
		self._max = val if val is None else val#torch.as_tensor(val)


	@property
	def range(self):
		return self.max - self.min



class Range(Dim):
	def __init__(self, min=None, max=None, shape=(), dtype=None, **kwargs):
		super().__init__(min=min, max=max, shape=shape, dtype=dtype, **kwargs)


	def _sample(self, shape):
		return torch.randint(self.min, self.max, shape, generator=self.rng)



class Naturals(Range):
	def __init__(self, max=None, *, min=0, **kwargs):
		super().__init__(min=min, max=max, **kwargs)



class Continuous(Dim):
	def _sample(self, shape):
		return self.unstandardize(self._sample_prior(torch.Size([*shape, *self.shape])))


	def _sample_prior(self, shape):
		return torch.randn(*shape, generator=self.rng)


	def distance(self, x, y, standardize=None):
		N = len(x) if len(x.shape) > 1 else 1
		return self.difference(x, y, standardize=standardize).view(N, -1).norm(p=2, dim=1)



class HalfBound(Continuous):
	def __init__(self, bound=0, side='lower', bound_type='exp', epsilon=1e-10,
	             min=None, max=None, **kwargs):
		
		if min is None and max is None:
			assert bound is not None, 'No bound provided'
			assert side in {'lower', 'upper'}, 'Bound side not specified'
			
			if side == 'lower':
				min = bound
			else:
				max = bound
		assert max is None or min is None, f'Too many bounds specified: min={min}, max={max}'
		assert bound_type in {'exp', 'soft', 'chi', 'abs'}
		if bound_type in {'chi', 'abs'}:
			print(f'WARNING: half-bound dim using transformation {bound_type} cannot be standardized')
		super().__init__(max=max, min=min, **kwargs)
		
		self._bound_type = bound_type
		self._epsilon = epsilon


	def __str__(self):
		terms = ('('+ ', '.join(map(str,self.shape))+'), ') if len(self) > 1 else ''
		lim = f'min={self.min.mean().item():.3g}' \
			if self.min is not None else f'max={self.max.mean().item():.3g}'
		return f'{self.__class__.__name__}({terms}{lim})'


	def standardize(self, vals):
		if self.min is not None:
			vals = vals - self.min.unsqueeze(0)
		elif self.max is not None:
			vals = vals.sub(self.max.unsqueeze(0)).mul(-1)
		
		vals = vals.clamp(min=self._epsilon)
		if self._bound_type == 'soft':
			vals = vals.exp().sub(1).log() # TODO: test this
		elif self._bound_type == 'chi':
			vals = vals.sqrt()
		elif self._bound_type == 'exp':
			vals = vals.log()
		
		return vals


	def unstandardize(self, vals):
		if self._bound_type == 'soft':
			vals = F.softplus(vals)
		elif self._bound_type == 'chi':
			vals = vals.pow(2)
		elif self._bound_type == 'exp':
			vals = vals.exp()
		else:
			vals = vals.abs()
		
		if self.min is not None:
			vals = vals + self.min.unsqueeze(0)
		elif self.max is not None:
			vals = -vals + self.max.unsqueeze(0)
		
		return vals



class Bound(Continuous):
	def __init__(self, min=0., max=1., epsilon=1e-10, **kwargs):
		min, max = torch.as_tensor(min).float(), torch.as_tensor(max).float()
		super().__init__(min=min, max=max, **kwargs)
		assert self.min is not None, f'No lower bound provided'
		assert self.max is not None, f'No upper bound provided'
		
		self._epsilon = epsilon


	def __str__(self):
		terms = ('('+ ', '.join(map(str,self.shape))+'), ') if len(self) > 1 else ''
		return f'{self.__class__.__name__}({terms}min={self.min.mean().item():.3g}, max={self.max.mean().item():.3g})'


	def _sample_prior(self, shape):
		return torch.rand(*shape, generator=self.rng)


	def standardize(self, vals):
		return vals.to(self.min).sub(self.min.unsqueeze(0)).div(self.range.unsqueeze(0)) \
			.clamp(min=self._epsilon, max=1 - self._epsilon).to(vals)


	def unstandardize(self, vals):
		return vals.to(self.range).clamp(min=self._epsilon, max=1 - self._epsilon) \
			.mul(self.range.unsqueeze(0)).add(self.min.unsqueeze(0)).to(vals)


	# def difference(self, x, y, standardize=None):
	# 	return super().difference(x, y, standardize=standardize)# * (self.range.unsqueeze(0) ** float(not standardize))



class Logspace(Bound):
	def standardize(self, vals):
		return super().standardize(vals.log())
	
	
	def unstandardize(self, vals):
		return super().unstandardize(vals).exp()



class Unbound(Continuous):
	def __init__(self, shape=None, min=None, max=None, **kwargs):
		if isinstance(shape, int):
			shape = shape,
		super().__init__(shape=shape, min=None, max=None, **kwargs)


	def standardize(self, vals):
		return vals


	def unstandardize(self, vals):
		return vals



class Periodic(Bound):
	def __init__(self, period=1., min=0., max=None, **kwargs):
		assert min is not None and (period is not None or max is not None), 'Not enough bounds provided'
		if max is None:
			max = min + period
		super().__init__(min=min, max=max, **kwargs)


	def __str__(self):
		return f'{self.__class__.__name__}({self.period.mean().item():.3g})'


	@property
	def period(self):
		return self.range


	@property
	def expanded_shape(self):
		return torch.Size((*self.shape, 2))


	def expand(self, vals):
		thetas = self.standardize(vals).mul(2*np.pi)
		return torch.stack([thetas.cos(), thetas.sin()], -1)


	def compress(self, vals):
		vals = vals.view(-1, *self.expanded_shape)
		return self.unstandardize(torch.atan2(vals[..., 1], vals[..., 0]).div(2 * np.pi).remainder(1))


	def difference(self, x, y, standardize=None):
		if standardize is None or standardize: # by default, standardize
			x, y = self.standardize(x), self.standardize(y)
		return angle_diff(x, y, period=1.) * (self.period ** float(standardize is None))


	def measure(self, x, y, standardize=None):
		if standardize is None or standardize: # by default, standardize
			x, y = self.standardize(x), self.standardize(y)
		return super().measure(x, y)


	def distance(self, x, y, standardize=None):
		return super().distance(x, y, standardize=standardize is None or standardize)


	def transform(self, vals, spec):
		if isinstance(spec, Categorical):
			spec.n += 1
		out = super().transform(vals, spec)
		if isinstance(spec, Categorical):
			spec.n -= 1
		return out



class MultiDim(Dim):
	def __init__(self, channels=None, dim=1, shape=None, **kwargs):
		assert channels is not None or shape is not None, 'need a dimensionality of the topology'
		super().__init__(shape=shape, **kwargs)
		if channels is None:
			channels = (0, *self.shape)[dim]
		assert channels > 0, 'topology must have more than 0 channels'
		self.dim = dim
		self.channels = channels


	def _fingerprint_data(self):
		return {
			'dim': str(self.dim),
			'channels': str(self.channels),
			**super()._fingerprint_data()
		}
	

	def __len__(self):
		return self.channels


	def __str__(self):
		return f'{self.__class__.__name__}({len(self)})'



class Surface(MultiDim):
	def geodesic(self, x, y, standardize=None):
		raise NotImplementedError


	def distance(self, x, y, standardize=None):
		return self.geodesic(x, y, standardize=standardize)



class LebesgueSurface(Surface, Lp):
	def standardize(self, vals):
		return F.normalize(vals, p=self.p, dim=self.dim)


	def __len__(self):
		return self.channels - 1


	def unstandardize(self, vals):
		return self.standardize(vals)


	def magnitude(self, x):
		return super().magnitude(x, dim=self.dim)



class Simplex(LebesgueSurface, Bound, L1):
	def geodesic(self, x, y, standardize=None):
		return super(Surface, self).distance(x, y, standardize=standardize)


	def _sample(self, shape):  # from Donald B. Rubin, The Bayesian bootstrap Ann. Statist. 9, 1981, 130-134.
		# discussed in https://cs.stackexchange.com/questions/3227/uniform-sampling-from-a-simplex

		extra_shape = [*shape, *self.shape]
		raw = super()._sample(shape).view(*extra_shape)

		dim = self.dim
		extra_shape[dim] = 1
		
		edges = torch.cat([torch.zeros(*extra_shape),
		                   raw.narrow(dim, 0, self.channels - 1).sort(dim)[0],
		                   torch.ones(*extra_shape)], dim)
		
		samples = edges.narrow(dim, 1, self.channels) - edges.narrow(dim, 0, self.channels)
		return samples



class Sphere(LebesgueSurface, Unbound, L2):
	def geodesic_cos(self, x, y, standardize=None): # returns cos(theta)
		if standardize:
			x, y = self.standardize(x), self.standardize(y)
		return x.mul(y).sum(self.dim)


	def geodesic(self, x, y, standardize=None): # theta: [0, pi]
		return self.geodesic_cos(x, y, standardize=standardize).acos()#.div(np.pi/2)


	def measure_euclidean(self, x, y, standardize=None):
		return super(Surface, self).distance(x, y, standardize=standardize)



class Spatial(MultiDim): # order of some dimensions is not permutable (channel dim are permutable)
	def __init__(self, channels, *size, shape=None, channel_first=True, **kwargs):
		if isinstance(size, int):
			size = (size,)
		if not len(size):
			size = shape

		shape = (channels,) if size is None else (
			(channels, *size) if channel_first else (*size, channels))

		self._channel_first = channel_first
		super().__init__(channels=channels, shape=shape, **kwargs)


	@property
	def channel_first(self):
		return self._channel_first
	@channel_first.setter
	def channel_first(self, val):
		if val != self.channel_first:
			channels, size = self.channels, self.size
			self.shape = (channels, *size) if val else (*size, channels)
			self._channel_first = val


	@property
	def channels(self):
		return self.shape[0] if self.channel_first else self.shape[-1]
	@channels.setter
	def channels(self, val):
		self.shape = (val, *self.size) if self.channel_first else (*self.size, val)


	@property
	def C(self):
		return self.channels
	@C.setter
	def C(self, val):
		self.channels = val


	@property
	def size(self):
		return self.shape[1:] if self.channel_first else self.shape[:-1]
	@size.setter
	def size(self, val):
		if isinstance(val, int):
			val = (val,)
		self.shape = (self.channels, *val) if self.channel_first else (*val, self.channels)


	def __str__(self):
		return f'{self.__class__.__name__}(C={self.channels}, size={self.size})'



class Sequence(Spatial):
	def __init__(self, channels=1, length=None, **kwargs):
		super().__init__(channels=channels, shape=(length,), **kwargs)
		self._length = length

	@property
	def length(self):
		return self._length
	@length.setter
	def length(self, val):
		self._length = val
		self.size = (val,)


	@property
	def L(self):
		return self.length
	@L.setter
	def L(self, val):
		self.length = val


	def __str__(self):
		return f'{self.__class__.__name__}(C={self.channels}, L={self.length})'



class Image(Spatial):
	def __init__(self, channels=1, height=None, width=None, **kwargs):
		super().__init__(channels=channels, shape=(height, width), **kwargs)
		self._height = height
		self._width = width

	@property
	def height(self):
		return self._height
	@height.setter
	def height(self, val):
		self._height = val
		self.size = (val, self.width)


	@property
	def width(self):
		return self._width
	@width.setter
	def width(self, val):
		self._width = val
		self.size = (self.height, val)

	@property
	def H(self):
		return self.height
	@H.setter
	def H(self, val):
		self.height = val


	@property
	def W(self):
		return self.width
	@W.setter
	def W(self, val):
		self.width = val


	def __str__(self):
		return f'{self.__class__.__name__}(C={self.channels}, H={self.height}, W={self.width})'



class Pixels(Image, Bound):
	def __init__(self, channels=1, height=None, width=None, as_bytes=True, min=None, max=None, dtype=None, **kwargs):
		min, max = (0, 255) if as_bytes else (0., 1.)
		if dtype is None:
			dtype = torch.uint8 if as_bytes else torch.float
		super().__init__(channels=channels, height=height, width=width, min=min, max=max, dtype=dtype, **kwargs)
		self.as_bytes = as_bytes



class Volume(Spatial):
	def __init__(self, channels=1, height=None, width=None, depth=None, **kwargs):
		super().__init__(channels=channels, shape=(height, width, depth), **kwargs)
		self._height = height
		self._width = width
		self._depth = depth


	@property
	def height(self):
		return self._height
	@height.setter
	def height(self, val):
		self._height = val
		self.size = (val, self.width, self.depth)


	@property
	def width(self):
		return self._width
	@width.setter
	def width(self, val):
		self._width = val
		self.size = (self.height, val, self.depth)


	@property
	def depth(self):
		return self._depth
	@depth.setter
	def depth(self, val):
		self._depth = val
		self.size = (self.height, self.width, val)


	@property
	def H(self):
		return self.height
	@H.setter
	def H(self, val):
		self.height = val

	@property
	def W(self):
		return self.width
	@W.setter
	def W(self, val):
		self.width = val

	@property
	def D(self):
		return self.depth
	@D.setter
	def D(self, val):
		self.depth = val

	def __str__(self):
		return f'{self.__class__.__name__}(C={self.channels}, H={self.height}, W={self.width}, D={self.depth})'



class Categorical(Dim):
	def __init__(self, n, **kwargs):
		if isinstance(n, _Sequence):
			n = list(n)
			n, values = len(n), n
		else:
			assert isinstance(n, int), f'bad: {n}'
			n, values = n, list(range(n))
		super().__init__(min=0, max=n - 1, **kwargs)
		# super().__init__(min=torch.as_tensor(0), max=torch.as_tensor(n - 1), **kwargs)
		self._min = self._min#.long()
		self._max = self._max#.long()
		self.n = n
		self.values = values


	@property
	def width(self): # for (default) neural representation
		return self.n


	def validate(self, value):
		if value in self.values:
			return
		return super().validate(value)


	def __str__(self):
		return f'{self.__class__.__name__}({self.n})'


	def _fingerprint_data(self):
		return {'n': str(self.n), **super()._fingerprint_data()}
	

	def standardize(self, vals):
		return vals / (self.n - 1)


	def unstandardize(self, vals):
		return (vals * self.n).long().clamp(max=self.n - 1)


	@property
	def expanded_shape(self):
		return torch.Size((*self.shape, self.n))


	def _sample(self, shape):
		samples = torch.randint(self.n, size=(*shape, *self.shape), generator=self.rng)
		return samples


	def expand(self, vals):
		return F.one_hot(vals.long(), self.n)


	def compress(self, vals):
		return vals.max(-1)[1]


	def difference(self, x, y, standardize=None):
		return (x - y).bool().float()


	def distance(self, x, y, standardize=None):
		N = len(x) if len(x.shape) > 1 else 1
		return self.difference(x, y).view(N, -1).sum(-1).bool().float()



class Selection(Categorical):
	def __init__(self, values=None, **kwargs):
		if values is None:
			values = []
		super().__init__(values, **kwargs)


	def __str__(self):
		return f'{self.__class__.__name__}({", ".join(map(str,self.values))})'

	def __contains__(self, item):
		return item in self.values

	@property
	def n(self):
		return len(self.values)
	@n.setter
	def n(self, val):
		pass

	def replace(self, values):
		self.values = values

	def append(self, value):
		self.values.append(value)

	def extend(self, values):
		self.values.extend(values)

	def remove(self, value):
		self.values.remove(value)

	def clear(self):
		self.values.clear()



class ImplicitSelection(Selection):
	def __init__(self, value_fn=None, **kwargs):
		super().__init__(None, **kwargs)
		self.value_fn = value_fn

	@property
	def values(self):
		if self.value_fn is None:
			return []
		return self.value_fn()
	@values.setter
	def values(self, val):
		pass




class Binary(Categorical):
	def __init__(self, n=None, **kwargs):
		super().__init__(n=2, **kwargs)


	def __str__(self):
		return f'Binary()'



class Joint(Dim):
	def __init__(self, *dims, names=None, shape=None, max=None, min=None, scales=None,
	             # seed=None, gen=None,
	             **kwargs):
		singles = []
		dim_names = []
		for i, d in enumerate(dims):
			if isinstance(d, Joint):
				singles.extend(d.dims)
				if d.names is not None:
					dim_names.extend(d.names)
				elif names is not None:
					dim_names.extend([f'{names[i]}-{di}' for di, dm in enumerate(d.dims)])
			else:
				singles.append(d)
				if names is not None:
					dim_names.append(names[i])
		dims = singles
		shape = (sum(len(dim) for dim in dims),)
		expanded_shape = torch.Size((sum(dim.expanded_shape.numel() for dim in dims),))
		
		super().__init__(shape=shape, min=None, max=None,
		                 # seed=seed, gen=gen,
		                 **kwargs)
		# if gen is not None:
		# 	for dim in dims:
		# 		dim.gen = gen
		# elif seed is not None:
		# 	for dim in dims:
		# 		seed = self.gen_deterministic_seed(seed)
		# 		dim.seed = seed

		self.names = dim_names
		self.dims = dims
		self._expanded_shape = expanded_shape
		self.scales = scales
		self._dim_indices = np.cumsum([0] + [len(dim) for dim in self.dims]).tolist()
		self._dim_expanded_indices = np.cumsum([0] + [dim.expanded_shape.numel() for dim in self.dims]).tolist()
		self._is_dense = any(1 for dim in dims if isinstance(dim, Continuous))


	def __str__(self):
		contents = ', '.join(str(x) for x in self.dims)
		return f'{self.__class__.__name__}({contents})'


	def __iter__(self):
		return iter(self.dims)


	def _fingerprint_data(self):
		return {'dims': self.dims, **super()._fingerprint_data()}
	

	@property
	def expanded_shape(self):
		return self._expanded_shape
	
	
	def select(self, data, idx, dim=1, use_expanded=False):
		inds = self._dim_expanded_indices if use_expanded else self._dim_indices
		start, stop = inds[idx], inds[idx+1]
		sel = [None]*dim + [slice(start, stop)]
		return data[tuple(sel)]
	
	
	def _dispatch(self, method, *vals, use_expanded=False, **base_kwargs):
		outs = []
		idx = 0
		B = None
		for dim in self.dims:
			D = dim.expanded_len() if use_expanded else len(dim)
			args = tuple(v.narrow(-1, idx, D) for v in vals)
			kwargs = base_kwargs.copy()
			
			out = getattr(dim, method)(*args, **kwargs)
			if B is None:
				B = out.size(0) #if len(out.size()) > 1 else 1
			out = out.view(B, -1)
			if self._is_dense:
				out = out.float()
			outs.append(out)
			
			idx += D
		
		return torch.cat(outs, -1)


	def standardize(self, vals):
		return self._dispatch('standardize', vals)


	def unstandardize(self, vals):
		return self._dispatch('unstandardize', vals)


	def expand(self, vals):
		return self._dispatch('expand', vals)


	def compress(self, vals):
		return self._dispatch('compress', vals, use_expanded=True)


	def _sample(self, shape):
		return self._dispatch('_sample', shape=shape)


	def distance(self, x, y, standardize=None, scale=None):
		if standardize is None and self.scales is not None: # specifying scales override intrinsic scales
			standardize = True
		mags = self.measure(x, y, standardize=standardize)
		if scale is None:
			scale = self.scales or torch.ones(mags.shape[-1]).to(mags)
		return (mags @ scale.view(-1, 1)).squeeze(-1)

		diffs = self.difference(x, y, standardize=standardize)
		if self.scales is None:
			return diffs.sum(-1)


	def measure(self, x, y, standardize=None):
		return self._dispatch('measure', x, y, standardize=standardize)


	def difference(self, x, y, standardize=None):
		return self._dispatch('difference', x, y, standardize=standardize)


	def __getitem__(self, item):
		return self.dims[item]





