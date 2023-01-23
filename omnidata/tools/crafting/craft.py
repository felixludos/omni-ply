from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set
from functools import cached_property
from omnibelt import method_propagator, method_decorator, OrderedSet, isiterable

from ..abstract import AbstractKit, AbstractTool
from .abstract import AbstractCrafty, AbstractCraft, AbstractCrafts, AbstractRawCraft, AbstractCraftTool



class craft(AbstractRawCraft):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._filter_callable_arg()


	_common_decorators = (method_propagator, cached_property, method_decorator, property, staticmethod, classmethod)

	def _filter_callable_arg(self):
		args = self._args
		if len(args):
			first = args[0]
			if callable(first) or isinstance(first, self._common_decorators):
				self._args = args[1:]
				self._fn = first



class custom_craft(craft): # (RawCraft is master) - not used!
	_CraftItem: AbstractCraft = None # must not be a subclass of SelfCrafting!

	def package_craft_item(self, owner: Type[AbstractCrafty], key: str):
		return self._CraftItem.package(owner, key, self)



####################

# TODO: turn crafts into descriptors (when not decorating methods)

class BasicCraft(AbstractCraft): # Craft is master
	@classmethod
	def package(cls, owner: Type[AbstractCrafty], key: str, raw: AbstractRawCraft):
		return cls(owner, key, raw)


	def __init__(self, owner: Type[AbstractCrafty], key: str, raw: AbstractRawCraft, **kwargs):
		super().__init__(**kwargs)
		self._raw = raw



# class SelfCrafting(AbstractCraft): # (making RawCraft master) - not used -> Craft is master, not RawCraft
# 	@classmethod
# 	def package(cls, owner: Type[AbstractCrafty], key: str, raw: custom_craft):
# 		return raw.package_craft_item(owner, key)



class SeamlessCraft(BasicCraft): # (making RawCraft master) - not used -> Craft is master, not RawCraft
	@classmethod
	def package(cls, owner: Type[AbstractCrafty], key: str, raw: AbstractRawCraft) -> 'SeamlessCraft':
		craft = super().package(owner, key, raw)
		craft._cleanup_raw(owner, key, raw, fn=craft.raw_fn)
		return craft


	def _cleanup_raw(self, owner: Type[AbstractCrafty], key: str, raw: AbstractRawCraft, fn: Optional[Callable] = None):
		self._owner_loc = key if fn is None else None
		setattr(owner, key, self if fn is None else fn)


	@property
	def raw_fn(self) -> Optional[Callable]:
		return getattr(self._raw, '_fn', None)



class WrappedCraft(SeamlessCraft):
	def _cleanup_raw(self, owner: Type[AbstractCrafty], key: str, raw: AbstractRawCraft, fn: Optional[Callable] = None):
		return super()._cleanup_raw(owner, key, raw, fn=self._wrap_craft_fn(owner, raw, fn))


	@staticmethod
	def _wrap_craft_fn(owner: Type[AbstractCrafty], raw: AbstractRawCraft, fn: Optional[Callable] = None) -> Callable:
		return fn



class PropertyCraft(WrappedCraft):
	_property_type = cached_property

	@classmethod
	def _wrap_craft_fn(cls, owner: Type[AbstractCrafty], raw: AbstractRawCraft,
	                   fn: Optional[Callable] = None) -> Callable:
		return cls._property_type(super()._wrap_craft_fn(owner, raw, fn))



####################



class SignatureCraft(BasicCraft):
	def gizmos(self) -> Iterator[str]:
		yield from self._gizmos


	class _ExtractionFailedError(ValueError):
		pass


	def _extract_signature_term(self, term):
		if isinstance(term, str):
			return (term,)
		elif isinstance(term, Iterable):
			return tuple(term)
		else:
			raise self._ExtractionFailedError(f'invalid gizmo: {term!r}')


	def _extract_signature(self, terms: Tuple[Union[str, Iterable[str]]]):
		past = set()
		signature = []
		for term in terms:
			targets = self._extract_signature_term(term)
			if any(t in past for t in targets):
				raise self._ExtractionFailedError(f'{term!r} is used more than once')
			signature.append(targets)
			past.update(targets)
		return signature


	def __init__(self, owner: Type[AbstractCrafty], key: str, raw: AbstractRawCraft, *,
	             signature=None, gizmos=None, **kwargs):
		super().__init__(owner, key, raw, **kwargs)

		try:
			if signature is None:
				signature = self._extract_signature(self._raw._args)
			if gizmos is None:
				gizmos = [target for targets in signature for target in targets]
		except self._ExtractionFailedError as e:
			raise ValueError(f'{owner.__name__}.{key}: {e}') from e

		self._vendors = {}
		self._signature = signature
		self._gizmos = gizmos


	def merge(self, gizmo, others: Iterable['SignatureCrafts']) -> 'SignatureCrafts': # N-O
		self._vendors.setdefault(gizmo).extend(others)



# class ReferenceCraft(SignatureCraft):
# 	pass


# class CallableCraft(AbstractCraft):
# 	def craft(self, instance: AbstractCrafty, gizmo: str, command: str, context: AbstractKit):
# 		raise NotImplementedError


class DescriptorCraft(AbstractCraft):
	CraftTool: AbstractCraftTool = None
	
	def _create_tool(self, instance: AbstractCrafty, owner: Type[AbstractCrafty]) -> AbstractCraftTool:
		return self.CraftTool(self, instance)
	
	
	def __get__(self, instance: AbstractCrafty, owner: Type[AbstractCrafty]) -> AbstractCraftTool:
		return self._create_tool(instance, owner)

	
	def craft(self, instance: AbstractCrafty, command: str, args: Tuple, kwargs: Dict):
		raise NotImplementedError



####################



class MachineCraft(SignatureCraft, SeamlessCraft):

	pass



class MaterialCraft(SignatureCraft, SeamlessCraft):
	def __init__(self, owner: Type[AbstractCrafty], key: str, raw: AbstractRawCraft, *,
	             signature=None, gizmos=None, **kwargs):
		super().__init__(owner, key, raw, signature=signature, gizmos=gizmos, **kwargs)
		self._getter = getattr(self._raw, '_method_name', None)
	
	
	
	pass



class SpaceCraft(SignatureCraft, PropertyCraft, SeamlessCraft):
	pass



class IndicatorCraft(MachineCraft):
	pass


