from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set
from functools import cached_property
from omnibelt import method_propagator, OrderedSet, isiterable

from .abstract import AbstractCrafty, AbstractCrafts, AbstractCraft
from .crafty import BasicCrafty
from .tools import CraftTool

# _common_decorators = (method_decorator, property, cached_property, staticmethod, classmethod, agnostic)


class BasicCrafts(AbstractCrafts):
	CraftTrigger = AbstractCraft

	@classmethod
	def process_raw_crafts(cls, owner: Type[AbstractCrafty]) -> AbstractCrafts:
		crafts = []
		for key, val in owner.__dict__.items():
			if isinstance(val, cls.CraftTrigger):
				cls._process_craft_item(crafts, owner, key, val)
		return cls(owner, crafts)


	@classmethod
	def _process_craft_item(cls, crafts: List[AbstractCraft], owner: Type[AbstractCrafty],
	                        key: str, craft: AbstractCraft):
		crafts.append(craft)


	def __init__(self, owner: Type[AbstractCrafty], crafts: List[AbstractCraft] = None, **kwargs):
		super().__init__(**kwargs)
		# self._crafts = crafts



class InheritableCrafts(BasicCrafts):
	@classmethod
	def process_raw_crafts(cls, owner: Type[BasicCrafty], *, inherit_crafts: bool = True) -> 'InheritableCrafts':
		crafts = super().process_raw_crafts(owner)
		if inherit_crafts:
			crafts = crafts._inherit_crafts(owner)
		return crafts


	def _inherit_crafts(self, owner: Type[BasicCrafty]) -> 'InheritableCrafts':
		bases = [getattr(base, '_processed_crafts', None) for base in owner.__bases__]
		bases = [base for base in bases if base is not None]
		if not bases:
			return self
		return self.merge_crafts(*bases)


	def merge_crafts(self, *others: AbstractCrafts) -> 'InheritableCrafts':
		raise NotImplementedError



class SeamlessCrafts(BasicCrafts):  # can be updated with craft items or other crafts
	@classmethod
	def process_raw_crafts(cls, owner: Type[AbstractCrafty]) -> AbstractCrafts:
		crafts = super().process_raw_crafts(owner)
		crafts._cleanup_owner(owner)
		return crafts


	def _cleanup_owner(self, owner: Type[AbstractCrafty]):
		for key, val in owner.__dict__.items():
			if isinstance(val, self.CraftTrigger) and val._fn is not None:
				setattr(owner, key, val._fn)



class NestableCrafts(BasicCrafts):
	@classmethod
	def _process_craft_item(cls, crafts: List[AbstractCraft], owner: Type[AbstractCrafty],
	                        key: str, craft: AbstractCraft):
		fn = craft._fn
		if isinstance(fn, cls.CraftTrigger):
			cls._process_craft_item(crafts, owner, key, fn)
			craft._fn = fn._fn
		else:
			craft._fn = cls._process_craft_fn(owner, craft)
		super()._process_craft_item(crafts, owner, key, craft)


	@classmethod
	def _process_craft_fn(cls, owner: Type[AbstractCrafty], craft: AbstractCraft) -> Callable:
		return craft._fn



class WrappingCraft(BasicCrafts):
	@classmethod
	def _process_craft_fn(cls, owner: Type[AbstractCrafty], craft: AbstractCraft) -> Callable:
		fn = super()._process_craft_item(owner, craft)
		if fn is not None:
			return cls._wrap_craft_fn(craft, fn)


	@classmethod
	def _wrap_craft_fn(cls, craft: AbstractCraft, fn: Callable) -> Callable:
		wrappers = cls._get_craft_wrappers()
		if craft._method_name in wrappers:
			return wrappers[craft._method_name](fn)
		return fn


	@staticmethod
	def _get_craft_wrappers():
		return {}



class PropertyCraft(WrappingCraft):
	_craft_property_type = cached_property


	@staticmethod
	def _get_craft_properties() -> Set[str]:
		return set()


	@classmethod
	def _get_craft_wrappers(cls):
		wrappers = super()._get_craft_wrappers()
		wrappers.update({k: cls._craft_property_type for k in cls._get_craft_properties()})
		return wrappers



class SpacedCraft(PropertyCraft):
	@staticmethod
	def _get_craft_properties() -> Set[str]:
		return {'space', *super()._get_craft_properties()}



class SignatureCrafts(InheritableCrafts):
	def __init__(self, owner: Type[AbstractCrafty], crafts: List[AbstractCraft] = None, **kwargs):
		super().__init__(**kwargs)
		self._owner = owner
		self._gizmos = {} if crafts is None else self._extract_gizmos(crafts)


	def gizmos(self) -> Iterator[str]:
		yield from self._gizmos.keys()


	def _package_raw_crafts(self, crafts: Iterable[AbstractCraft]) -> Iterator[Dict[str, Any]]:
		for base in crafts:
			yield {'args': base._args, 'kwargs': base._kwargs, 'name': base._method_name, 'type': type(base).__name__,
			       'fn': base._name if base._fn is not None else None, }


	def _extract_gizmos(self, crafts: List[AbstractCraft]):
		gizmos = {}

		for info in self._package_raw_crafts(crafts):
			name = info.get('name')
			targets = info['args']
			targets = tuple(tuple(target) if isiterable(target) else (target,) for target in targets)

			context = info.copy()
			if len(targets) > 1:
				context['signature'] = targets

			for target in targets:
				spec = context.copy()
				if len(target) > 1:
					spec['aliases'] = target

				for gizmo in target:
					gizmos.setdefault(gizmo, {})[name] = spec.copy()

		return gizmos


	def gizmo_info(self, gizmo: str, default: Optional[Any] = None):
		return self._gizmos.get(gizmo, default)


	def _merge_gizmo(self, current, old):
		current.update(old)
		return current


	def merge_crafts(self, *others: 'SignatureCrafts') -> 'SignatureCrafts':
		gizmos = self._gizmos

		for other in others:
			for gizmo in other.gizmos():
				if gizmo in gizmos:
					gizmos[gizmo] = self._merge_gizmo(gizmos[gizmo], other.gizmo_info(gizmo))

		return self



########################################################################################################################



class SimpleCrafts(AbstractCrafts):
	Tool = CraftTool

	def crafting(self, instance: 'Crafty'):
		return self.Tool(instance, self)



class CustomCrafts(SimpleCrafts): # TODO: add support for custom craft initialization
	pass


########################################################################################################################


class Crafts(AbstractCrafts): # can be updated with craft items or other crafts
	def merge_craft(self, other: 'Crafts'):
		raise NotImplementedError


	@classmethod
	def package(cls, owner: Type['Crafty']):


		return cls(owner)


	def __init__(self, base: 'craft', **kwargs):
		super().__init__(**kwargs)





class TooledCraft(SignatureCrafts):
	def gizmos(self):
		raise NotImplementedError



class ConsolidationCrafts(Crafts):
	def consolidate_craft_items(self, instance: 'Crafty', existing: List['CraftTool'], items: List['Crafts']):
		raise NotImplementedError






