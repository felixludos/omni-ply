from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type

from omnibelt import operators, DecoratedOperational, AbstractOperator, AbstractOperational, \
	auto_operation as operation, Operationalized
from omnibelt.crafting import ProcessedCrafts, SeamlessCrafts, InheritableCrafts, \
	RawCraftItem, AwareCraft, SignatureCraft, \
	AbstractCrafty, AbstractCraft, AbstractCrafts, AbstractRawCraft, AbstractCraftOperator

from .abstract import AbstractTool, Tooled, AbstractKit, AbstractContext, SingleVendor, AbstractSpaced
from .errors import MissingGizmoError, ToolFailedError


class RawCraft(RawCraftItem):  # decorator base
	_CraftItem = None


class CraftToolBase(SignatureCraft, AwareCraft, DecoratedOperational, Operationalized, AbstractTool):

	def deep_history(self) -> Iterator['CraftToolBase']:
		ids = set()

		for tool in self._history:
			if id(tool) not in ids:
				ids.add(id(tool))
				yield tool
				yield from tool.deep_history()


	def gizmos(self) -> Iterator[str]:
		past = set()
		for arg in self._data['args']:
			if arg not in past:
				past.add(arg)
				yield arg
		for tool in self.deep_history():
			for arg in tool.gizmos():
				if arg not in past:
					past.add(arg)
					yield arg


	def top_level_keys(self):
		past = set()
		for key in super().top_level_keys():
			if key not in past:
				past.add(key)
				yield key
		for tool in self.deep_history():
			for key in tool.top_level_keys():
				if key not in past:
					past.add(key)
					yield key


	def _full_operations(self) -> Iterator[Tuple[str, Callable]]:
		for op in self._known_operations:
			yield op, getattr(self, op)
		past = set(self._known_operations.keys())
		for tool in self.deep_history():
			for op, func in tool._full_operations():
				if op not in past:
					past.add(op)
					yield op, func


	def _create_operator(self, instance, owner, *, ops=None, **kwargs):
		if ops is None:
			ops = dict(self._full_operations())
		return super()._create_operator(instance, owner, ops=ops, **kwargs)


	def __init__(self, manager: 'AbstractCrafts', owner: Type[AbstractCrafty], key: str,
	             raw: RawCraft, *, history=None, **kwargs):
		if history is None:
			history = []
		super().__init__(manager, owner, key, raw, **kwargs)
		self._history = history


	def merge(self, others: Iterable['CraftToolBase']):  # N-O
		self._history.extend(other for other in others if other not in self._history)



class MultiCraft(CraftToolBase):
	def __init__(self, manager: 'AbstractCrafts', owner: Type[AbstractCrafty], key: str,
	             raw: RawCraft, *, signature=None, history=None, data=None, **kwargs):
		if data is None:
			data = raw.extract_craft_data()
		try:
			if signature is None:
				signature = self._extract_signature(data['args'])
			if history is None:
				history = {target: [] for targets in signature for target in targets}
		except self._ExtractionFailedError as e:
			raise ValueError(f'{owner.__name__}.{key}: {e}') from e
		super().__init__(manager, owner, key, raw, history=history, data=data, **kwargs)
		self._signature = signature


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



class SpacedTool(CraftToolBase, AbstractSpaced):
	@operation.space_of
	def send_space_of(self, instance: Any, gizmo: str) -> Any:
		raise NotImplementedError



class GetterTool(SpacedTool, AbstractSpaced):
	def signature(self): # for static analysis
		raise NotImplementedError


	@operation.get_from
	def send_get_from(self, instance: Any, ctx: AbstractContext, gizmo: str) -> Any:
		raise NotImplementedError



class PreparedTool(CraftToolBase, AbstractSpaced):
	@operation.prepare
	def send_prepare(self, instance: Any, gizmo: str, **kwargs) -> Any:
		raise NotImplementedError




# class GetterCraftTool(CraftTool):
# 	def merge(self, gizmo, others: Iterable['CraftToolBase']):  # N-O
# 		for other in others:
# 			self.update_top_level_keys(other.top_level_keys())
# 		self._vendors.setdefault(gizmo).extend(others)









































