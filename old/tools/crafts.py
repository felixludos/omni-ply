from typing import Tuple, List, Dict, Optional, Union, Any, Callable, Sequence, Iterator, Iterable, Type, Set

import inspect
from functools import cached_property
from collections import OrderedDict

# import torch

from omnibelt import method_decorator, agnostic, unspecified_argument, filter_duplicates, get_printer
from omnibelt.crafts import AbstractCraft, AbstractCrafty, NestableCraft, SkilledCraft, IndividualCrafty


from .abstract import Loggable, AbstractAssessible, AbstractTool
from .errors import MachineError, ToolFailedError
from .assessments import Signatured

prt = get_printer(__name__)



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


	def __init__(self, label: str, **kwargs): # TODO: infer label from function name if not specified
		super().__init__(**kwargs)
		self._label = label


	def _validate_label(self, owner, label): # TODO: may be unnecessary (-> split into a subclass)
		return label


	@property
	def label(self):
		return self._label



class CopyCraft(LabelCraft):
	def copy(self, label: str = None, *args, **kwargs):
		# new = self.__class__(label, *args, **kwargs)
		# new.__dict__.update(self.__dict__)
		# return new
		if label is None:
			label = self.label
		return self.__class__(label, *args, **kwargs)


	def __copy__(self):
		return self.copy()



class ValidatedCraft(CopyCraft):
	def _validate_label(self, owner, label):  # TODO: may be unnecessary (-> split into a subclass)
		return owner.validate_label(label)



class ReplaceableCraft(ValidatedCraft):
	def __init__(self, label: str, *, replacements=None, **kwargs):
		if replacements is None:
			replacements = {}
		super().__init__(label, **kwargs)
		self.replacements = replacements

	@staticmethod
	def _update_application(old: Dict[str,str], new: Dict[str,str]): # TODO: test for infinite loops!
		existing = {}
		for key, value in old.items():
			existing.setdefault(value, []).append(key)

		composition = {}
		for k,v in new.items():
			if k in existing: # continue mapping
				for key in existing[k]:
					composition[key] = v
			else:
				composition[k] = v
		for k,v in old.items():
			if k not in composition:
				composition[k] = v
		return composition


	def replace(self, replacements: Dict[str, str], **kwargs):
		return self.copy(replacements=self._update_application(self.replacements, replacements), **kwargs)


	def _validate_label(self, owner, label):
		return super()._validate_label(owner, self.replacements.get(label, label))



class AnalysisCraft(ReplaceableCraft, Signatured, AbstractAssessible):
	class Skill(LabelCraft.Skill, Signatured, AbstractAssessible):
		_base: 'AnalysisCraft'


		def signatures(self, owner = None):
			if owner is None:
				owner = self._instance
			yield from self._base.signatures(owner)


	def signatures(self, owner: Type[AbstractCrafty] = None):
		yield self._Signature(self._validate_label(owner, self.label))



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



class FunctionCraft(method_decorator, NestableCraft, CopyCraft):
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
		if self.label is not None and not self.label.isidentifier():
			prt.warning(f'Label {self.label} is not a valid identifier (for {owner.__name__}.{name})')
		self._name = name

		if self.wrapped is not None and isinstance(self.wrapped, method_decorator):
			self.wrapped._setup_decorator(owner, name)

		return super()._setup_decorator(owner, name)


	def setup(self, owner: Type, name: str):
		return self._setup_decorator(owner, name)


	def _get_instance_fn(self, instance: AbstractCrafty, name: Optional[str] = None):
		if name is None:
			name = self._name
		# if isinstance(instance, type):
		# 	content = self.content
		# 	return content
		fn = getattr(instance, name)
		if not hasattr(fn, '__name__'):
			if isinstance(fn, NestableCraft):
				return fn.content
			return self.content
		return fn



class FunctionToolCraft(FunctionCraft, ToolCraft):
	def _get_from(self, instance: AbstractCrafty, ctx, gizmo: str):
		return self._get_from_fn(instance, self._get_instance_fn(instance), ctx, gizmo)


	def _get_from_fn(self, instance, fn, ctx, gizmo):
		return fn(ctx)



