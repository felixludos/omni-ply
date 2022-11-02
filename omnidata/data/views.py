

from .abstract import AbstractView, AbstractBatch, AbstractProgress



class ViewBase(AbstractView):
	def __init__(self, source=None, **kwargs):
		super().__init__(source=source, **kwargs)
		self._source = source

	@property
	def source(self):
		return self._source
	@source.setter
	def source(self, source):
		self._source = source


	pass



class BatchBase(ViewBase, AbstractBatch):
	def __init__(self, N=None, *, sel=None, progress=None, **kwargs):
		super().__init__(**kwargs)
		self._progress = progress
		self._N = N
		self._sel = sel
	
	@property
	def size(self):
		if self._sel is None:
			return self._N
		return len(self._sel)
	
	class MissingSelectionError(ValueError):
		pass
	
	@property
	def sel(self):
		if self._sel is None:
			raise self.MissingSelectionError
		return self._sel



class ProgressBase(AbstractProgress):
	def __init__(self, source, **kwargs):
		super().__init__(**kwargs)
		self._total_samples = 0
		self._total_batches = 0
	
	pass







