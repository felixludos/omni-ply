from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable
from collections import OrderedDict
import torch

from ..features import Seeded, Prepared

from .abstract import AbstractView, AbstractBatch, AbstractProgression, AbstractBatchable, AbstractSelector



class ViewBase(AbstractView):
	def __init__(self, source=None, **kwargs):
		super().__init__(source=source, **kwargs)
		self._source = source

	@property
	def source(self):
		return self._source



class IndexSelector(AbstractSelector):
	def __init__(self, *, indices=None, **kwargs):
		super().__init__(**kwargs)
		self._indices = indices
		
	@property
	def indices(self):
		return self._indices
	
	def compose(self, other: 'AbstractSelector') -> 'AbstractSelector':
		return self.indices[other.indices]



class IndexView(ViewBase, IndexSelector): # -> Subset
	def validate_selection(self, selection: 'AbstractSelector'):
		base = self.indices
		if base is None:
			return selection
		return super().validate_selection(self.compose(selection))



class BatchableView(ViewBase, AbstractBatchable):
	def iterate(self, **kwargs):
		if self.Progression is None:
			return self.source.Progression(self, **kwargs)
		return self.Progression(self, **kwargs)



class CachedView(ViewBase):
	def __init__(self, source=source, cache_table=None, **kwargs):
		if cache_table is None:
			cache_table = self._CacheTable()
		super().__init__(source=source, **kwargs)
		self._cache_table = cache_table
	
	_CacheTable = OrderedDict
	
	def cached(self):
		yield from self._cache_table.keys()

	def _get_from(source, key):
		if key in self._cache_table:
			return self._cache_table[key]
		return super()._get_from(source, key)



class BatchBase(AbstractBatch):
	def __init__(self, progress=None, *, size=None, **kwargs):
		super().__init__(**kwargs)
		self._progress = progress
		self._size = size

	@property
	def progress(self):
		return self._progress
	
	@property
	def size(self):
		return self._size
	


class IndexedBatch(BatchBase, IndicesView):
	def __init__(self, progress=None, *, indices=None, **kwargs):
		super().__init__(progress=progress, indices=indices, **kwargs)
		self._indices = indices
	
	class MissingIndicesError(ValueError): pass
	
	@property
	def indices(self):
		if self._indices is None:
			raise self.MissingIndicesError
		return self._indices
	
	@property
	def size(self):
		if self._size is None:
			return len(self.indices)
		return self._size
	
	
	def compose(self, other: 'IndexedBatch') -> 'IndexedBatch':
		return self.indices[other.indices]



class Batch(CachedView, BatchBase):
	pass



