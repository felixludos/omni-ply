from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set
from omnibelt import method_propagator

from ..abstract import AbstractTool, AbstractKit, Gizmoed



class AbstractCrafty(Gizmoed): # owner of crafts
	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		cls._process_raw_crafts()


	@classmethod
	def _process_raw_crafts(cls):
		pass



class AbstractRawCraft(method_propagator): # decorator wrapping a property/method - aka craft-item
	def package_craft_item(self, owner: Type[AbstractCrafty], key: str) -> 'AbstractCraft':
		raise NotImplementedError



class AbstractCraft(Gizmoed):
	@classmethod
	def package(cls, owner: Type[AbstractCrafty], key: str, raw: AbstractRawCraft) -> 'AbstractCraft':
		raise NotImplementedError


	def merge(self, gizmo: str, others: Iterable['AbstractCraft']) -> 'AbstractCraft':
		raise NotImplementedError



class AbstractCrafts(AbstractKit):
	def crafting(self, instance: 'AbstractCrafty') -> Iterator['AbstractCraftTool']:
		raise NotImplementedError


	@classmethod
	def process_raw_crafts(cls, owner: Type['AbstractCrafty']) -> 'AbstractCrafts': # custom constructor
		raise NotImplementedError


	def gizmo_info(self, gizmo: str, default: Optional[Any] = None):
		raise NotImplementedError


# def merge_craft(self, other: 'Crafts'):
	# 	raise NotImplementedError


	# @classmethod
	# def package(cls, owner: Type['Crafty']):
	# 	raise NotImplementedError



class AbstractCraftTool(AbstractTool):
	pass


