class CustomArgumentCraft(FunctionToolCraft):
	def _get_fn_args(self, instance, fn, ctx, gizmo):
		return (), {}


	def _get_from_fn(self, instance, fn, ctx, gizmo):
		args, kwargs = self._get_fn_args(instance, fn, ctx, gizmo)
		return fn(*args, **kwargs)



class MetaArgCraft(CustomArgumentCraft):
	def _known_meta_args(self, owner) -> Iterator[str]:
		yield from ()


	def _known_input_args(self, owner) -> Iterator[str]:
		yield from ()


	def signatures(self, owner: Type[AbstractCrafty] = None):
		assert owner is not None
		label = self._validate_label(owner, self.label)
		yield self._Signature(label, inputs=tuple(self._known_input_args(owner)),
		                      meta=tuple(self._known_meta_args(owner)), fn=self._get_instance_fn(owner))



class SeededCraft(MetaArgCraft):
	_context_seed_key = 'seed'
	_context_rng_key = 'rng'

	def __init__(self, label: str = None, *, include_seed=None, include_rng=None, **kwargs):
		if include_seed and not isinstance(include_seed, str):
			include_seed = self._context_seed_key
		if include_rng and not isinstance(include_rng, str):
			include_rng = self._context_rng_key
		super().__init__(label=label, **kwargs)
		self._include_seed = include_seed
		self._include_rng = include_rng


	def _known_meta_args(self, instance):
		yield from super()._known_meta_args(instance)
		if self._include_seed:
			yield self._include_seed
		if self._include_rng:
			yield self._include_rng


	def _get_fn_args(self, instance, fn, ctx, gizmo):
		args, kwargs = super()._get_fn_args(instance, fn, ctx, gizmo)
		if self._include_seed:
			kwargs[self._include_seed] = getattr(ctx, self._context_seed_key, None)
		if self._include_rng:
			kwargs[self._include_rng] = getattr(ctx, self._context_rng_key, None)
		return args, kwargs



class AutoCraft(NestableCraft, LabelCraft):
	def __init__(self, label: Optional[str] = None, *args, **kwargs):
		super().__init__(label=label, *args, **kwargs)


	@property
	def label(self):
		if self._label is None:
			return self.content.__name__
		return self._label



class TransformableCraft(AbstractCraft):
	@staticmethod
	def _parse_fn_args(fn: Callable, *, raw: Optional[bool] = False,
	                   skip: Optional[Set[str]] = None) -> Iterator[Tuple[str, Any]]:
		params = inspect.signature(fn).parameters
		param_items = iter(params.items())
		if raw:
			next(param_items) # skip self/cls arg
		for name, param in param_items:
			if skip is None or name not in skip:
				yield name, param.default



class TransformCraft(TransformableCraft, MetaArgCraft):
	def _transform_inputs(self, owner, fn, *, raw: Optional[bool] = None):
		if raw is None:
			raw = isinstance(owner, type)
		skip = set(self._known_meta_args(owner))
		# for key, default in self._parse_fn_args(fn, raw=raw, skip=skip):
		# 	yield self._validate_label(owner, key), default
		yield from self._parse_fn_args(fn, raw=raw, skip=skip)


	_MachineError = MachineError
	def _fillin_fn_args(self, owner, fn: Callable, ctx, *, existing=None):
		# TODO: allow for arbitrary default values -> use omnibelt extract_signature

		if existing is None:
			existing = {}
		for key, default in self._transform_inputs(owner, fn, raw=False):
			name = self._validate_label(owner, key)
			try:
				existing[key] = ctx[name]
			except KeyError:
				if default is inspect.Parameter.empty:
					raise self._MachineError(key, self.label, owner)
				existing[key] = default

		return existing


	def _known_input_args(self, owner) -> Tuple:
		yield from filter_duplicates(super()._known_input_args(owner),
		        (self._validate_label(owner, key)
		         for key, default in self._transform_inputs(owner, self._get_instance_fn(owner))
		         if default is inspect.Parameter.empty))


	def _get_fn_args(self, instance, fn, ctx, gizmo):
		args, kwargs = super()._get_fn_args(instance, fn, ctx, gizmo)
		kwargs.update(self._fillin_fn_args(instance, fn, ctx))
		return args, kwargs



