from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set

import inspect
from functools import cached_property
from collections import OrderedDict

import torch

from omnibelt import method_decorator, agnostic
from omnibelt.crafts import AbstractCraft, AbstractCrafty, NestableCraft, SkilledCraft, IndividualCrafty


from .abstract import Loggable, AbstractAssessible, AbstractTool
from .assessments import Signatured



class LabelCraft(SkilledCraft):
	class Skill(SkilledCraft.Skill):
		_base: 'LabelCraft'

		@property
		def label(self):
			return self.validate_label(self._base.label)


		def validate_label(self, label, *, owner = None):
			if owner is None:
				owner = self._instance
			return self._base._validate_label(owner, label)


	def __init__(self, label: str, **kwargs):
		super().__init__(**kwargs)
		self._label = label


	def _validate_label(self, owner, label): # TODO: may be unnecessary (-> split into a subclass)
		return owner.validate_label(label)


	@property
	def label(self):
		return self._label



class CopyCraft(LabelCraft):
	def copy(self, label: str = None, *args, **kwargs):
		if label is None:
			label = self.label
		return self.__class__(label, *args, **kwargs)


	def __copy__(self):
		return self.copy()



class ReplaceableCraft(CopyCraft):
	def __init__(self, label: str, *, replacements=None, **kwargs):
		if replacements is None:
			replacements = {}
		super().__init__(label, **kwargs)
		self._replacements = replacements


	def replace(self, replacements: Dict[str, str], **kwargs):
		return self.copy(replacements={**self._replacements, **replacements}, **kwargs)


	def _validate_label(self, owner, label):
		return super()._validate_label(owner, self._replacements.get(label, label))



class AnalysisCraft(ReplaceableCraft, Signatured, AbstractAssessible):
	class Skill(LabelCraft.Skill, Signatured, AbstractAssessible):
		_base: 'AnalysisCraft'


		def signatures(self, owner = None):
			if owner is None:
				owner = self._instance
			yield from self._base.signatures(owner)


	def signatures(self, owner: Type[AbstractCrafty] = None):
		yield self._Signature(self.label)



class ToolCraft(NestableCraft, AnalysisCraft):
	class Skill(AnalysisCraft.Skill, AbstractTool):
		_base: 'ToolCraft'

		def has_gizmo(self, gizmo: str) -> bool:
			return self._base._has_gizmo(self._instance, gizmo)


		def gizmos(self) -> Iterator[str]:
			yield from self._base._gizmos(self._instance)


		def get_from(self, ctx, gizmo: str):
			return self._base._get_from(self._instance, ctx, gizmo)


	def _has_gizmo(self, instance: AbstractCrafty, gizmo: str) -> bool:
		return gizmo == self._validate_label(instance, self.label)


	def _gizmos(self, instance: AbstractCrafty) -> Iterator[str]:
		yield self._validate_label(instance, self.label)


	def _get_from(self, instance: AbstractCrafty, ctx, gizmo: str):
		raise NotImplementedError



class LoggingCraft(ToolCraft):
	class Skill(ToolCraft.Skill, Loggable):
		_base: 'LoggingCraft'

		def log(self, ctx):
			return self._base._log(self._instance, ctx)


	def _log(self, instance: AbstractCrafty, ctx):
		raise NotImplementedError



class SimpleLoggingCraft(LoggingCraft):
	def log(self, instance: AbstractCrafty, ctx):
		return self._log_value(ctx[self.label])


	def _log_value(self, value):
		raise NotImplementedError



class FunctionCraft(method_decorator, CopyCraft):
	def __init__(self, label: str, *, fn=None, **kwargs):
		super().__init__(label=label, fn=fn, **kwargs)


	def copy(self, label: str = None, *args, **kwargs):
		new = super().copy(label=label, *args, **kwargs)
		new._fn = self._fn
		new._name = self._name
		return new


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
	def _get_from(self, instance: AbstractCrafty, ctx, gizmo: str):
		return self._get_from_fn(self._get_instance_fn(instance), ctx, gizmo)


	def _get_from_fn(self, fn, ctx, gizmo):
		return fn(ctx)



