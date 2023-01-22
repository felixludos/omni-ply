from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set
from functools import cached_property
from omnibelt import method_propagator, OrderedSet, isiterable

from ..abstract import SingleVendor
from .abstract import AbstractCrafty, AbstractCrafts, AbstractRawCraft, AbstractCraft
from .crafty import BasicCrafty
from .tools import CraftTool

# _common_decorators = (method_decorator, property, cached_property, staticmethod, classmethod, agnostic)


class BasicCrafts(AbstractCrafts): # container for crafts
	CraftTrigger = AbstractRawCraft

	@classmethod
	def process_raw_crafts(cls, owner: Type[AbstractCrafty]) -> 'BasicCrafts':
		crafts = []
		for key, val in owner.__dict__.items(): # O-N
			if isinstance(val, cls.CraftTrigger):
				cls._process_craft(crafts, owner, key, val)
		return cls(owner, crafts)


	@classmethod
	def _process_craft(cls, crafts: List[AbstractCraft], owner: Type[AbstractCrafty],
	                        key: str, craft: AbstractRawCraft):
		crafts.append(cls._create_craft_item(owner, key, craft))


	@classmethod
	def _create_craft_item(cls, owner: Type[AbstractCrafty], key: str, craft: AbstractRawCraft) -> AbstractCraft:
		return craft.package_craft_item(owner, key)


	def __init__(self, owner: Type[AbstractCrafty], crafts: List[AbstractCraft] = None, **kwargs):
		super().__init__(**kwargs)



class ItemCrafts(BasicCrafts):
	CraftItem: AbstractCraft = None

	@classmethod
	def _create_craft_item(cls, owner: Type[AbstractCrafty], key: str, craft: AbstractRawCraft) -> AbstractCraft:
		if cls.CraftItem is None:
			return super()._create_craft_item(owner, key, craft)
		return cls.CraftItem.package(owner, key, craft)



class InheritableCrafts(BasicCrafts):
	@classmethod
	def process_raw_crafts(cls, owner: Type[BasicCrafty], *, inherit_crafts: bool = True) -> 'InheritableCrafts':
		crafts = super().process_raw_crafts(owner)
		if inherit_crafts:
			crafts = crafts._inherit_crafts(owner)
		return crafts


	def _inherit_crafts(self, owner: Type[BasicCrafty]) -> 'InheritableCrafts':
		bases = [getattr(base, '_processed_crafts', None) for base in owner.__bases__] # N-O
		bases = [base for base in bases if base is not None]
		if not bases:
			return self
		return self.merge_crafts(*bases)


	def merge_crafts(self, *others: AbstractCrafts) -> 'InheritableCrafts': # O-N(O-N)
		raise NotImplementedError



class NestableCrafts(BasicCrafts):
	@classmethod
	def _process_craft(cls, crafts: List[AbstractRawCraft], owner: Type[AbstractCrafty],
	                        key: str, craft: AbstractRawCraft):
		raise NotImplementedError # TODO: not working yet
		fn = getattr(craft, '_fn', None)
		if isinstance(fn, cls.CraftTrigger): # semantic order
			cls._process_craft(crafts, owner, key, fn)
			setattr(craft, '_fn', getattr(fn, '_fn', None))
		super()._process_craft(crafts, owner, key, craft)



class ConsolidatedCrafts(BasicCrafts, SingleVendor):
	def __init__(self, owner: Type[AbstractCrafty], crafts: List[AbstractCraft] = None, **kwargs): # O-N
		super().__init__(**kwargs)
		self._owner = owner
		self._vendors = {} if crafts is None else self._process_vendors(crafts)


	def gizmos(self) -> Iterator[str]: # O-N
		yield from reversed(self._vendors.keys())


	def tools(self) -> Iterator[AbstractCraft]: # N-O
		yield from self._vendors.values()


	def vendor(self, gizmo: str, default: Any = None):
		return self._vendors.get(gizmo, default)


	def merge_crafts(self, *others: AbstractCrafts) -> 'ConsolidatedCrafts': # N-O
		self._vendors.update({
			gizmo: self._merge_vendors(gizmo, *self.vendors(gizmo), *other.vendors(gizmo))
			for other in others # N-O
			for gizmo in other.gizmos()
		})
		return self


	@staticmethod
	def _merge_vendors(gizmo: str, main: AbstractCraft, *others: AbstractCraft) -> AbstractCraft: # N-O
		return main.merge(gizmo, others) if others else main


	def _process_vendors(self, crafts: List[AbstractCraft]) -> Dict[str, AbstractCraft]: # O-N
		vendor_table = {}
		for craft in reversed(crafts): # N-O
			for gizmo in craft.gizmos():
				vendor_table.setdefault(gizmo, []).append(craft) # N-O
		return {gizmo: self._merge_vendors(gizmo, *vendors) # N-O
		        for gizmo, vendors in vendor_table.items()}



