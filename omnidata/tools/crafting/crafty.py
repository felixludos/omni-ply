from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set
from functools import cached_property
from omnibelt import method_propagator, OrderedSet, isiterable

from .abstract import AbstractCrafty



class BasicCrafty(AbstractCrafty): # contains crafts (and craft sources when instantiated)
	Crafts = None
	_processed_crafts = None

	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		if '_processed_crafts' not in cls.__dict__:
			cls._processed_crafts = None if cls.Crafts is None else cls.Crafts.process_raw_crafts(cls)



class StandardCrafty(BasicCrafty):
	Crafts = None

	@classmethod
	def _process_raw_crafts(cls, inherit_crafts: bool = True) -> List[Crafts]: # simple consolidation
		return cls.Crafts.process_raw_crafts(inherit_crafts=inherit_crafts)


	def _process_known_crafts(self): # full consolidation
		return [craft.crafting(self) for craft in self._known_crafts]


	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self._processed_crafts is not None:
			self._processed_crafts = self._processed_crafts.crafting(self)



# class LiveCrafty(Crafty): # also cosolidates at instantiation (in case some crafts are added after class creation)
# 	def _process_known_crafts(self, craft_items: Optional[List['Crafts']] = None): # full consolidation
# 		if craft_items is None:
# 			craft_items = self._known_crafts
#
# 		tools = []
#
# 		while craft_items:
# 			craft = craft_items.pop()
#
# 			if isinstance(craft, ConsolidationCrafts):
# 				related = []
# 				remaining = []
# 				for item in craft_items:
# 					if craft.consolidate(item):
# 						related.append(item)
# 					else:
# 						remaining.append(item)
#
#
# 			if isinstance(craft, ConsolidationCrafts):
# 				craft_items.extend(craft.consolidate_craft_items(self, tools, craft_items))
# 			tools, craft_items = craft.consolidate_craft_items(self, tools, craft_items)
#
# 		return list(reversed(tools))