class MachineCraft(FunctionToolCraft):
	@staticmethod
	def _parse_fn_args(fn: Callable, *, raw: Optional[bool] = False) -> Iterator[Tuple[str, Any]]:
		params = inspect.signature(fn).parameters
		param_items = iter(params.items())
		if raw:
			next(param_items) # skip self/cls arg
		for name, param in param_items:
			yield name, param.default


	@classmethod
	def _fillin_fn_args(cls, fn: Callable, ctx):
		# TODO: allow for arbitrary default values -> use omnibelt extract_signature

		inp = {}
		for key, default in cls._parse_fn_args(fn):
			try:
				inp[key] = ctx[key]
			except KeyError:
				if default is inspect.Parameter.empty:
					raise
				inp[key] = default

		return inp


	def _machine_inputs(self, owner, *, raw: Optional[bool] = None):
		fn = self._get_instance_fn(owner)
		if raw is None:
			raw = isinstance(owner, type)
		for key, default in self._parse_fn_args(fn, raw=raw):
			if default is inspect.Parameter.empty:
				yield self._validate_label(owner, key)


	def signatures(self, owner: Type[AbstractCrafty] = None):
		assert owner is not None
		label = self._validate_label(owner, self.label)
		yield self._Signature(label, inputs=tuple(self._machine_inputs(owner)))


	def _get_from(self, instance: AbstractCrafty, ctx, gizmo: str):
		inputs = {inp: ctx[inp] for inp in self._machine_inputs(instance, raw=False)}
		return self._get_from_fn(self._get_instance_fn(instance), ctx, gizmo, inputs=inputs)


	def _get_from_fn(self, fn, ctx, gizmo, *, inputs=None):
		return fn(**inputs)



class BatchCraft(FunctionToolCraft):
	def _get_from_fn(self, fn, ctx, gizmo):
		return fn(getattr(ctx, 'batch', ctx))



class SizeCraft(FunctionToolCraft):
	def _get_from_fn(self, fn, ctx, gizmo):
		return fn(getattr(ctx, 'size', ctx))


	def signatures(self, owner: Type[AbstractCrafty] = None):
		assert owner is not None
		label = self._validate_label(owner, self.label)
		yield self._Signature(label, meta='size')



class IndexCraft(FunctionToolCraft):
	def _get_from_fn(self, fn, ctx, gizmo):
		return fn(getattr(ctx, 'indices', ctx))


	def signatures(self, owner: Type[AbstractCrafty] = None):
		assert owner is not None
		label = self._validate_label(owner, self.label)
		yield self._Signature(label, meta='indices')



class SampleCraft(FunctionToolCraft):
	def _get_from_fn(self, fn, ctx, gizmo):
		size = getattr(ctx, 'size', None)
		if size is None:
			return fn()
		return torch.stack([fn() for _ in range(size)])


	def signatures(self, owner: Type[AbstractCrafty] = None):
		assert owner is not None
		label = self._validate_label(owner, self.label)
		yield self._Signature(label)



class IndexSampleCraft(FunctionToolCraft):
	def _get_from_fn(self, fn, ctx, gizmo):
		indices = getattr(ctx, 'indices', None)
		if indices is None:
			return fn(getattr(ctx, 'index', ctx))
		return torch.stack([fn(i) for i in indices])


	def signatures(self, owner: Type[AbstractCrafty] = None):
		assert owner is not None
		label = self._validate_label(owner, self.label)
		yield self._Signature(label, meta='index')



class CachedPropertyCraft(ReplaceableCraft, cached_property):
	def __init__(self, gizmo: str, *, func=None, **kwargs):
		super().__init__(gizmo=gizmo, func=func, **kwargs)


	def copy(self, label: str = None, **kwargs):
		new = super().copy(label=label, **kwargs)
		new.func = self.func
		new.attrname = self.attrname
		return new


	def __call__(self, func: Callable):
		self.func = func
		return self


	def _get_instance_val(self, instance: AbstractCrafty):
		return getattr(instance, self.attrname)



class SpaceCraft(CachedPropertyCraft):
	class Skill(CachedPropertyCraft.Skill):
		_base: 'SpaceCraft'


		def space_of(self, gizmo: str):
			return self._base._space_of(self._instance, gizmo)


	def _space_of(self, instance: AbstractCrafty, gizmo: str = None):
		return self._get_instance_val(instance)



class OptionalCraft(MachineCraft):
	class Skill(MachineCraft.Skill):
		pass



class DefaultCraft(MachineCraft):
	class Skill(MachineCraft.Skill):
		pass



class InitCraft(CachedPropertyCraft):
	class Skill(CachedPropertyCraft.Skill):
		_base: 'InitCraft'


		def init(self, instance: Optional[AbstractCrafty] = None):
			if instance is None:
				instance = self._instance
			return self._base.init(instance)


	def init(self, instance: AbstractCrafty):
		return self._process_init_val(instance, self._get_instance_val(instance))


	def _process_init_val(self, instance, val):
		return val



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






