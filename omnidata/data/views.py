from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable

import torch

from ..features import Seeded, Prepared

from .abstract import AbstractView, AbstractBatch, AbstractProgression



class ViewBase(AbstractView):
	def __init__(self, source=None, **kwargs):
		super().__init__(source=source, **kwargs)
		self._source = source

	@property
	def source(self):
		return self._source
	# @source.setter
	# def source(self, source):
	# 	self._source = source



class CachedView(ViewBase):
	def cached(self):
		yield from self.source.cached()



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
	


class IndexedBatch(BatchBase):
	def __init__(self, progress=None, *, indices=None, **kwargs):
		super().__init__(progress=progress, indices=indices, **kwargs)
		self._indices = indices
	
	class MissingIndicesError(ValueError):
		pass
	
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
