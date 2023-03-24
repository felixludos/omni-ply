from typing import Optional, Type

from omnibelt import unspecified_argument, filter_duplicates

# from ..parameters import hparam, with_hparams, Parameterized
from ..tools.top import Cached, DynamicContext, SeededContext, ScopedContext

from .abstract import AbstractBatchable, AbstractCountableData, AbstractBatch
from .views import ViewBase, SizeSelector, IndexSelector
from .progression import AbstractProgression, StreamProgression, SetProgression



class Batchable(AbstractBatchable):
	# _Batch: Type[AbstractBatch] = None
	_Progression: Type[AbstractProgression] = None


	def iterate(self, batch_size: Optional[int] = unspecified_argument, **kwargs):
		self.prepare()
		if batch_size is not unspecified_argument:
			kwargs['batch_size'] = batch_size
		return self._Progression(**kwargs).set_source(self)



class BatchableView(Batchable, ViewBase):
	def iterate(self, batch_size: Optional[int] = unspecified_argument, **kwargs):
		self.prepare()
		if batch_size is not unspecified_argument:
			kwargs['batch_size'] = batch_size
		if self._Progression is None:
			return self.source._Progression(self, **kwargs).set_source(self)
		return self._Progression(**kwargs).set_source(self)



## top level



class BatchBase(Cached, SizeSelector, ScopedContext, DynamicContext, BatchableView, AbstractBatch):
	def __init__(self, progress: AbstractProgression = None, **kwargs):
		super().__init__(progress=progress, **kwargs)
		self._progress = progress


	def sources(self):
		yield from filter_duplicates((self.source, ), super().sources())


	def set_progress(self, progress: AbstractProgression):
		self._progress = progress


	@property
	def progress(self):
		return self._progress

	# def __init__(self, progress: AbstractProgression = None, **kwargs):
	# 	super().__init__(progress=progress, **kwargs)
	# 	self._progress = progress
	#
	#
	# @property
	# def source(self):
	# 	if self._source is None:
	# 		return self.progress.source
	# 	return self._source
	#
	#
	# @property
	# def progress(self):
	# 	return self._progress


	def __str__(self):
		gizmos = [(gizmo if self.is_cached(gizmo) else '{' + gizmo + '}') for gizmo in self.gizmos()]
		return f'{self.title}({", ".join(gizmos)})'



class IndexBatch(IndexSelector, BatchBase):
	pass
	# def __init__(self, *args, **kwargs):
	# 	super().__init__(*args, **kwargs)
	# 	if self.source is not None:
	# 		self.include(self.source)





# class Batchable(BatchableBase, Parameterized):
# 	_Progression = StreamProgression
#
# 	batch_size = hparam(inherit=True)
#
# 	sample_limit = hparam(inherit=True)
# 	batch_limit = hparam(inherit=True)
#
# 	strict_limit = hparam(False, inherit=True, hidden=True)
# 	strict_batch_size = hparam(False, inherit=True, hidden=True)
#
# 	use_pbar = hparam(False, inherit=True, hidden=True)
# 	pbar_samples = hparam(True, inherit=True, hidden=True)
#
#
# 	@with_hparams
# 	def iterate(self, batch_size, sample_limit=None, batch_limit=None,
# 	            strict_limit=False, strict_batch_size=False,
# 	            use_pbar=False, pbar_samples=True, **kwargs):
# 		return super().iterate(batch_size=batch_size, sample_limit=sample_limit, batch_limit=batch_limit,
# 		                       strict_limit=strict_limit, strict_batch_size=strict_batch_size,
# 		                       use_pbar=use_pbar, pbar_samples=pbar_samples, **kwargs)
#
#
#
# class Epochable(Batchable, AbstractCountableData):
# 	_Progression = SetProgression
#
# 	epoch_limit = hparam(inherit=True)
# 	shuffle_batches = hparam(False, inherit=True, hidden=True)
# 	infinite_iteration = hparam(False, inherit=True, hidden=True)
#
# 	@with_hparams
# 	def iterate(self, batch_size, epochs=None, epoch_limit=None, shuffle=None, shuffle_batches=False,
# 	            infinite_iteration=False, infinite=None, **kwargs):
# 		if epoch_limit is None:
# 			epoch_limit = epochs
# 		if shuffle is None:
# 			shuffle = shuffle_batches
# 		if infinite is None:
# 			infinite = infinite_iteration
# 		return super().iterate(batch_size=batch_size, epochs=epoch_limit, shuffle=shuffle,
# 		                       infinite=infinite, **kwargs)
























