from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set

import inspect
from functools import cached_property

import torch

from omnibelt import method_decorator, agnostic
from omnibelt.crafts import AbstractCraft, NestableCraft, OperationalCraft, AbstractCrafty, ProcessedIndividualCrafty


from ..features import Prepared



class LabelCraft(AbstractCraft):
	def __init__(self, label: str, **kwargs):
		super().__init__(**kwargs)
		self._label = label


	@property
	def label(self):
		return self._label



class ToolCraft(LabelCraft, NestableCraft, OperationalCraft):
	class Operator(OperationalCraft.Operator):
		_base: 'ToolCraft'

		def get_from(self, ctx, gizmo: str):
			return self._base.get_from(self._instance, ctx, gizmo)


	def get_from(self, instance: AbstractCrafty, ctx, gizmo: str):
		raise NotImplementedError



class Loggable:
	@staticmethod
	def log(ctx):
		raise NotImplementedError



class LoggingCraft(ToolCraft):
	class Operator(ToolCraft.Operator, Loggable):
		_base: 'LoggingCraft'

		def log(self, ctx):
			return self._base.log(self._instance, ctx)


	def log(self, instance: AbstractCrafty, ctx):
		raise NotImplementedError



class SimpleLoggingCraft(LoggingCraft):
	def log(self, instance: AbstractCrafty, ctx):
		return self._log_value(ctx[self.label])


	def _log_value(self, value):
		raise NotImplementedError



class FunctionCraft(method_decorator, LabelCraft):
	def __init__(self, label: str, *, fn=None, **kwargs):
		super().__init__(label=label, fn=fn, **kwargs)


	@property
	def wrapped(self):
		return self._fn


	_name = None
	def _setup_decorator(self, owner: Type, name: str) -> method_decorator:
		self._name = name
		return super()._setup_decorator(owner, name)


	def _get_instance_fn(self, instance: AbstractCrafty, name: Optional[str] = None):
		if name is None:
			name = self._name
		return getattr(instance, name)



class FunctionToolCraft(FunctionCraft, ToolCraft):
	def get_from(self, instance: AbstractCrafty, ctx, gizmo: str):
		if self._name is None:
			raise TypeError('no name')
		if self._label != gizmo:
			raise ValueError(f'gizmo mismatch: {self._label} != {gizmo}')
		return self._get_from_fn(self._get_instance_fn(instance), ctx, gizmo)


	def _get_from_fn(self, fn, ctx, gizmo):
		return fn(ctx)



class MachineCraft(FunctionToolCraft):
	@staticmethod
	def _parse_context_args(fn: Callable, ctx):
		# TODO: allow for default values -> use omnibelt extract_signature

		args = {}
		params = inspect.signature(fn).parameters
		for name, param in params[1:].items():
			if name in ctx:
				args[name] = ctx[name]

		return args


	def _get_from_fn(self, fn, ctx, gizmo):
		return fn(**self._parse_context_args(fn, ctx))



class BatchCraft(FunctionToolCraft):
	def _get_from_fn(self, fn, ctx, gizmo):
		return fn(getattr(ctx, 'batch', ctx))



class SizeCraft(FunctionToolCraft):
	def _get_from_fn(self, fn, ctx, gizmo):
		return fn(getattr(ctx, 'size', ctx))



class IndexCraft(FunctionToolCraft):
	def _get_from_fn(self, fn, ctx, gizmo):
		return fn(getattr(ctx, 'indices', ctx))



class SampleCraft(FunctionToolCraft):
	def _get_from_fn(self, fn, ctx, gizmo):
		size = getattr(ctx, 'size', None)
		if size is None:
			return fn()
		return torch.stack([fn() for _ in range(size)])



class IndexSampleCraft(IndexCraft, SampleCraft):
	def _get_from_fn(self, fn, ctx, gizmo):
		indices = getattr(ctx, 'indices', None)
		if indices is None:
			return fn(getattr(ctx, 'index', ctx))
		return torch.stack([fn(i) for i in indices])



