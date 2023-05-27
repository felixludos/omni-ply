from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set
import math

from ..features import Prepared
from ..tools.moguls import BatchMogul, EpochStatMogul, SeedingMogul, SimpleMogul
from ..parameters import hparam, Parameterized

from .abstract import AbstractProgression, AbstractBatchable, AbstractBatch
from .errors import BudgetExceeded
from .progression import ProgressionBase



_inf = float('inf')


class BudgetLoader(Parameterized, SeedingMogul, SimpleMogul, AbstractProgression):
	batch_size = hparam(required=True)

	sample_limit = hparam(None)
	batch_limit = hparam(None)
	@hparam
	def epoch_limit(self):
		if self.epoch_size is not None and self.sample_limit is None and self.batch_limit is None:
			if self.strict_limit is None:
				self.strict_limit = True
			return 1


	strict_limit = hparam(None, hidden=True)
	strict_batch_size = hparam(None, hidden=True)

	shuffle = hparam(False, hidden=True)
	@hparam
	def infinite(self): # TODO: deal with circular hparam dependencies
		return self.sample_limit is None and self.batch_limit is None and self.epoch_limit is None

	# use_pbar = hparam(False, inherit=True, hidden=True) # TODO
	# pbar_samples = hparam(True, inherit=True, hidden=True)


	@hparam
	def epoch_size(self):
		src = self.source
		if src is not None:
			try:
				return src.size
			except AttributeError:
				pass


	def __init__(self, source: AbstractBatchable = None, **kwargs):
		super().__init__(**kwargs)
		self._loader = None
		self._full_epochs = None
		self._total_samples = None
		self._total_batches = None
		if source is not None:
			self.set_source(source)


	def set_source(self, source: AbstractBatchable, **kwargs):
		if isinstance(source, AbstractProgression):
			source = source.source
		self._loader = source.iterate(self.batch_size, **kwargs)
		self._is_ready = False
		self.prepare()
		return self


	@property
	def source(self) -> AbstractBatchable:
		return self._loader.source


	# def sources(self) -> Iterator['AbstractBatchable']:
	# 	yield self.source


	@property
	def current_batch(self) -> AbstractBatch:
		return self._loader.current_batch


	_BudgetExceeded = BudgetExceeded

	def create_batch(self, size: Optional[int] = None) -> AbstractBatch:
		if self.done():
			raise self._BudgetExceeded
		if size is None:
			size = self.batch_size
		if self.remaining_samples is not None:
			size = min(size, self.remaining_samples)
		ctx = self._loader.create_batch(size)
		ctx.set_progress(self)
		return ctx


	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)

		if not self.infinite:
			if self.epoch_size is None:
				self._total_samples, self._total_batches = self.compute_budget(
					samples_per_batch=self.batch_size, strict_batch_size=self.strict_batch_size,
					sample_limit=self.sample_limit, batch_limit=self.batch_limit, strict_limit=self.strict_limit,
				)
			else:
				self._total_samples, self._total_batches, self._full_epochs = self.compute_epoch_budget(
					dataset_size=self.epoch_size, samples_per_batch=self.batch_size,
					strict_batch_size=self.strict_batch_size,
					epochs=self.epoch_limit, sample_limit=self.sample_limit,
					batch_limit=self.batch_limit, strict_limit=self.strict_limit
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

			remainder = sample_limit % samples_per_batch
			total = sample_limit - remainder
			if remainder > 0:
				if strict_limit and not strict_batch_size:
					total += remainder
				elif not strict_limit:
					total += samples_per_batch

			# total = sample_limit - (sample_limit % samples_per_batch)
			# remainder = sample_limit % samples_per_batch
			# if remainder > 0:
			# 	if strict_limit and not strict_batch_size:
			# 		total += remainder
			# 	elif not strict_limit:
			# 		total += samples_per_batch
			if total_samples is None or total < total_samples:
				total_samples = total

		total_batches = total_samples // samples_per_batch
		remainder = total_samples % samples_per_batch
		if not strict_batch_size and remainder > 0:
			total_batches += 1

		return total_samples, total_batches


	@staticmethod
	def compute_epoch_budget(dataset_size, samples_per_batch, strict_batch_size=True,
	                   epochs=None, sample_limit=None, batch_limit=None, strict_limit=True):
		if epochs is None and sample_limit is None and batch_limit is None:
			return None, None, None  # infinite

		strict_limit = bool(strict_limit)
		strict_batch_size = bool(strict_batch_size)

		samples_per_epoch = dataset_size - int(strict_batch_size) * (dataset_size % samples_per_batch)
		batches_per_epoch = int(math.ceil(samples_per_epoch / samples_per_batch))

		total_samples = None if epochs is None else samples_per_epoch * epochs
		if batch_limit is not None:
			total = (batch_limit % batches_per_epoch) * samples_per_batch \
			        + (batch_limit // batches_per_epoch) * samples_per_epoch
			if total_samples is None or total < total_samples:
				total_samples = total
		if sample_limit is not None:
			remainder = sample_limit % samples_per_batch
			total = sample_limit - remainder
			if remainder > 0:
				if strict_limit and not strict_batch_size:
					total += remainder
				elif not strict_limit:
					total += samples_per_batch
			# total = samples_per_epoch * (sample_limit // samples_per_epoch)
			# remainder = sample_limit % samples_per_epoch
			# total += samples_per_batch * (remainder // samples_per_batch)
			# remainder = remainder % samples_per_batch
			# if remainder > 0:
			# 	if strict_limit and not strict_batch_size:
			# 		total += remainder
			# 	elif not strict_limit:
			# 		total += samples_per_batch
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
	def sample_count(self) -> int:
		return self._loader.sample_count
	@property
	def batch_count(self) -> int:
		return self._loader.batch_count


	@property
	def budget_samples(self) -> Optional[int]:
		return self._total_samples
	@property
	def budget_batches(self) -> Optional[int]:
		return self._total_batches


	@property
	def full_epochs(self) -> Optional[int]:
		return self._full_epochs
	@property
	def completed_epochs(self) -> int:
		if self.epoch_size is not None:
			return self.sample_count // self.epoch_size


	@property
	def current_epoch(self) -> int:
		if self.epoch_size is not None:
			return self.completed_epochs + 1


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
	def remaining_epochs(self): # only lists full epochs
		if self.epoch_size is not None:
			if self._full_epochs is None:
				return _inf
			return self._full_epochs - self.completed_epochs
	@property
	def remaining_samples_in_epoch(self):
		if self.epoch_size is not None:
			return self.epoch_size - self.sample_count % self.epoch_size
	@property
	def remaining_batches_in_epoch(self): # only lists full batches
		if self.epoch_size is not None:
			return self.remaining_samples_in_epoch // self.batch_size


	def done(self) -> bool:
		todo = self.remaining_samples
		return todo is None or todo <= 0























#
# _inf = float('inf')
#
# class BudgetProgressionBase(AbstractProgression):
# 	def __init__(self, *, sample_limit=None, batch_limit=None, strict_limit=True, strict_batch_size=False, **kwargs):
# 		super().__init__(**kwargs)
# 		self._sample_limit = sample_limit
# 		self._batch_limit = batch_limit
#
# 		self._strict_limit = strict_limit
# 		self._strict_batch_size = strict_batch_size
#
# 		self._total_samples = None
# 		self._total_batches = None
#
#
# 	def _prepare(self, *args, **kwargs):
# 		super()._prepare(*args, **kwargs)
# 		self._total_samples, self._total_batches = self.compute_budget(
# 			samples_per_batch=self.batch_size, strict_batch_size=self._strict_batch_size,
# 			sample_limit=self._sample_limit, batch_limit=self._batch_limit, strict_limit=self._strict_limit,
# 		)
#
#
# 	@staticmethod
# 	def compute_budget(samples_per_batch, strict_batch_size=False,
# 	                   sample_limit=None, batch_limit=None, strict_limit=True):
# 		if sample_limit is None and batch_limit is None:
# 			return None, None  # infinite
#
# 		total_samples = None
# 		if batch_limit is not None:
# 			total_samples = batch_limit * samples_per_batch
# 		if sample_limit is not None:
# 			total = sample_limit - (sample_limit % samples_per_batch)
# 			remainder = sample_limit % samples_per_batch
# 			if remainder > 0:
# 				if strict_limit and not strict_batch_size:
# 					total += remainder
# 				elif not strict_limit:
# 					total += samples_per_batch
# 			if total_samples is None or total < total_samples:
# 				total_samples = total
#
# 		total_batches = total_samples // samples_per_batch
# 		remainder = total_samples % samples_per_batch
# 		if not strict_batch_size and remainder > 0:
# 			total_batches += 1
#
# 		return total_samples, total_batches
#
#
# 	@property
# 	def budget_samples(self) -> Optional[int]:
# 		return self._total_samples
# 	@property
# 	def budget_batches(self) -> Optional[int]:
# 		return self._total_batches
#
#
# 	@property
# 	def remaining_samples(self):
# 		if self._total_samples is None:
# 			return _inf
# 		return self._total_samples - self.sample_count
# 	@property
# 	def remaining_batches(self):
# 		if self._total_batches is None:
# 			return _inf
# 		return self._total_batches - self.batch_count
#
#
#
# class EpochBudgetProgressionBase(BudgetProgressionBase, EpochStatMogul):
# 	def __init__(self, *, epoch_limit=None, **kwargs):
# 		super().__init__(**kwargs)
# 		self._epoch_limit = epoch_limit
# 		self._full_epochs = None
#
#
# 	def _prepare(self, *args, **kwargs):
# 		super()._prepare(*args, **kwargs)
#
# 		if self._epoch_limit is None \
# 				and self._sample_limit is None \
# 				and self._batch_limit is None:
# 			self._epochs = 1
#
# 		self._total_samples, self._total_batches, self._full_epochs = self.compute_epoch_budget(
# 			dataset_size=self.epoch_size, samples_per_batch=self.batch_size,
# 			strict_batch_size=self._strict_batch_size,
# 			epochs=self._epochs, sample_limit=self._sample_limit,
# 			batch_limit=self._batch_limit, strict_limit=self._strict_limit
# 		)
#
#
# 	@staticmethod
# 	def compute_epoch_budget(dataset_size, samples_per_batch, strict_batch_size=True,
# 	                   epochs=None, sample_limit=None, batch_limit=None, strict_limit=True):
# 		if epochs is None and sample_limit is None and batch_limit is None:
# 			return None, None, None  # infinite
#
# 		samples_per_epoch = dataset_size - int(strict_batch_size) * (dataset_size % samples_per_batch)
# 		batches_per_epoch = int(math.ceil(samples_per_epoch / samples_per_batch))
#
# 		total_samples = None if epochs is None else samples_per_epoch * epochs
# 		if batch_limit is not None:
# 			total = (batch_limit % batches_per_epoch) * samples_per_batch \
# 			        + (batch_limit // batches_per_epoch) * samples_per_epoch
# 			if total_samples is None or total < total_samples:
# 				total_samples = total
# 		if sample_limit is not None:
# 			total = samples_per_epoch * (sample_limit // samples_per_epoch)
# 			remainder = sample_limit % samples_per_epoch
# 			total += samples_per_batch * (remainder // samples_per_batch)
# 			remainder = remainder % samples_per_batch
# 			if remainder > 0:
# 				if strict_limit and not strict_batch_size:
# 					total += remainder
# 				elif not strict_limit:
# 					total += samples_per_batch
# 			if total_samples is None or total < total_samples:
# 				total_samples = total
#
# 		full_epochs = total_samples // samples_per_epoch
# 		remainder = total_samples % samples_per_epoch
# 		total_batches = full_epochs * batches_per_epoch + remainder // samples_per_batch
# 		remainder = remainder % samples_per_batch
# 		if not strict_batch_size and remainder > 0:
# 			total_batches += 1
#
# 		return total_samples, total_batches, full_epochs
#
#
# 	@property
# 	def full_epochs(self) -> Optional[int]:
# 		return self._full_epochs
#
#
# 	@property
# 	def remaining_epochs(self):
# 		if self._full_epochs is None:
# 			return float('inf')
# 		return self._full_epochs - self.current_epoch





# class BarredProgression(ProgressionBase, ProgressBarred):
# 	def __init__(self, source, use_pbar=False, pbar_samples=True, **kwargs):
# 		super().__init__(source=source, **kwargs)
# 		self._use_pbar = use_pbar
# 		self._pbar_samples = pbar_samples
#
# 	def _create_pbar(self, *, unit=None, **kwargs):
# 		if unit is None:
# 			unit = 'smpl' if self._pbar_samples else 'batch'
# 		return super()._create_pbar(unit=unit, **kwargs)
#
# 	def _prepare(self, *args, **kwargs):
# 		super()._prepare(*args, **kwargs)
# 		if self._use_pbar:
# 			self._create_pbar()
#
# 	def _next_batch(self):
# 		pbar = self._pbar
# 		try:
# 			batch = super()._next_batch()
# 		except StopIteration:
# 			if pbar is not None:
# 				pbar.close()
# 			raise
# 		else:
# 			if pbar is not None:
# 				pbar.update(self.batch_size if self._pbar_samples else 1)
# 			return batch
#
# 	def set_description(self, desc):
# 		if self._pbar is not None:
# 			self._pbar.set_description(desc)
#
#
#
# class TrackedProgression(BarredProgression, AbstractBudgetProgression): # TODO: add a progress bar
# 	def _create_pbar(self, total=None, **kwargs):
# 		if total is None:
# 			total = self.budget_samples if self._pbar_samples else self.budget_batches
# 		return super()._create_pbar(total=total, **kwargs)

























