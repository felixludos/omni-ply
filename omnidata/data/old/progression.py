from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable

import math
import torch

from ..features import Prepared, ProgressBarred

from .abstract import AbstractProgression
from .sources import Shufflable


class AbstractBudgetProgression(AbstractProgression):
	@property
	def budget_samples(self) -> Optional[int]:
		raise NotImplementedError

	@property
	def budget_batches(self) -> Optional[int]:
		raise NotImplementedError

	@property
	def remaining_samples(self):
		raise NotImplementedError

	@property
	def remaining_batches(self):
		raise NotImplementedError



class ProgressionBase(AbstractProgression, Prepared):
	def __init__(self, source, batch_size, batch_cls=None, **kwargs):
		super().__init__(**kwargs)
		if batch_cls is not None:
			self.Batch = batch_cls
		self._current_batch = None
		self._source = source
		self._batch_size = batch_size
		self._sample_count = 0
		self._batch_count = 0

	def get_batch(self):
		if self._current_batch is None:
			return self.next_batch()
		return self._current_batch

	@property
	def current_batch(self):
		return self._current_batch

	@property
	def batch_size(self):
		return self._batch_size
	@batch_size.setter
	def batch_size(self, batch_size):
		self._batch_size = batch_size

	@property
	def source(self):
		return self._source

	def done(self):
		return False

	@property
	def sample_count(self) -> int:
		return self._sample_count
	@property
	def batch_count(self) -> int:
		return self._batch_count

	Batch = None
	def _create_batch(self, **kwargs):
		Batch = self.source.Batch if self.Batch is None else self.Batch
		return Batch(progress=self, **kwargs)

	def next_batch(self):
		self.prepare()
		batch = self._next_batch()
		batch = self.source.validate_context(batch)
		self._sample_count += batch.size
		self._batch_count += 1
		self._current_batch = batch
		return batch

	def _next_batch(self):
		return self._create_batch(size=self._batch_size)



_inf = float('inf')

class BudgetProgression(ProgressionBase, AbstractBudgetProgression):
	def __init__(self, source, batch_size, *, sample_limit=None, batch_limit=None,
	             strict_limit=True, strict_batch_size=False, **kwargs):
		super().__init__(source=source, batch_size=batch_size, **kwargs)
		self._sample_limit = sample_limit
		self._batch_limit = batch_limit

		self._strict_limit = strict_limit
		self._strict_batch_size = strict_batch_size

		self._total_samples = None
		self._total_batches = None

	def _next_batch(self):
		if self.done:
			raise StopIteration
		size = self._batch_size if self._strict_batch_size else min(self._batch_size, self.remaining_samples)
		return self._create_batch(size=size)

	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)
		self._total_samples, self._total_batches = self.compute_budget(
			samples_per_batch=self.batch_size, strict_batch_size=self._strict_batch_size,
			sample_limit=self._sample_limit, batch_limit=self._batch_limit, strict_limit=self._strict_limit,
		)

	@staticmethod
	def compute_budget(samples_per_batch, strict_batch_size=False,
	                   sample_limit=None, batch_limit=None, strict_limit=True):
		if sample_limit is None and batch_limit is None:
			return None, None  # infinite

		total_samples = None
		if batch_limit is not None:
			total_samples = batch_limit * samples_per_batch
		if sample_limit is not None:
			total = sample_limit - (sample_limit % samples_per_batch)
			remainder = sample_limit % samples_per_batch
			if remainder > 0:
				if strict_limit and not strict_batch_size:
					total += remainder
				elif not strict_limit:
					total += samples_per_batch
			if total_samples is None or total < total_samples:
				total_samples = total

		total_batches = total_samples // samples_per_batch
		remainder = total_samples % samples_per_batch
		if not strict_batch_size and remainder > 0:
			total_batches += 1

		return total_samples, total_batches

	@property
	def budget_samples(self) -> Optional[int]:
		return self._total_samples

	@property
	def budget_batches(self) -> Optional[int]:
		return self._total_batches

	@property
	def remaining_samples(self):
		if self._total_samples is None:
			return _inf
		return self._total_samples - self.sample_count

	@property
	def remaining_batches(self):
		if self._total_batches is None:
			return _inf
		return self._total_batches - self.batch_count

	@property
	def done(self):
		return self.remaining_samples <= 0 or self.remaining_batches <= 0