class SignatureCraft(TransformCraft):
	def __init__(self, signature, *, fn_name=None, label=None, **kwargs):
		if fn_name is None:
			assert signature.fn is not None, f'no function provided for signature {signature}'
			fn_name = signature.fn.__name__
		if label is None:
			label = signature.output
		else:
			signature.output = label
		super().__init__(label=label, **kwargs)
		self._fn_name = fn_name
		self._signature = signature


	_MachineError = MachineError
	def _fillin_fn_args(self, owner, fn: Callable, ctx, *, existing=None):
		# TODO: allow for arbitrary default values -> use omnibelt extract_signature
		if len(self._signature.meta):
			raise NotImplementedError # TODO

		inputs = [existing[key] if existing is not None and key in existing else ctx[key]
		          for key in self._known_input_args(owner)]
		return inputs


	def replace(self, replacements: Dict[str, str], **kwargs):
		new = super().replace(replacements, **kwargs)
		new._signature = self._signature.replace(replacements)
		return new


	def _known_meta_args(self, owner) -> Iterator[str]:
		yield from self._signature.meta


	def _known_input_args(self, owner) -> Iterator[str]:
		yield from self._signature.inputs


	def signatures(self, owner: Type[AbstractCrafty] = None):
		yield self._signature



class MachineCraft(AutoCraft, SeededCraft, TransformCraft):
	_MachineError = MachineError
	def _fillin_fn_args(self, owner, fn: Callable, ctx, *, existing=None):
		# TODO: allow for arbitrary default values -> use omnibelt extract_signature

		if existing is None:
			existing = {}
		for key, default in self._transform_inputs(owner, fn, raw=False):
			name = self._validate_label(owner, key)
			try:
				existing[key] = ctx[name]
			except KeyError:
				if default is inspect.Parameter.empty:
					raise self._MachineError(key, self.label, owner)
				existing[key] = default

		return existing


	def _get_fn_args(self, instance, fn, ctx, gizmo):
		args, kwargs = super()._get_fn_args(instance, fn, ctx, gizmo)
		kwargs.update(self._fillin_fn_args(instance, fn, ctx))
		return args, kwargs



class MaterialCraft(AutoCraft, SeededCraft):
	pass



class ContextToolCraft(MaterialCraft):
	def _get_fn_args(self, instance, fn, ctx, gizmo):
		args, kwargs = super()._get_fn_args(instance, fn, ctx, gizmo)
		return (ctx, *args), kwargs



class BatchCraft(MaterialCraft):
	_context_batch_key = 'batch'
	def _get_fn_args(self, instance, fn, ctx, gizmo):
		args, kwargs = super()._get_fn_args(instance, fn, ctx, gizmo)
		return (getattr(ctx, self._context_batch_key, ctx), *args), kwargs


	def _known_meta_args(self, instance):
		yield self._context_batch_key
		yield from super()._known_meta_args(instance)



class SizeCraft(MaterialCraft):
	_context_size_key = 'size'
	def _get_fn_args(self, instance, fn, ctx, gizmo):
		args, kwargs = super()._get_fn_args(instance, fn, ctx, gizmo)
		return (getattr(ctx, self._context_size_key, ctx), *args), kwargs


	def _known_meta_args(self, instance):
		yield self._context_size_key
		yield from super()._known_meta_args(instance)



class IndexCraft(MaterialCraft):
	_context_indices_key = 'indices'
	def _get_fn_args(self, instance, fn, ctx, gizmo):
		args, kwargs = super()._get_fn_args(instance, fn, ctx, gizmo)
		return (getattr(ctx, self._context_indices_key, ctx), *args), kwargs


	def _known_meta_args(self, instance):
		yield self._context_indices_key
		yield from super()._known_meta_args(instance)



class SampleCraft(MaterialCraft):
	_context_size_key = 'size'
	def _get_from_fn(self, instance, fn, ctx, gizmo):
		size = getattr(ctx, self._context_size_key, None)
		args, kwargs = self._get_fn_args(instance, fn, ctx, gizmo)
		if size is None:
			return fn(*args, **kwargs)
		return torch.stack([fn(*args, **kwargs) for _ in range(size)])



