from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable

from omnibelt import unspecified_argument

from ..parameters import hparam, with_hparams, Parameterized

from .abstract import AbstractBatchable, AbstractCountableData, AbstractSelector, AbstractView, AbstractBatch
from .views import ViewBase, SizeSelector, IndexSelector, IndexView
from .progression import AbstractProgression, StreamProgression, SetProgression



class BatchableBase(AbstractBatchable):
	# _Batch = None # should get checked/used by Progression
	_Progression = None

	# @classmethod
	# def _parse_context(cls, source):
	# 	raise NotImplementedError
	# 	if source is None or isinstance(source, AbstractSelector):
	# 		return source
	# 	# if source is None:
	# 	# 	return cls.Batch()
	# 	if isinstance(source, int):
	# 		return cls._Batch(size=source)
	# 	if isinstance(source, Iterable):
	# 		return cls._Batch(indices=source)
	# 	raise NotImplementedError(source)


	def iterate(self, batch_size: Optional[int] = unspecified_argument, **kwargs):
		self.prepare()
		if batch_size is not unspecified_argument:
			kwargs['batch_size'] = batch_size
		return self._Progression(self, **kwargs)



class BatchableView(BatchableBase, ViewBase):
	def iterate(self, batch_size: Optional[int] = unspecified_argument, **kwargs):
		self.prepare()
		if batch_size is not unspecified_argument:
			kwargs['batch_size'] = batch_size
		if self._Progression is None:
			return self.source._Progression(self, **kwargs)
		return self._Progression(self, **kwargs)



class Batchable(BatchableBase, Parameterized):
	_Progression = StreamProgression

	batch_size = hparam(inherit=True)

	sample_limit = hparam(inherit=True)
	batch_limit = hparam(inherit=True)

	strict_limit = hparam(False, inherit=True, hidden=True)
	strict_batch_size = hparam(False, inherit=True, hidden=True)

	use_pbar = hparam(False, inherit=True, hidden=True)
	pbar_samples = hparam(True, inherit=True, hidden=True)

	@with_hparams
	def iterate(self, batch_size, sample_limit=None, batch_limit=None,
	            strict_limit=False, strict_batch_size=False,
	            use_pbar=False, pbar_samples=True, **kwargs):
		return super().iterate(batch_size=batch_size, sample_limit=sample_limit, batch_limit=batch_limit,
		                       strict_limit=strict_limit, strict_batch_size=strict_batch_size,
		                       use_pbar=use_pbar, pbar_samples=pbar_samples, **kwargs)



class Epochable(Batchable, AbstractCountableData):
	_Progression = SetProgression

	epoch_limit = hparam(inherit=True)
	shuffle_batches = hparam(False, inherit=True, hidden=True)
	infinite_iteration = hparam(False, inherit=True, hidden=True)

	@with_hparams
	def iterate(self, batch_size, epochs=None, epoch_limit=None, shuffle=None, shuffle_batches=False,
	            infinite_iteration=False, infinite=None, **kwargs):
		if epoch_limit is None:
			epoch_limit = epochs
		if shuffle is None:
			shuffle = shuffle_batches
		if infinite is None:
			infinite = infinite_iteration
		return super().iterate(batch_size=batch_size, epochs=epoch_limit, shuffle=shuffle,
		                       infinite=infinite, **kwargs)



class BatchBase(Epochable, BatchableView, CachedView, SizeSelector, AbstractBatch):
	def __init__(self, progress: AbstractProgression = None, **kwargs):
		super().__init__(progress=progress, **kwargs)
		self._progress = progress


	@property
	def source(self):
		if self._source is None:
			return self.progress.source
		return self._source


	@property
	def progress(self):
		return self._progress



class IndexBatch(IndexView, BatchBase):
	pass



class StreamBatch(BatchBase):
	pass
Batchable._Batch = StreamBatch


class Batch(IndexBatch):
	pass
Epochable._Batch = Batch
























