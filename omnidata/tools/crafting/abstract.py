from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set
from omnibelt import method_propagator

from ..abstract import AbstractTool, Gizmoed



class AbstractCrafty(Gizmoed): # owner of crafts
	pass



class AbstractCraft(method_propagator): # decorator wrapping a property/method - aka craft-item
	def emit_craft_contents(self) -> Iterator['AbstractCraft']:
		yield self



class AbstractCrafts(Gizmoed):
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


