class IndexSampleCraft(MaterialCraft):
	_context_index_key = 'index'
	_context_indices_key = 'indices'


	def _get_from_fn(self, instance, fn, ctx, gizmo):
		indices = getattr(ctx, self._context_indices_key, None)
		args, kwargs = self._get_fn_args(instance, fn, ctx, gizmo)
		if indices is None:
			return fn(getattr(ctx, self._context_index_key, ctx), *args, **kwargs)
		return torch.stack([fn(i, *args, **kwargs) for i in indices])


	def _known_meta_args(self, instance):
		yield self._context_index_key
		yield from super()._known_meta_args(instance)



class CachedPropertyCraft(ReplaceableCraft, cached_property):
	def __init__(self, label: str, *, func=None, **kwargs):
		super().__init__(label=label, func=func, **kwargs)


	def copy(self, label: str = None, **kwargs):
		new = super().copy(label=label, **kwargs)
		new.func = self.func
		new.attrname = self.attrname
		return new


	def is_cached(self, instance: AbstractCrafty):
		return self.attrname in instance.__dict__


	def __call__(self, func: Callable):
		self.func = func
		return self


	def _get_instance_val(self, instance: AbstractCrafty, default: Optional[Any] = unspecified_argument):
		return getattr(instance, self.attrname) if default is unspecified_argument \
			else getattr(instance, self.attrname, default)


	def update_value(self, instance: AbstractCrafty, value):
		instance.__dict__[self.attrname] = value


	def __get__(self, instance, owner=None):
		if self.func is None and self.attrname not in instance.__dict__:
			raise ToolFailedError(f'No function or value for {self.label} in {instance}')
		return super().__get__(instance, owner)

	
	def __set__(self, instance, value):
		if instance is None:
			return
		self.update_value(instance, value)



class SpaceCraft(CachedPropertyCraft): # TransformCraft
	class Skill(CachedPropertyCraft.Skill):
		_base: 'SpaceCraft'


		def change_space_of(self, gizmo: str, space: str):
			return self._base._change_space_of(self._instance, gizmo, space)


		def space_of(self, gizmo: str):
			return self._base._space_of(self._instance, gizmo)


		def is_missing(self, gizmo: str = None):
			if gizmo is None:
				gizmo = self.label
			return self._base._is_missing(self._instance, gizmo)


		def clear_space(self, gizmo: str) -> bool:
			return self._base._clear_space(self._instance, gizmo)

	
	def _change_space_of(self, instance: AbstractCrafty, gizmo, space):
		self.update_value(instance, space)


	def _space_of(self, instance: AbstractCrafty, gizmo: str = None):
		return self._get_instance_val(instance)


	def _is_missing(self, instance: AbstractCrafty, gizmo: str = None):
		return self.func is None and self.attrname not in instance.__dict__


	def _clear_space(self, instance: AbstractCrafty, gizmo: str = None):
		if self.attrname in instance.__dict__:
			del instance.__dict__[self.attrname]
			return True
		return False



class TransformedSpaceCraft(TransformableCraft, SpaceCraft): # TODO: future
	def _get_instance_val(self, instance: AbstractCrafty, default: Optional[Any] = unspecified_argument):
		fn = self.func
		if self.is_cached(instance) or fn is None \
				or len(inspect.signature(fn.__get__(instance, type(instance))).parameters) == 0:
			return super()._get_instance_val(instance, default)

		op = fn.__get__(instance, type(instance))
		bases = {}
		for name, val in self._parse_fn_args(op):
			bases[name] = instance.space_of(val) # TODO: deal with cycles

		return op(**bases)



# class SpecSpaceCraft(SpaceCraft):
# 		_missing_space_flag = object()
# 		def _space_of(self, instance: AbstractCrafty, gizmo: str = None):
# 			space = self._get_instance_val(instance, self._missing_space_flag)
# 			if space is self._missing_space_flag:
# 				return instance._default_space_of(gizmo)
# 			return space



# class SchemaSpaceCraft(SpaceCraft):
# 	_missing_space_flag = object()
# 	def _space_of(self, instance: AbstractCrafty, gizmo: str = None):
# 		space = self._get_instance_val(instance, self._missing_space_flag)
# 		if space is self._missing_space_flag:
# 			return instance._default_space_of(gizmo)
# 		return space



class ContextualSpaceCraft(SpaceCraft):
	pass



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
	'''For crafts which contain methods to create crafts, but can't be used directly themselves'''
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
	from_context = ContextToolCraft
	from_batch = BatchCraft






