
# from ..persistent import Fingerprinted

from .routers import DataCollection, AutoCollection, BranchedDataRouter, AliasedCollection, CountableDataRouter
from .views import IndexView, CachedView, BatchBase, IndexBatch, BatchableView
from .sources import Splitable, TensorSource, SpacedSource, BatchableSource, BuildableData
from .progression import TrackedProgression, BarredProgression
from .materials import Materialed


class Batch(BatchableView, CachedView, IndexBatch):
	pass


class Buffer(TensorSource, SpacedSource, BatchableSource, BuildableData):
	Batch = Batch


class _FeaturedDataRouter(AutoCollection, AliasedCollection, BatchableSource,
                          Materialed, DataCollection, BuildableData):
	_SimpleMaterial = Buffer



class Datastream(_FeaturedDataRouter): # not countable (but batchable)
	Progression = BarredProgression
	class Material(_FeaturedDataRouter.Material):
		pass
	class Batch(BatchableView, CachedView, BatchBase):
		pass
	class View(BatchableView):
		pass



class Dataset(Splitable, CountableDataRouter, _FeaturedDataRouter):
	Batch = Batch
	Progression = TrackedProgression
	class Material(_FeaturedDataRouter.Material):
		pass
	class View(BatchableView, IndexView):
		pass
	Subset = View



class SimpleDataset(Dataset): # TODO: test with ints as keys
	_is_ready = True

	def __init__(self, *unnamed_data, **named_data):
		super().__init__()
		self._register_init_data(unnamed_data, named_data)

	def _register_init_data(self, unnamed_data, named_data):
		for i, x in enumerate(unnamed_data):
			self.register_material(i, x)
		for k, v in named_data.items():
			self.register_material(k, v)

















