from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable
from collections import OrderedDict
import torch

from ..features import Seeded, Prepared

from .abstract import AbstractView, AbstractRouterView, AbstractBatch, \
	AbstractProgression, AbstractBatchable, AbstractSelector



class RouterViewBase(AbstractRouterView):
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



class IndexView(RouterViewBase, IndexSelector): # -> Subset
	def validate_selection(self, selection: 'AbstractSelector'):
		base = self.indices
		if base is None:
			return selection
		return super().validate_selection(self.compose(selection))



class BatchableView(RouterViewBase, AbstractBatchable):
	def iterate(self, **kwargs):
		if self.Progression is None:
			return self.source.Progression(self, **kwargs)
		return self.Progression(self, **kwargs)



class CachedView(RouterViewBase):
	def __init__(self, source=None, cache_table=None, **kwargs):
		if cache_table is None:
			cache_table = self._CacheTable()
		super().__init__(source=source, **kwargs)
		self._cache_table = cache_table
	
	_CacheTable = OrderedDict
	
	def cached(self):
		yield from self._cache_table.keys()

	def clear_cache(self):
		self._cache_table.clear()

	def __str__(self):
		cached = set(self.cached())
		return f'{self._title()}(' \
		       f'{", ".join((key if key in cached else "{" + key + "}") for key in self.available())})'

	def _get_from(self, source, key=None):
		if key in self._cache_table:
			return self._cache_table[key]
		out = super()._get_from(source, key)
		if out is not None:
			self._cache_table[key] = out
		return out



class BatchBase(AbstractBatch, RouterViewBase):
	def __init__(self, progress=None, *, size=None, **kwargs):
		super().__init__(progress=progress, **kwargs)
		self._progress = progress
		self._size = size

	@property
	def source(self):
		if self._source is None:
			return self.progress.source
		return self._source

	@property
	def progress(self):
		return self._progress

	@property
	def size(self):
		return self._size
	


class IndexBatch(BatchBase, IndexView):
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
	
	
	def compose(self, other: 'IndexBatch') -> 'IndexBatch':
		return self.indices[other.indices]





