from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable

import math
import torch

from ..features import Prepared, ProgressBarred

from .abstract import AbstractProgression
from .sources import Shufflable


class ProgressionBase(AbstractProgression):
	def __init__(self, source, batch_size, batch_cls=None, **kwargs):
		super().__init__(**kwargs)
		if batch_cls is not None:
			self.Batch = batch_cls
		self._current_batch = None
		self._source = source
		self._batch_size = batch_size
		self._sample_count = 0
		self._batch_count = 0

	@property
	def current_batch(self):
		if self._current_batch is None:
			self._current_batch = self._next_batch()
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
		batch = Batch(progress=self, **kwargs)
		return batch

	def next_batch(self):
		batch = self._next_batch()
		batch = self.source.validate_selector(batch)
		return batch

	def _next_batch(self):
		batch = self._create_batch(size=self.batch_size)
		self.source.validate_selector(batch)
		self._sample_count += batch.size
		self._batch_count += 1
		self._current_batch = batch
		return batch



class BarredProgression(ProgressionBase, ProgressBarred):
	def __init__(self, source, use_pbar=False, pbar_samples=True, **kwargs):
		super().__init__(source=source, **kwargs)
		self._use_pbar = use_pbar
		self._pbar_samples = pbar_samples

	def _create_pbar(self, unit=None, **kwargs):
		if unit is None:
			unit = 'smpl' if self._pbar_samples else 'batch'
		return super()._create_pbar(unit=unit, **kwargs)

	def _next_batch(self):
		if self._use_pbar and self._pbar is None:
			self._create_pbar()
		batch = super()._next_batch()
		if self._pbar is not None:
			self._pbar.update(batch.size if self._pbar_samples else 1)
		return batch

	def set_description(self, desc):
		if self._pbar is not None:
			self._pbar.set_description(desc)



class EpochProgression(ProgressionBase, Prepared):
	def __init__(self, source, *, epoch_size=None, strict_batch_size=True, **kwargs):
		if epoch_size is None:
			epoch_size = source.size
		super().__init__(source, **kwargs)
		self._selections = None
		self._sel_index = 0
		self._epoch_size = epoch_size
		self._strict_batch_size = strict_batch_size

	@property
	def epoch_size(self):
		return self._epoch_size
	@epoch_size.setter
	def epoch_size(self, epoch_size):
		self._epoch_size = epoch_size

	@property
	def done(self):
		return self.remaining_samples <= 0 or self.remaining_batches <= 0

	@property
	def remaining_batches(self) -> Optional[int]:
		return len(self._selections) - self._sel_index

	@property
	def remaining_samples(self) -> Optional[int]:
		if self._strict_batch_size:
			return self.remaining_batches * self.batch_size
		return self.epoch_size - self.sample_count

	def _generate_sample_order(self):
		return torch.arange(self.epoch_size)

	def _generate_selections(self, indices):
		sels = list(indices.split(self.batch_size))
		if self._strict_batch_size and len(sels) and len(sels[-1]) != self.batch_size:
			sels.pop()
		self._selections = sels
		self._sel_index = 0

	def _setup(self):
		self.prepare()
		self._generate_selections(self._generate_sample_order())

	def _create_batch(self, **kwargs):
		Batch = self.source.Batch if self.Batch is None else self.Batch
		return Batch(progress=self, **kwargs)

	def _next_batch(self):
		if self._selections is None:
			self._setup()

		idx = self._sel_index
		if idx >= len(self._selections):
			raise StopIteration
		batch = self._create_batch(indices=self._selections[idx])
		self._sel_index += 1

		self._sample_count += batch.size
		self._batch_count += 1
		self._current_batch = batch
		return batch



class ShuffleProgression(EpochProgression, Shufflable):
	def __init__(self, source, *, shuffle_batches=True, **kwargs):
		super().__init__(source=source, **kwargs)
		self._shuffle_batches = shuffle_batches

	def _generate_sample_order(self):
		if self._shuffle_batches:
			return self._shuffle_indices(self.epoch_size)
		return super()._generate_sample_order()



class InfiniteProgression(EpochProgression):
	def __init__(self, source, infinite=False, **kwargs):
		super().__init__(source=source, **kwargs)
		self._infinite = infinite
		self._completed_epochs = 0


	@property
	def remaining_batches(self) -> Optional[int]:
		if self._infinite:
			return None
		return len(self._selections) - self._sel_index

	@property
	def remaining_samples(self) -> Optional[int]:
		if self._infinite:
			return None
		if self._strict_batch_size:
			return self.remaining_batches * self.batch_size
		return self.epoch_size - self.sample_count


	@property
	def current_epoch(self) -> int:
		return self.completed_epochs + 1

	@property
	def completed_epochs(self) -> int:
		return self._completed_epochs

	class EndLoop(StopIteration):
		pass

	def _new_epoch(self):
		if self._infinite:
			self._completed_epochs += 1
			self._setup()
		raise self.EndLoop

	def _next_batch(self):
		try:
			return super()._next_batch()
		except StopIteration:
			try:
				self._new_epoch()
			except self.EndLoop:
				pass
			else:
				return super()._next_batch()
			raise



class BudgetProgression(InfiniteProgression):
	def __init__(self, source, epochs=None, sample_limit=None, batch_limit=None, strict_limit=True, **kwargs):
		super().__init__(source=source, **kwargs)
		self._epochs = epochs
		self._sample_limit = sample_limit
		self._batch_limit = batch_limit
		self._strict_limit = strict_limit
		self._total_samples = None
		self._total_batches = None
		self._full_epochs = None

	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)
		self._total_samples, self._total_batches, self._full_epochs = self.compute_budget(
			dataset_size=self.epoch_size, samples_per_batch=self.batch_size,
			strict_batch_size=self._strict_batch_size,
			epochs=self._epochs, sample_limit=self._sample_limit,
			batch_limit=self._batch_limit, strict_limit=self._strict_limit
		)

	@staticmethod
	def compute_budget(dataset_size, samples_per_batch, strict_batch_size=True,
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
	def total_samples(self) -> Optional[int]:
		return self._total_samples

	@property
	def total_batches(self) -> Optional[int]:
		return self._total_batches

	@property
	def full_epochs(self) -> Optional[int]:
		return self._full_epochs


	@property
	def remaining_epochs(self):
		if self._full_epochs is None:
			return float('inf')
		return self._full_epochs - self.current_epoch

	@property
	def remaining_samples(self):
		if self._total_samples is None:
			return float('inf')
		return self._total_samples - self.sample_count

	@property
	def remaining_batches(self):
		if self._total_batches is None:
			return float('inf')
		return self._total_batches - self.batch_count


	@property
	def done(self):
		return self.remaining_samples <= 0 or self.remaining_batches <= 0



class TrackedProgression(BudgetProgression, BarredProgression): # TODO: add a progress bar
	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)
		if self._use_pbar:
			self._create_pbar(total=self.total_samples if self._pbar_samples else self.total_batches)


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

















