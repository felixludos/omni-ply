from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set
import math
# from ..persistent import Fingerprinted
from ..tools import Industrial
from ..parameters import Parameterized, Structured, hparam

from .abstract import AbstractDataSource
from .routers import DataCollection, AutoCollection, AliasedCollection, CountableDataRouter
from .views import IndexSelector
from .sources import Splitable, TensorSource, SpacedSource#, BuildableData
from .progression import SetProgression, StreamProgression, AbstractProgression
from .budgeting import BudgetLoader
from .batches import Batchable, BatchBase, IndexBatch



class Bunch(BatchBase):
	pass
StreamProgression._Context = Bunch



class Batch(IndexBatch):
	_Progression = SetProgression
	pass
SetProgression._Context = Batch



class Buffer(Parameterized, Batchable, TensorSource, SpacedSource):#, BuildableData): # TODO: should be epochable
	_Progression = SetProgression
	pass



# print()
# print('\n'.join(map(str, Structured.mro())))
# print()
# print('\n'.join(map(str, Batchable.mro())))
# print()
# print('\n'.join(map(str, AutoCollection.mro())))
# print()
# print('\n'.join(map(str, AliasedCollection.mro())))
# print()
# print('\n'.join(map(str, DataCollection.mro())))
class _FeaturedDataRouter(AutoCollection, AliasedCollection, DataCollection, Structured, Batchable):
	# #, BuildableData):
	# def register_buffer(self, gizmo: str, buffer=None, **kwargs):
	# 	buffer = super().register_buffer(gizmo, buffer, **kwargs)
	# 	if gizmo in self._spaces:
	# 		del self._spaces[gizmo]
	# 	return buffer
	pass



class Datastream(_FeaturedDataRouter): # not countable (but batchable)
	_Progression = StreamProgression
	pass



class Subset(Splitable, Batchable, IndexSelector):
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







