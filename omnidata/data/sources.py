from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable

from collections import OrderedDict
from omnibelt import unspecified_argument, get_printer

import math
import torch

from ..structure import Generator
from ..features import Seeded
from .abstract import AbstractDataRouter, AbstractDataSource, AbstractSelector, AbstractBatchable
from .views import IndexView, BatchBase

prt = get_printer(__file__)


class Shufflable(Seeded):
	@staticmethod
	def _is_big_number(N):
		return N > 10000000

	def _shuffle_indices(self, N, gen=None):
		if gen is None:
			gen = self.gen
		# TODO: include a warning if cls._is_big_number(N)
		return torch.randint(N, size=(N,), generator=gen) \
			if self._is_big_number(N) else torch.randperm(N, generator=gen)



class BatchableSource(AbstractBatchable):
	Batch = BatchBase
	@classmethod
	def _parse_selection(cls, source):
		if isinstance(source, AbstractSelector):
			return source
		if isinstance(source, int):
			return cls.Batch(size=source)
		if isinstance(source, Iterable):
			return cls.Batch(indices=source)
		raise NotImplementedError(source)




class CountableSource(AbstractDataSource):
	class _SizeError(ValueError):
		def __init__(self, msg=None):
			if msg is None:
				msg = 'Size of data source is not known'
			super().__init__(msg)

	@property
	def size(self):
		raise self._SizeError()



class SpacedSource(AbstractDataSource):
	def __init__(self, *, space=None, **kwargs):
		super().__init__(**kwargs)
		self._space = space

	@property
	def space(self):
		return self._space
	@space.setter
	def space(self, space):
		self._space = space



class SingleSource(AbstractDataSource):
	def _get_from(self, source, key):
		return self._get(source)

	@staticmethod
	def _get(source):
		raise NotImplementedError

	pass



class SampleSource(SingleSource, Sampler):

	_sample_key = None
	def _sample(self, shape, gen):
		if sample_key is unspecified_argument:
			sample_key = self._sample_key
		N = shape.numel()
		samples = self.sample_material(sample_key, N, gen=gen)
		return util.split_dim(samples, *shape)




# class SelectorSource(AbstractDataSource, AbstractSelector):
# 	def get(self, key):
# 		return self.get_from(self, key)



# class GenerativeSource(AbstractDataSource, Generator):
# 	def _get_from(self, source, key):
# 		return self.generate(source.size)





class Subsetable(CountableSource, Shufflable):
	@staticmethod
	def _split_indices(indices, cut):
		assert cut != 0
		last = cut < 0
		cut = abs(cut)
		total = len(indices)
		if isinstance(cut, float):
			assert 0 < cut < 1
			cut = int(cut * total)
		part1, part2 = indices[:cut], indices[cut:]
		if last:
			part1, part2 = part2, part1
		return part1, part2
	
	Subset = None # indexed view
	def subset(self, cut=None, *, indices=None, shuffle=False, hard_copy=True, gen=None):
		if not hard_copy:
			raise NotImplementedError # TODO: hard copy
		if indices is None:
			assert cut is not None, 'Either cut or indices must be specified'
			indices, _ = self._split_indices(indices=self._shuffle_indices(self.size, gen=gen) \
				if shuffle else torch.arange(self.size), cut=cut)
		return self.Subset(indices=indices)
	


class Splitable(Subsetable):
	def split(self, splits, shuffle=False, gen=None):
		if gen is None:
			gen = self.gen
		auto_name = isinstance(splits, (list, tuple, set))
		if auto_name:
			named_cuts = [(f'part{i}', r) for i, r in enumerate(splits)]
		else:
			assert isinstance(splits, dict), f'unknown splits: {splits}'
			assert not any(x for x in splits if x is None), 'names of splits cannot be None'
			named_cuts = list(splits.items())
		names, cuts = zip(*sorted(named_cuts, key=lambda nr: (isinstance(nr[1], int), isinstance(nr[1], float),
		                                                      nr[1] is None, nr[0]), reverse=True))

		remaining = self.size
		nums = []
		itr = iter(cuts)
		for cut in itr:
			if isinstance(cut, int):
				nums.append(cut)
				remaining -= cut
			else:
				if isinstance(cut, float):
					ratios = []
					while isinstance(cut, float):
						ratios.append(cut)
						cut = next(itr, 'done')
					if len(cuts):
						rationums = [int(remaining * abs(ratio)) for ratio in ratios]
						nums.extend([int(math.copysign(1, r) * n) for r, n in zip(ratios, rationums)])
						remaining -= sum(rationums)
				if cut is None:
					pieces = len([cut, *itr])
					assert remaining > pieces, f'cant evenly distribute {remaining} samples into {pieces} cuts'
					evennums = [int(remaining // pieces) for _ in range(pieces)]
					nums.extend(evennums)
					remaining -= sum(evennums)

		if remaining > 0:
			nums[-1] += remaining

		indices = self._shuffle_indices(self.size, gen=gen) if shuffle else torch.arange(self.size)

		plan = dict(zip(names, nums))
		parts = {}
		for name in sorted(names):
			num = plan[name]
			part, indices = self._split_indices(indices, num)
			parts[name] = self.subset(indices=part)
		if auto_name:
			return [parts[name] for name, _ in named_cuts]
		return parts



class TensorSource(CountableSource):
	def __init__(self, data=None, **kwargs):
		super().__init__(**kwargs)
		self._data = data

	@property
	def size(self):
		return len(self._data)

	@property
	def data(self):
		return self._data

	@data.setter
	def data(self, data):
		self._data = data

	def _get_from(self, source, key=None):
		return self.data[source.indices]



class MultiModed(Splitable): # TODO
	pass



















