from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable
from collections import OrderedDict
# import torch

from ..features import Seeded, Prepared
from ..tools.abstract import AbstractScope
from ..tools.context import SizedContext, Cached

from .abstract import AbstractView, AbstractRouterView, AbstractBatch, AbstractDataRouter, AbstractIndexedData, \
	AbstractProgression, AbstractBatchable, AbstractSelector, AbstractCountableData, AbstractCountableRouterView



class ViewBase(AbstractView):
	def __init__(self, source: AbstractDataRouter = None, **kwargs):
		super().__init__(source=source, **kwargs)
		self._source = source


	@property
	def source(self):
		return self._source



class RouterViewBase(ViewBase, AbstractRouterView):
	pass



class SizeSelector(SizedContext, RouterViewBase, AbstractSelector, AbstractCountableData):
	def compose(self, other: AbstractSelector) -> AbstractSelector:
		if isinstance(other, SizeSelector):
			self._size = min(self._size, other._size)
		return self



class SingleIndexSelector(SizeSelector):
	def __init__(self, index: int, **kwargs):
		super().__init__(size=1, **kwargs)
		self._index = index


	@property
	def index(self):
		return self._index


	@property
	def size(self):
		return 1



class IndexView(RouterViewBase, AbstractIndexedData):
	def __init__(self, indices, **kwargs):
		super().__init__(indices=indices, **kwargs)
		self._indices = indices


	@property
	def indices(self):
		return self._indices


# print()
# print('\n'.join(map(str, IndexView.mro())))
# print()
# print('\n'.join(map(str, SizeSelector.mro())))
class IndexSelector(IndexView, SizeSelector):
	def compose(self, other: AbstractSelector) -> AbstractSelector:
		# TODO: check case where other is just the indices directly
		if isinstance(other, IndexSelector) and other.indices is not None:
			self._indices = other.indices[self.indices]
		return self


	@property
	def size(self):
		if self._size is None:
			return len(self.indices)
		return self._size

# class IndexView(IndexSelector, AbstractCountableRouterView): # -> Subset
# 	def validate_context(self, selection: 'AbstractSelector'):
# 		return super().validate_context(selection.compose(self))



# class CachedView(AbstractRouterView):
# 	def __init__(self, source=None, cache_table=None, **kwargs):
# 		if cache_table is None:
# 			cache_table = self._CacheTable()
# 		super().__init__(source=source, **kwargs)
# 		self._cache_table = cache_table
#
# 	_CacheTable = OrderedDict
#
# 	def cached(self):
# 		yield from self._cache_table.keys()
#
# 	def clear_cache(self):
# 		self._cache_table.clear()
#
# 	def __str__(self):
# 		cached = set(self.cached())
# 		return f'{self._title()}(' \
# 		       f'{", ".join((key if key in cached else "{" + key + "}") for key in self.available_buffers())})'
#
# 	def _get_from(self, source, key=None):
# 		if key not in self._cache_table:
# 			out = super()._get_from(self, key)
# 			self._cache_table[key] = out
# 		if source is None or source is self:
# 			return self._cache_table[key]
# 		return self._cache_table[key][source.indices]




# class MissingIndicesError(ValueError): pass

# @property
# def indices(self):
# 	if self._indices is None:
# 		raise self.MissingIndicesError
# 	return self._indices
#
# @property
# def size(self):
# 	if self._size is None:
# 		return len(self.indices)
# 	return self._size

# def compose(self, other: 'IndexBatch') -> 'IndexBatch':
# 	return self.indices[other.indices]