class CachedPropertyCraft(LabelCraft, cached_property):
	def __init__(self, gizmo: str, *, func=None, **kwargs):
		super().__init__(gizmo=gizmo, func=func, **kwargs)


	def __call__(self, func: Callable):
		self.func = func
		return self


	def _get_instance_val(self, instance: AbstractCrafty):
		return getattr(instance, self.attrname)



class SpaceCraft(OperationalCraft, CachedPropertyCraft):
	class Operator(OperationalCraft.Operator):
		_base: 'SpaceCraft'

		def space_of(self, gizmo: str):
			return self._base.space_of(self._instance, gizmo)


	def space_of(self, instance: AbstractCrafty, gizmo: str = None):
		return self._get_instance_val(instance)




class OptionalCraft(MachineCraft):
	pass



class DefaultCraft(MachineCraft):
	pass



class InitCraft(OperationalCraft, CachedPropertyCraft):
	class Operator(OperationalCraft.Operator):
		_base: 'InitCraft'

		def init(self):
			return self._base.init(self._instance)


	def init(self, instance: AbstractCrafty):
		return self._process_init_val(instance, self._get_instance_val(instance))


	def _process_init_val(self, instance, val):
		return val

	pass



class TensorCraft(InitCraft):
	def _process_init_val(self, instance, val):
		if isinstance(val, torch.Tensor):
			buffer = getattr(instance, 'Buffer', None)
			return buffer(val)
		return val


########################################################################################################################



class MethodCraft(AbstractCraft):
	def __init__(self, *args, **kwargs):
		raise TypeError('This craft cannot be directly instantiated')



class SpacedCraft(LabelCraft):
	_space_craft_type = SpaceCraft

	@agnostic
	def space(self, *args, **kwargs):
		if isinstance(self, type):
			self: Type['SpacedCraft']
			return self._space_craft_type(*args, **kwargs)
		return self._space_craft_type(self.label)(*args, **kwargs)


class ContextedCraft(LabelCraft):
	from_context = FunctionToolCraft



########################################################################################################################



class CraftyKit(ProcessedIndividualCrafty):
	class _Tool:
		def __init__(self, gizmo: str):
			self._gizmo = gizmo
			self._standard = []
			self._optionals = []
			self._defaults = []


		def add(self, craft: ToolCraft):
			if isinstance(craft, OptionalCraft):
				self._optionals.append(craft)
			elif isinstance(craft, DefaultCraft):
				self._defaults.append(craft)
			else:
				self._standard.append(craft)


		def vendors(self):
			yield from self._standard
			yield from self._optionals
			yield from self._defaults


		def get_from(self, ctx, gizmo: str):
			for vendor in self.vendors():
				return vendor.get_from(self, ctx, gizmo)


	def _process_all_crafts(self):
		self._tools = {}
		self._spaces = {}
		super()._process_all_crafts()


	def _process_craft(self, craft: LabelCraft):
		super()._process_craft(craft)
		if isinstance(craft, ToolCraft):
			if craft.label not in self._tools:
				self._tools[craft.label] = self._Tool(craft.label)
			self._tools[craft.label].add(craft)
		if isinstance(craft, SpaceCraft):
			self._spaces.setdefault(craft.label, []).append(craft)


	def get_from(self, ctx, gizmo: str):
		return self._tools[gizmo].get_from(ctx, gizmo)


	def space_of(self, gizmo: str):
		return self._spaces[gizmo][0].space_of(self, gizmo)


	def vendors(self, gizmo: str):
		yield from self._tools[gizmo].vendors()


	def has_gizmo(self, gizmo: str):
		return gizmo in self._tools


	def gizmos(self):
		yield from self._tools.keys()



class MaterialedCrafty(CraftyKit, Prepared): # allows materials to be initialized when prepared
	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)

		materials = {}
		for gizmo, tool in self._tools.items():
			for craft in tool.vendors():
				if isinstance(craft, InitCraft):
					materials[gizmo] = craft.init(self)
				break
		self._tools.update(materials)