class EpochProgression(ProgressionBase):
	def __init__(self, source, batch_size, *, epoch_size=None, strict_batch_size=False, **kwargs):
		if epoch_size is None:
			epoch_size = source.size
		super().__init__(source=source, batch_size=batch_size, **kwargs)
		self._selections = None
		self._sel_index = 0
		self._epoch_size = epoch_size
		self._strict_batch_size = strict_batch_size

	def _epoch_end(self):
		raise StopIteration

	def _next_batch(self):
		if self._selections is None:
			self._setup_epoch()

		if self._sel_index >= len(self._selections):
			self._epoch_end()

		batch = self._create_batch(indices=self._selections[self._sel_index])
		self._sel_index += 1
		return batch

	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)
		assert self.batch_size <= self.epoch_size, f'Batch size ({self.batch_size}) must be ' \
		                                           f'less than or equal to epoch size ({self.epoch_size})'

	@property
	def epoch_size(self):
		return self._epoch_size
	@epoch_size.setter
	def epoch_size(self, epoch_size):
		self._epoch_size = epoch_size

	def _generate_sample_order(self):
		return torch.arange(self.epoch_size)

	def _generate_selections(self, indices):
		sels = list(indices.split(self.batch_size))
		if self._strict_batch_size and len(sels) and len(sels[-1]) != self.batch_size:
			sels.pop()
		return sels

	def _setup_epoch(self):
		self._selections = self._generate_selections(self._generate_sample_order())
		self._sel_index = 0

	# @property
	# def remaining_batches_in_epoch(self) -> Optional[int]:
	# 	return len(self._selections) - self._sel_index
	#
	# @property
	# def remaining_samples_in_epoch(self) -> Optional[int]:
	# 	if self._strict_batch_size:
	# 		return self.remaining_samples_in_epoch * self.batch_size
	# 	return self.epoch_size - self.sample_count



class ShuffleProgression(EpochProgression, Shufflable):
	def __init__(self, source, batch_size, *, shuffle=False, **kwargs):
		super().__init__(source=source, batch_size=batch_size, **kwargs)
		self._shuffle_batches = shuffle

	def _generate_sample_order(self):
		if self._shuffle_batches:
			return self._shuffle_indices(self.epoch_size)
		return super()._generate_sample_order()



class InfiniteProgression(EpochProgression):
	def __init__(self, source, batch_size, infinite=False, **kwargs):
		super().__init__(source=source, batch_size=batch_size, **kwargs)
		self._infinite = infinite
		self._completed_epochs = 0

	def _epoch_end(self):
		if self._infinite:
			self._completed_epochs += 1
			self._setup_epoch()
		else:
			raise StopIteration

	# @property
	# def remaining_batches_in_epoch(self) -> Optional[int]:
	# 	if self._infinite:
	# 		return None
	# 	return len(self._selections) - self._sel_index
	#
	# @property
	# def remaining_samples_in_epoch(self) -> Optional[int]:
	# 	if self._infinite:
	# 		return None
	# 	if self._strict_batch_size:
	# 		return self.remaining_batches_in_epoch * self.batch_size
	# 	return self.epoch_size - self.sample_count


	@property
	def current_epoch(self) -> int:
		return self.completed_epochs + 1

	@property
	def completed_epochs(self) -> int:
		return self._completed_epochs