# class SignatureCrafts(InheritableCrafts):
# 	def __init__(self, owner: Type[AbstractCrafty], crafts: List[AbstractRawCraft] = None, **kwargs):
# 		super().__init__(**kwargs)
# 		self._owner = owner
# 		self._gizmos = {} if crafts is None else self._extract_gizmos(crafts)
#
#
# 	def gizmos(self) -> Iterator[str]:
# 		yield from self._gizmos.keys()
#
#
# 	def _package_raw_crafts(self, crafts: Iterable[AbstractRawCraft]) -> Iterator[Dict[str, Any]]:
# 		for base in crafts:
# 			yield {'args': base._args, 'kwargs': base._kwargs, 'name': base._method_name, 'type': type(base).__name__,
# 			       'fn': base._name if base._fn is not None else None, }
#
#
# 	def _extract_gizmos(self, crafts: List[AbstractRawCraft]):
# 		gizmos = {}
#
# 		for info in self._package_raw_crafts(crafts):
# 			name = info.get('name')
# 			targets = info['args']
# 			targets = tuple(tuple(target) if isiterable(target) else (target,) for target in targets)
#
# 			context = info.copy()
# 			if len(targets) > 1:
# 				context['signature'] = targets
#
# 			for target in targets:
# 				spec = context.copy()
# 				if len(target) > 1:
# 					spec['aliases'] = target
#
# 				for gizmo in target:
# 					gizmos.setdefault(gizmo, {})[name] = spec.copy()
#
# 		return gizmos
#
#
# 	def gizmo_info(self, gizmo: str, default: Optional[Any] = None):
# 		return self._gizmos.get(gizmo, default)
#
#
# 	def _merge_gizmo(self, current, old):
# 		current.update(old)
# 		return current
#
#
# 	def merge_crafts(self, *others: 'SignatureCrafts') -> 'SignatureCrafts':
# 		gizmos = self._gizmos
#
# 		for other in others:
# 			for gizmo in other.gizmos():
# 				if gizmo in gizmos:
# 					gizmos[gizmo] = self._merge_gizmo(gizmos[gizmo], other.gizmo_info(gizmo))
#
# 		return self


########################################################################################################################


class SimpleCrafts(AbstractCrafts):
	Tool = CraftTool

	def crafting(self, instance: AbstractCrafty):
		return self.Tool(instance, self)



class CustomCrafts(SimpleCrafts): # TODO: add support for custom craft initialization
	pass


########################################################################################################################



# class SeamlessCrafts(BasicCrafts):  # can be updated with craft items or other crafts
# 	@classmethod
# 	def process_raw_crafts(cls, owner: Type[AbstractCrafty]) -> AbstractCrafts:
# 		crafts = super().process_raw_crafts(owner)
# 		crafts._cleanup_owner(owner)
# 		return crafts
#
#
# 	def _cleanup_owner(self, owner: Type[AbstractCrafty]):
# 		for key, val in owner.__dict__.items():
# 			if isinstance(val, self.CraftTrigger) and val._fn is not None:
# 				setattr(owner, key, val._fn)


# class WrappingCraft(BasicCrafts):
# 	@classmethod
# 	def _process_craft_fn(cls, owner: Type[AbstractCrafty], craft: AbstractRawCraft) -> Callable:
# 		fn = super()._process_craft_item(owner, craft)
# 		if fn is not None:
# 			return cls._wrap_craft_fn(craft, fn)
#
#
# 	@classmethod
# 	def _wrap_craft_fn(cls, craft: AbstractRawCraft, fn: Callable) -> Callable:
# 		wrappers = cls._get_craft_wrappers()
# 		if craft._method_name in wrappers:
# 			return wrappers[craft._method_name](fn)
# 		return fn
#
#
# 	@staticmethod
# 	def _get_craft_wrappers():
# 		return {}



# class PropertyCraft(WrappingCraft):
# 	_craft_property_type = cached_property
#
#
# 	@staticmethod
# 	def _get_craft_properties() -> Set[str]:
# 		return set()
#
#
# 	@classmethod
# 	def _get_craft_wrappers(cls):
# 		wrappers = super()._get_craft_wrappers()
# 		wrappers.update({k: cls._craft_property_type for k in cls._get_craft_properties()})
# 		return wrappers
#
#
#
# class SpacedCraft(PropertyCraft):
# 	@staticmethod
# 	def _get_craft_properties() -> Set[str]:
# 		return {'space', *super()._get_craft_properties()}





