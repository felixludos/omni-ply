from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable

import math
# import torch

from omniplex.features import Prepared, ProgressBarred
from omniplex.tools.abstract import AbstractScope, AbstractTool, AbstractResource
from omniplex.tools.moguls import BatchMogul, IteratorMogul, SelectionMogul, LimitMogul, \
	BatchBudgetStatMogul, EpochStatMogul, EpochBudgetMogul, SimpleMogul

from omniplex.data.abstract import AbstractProgression, AbstractContext
from omniplex.data.errors import BudgetExceeded, EpochEnd, UnknownSize
from omniplex.data.sources import Shufflable



# class AbstractBudgetProgression(AbstractProgression, BatchBudgetStatMogul):
# 	pass


_inf = float('inf')

class BudgetProgression(BatchProgression, ProgressionBase, BatchBudgetStatMogul):
	def __init__(self, *, sample_limit=None, batch_limit=None,
	             strict_limit=True, strict_batch_size=False, **kwargs):
		super().__init__(**kwargs)
		self._sample_limit = sample_limit
		self._batch_limit = batch_limit

		self._strict_limit = strict_limit
		self._strict_batch_size = strict_batch_size

		self._total_samples = None
		self._total_batches = None


	_BudgetExceeded = BudgetExceeded
	def _validate_context(self, ctx: AbstractContext) -> AbstractContext:
		ctx = super()._validate_context(ctx)
		if self.remaining_samples < 0:
			raise self._BudgetExceeded(f'Exceeded sample budget of {self._total_samples} samples')
		if self.remaining_batches < 0:
			raise self._BudgetExceeded(f'Exceeded batch budget of {self._total_batches} batches')
		return ctx


	def _create_context(self, *args, size=None, **kwargs):
		if size is None:
			size = self._batch_size if self._strict_batch_size else min(self._batch_size, self.remaining_samples)
		return super()._create_context(*args, size=size, **kwargs)


	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)
		self._total_samples, self._total_batches = self.compute_budget(
			samples_per_batch=self.batch_size, strict_batch_size=self._strict_batch_size,
			sample_limit=self._sample_limit, batch_limit=self._batch_limit, strict_limit=self._strict_limit,
		)


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


	def done(self):
		return self.remaining_samples <= 0 or self.remaining_batches <= 0



class InfiniteProgression(EpochProgression):
	def __init__(self, infinite=False, **kwargs):
		super().__init__(**kwargs)
		self._infinite = infinite
		self._completed_epochs = 0


	def _epoch_end(self):
		if self._infinite:
			self._completed_epochs += 1
			self._indices = None
			return self._next_batch_indices(self.batch_size)
		else:
			raise self._EpochEnd


	@property
	def current_epoch(self) -> int:
		return self.completed_epochs + 1


	@property
	def completed_epochs(self) -> int:
		return self._completed_epochs



class EpochBudgetProgression(InfiniteProgression, ShuffleProgression, BudgetProgression,
                             BatchBudgetStatMogul, EpochBudgetMogul):
	def __init__(self, batch_size, *, epochs=None, **kwargs):
		super().__init__(batch_size=batch_size, **kwargs)
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


	def _generate_sample_order(self):
		indices = super()._generate_sample_order()
		if self._strict_limit:
			indices = indices[:self.remaining_samples]
		return indices


	@property
	def full_epochs(self) -> Optional[int]:
		return self._full_epochs


	@property
	def remaining_epochs(self):
		if self._full_epochs is None:
			return _inf
		return self._full_epochs - self.current_epoch



# class BarredProgression(ProgressionBase, ProgressBarred):
# 	def __init__(self, batch_size, *, use_pbar=False, pbar_samples=True, **kwargs):
# 		super().__init__(batch_size=batch_size, **kwargs)
# 		self._use_pbar = use_pbar
# 		self._pbar_samples = pbar_samples
#
#
# 	def _create_pbar(self, *, unit=None, **kwargs):
# 		if unit is None:
# 			unit = 'smpl' if self._pbar_samples else 'batch'
# 		return super()._create_pbar(unit=unit, **kwargs)
#
#
# 	def _prepare(self, *args, **kwargs):
# 		super()._prepare(*args, **kwargs)
# 		if self._use_pbar:
# 			self._create_pbar()
#
#
# 	def _create_batch(self):
# 		pbar = self._pbar
# 		try:
# 			batch = super()._create_batch()
# 		except StopIteration:
# 			if pbar is not None:
# 				pbar.close()
# 			raise
# 		else:
# 			if pbar is not None:
# 				pbar.update(self.batch_size if self._pbar_samples else 1)
# 			return batch
#
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



class StreamProgression(BudgetProgression, BatchProgression):
	pass



class SetProgression(EpochBudgetProgression, EpochProgression):
	pass