class EpochBudgetProgression(InfiniteProgression, ShuffleProgression, BudgetProgression, AbstractBudgetProgression):
	def __init__(self, source, batch_size, *, epochs=None, **kwargs):
		super().__init__(source=source, batch_size=batch_size, **kwargs)
		self._epochs = epochs
		self._full_epochs = None

	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)

		if self._epochs is None \
				and self._sample_limit is None \
				and self._batch_limit is None \
				and not self._infinite:
			self._epochs = 1

		self._total_samples, self._total_batches, self._full_epochs = self.compute_epoch_budget(
			dataset_size=self.epoch_size, samples_per_batch=self.batch_size,
			strict_batch_size=self._strict_batch_size,
			epochs=self._epochs, sample_limit=self._sample_limit,
			batch_limit=self._batch_limit, strict_limit=self._strict_limit
		)

	def _epoch_end(self):
		self._completed_epochs += 1
		self._setup_epoch()

	def _next_batch(self):
		if self.done:
			raise StopIteration
		return super()._next_batch()

	def _generate_selections(self, indices):
		sels = super()._generate_selections(indices)
		if self._strict_limit and self.remaining_samples < self.batch_size:
			sels[0] = sels[0][:self.remaining_samples]
			sels = sels[:1]
		return sels

	@staticmethod
	def compute_epoch_budget(dataset_size, samples_per_batch, strict_batch_size=True,
	                   epochs=None, sample_limit=None, batch_limit=None, strict_limit=True):
		if epochs is None and sample_limit is None and batch_limit is None:
			return None, None, None  # infinite

		samples_per_epoch = dataset_size - int(strict_batch_size) * (dataset_size % samples_per_batch)
		batches_per_epoch = int(math.ceil(samples_per_epoch / samples_per_batch))

		total_samples = None if epochs is None else samples_per_epoch * epochs
		if batch_limit is not None:
			total = (batch_limit % batches_per_epoch) * samples_per_batch \
			        + (batch_limit // batches_per_epoch) * samples_per_epoch
			if total_samples is None or total < total_samples:
				total_samples = total
		if sample_limit is not None:
			total = samples_per_epoch * (sample_limit // samples_per_epoch)
			remainder = sample_limit % samples_per_epoch
			total += samples_per_batch * (remainder // samples_per_batch)
			remainder = remainder % samples_per_batch
			if remainder > 0:
				if strict_limit and not strict_batch_size:
					total += remainder
				elif not strict_limit:
					total += samples_per_batch
			if total_samples is None or total < total_samples:
				total_samples = total

		full_epochs = total_samples // samples_per_epoch
		remainder = total_samples % samples_per_epoch
		total_batches = full_epochs * batches_per_epoch + remainder // samples_per_batch
		remainder = remainder % samples_per_batch
		if not strict_batch_size and remainder > 0:
			total_batches += 1

		return total_samples, total_batches, full_epochs


	@property
	def full_epochs(self) -> Optional[int]:
		return self._full_epochs


	@property
	def remaining_epochs(self):
		if self._full_epochs is None:
			return float('inf')
		return self._full_epochs - self.current_epoch



class BarredProgression(ProgressionBase, ProgressBarred):
	def __init__(self, source, use_pbar=False, pbar_samples=True, **kwargs):
		super().__init__(source=source, **kwargs)
		self._use_pbar = use_pbar
		self._pbar_samples = pbar_samples

	def _create_pbar(self, *, unit=None, **kwargs):
		if unit is None:
			unit = 'smpl' if self._pbar_samples else 'batch'
		return super()._create_pbar(unit=unit, **kwargs)

	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)
		if self._use_pbar:
			self._create_pbar()

	def _next_batch(self):
		pbar = self._pbar
		try:
			batch = super()._next_batch()
		except StopIteration:
			if pbar is not None:
				pbar.close()
			raise
		else:
			if pbar is not None:
				pbar.update(self.batch_size if self._pbar_samples else 1)
			return batch

	def set_description(self, desc):
		if self._pbar is not None:
			self._pbar.set_description(desc)



class TrackedProgression(BarredProgression, AbstractBudgetProgression): # TODO: add a progress bar
	def _create_pbar(self, total=None, **kwargs):
		if total is None:
			total = self.budget_samples if self._pbar_samples else self.budget_batches
		return super()._create_pbar(total=total, **kwargs)



class StreamProgression(TrackedProgression, BudgetProgression):
	pass



class SetProgression(TrackedProgression, EpochBudgetProgression):
	pass










