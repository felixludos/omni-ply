from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set

import inspect
from functools import cached_property
from collections import OrderedDict

import torch

from omnibelt import method_decorator, agnostic
from omnibelt.crafts import AbstractCraft, AbstractCrafty, NestableCraft, SkilledCraft, IndividualCrafty


from ..features import Prepared

from .abstract import AbstractSpacedTool, Loggable, AbstractAssessible
from .errors import ToolFailedError, MissingGizmoError
from .assessments import Signatured



class LabelCraft(SkilledCraft):
	class Skill(SkilledCraft.Skill):
		_base: 'LabelCraft'

		@property
		def label(self):
			return self._base.label


	def __init__(self, label: str, **kwargs):
		super().__init__(**kwargs)
		self._label = label


	@property
	def label(self):
		return self._label



class AnalysisCraft(LabelCraft, Signatured, AbstractAssessible):
	class Skill(SkilledCraft.Skill, Signatured, AbstractAssessible):
		def signatures(self, owner = None):
			if owner is None:
				owner = self._instance
			yield from self._base.signatures(owner)


	def signature(self, owner: Type[AbstractCrafty]):
		yield self._Signature(self.label)





class ToolCraft(NestableCraft, AnalysisCraft):
	class Skill(AnalysisCraft.Skill):
		_base: 'ToolCraft'

		@property
		def label(self):
			return self._base.label


		def get_from(self, ctx, gizmo: str):
			return self._base.get_from(self._instance, ctx, gizmo)


	def get_from(self, instance: AbstractCrafty, ctx, gizmo: str):
		raise NotImplementedError



class LoggingCraft(ToolCraft):
	class Skill(ToolCraft.Skill, Loggable):
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
				yield key


	def signatures(self, owner: Type[AbstractCrafty]):
		yield self._Signature(self.label, inputs=tuple(self._machine_inputs(owner)))


	def _get_from_fn(self, fn, ctx, gizmo):
		return fn(**self._fillin_fn_args(fn, ctx))



class BatchCraft(FunctionToolCraft):
	def _get_from_fn(self, fn, ctx, gizmo):
		return fn(getattr(ctx, 'batch', ctx))



class SizeCraft(FunctionToolCraft):
	def _get_from_fn(self, fn, ctx, gizmo):
		return fn(getattr(ctx, 'size', ctx))


	def signatures(self, owner: Type[AbstractCrafty]):
		yield self._Signature(self.label, meta='size')



class IndexCraft(FunctionToolCraft):
	def _get_from_fn(self, fn, ctx, gizmo):
		return fn(getattr(ctx, 'indices', ctx))


	def signatures(self, owner: Type[AbstractCrafty]):
		yield self._Signature(self.label, meta='indices')



class SampleCraft(FunctionToolCraft):
	def _get_from_fn(self, fn, ctx, gizmo):
		size = getattr(ctx, 'size', None)
		if size is None:
			return fn()
		return torch.stack([fn() for _ in range(size)])


	def signatures(self, owner: Type[AbstractCrafty]):
		yield self._Signature(self.label)



class IndexSampleCraft(FunctionToolCraft):
	def _get_from_fn(self, fn, ctx, gizmo):
		indices = getattr(ctx, 'indices', None)
		if indices is None:
			return fn(getattr(ctx, 'index', ctx))
		return torch.stack([fn(i) for i in indices])


	def signatures(self, owner: Type[AbstractCrafty]):
		yield self._Signature(self.label, meta='index')



class CachedPropertyCraft(LabelCraft, cached_property):
	def __init__(self, gizmo: str, *, func=None, **kwargs):
		super().__init__(gizmo=gizmo, func=func, **kwargs)


	def __call__(self, func: Callable):
		self.func = func
		return self


	def _get_instance_val(self, instance: AbstractCrafty):
		return getattr(instance, self.attrname)



class SpaceCraft(CachedPropertyCraft):
	class Skill(CachedPropertyCraft.Skill):
		_base: 'SpaceCraft'

		def space_of(self, gizmo: str):
			return self._base.space_of(self._instance, gizmo)


	def space_of(self, instance: AbstractCrafty, gizmo: str = None):
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



########################################################################################################################



class CraftyKit(IndividualCrafty, AbstractSpacedTool):
	class _ToolOrderer:
		def __init__(self, gizmo: str):
			self._gizmo = gizmo
			self._standard = []
			self._optionals = []
			self._defaults = []


		def add(self, skill: ToolCraft.Skill):
			if isinstance(skill, OptionalCraft.Skill):
				self._optionals.append(skill)
			elif isinstance(skill, DefaultCraft.Skill):
				self._defaults.append(skill)
			else:
				self._standard.append(skill)


		def tool_options(self):
			yield from self._standard
			yield from self._optionals
			yield from self._defaults


		def as_tool(self):
			return next(self.tool_options())


		def get_from(self, ctx, gizmo: str):
			for vendor in self.tool_options():
				try:
					return vendor.get_from(ctx, gizmo)
				except ToolFailedError:
					pass


	def _process_crafts(self):
		self._tools = {}
		self._spaces = {}
		super()._process_crafts()


	def _process_skill(self, skill: LabelCraft.Skill):
		super()._process_skill(skill)
		if isinstance(skill, ToolCraft.Skill):
			if skill.label not in self._tools:
				self._tools[skill.label] = self._ToolOrderer(skill.label)
			self._tools[skill.label].add(skill)
		if isinstance(skill, SpaceCraft.Skill):
			self._spaces.setdefault(skill.label, []).append(skill)


	def get_from(self, ctx, gizmo: str):
		if gizmo not in self._tools:
			raise MissingGizmoError(gizmo)
		return self._tools[gizmo].get_from(ctx, gizmo)


	def space_of(self, gizmo: str):
		return self._spaces[gizmo][0].space_of(self, gizmo)


	def vendors(self, gizmo: str):
		yield from self._tools[gizmo].tool_options()


	def has_gizmo(self, gizmo: str):
		return gizmo in self._tools


	def gizmos(self):
		yield from self._tools.keys()



class MaterialedCrafty(CraftyKit, Prepared): # allows materials to be initialized when prepared
	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)

		materials = {}
		for gizmo, tool in self._tools.items():
			for skill in tool.tool_options():
				if isinstance(skill, InitCraft.Skill):
					materials[gizmo] = skill.init(self)
				break
		self._tools.update(materials)


class SignaturedCrafty(CraftyKit, Signatured):
	@agnostic
	def signatures(self, owner = None) -> Iterator['AbstractSignature']:
		if isinstance(self, type):
			self: Type['SignaturedCrafty']
			for loc, key, craft in self._emit_all_craft_items():
				if isinstance(craft, Signatured):
					yield from craft.signatures(self)
		else:
			for _, tool in self._tools.items():
				if isinstance(tool, self._ToolOrderer):
					tool = tool.as_tool()
				if isinstance(tool, Signatured):
					yield from tool.signatures(self)



class AssessibleCrafty(CraftyKit, AbstractAssessible):
	@classmethod
	def assess_static(cls, assessment):
		super().assess_static(assessment)
		for owner, key, craft in cls._emit_all_craft_items():
			if isinstance(craft, AbstractAssessible):
				assessment.add_edge(cls, craft, name=key, loc=owner)
				assessment.expand(craft)


	def assess(self, assessment):
		super().assess(assessment)
		for gizmo, tool in self._tools.items():
			if isinstance(tool, self._ToolOrderer):
				tool = tool.as_tool()
			if isinstance(tool, AbstractAssessible):
				assessment.add_edge(self, tool, gizmo=gizmo)
				assessment.expand(tool)







