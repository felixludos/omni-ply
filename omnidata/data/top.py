# from ..persistent import Fingerprinted
from ..parameters import hparam, with_hparams, Parameterized
from ..tools import Industrial, material, machine, space

from .abstract import AbstractBatchable
from .routers import DataCollection, AutoCollection, BranchedDataRouter, AliasedCollection, CountableDataRouter
from .views import IndexView
from .sources import Splitable, TensorSource, SpacedSource, BuildableData
from .progression import SetProgression, StreamProgression
# from .materials import Materialed
from .batches import Batchable, Epochable



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

















