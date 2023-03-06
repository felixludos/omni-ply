from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set
import math
# from ..persistent import Fingerprinted
from ..tools import Industrial
from ..parameters import Parameterized, hparam

from .routers import DataCollection, AutoCollection, AliasedCollection, CountableDataRouter
from .views import IndexView
from .sources import Splitable, TensorSource, SpacedSource#, BuildableData
from .progression import SetProgression, StreamProgression, AbstractProgression
from .budgeting import BudgetLoader
from .batches import Batchable, BatchBase, IndexBatch



class Bunch(BatchBase):
	pass
StreamProgression._Context = Bunch



class Batch(IndexBatch):
	pass
SetProgression._Context = Batch



class Buffer(Batchable, TensorSource, SpacedSource, Parameterized):#, BuildableData): # TODO: should be epochable
	_Progression = SetProgression
	pass



class _FeaturedDataRouter(Batchable, AutoCollection, AliasedCollection, Industrial, DataCollection, Parameterized):
	#, BuildableData):
	pass



class Datastream(_FeaturedDataRouter): # not countable (but batchable)
	_Progression = StreamProgression
	pass



class Subset(Batchable, IndexView):
	_Progression = SetProgression
	pass



class Dataset(Splitable, CountableDataRouter, _FeaturedDataRouter):
	_Progression = SetProgression
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



######







