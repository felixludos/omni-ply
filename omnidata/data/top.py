# from ..persistent import Fingerprinted
from ..tools import Industrial

from .routers import DataCollection, AutoCollection, AliasedCollection, CountableDataRouter
from .views import IndexView
from .sources import Splitable, TensorSource, SpacedSource, BuildableData
from .batches import Batchable, Epochable, BatchBase, IndexBatch



class StreamBatch(BatchBase):
	pass
Batchable._Batch = StreamBatch



class Batch(IndexBatch):
	pass
Epochable._Batch = Batch



class Buffer(TensorSource, SpacedSource, BuildableData): # TODO: should be epochable
	pass



class _FeaturedDataRouter(AutoCollection, AliasedCollection, Industrial, DataCollection, BuildableData):
	pass



class Datastream(Batchable, _FeaturedDataRouter): # not countable (but batchable)
	pass



class Subset(Epochable, IndexView):
	pass



class Dataset(Splitable, CountableDataRouter, Epochable, _FeaturedDataRouter):
	_Buffer = Buffer
	_Subset = Subset



class SimpleDataset(Dataset):
	_is_ready = True

	def __init__(self, *unnamed_data, **named_data):
		super().__init__()
		self._register_init_data(unnamed_data, named_data)


	def _register_init_data(self, unnamed_data, named_data):
		for i, x in enumerate(unnamed_data):
			self.register_buffer(i, x)
		for k, v in named_data.items():
			self.register_buffer(k, v)

















