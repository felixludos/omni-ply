

from .routers import DataCollection, SimpleDataCollection, BranchedDataRouter, AliasedDataCollection
from .views import IndexView, CachedView, BatchBase, IndexBatch, BatchableView
from .sources import Subsetable, Splitable, TensorSource, SpacedSource
from .progression import TrackedProgression, BarredProgression


class Buffer(TensorSource, SpacedSource):
	pass


# class Generativestream(DataStream):
# 	pass

# ExpectingDataRouter



class Datastream(DataCollection): # not size (but batchable)
	class Progression(BarredProgression):
		class Batch(BatchableView, CachedView, BatchBase):
			pass
	class View(BatchableView):
		pass




class Dataset(Splitable, DataCollection):
	def __init__(self, *, default_len=None, **kwargs):
		super().__init__(**kwargs)
		self._default_len = default_len


	@property
	def size(self):
		if self.is_ready:
			return next(self.materials()).size
		if self._default_len is None:
			raise self._SizeError()
		return self._default_len


	_SimpleMaterial = Buffer
	class Progression(TrackedProgression):
		class Batch(BatchableView, CachedView, IndexBatch):
			pass
	class View(BatchableView, IndexView):
		pass
	Subset = View
















