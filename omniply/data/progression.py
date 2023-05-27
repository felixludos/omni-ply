from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable

import math
# import torch

from ..features import Prepared, ProgressBarred
from ..tools.abstract import AbstractScope, AbstractTool, AbstractResource
from ..tools.moguls import BatchMogul, IteratorMogul, SelectionMogul, LimitMogul, \
	EpochStatMogul, SimpleMogul, SeedingMogul

from .abstract import AbstractProgression, AbstractBatch
from .errors import BudgetExceeded, EpochEnd, UnknownSize
from .sources import Shufflable



class ProgressionBase(SimpleMogul, SeedingMogul, AbstractProgression):
	def __init__(self, source: Optional[AbstractTool] = None, **kwargs):
		super().__init__(**kwargs)
		self._source = None
		self._resource = None
		self._current_context = None
		self._sample_count = 0
		self._batch_count = 0
		if source is not None:
			self.set_source(source)


	def done(self) -> bool:
		return False


	def set_source(self, source: AbstractTool):
		self._source = source
		self._resource = self._as_resource(source)
		return self


	@property
	def source(self) -> AbstractTool:
		return self._source


	@property
	def current_batch(self) -> AbstractBatch:
		return self._current_context


	def current_context(self) -> AbstractBatch:
		if self._current_context is None:
			return self.create_batch()
		return self._current_context


	@property
	def sample_count(self) -> int:
		return self._sample_count
	@property
	def batch_count(self) -> int:
		return self._batch_count


	def _validate_context(self, ctx: AbstractBatch) -> AbstractBatch:
		ctx: AbstractBatch = super()._validate_context(ctx)
		self._sample_count += ctx.size
		self._batch_count += 1
		self._current_context = ctx
		ctx.set_progress(self)
		return ctx


	def create_batch(self, size=None) -> AbstractBatch:
		self.prepare()
		return self._create_context(size=size)



class BatchProgression(ProgressionBase):
	def __init__(self, batch_size: Optional[int] = None, **kwargs):
		super().__init__(**kwargs)
		self._batch_size = batch_size


	@property
	def batch_size(self):
		return self._batch_size


	def _create_context(self, *args, size=None, **kwargs):
		if size is None:
			size = self.batch_size
		return super()._create_context(*args, size=size, **kwargs)



class EpochProgression(ProgressionBase, EpochStatMogul):
	def __init__(self, epoch_size: Optional[int] = None, **kwargs):
		super().__init__(**kwargs)
		self._indices = None
		self._order_index = 0
		self._epoch_size = epoch_size

		self._batch_in_epoch = 0
		self._samples_in_epoch = 0


	def set_source(self, source: AbstractTool):
		self._indices = None
		return super().set_source(source)


	def _setup_epoch(self, remaining: Optional['torch.Tensor'] = None):
		self._indices = self._generate_sample_order()
		# TODO: add option to not overlap epochs (e.g. for contrastive learning, to make sure samples in batch are unique)
		if remaining is not None:
			self._indices = torch.cat([remaining, self._indices])
		self._order_index = 0
		self._batch_in_epoch = 0
		self._samples_in_epoch = 0


	_EpochEnd = EpochEnd
	def _reset_epoch(self):
		remaining = None
		if self._indices is not None:
			remaining = self.epoch_size - self._order_index
			remaining = self._indices[self._order_index:self._order_index + remaining]
		self._setup_epoch(remaining)


	def _validate_context(self, ctx: AbstractBatch) -> AbstractBatch:
		ctx = super()._validate_context(ctx)
		self._batch_in_epoch += 1
		self._samples_in_epoch += ctx.size
		return ctx


	def _next_batch_indices(self, size: int) -> 'torch.Tensor':
		remaining = self.epoch_size - self._order_index
		if remaining < size:
			self._reset_epoch()
			return self._next_batch_indices(size)
		indices = self._indices[self._order_index:self._order_index + size]
		self._order_index += size
		return indices


	def _create_context(self, *args, indices: Optional['torch.Tensor'] = None, size: Optional[int] = None, **kwargs):
		if self._indices is None:
			self._setup_epoch()

		if size is None:
			size = self.batch_size
		if indices is None:
			indices = self._next_batch_indices(size)

		return super()._create_context(*args, indices=indices, **kwargs)


	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)
		assert self.batch_size <= self.epoch_size, f'Batch size ({self.batch_size}) must be ' \
		                                           f'less than or equal to epoch size ({self.epoch_size})'


	@property
	def epoch_size(self) -> int:
		if self._epoch_size is None:
			return self.source.size
		return self._epoch_size
	@epoch_size.setter
	def epoch_size(self, epoch_size: int):
		self._epoch_size = epoch_size


	@property
	def batch_in_epoch(self) -> int:
		return self._batch_in_epoch
	@property
	def samples_in_epoch(self) -> int:
		return self._samples_in_epoch


	def _generate_sample_order(self) -> 'torch.Tensor':
		return self.source._validate_selection(torch.arange(self.epoch_size))



class ShuffleProgression(EpochProgression, Shufflable):
	def __init__(self, *, shuffle: Optional[bool] = False, **kwargs):
		super().__init__(**kwargs)
		self._shuffle_batches = shuffle


	def _generate_sample_order(self) -> 'torch.Tensor':
		if self._shuffle_batches:
			return self._shuffle_indices(self.epoch_size)
		return super()._generate_sample_order()



#### top-level classes


class SetProgression(BatchProgression, EpochProgression):
	pass



class StreamProgression(BatchProgression):
	pass














