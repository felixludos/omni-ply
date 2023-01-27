from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type
from functools import cached_property

from omnibelt import operators, DecoratedOperational, AbstractOperator, AbstractOperational, \
	auto_operation as operation, Operationalized, agnosticproperty, agnostic
from omnibelt.crafting import ProcessedCrafts, SeamlessCrafts, InheritableCrafts, WrappedCraft, PropertyCraft, \
	RawCraftItem, AwareCraft, SignatureCraft, \
	AbstractCrafty, AbstractCraft, AbstractCrafts, AbstractRawCraft, AbstractCraftOperator

from ..features import Prepared

from .abstract import AbstractTool, Tooled, AbstractKit, AbstractContext, SingleVendor, AbstractSpaced
from .errors import MissingGizmoError, ToolFailedError


class RawCraft(RawCraftItem):  # decorator base
	_args = None
	_CraftItem = None


	class _propagator_reference(RawCraftItem._propagator_reference):
		def __init__(self, *args, backup_args=None, **kwargs):
			if backup_args is None:
				backup_args = ()
			super().__init__(*args, **kwargs)
			self._backup_args = backup_args


		def __call__(self, *args, **kwargs):
			return super().__call__(*args, *self._backup_args, **kwargs)


	@agnostic
	def _agnostic_propagator(self, item, **kwargs):
		return self._make_propagator(item, backup_args=self._args, **kwargs)



class GetterRawCraft(RawCraft):  # decorator base
	@agnosticproperty # TODO: candidate for a class init argument (?)
	def prepare(self):
		return self._agnostic_propagator('prepare')



class CraftToolOperator(SignatureCraft.Operator, DecoratedOperational.Operator, Prepared):
	def _prepare(self, *args, **kwargs):
		return self._send_operation('prepare')(*args, **kwargs)


	def has_gizmo(self, gizmo):
		return gizmo in self._gizmos


	def gizmos(self) -> Iterator[str]:
		yield from self._gizmos
		# past = set()
		# for arg in self._data['args']:
		# 	if arg not in past:
		# 		past.add(arg)
		# 		yield arg
		# for tool in self._history:
		# 	for arg in tool.gizmos():
		# 		if arg not in past:
		# 			past.add(arg)
		# 			yield arg


	def _extract_gizmos(self, args):
		past = set()
		for arg in args:
			if arg not in past:
				past.add(arg)
				yield arg


	def __init__(self, base: 'CraftTool', instance: Any, *, history=None, gizmos=None, **kwargs):
		# if history is None:
		# 	history = []
		if gizmos is None:
			gizmos = list(self._extract_gizmos(base._data['args']))
		super().__init__(base, instance, **kwargs)
		self._history = [] #history # TESTING
		self._gizmos = gizmos
		self._base = base # TESTING


	def merge(self, others: Iterable['CraftToolOperator']):  # N-O
		for other in others:
			for op, fn in other._ops.items():
				if op not in self._ops:
					self._ops[op] = fn
			self._gizmos.extend(gizmo for gizmo in other._gizmos if gizmo not in self._gizmos)
		self._history.extend(other for other in others if other not in self._history) # TESTING
		return self



class CraftToolBase(SignatureCraft, AwareCraft, DecoratedOperational, AbstractTool):
	def _create_operator(self, instance, owner, *, ops=None, **kwargs):
		if ops is None:
			ops = {name: getattr(self, op.attr_name)
			       for name, op in self._known_operations.items()}
		return super()._create_operator(instance, owner, ops=ops, **kwargs)


	def _select_op(self, data, ops):

		method = data['method']

		if method in ops:
			return {method: ops[method]}

		raise NotImplementedError



class endpoint(operation):
	pass



class CraftTool(CraftToolBase):
	Operator = CraftToolOperator


	def _select_op(self, data, ops):

		method = data['method']

		if method == 'prepare':
			return {'prepare': ops['prepare']}

		if method in ops:
			return {method: ops[method]}


	@endpoint.prepare
	def send_prepare(self, instance: Any, *args, **kwargs) -> Any:
		return getattr(instance, self._data['name'])(*args, **kwargs)





class MultiCraft(CraftTool):
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



class SpacedTool(CraftTool, AbstractSpaced, PropertyCraft):
	@operation.space_of
	def send_space_of(self, instance: Any, gizmo: str) -> Any:
		val = getattr(instance, self._data['name'])
		return val



class CachedSpaceTool(SpacedTool):
	_property_type = cached_property # TODO: call __set_name__ on the property before using



class GetterTool(CraftTool, AbstractSpaced):
	def signature(self): # for static analysis
		raise NotImplementedError


	@operation.get_from
	def send_get_from(self, instance: Any, ctx: AbstractContext, gizmo: str) -> Any:
		raise NotImplementedError






# class GetterCraftTool(CraftTool):
# 	def merge(self, gizmo, others: Iterable['CraftToolBase']):  # N-O
# 		for other in others:
# 			self.update_top_level_keys(other.top_level_keys())
# 		self._vendors.setdefault(gizmo).extend(others)








	# def gizmos(self) -> Iterator[str]:
	# 	past = set()
	# 	for arg in self._data['args']:
	# 		if arg not in past:
	# 			past.add(arg)
	# 			yield arg
	# 	for tool in self._history:
	# 		for arg in tool.gizmos():
	# 			if arg not in past:
	# 				past.add(arg)
	# 				yield arg
	#
	#
	# def top_level_keys(self):
	# 	past = set()
	# 	for key in super().top_level_keys():
	# 		if key not in past:
	# 			past.add(key)
	# 			yield key
	# 	for tool in self._history:
	# 		for key in tool.top_level_keys():
	# 			if key not in past:
	# 				past.add(key)
	# 				yield key


	# def _full_operations(self) -> Dict[str, Callable]: # 0-N
	# 	ops = {}
	# 	for tool in reversed(self._history):
	# 		ops.update(tool._full_operations())
	# 	ops.update({op: getattr(self, attr) for op, attr in self._known_operations.items()})
	# 	return ops
	#
	#
	# def _create_operator(self, instance, owner, *, ops=None, **kwargs):
	# 	if ops is None:
	# 		ops = dict(self._full_operations())
	# 	return super()._create_operator(instance, owner, ops=ops, **kwargs)


	# def __init__(self, manager: 'AbstractCrafts', owner: Type[AbstractCrafty], key: str,
	#              raw: RawCraft, *, history=None, **kwargs):
	# 	if history is None:
	# 		history = []
	# 	super().__init__(manager, owner, key, raw, **kwargs)
	# 	self._history = history


	# def merge(self, others: Iterable['CraftToolBase']):  # N-O
	# 	self._history.extend(other for other in others if other not in self._history)
	# 	return self


































