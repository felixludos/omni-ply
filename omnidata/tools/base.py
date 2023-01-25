from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type

from omnibelt import operators, DecoratedOperational, AbstractOperator, AbstractOperational, \
	auto_operation as operation, Operationalized
from omnibelt.crafting import ProcessedCrafts, SeamlessCrafts, InheritableCrafts, \
	RawCraftItem, AwareCraft, SignatureCraft, \
	AbstractCrafty, AbstractCraft, AbstractCrafts, AbstractRawCraft, AbstractCraftOperator

from .abstract import AbstractTool, Tooled, AbstractKit, AbstractContext, SingleVendor, AbstractSpaced
from .errors import MissingGizmoError, ToolFailedError



class RawCraft(RawCraftItem): # decorator base
	_CraftItem = None



class CraftToolBase(SignatureCraft, AwareCraft, AbstractTool):
	def gizmos(self) -> Iterator[str]:
		yield from self._gizmos


	def _lineage(self, gizmo: str) -> Iterator['AbstractTool']:
		yield from self._vendors.get(gizmo, ())


	def _call_fallback(self, gizmo: str, fn_name, *args, **kwargs) -> Any:
		count = 0
		for tool in self._lineage(gizmo):
			try:
				fn = getattr(tool, fn_name, None)
				if fn is not None:
					return fn(tool, *args, **kwargs)
			except ToolFailedError:
				pass
			count += 1
		raise ToolFailedError(gizmo, f'Tool failed for {gizmo!r} after {count} fallbacks')


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


	def __init__(self, manager: 'AbstractCrafts', owner: Type[AbstractCrafty], key: str,
	             raw: AbstractRawCraft, *, signature=None, gizmos=None, **kwargs):
		super().__init__(manager, owner, key, raw, **kwargs)
		try:
			if signature is None:
				signature = self._extract_signature(self._data['args'])
			if gizmos is None:
				gizmos = [target for targets in signature for target in targets]
		except self._ExtractionFailedError as e:
			raise ValueError(f'{owner.__name__}.{key}: {e}') from e

		self._vendors = {}
		self._signature = signature
		self._gizmos = gizmos


	def merge(self, gizmo, others: Iterable['CraftToolBase']):  # N-O
		for other in others:
			self.update_top_level_keys(other.top_level_keys())
		self._vendors.setdefault(gizmo).extend(others)



class ValidatedCraftTool(CraftToolBase):
	def __init__(self, manager: 'AbstractCrafts', owner: Type[AbstractCrafty], key: str,
	             raw: AbstractRawCraft, *, signature=None, gizmos=None, **kwargs):
		super().__init__(manager, owner, key, raw, signature=signature, gizmos=gizmos, **kwargs)
		self._is_valid = True


	def invalidate(self):
		self._is_valid = False


	@property
	def is_valid(self):
		return self._is_valid



class CraftTool(ValidatedCraftTool, AbstractSpaced, DecoratedOperational, Operationalized):
	@operation.get_from
	def send_get_from(self, instance: Any, ctx: AbstractContext, gizmo: str) -> Any:
		return self._call_fallback(gizmo, 'send_get_from', instance, ctx, gizmo)


	@operation.space_of
	def send_space_of(self, instance: Any, gizmo: str) -> Any:
		return self._call_fallback(gizmo, 'send_space_of', instance, gizmo)



# class GetterCraftTool(CraftTool):
# 	def merge(self, gizmo, others: Iterable['CraftToolBase']):  # N-O
# 		for other in others:
# 			self.update_top_level_keys(other.top_level_keys())
# 		self._vendors.setdefault(gizmo).extend(others)









































