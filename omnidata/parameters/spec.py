from typing import Iterable, Iterator, Union, Optional, Any, Type, Callable, Tuple, Dict, List, Sequence, Mapping
from omnibelt import agnostic, unspecified_argument, extract_function_signature
from omnibelt.nodes import AddressNode, IndexedSparseNode

import inspect
from collections import UserList

from ..features import Prepared

from .abstract import AbstractSubmodule, AbstractBuilder, AbstractParameterized, AbstractSpec
from .parameterized import ParameterizedBase
# from .building import SelfAware
from .submodules import SubmoduleBase


# TODO: add abstract spec class



class SubmoduleParameterized(ParameterizedBase):
	Submodule = SubmoduleBase

	@classmethod
	def register_submodule(cls, name=None, _instance=None, **kwargs):
		_instance = cls.Submodule(name=name, **kwargs) if _instance is None else cls.Submodule.extract_from(_instance)
		if name is None:
			name = _instance.name
		return cls._register_hparam(name, _instance)

	@agnostic
	def submodules(self):
		for key, val in self.named_submodules():
			yield val

	@agnostic
	def named_submodules(self):
		for key, val in self.named_hyperparameters():
			if isinstance(val, SubmoduleBase):
				yield key, val



class PreparedParameterized(SubmoduleParameterized, Prepared):
	@agnostic
	def _prepare_submodule(self, name, submodule, **kwargs):
		val = getattr(self, name, None)
		if isinstance(val, Prepared):
			val.prepare(**kwargs)


	@agnostic
	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)
		for name, submodule in self.named_submodules():
			self._prepare_submodule(name, submodule)

	@agnostic
	def reset(self):
		self._prepared = False
		self.reset_hparams()



class SpecBase(AddressNode, IndexedSparseNode, AbstractSpec, Prepared):
	SubNode = None

	def __init__(self, payload=None, *, info=None, base=None, src=None,
	             auto_expand=False, hidden=False, **kwargs):
		super().__init__(payload=payload, **kwargs)
		self._src = src
		self._base = base
		self._info = info # None if this is a branch node (except if its a machine)
		self._hidden = hidden
		self._auto_expand = auto_expand
		self._sub_loader = None if self._src is None else self._lazy_children_loader(self._src, **kwargs)

	@property
	def missing(self):
		return self._payload is None and (self._info is None or self.payload is self.empty_value)

	@property
	def payload(self):
		if self._payload is None:
			info = self.info
			if info is None:
				return self.empty_value
			try:
				return info.get_value(self.base)
			except info.MissingValueError:
				return self.empty_value
		return self._payload

	@property
	def base(self):
		return self._base

	@property
	def name(self):
		if self.has_parent:
			return self.parent_key

	@property
	def info(self):
		return self._info

	@property
	def is_default(self):
		info = self.info
		if info is None:
			return not any(not item.is_default for item in self)
		return not info.is_cached(self.base)

	@property
	def is_leaf(self):
		return self._src is None

	# class NotAllowed(ValueError): pass
	# def set(self, addr: str, value: Any, **kwargs) -> 'LocalNode':
	# 	raise self.NotAllowed('Specs are immutable')

	def view(self, *args, **kwargs):
		self.prepare()
		return list(self.children(*args, **kwargs))

	def _lazy_children_loader(self, src, **kwargs):
		for key, info in src.named_hyperparameters(hidden=self._hidden):
			sub = self.__class__ if self.SubNode is None else self.SubNode
			out = sub(parent_key=key, info=info, base=src, parent=self,
			          auto_expand=self._auto_expand, **kwargs)
			self._children[key] = out
			if self._auto_expand:
				out.prepare()
			yield out

	def _prepare(self, *args, **kwargs):
		super()._prepare(*args, **kwargs)
		if self._sub_loader is not None:
			for item in self._sub_loader: pass # finish the iterator
			self._sub_loader = None


	def _str_payload(self):
		if self.is_leaf:
			name = self.name
			payload = self.payload
			if payload is self.empty_value:
				return f'{name}=[missing]'
			return f'{name}={repr(payload)}'
		terms = list(map(str, self._children.keys()))
		if self._sub_loader is not None:
			terms.append('...')
		existing = ', '.join(terms)
		return existing

	def __repr__(self):
		if self.is_leaf:
			return f'<{self._str_payload()}>'
		base = self.base.__name__ if isinstance(self.base, type) else self.base.__class__.__name__ #+ '()'
		return f'{self.__class__.__name__}<{base}>({self._str_payload()})'


class StatusSpec(SpecBase):
	@property
	def required(self):
		return getattr(self.info, 'required', False)

	@property
	def status(self):
		return 'required' if self.required else 'optional'

	def _str_payload(self):
		if self.is_leaf:
			name = self.name
			payload = f'{name}:[{self.status}]'
			value = self.payload
			if value is not self.empty_value:
				payload += f'={repr(value)}'
			return payload
		return super()._str_payload()



class SubmoduleSpec(SpecBase):
	@staticmethod
	def _infer_src(param, base):
		if param is not None and isinstance(param, AbstractSubmodule):
			try:
				src = param.get_value(base)
			except param.MissingValueError:
				src = param.get_builder()
			return src

	def __init__(self, payload=None, *, info=None, base=None, src=None, **kwargs):
		if src is None:
			src = self._infer_src(info, base)
		super().__init__(payload=payload, info=info, base=base, src=src, **kwargs)

	@property
	def is_submodule(self):
		return isinstance(self.info, AbstractSubmodule)



class BuildableSpec(SubmoduleSpec):
	class _find_spec_value:
		def __init__(self, spec, **kwargs):
			super().__init__(**kwargs)
			self.spec = spec

		def __call__(self, name, default=inspect.Parameter.empty):
			item = self.spec.get(name, None)
			if item is None or item.missing:
				if default is inspect.Parameter.empty:
					raise KeyError(name)
				return default
			return item.payload


	def _populate_existing(self, target, existing):
		self.prepare()
		assert issubclass(target, AbstractParameterized), f'{target} is not parameterized'
		for name, _ in target.named_hyperparameters(hidden=True):
			if name not in existing:
				item = self.get(name, unspecified_argument)
				if item is not unspecified_argument:
					existing[name] = item.to_python()
		return existing

	def _extract_values(self, method, args=None, kwargs=None):
		fixed_args, fixed_kwargs, missing = extract_function_signature(method, args=args, kwargs=kwargs,
		                                                               allow_positional=False, include_missing=True,
		                                                               default_fn=self._find_spec_value(self))
		assert not len(missing), f'{self} missing hyperparameters: {missing}'
		return fixed_args, fixed_kwargs

	def to_python(self):
		return self.payload if self.has_payload or self.is_leaf else self.build()

	@property
	def aaa(self): # TESTING
		return self.view()

	def restore_with(self, target, *args, **kwargs):
		assert issubclass(target, AbstractParameterized), f'{target} is not parameterized'
		fixed_args, necessary_kwargs = self._extract_values(target, args=args, kwargs=kwargs)
		fixed_kwargs = self._populate_existing(target, necessary_kwargs)
		return target(*fixed_args, **fixed_kwargs)

	def restore(self, *args, **kwargs):
		base = self.base
		if not isinstance(base, type):
			base = type(base)
		return self.restore(base, *args, **kwargs)

	def build_with(self, builder, *args, **kwargs):
		base = builder if isinstance(builder, type) else type(builder)
		if not isinstance(base, AbstractBuilder):
			return self.restore_with(base, *args, **kwargs)
		fixed_args, necessary_kwargs = self._extract_values(builder.build, args=args, kwargs=kwargs)
		fixed_kwargs = self._populate_existing(builder, necessary_kwargs)
		return builder.build(*fixed_args, **fixed_kwargs)

	def build(self, *args, **kwargs):
		return self.build_with(self.base, *args, **kwargs)


# TODO: auto spec from config (given base)

# TODO: auto compilation: spec (+ config) -> code


class SpeccedBase(AbstractParameterized):
	Spec = None

	@classmethod
	def init_from_spec(cls, spec):
		return spec.restore_with(cls)

	@agnostic
	def show_spec(self, **kwargs): # convenience method
		return list(self.spec(**kwargs))

	@agnostic
	def spec(self, *, hidden=True, auto_expand=False, **kwargs):
		spec = self.Spec(src=self, base=self, hidden=hidden, auto_expand=auto_expand, **kwargs)
		if auto_expand:
			spec.prepare()
		return spec



class BuilderSpecced(SpeccedBase, AbstractBuilder):
	@agnostic
	def build_from_spec(self, spec):
		return spec.build_with(self)


class SpecBuilder(BuilderSpecced):
	@agnostic
	def build(self, *args, **kwargs):
		return self.spec().build(*args, **kwargs)



# class SpecItemBase(AbstractSpecItem):
# 	def __init__(self, name, info, base, owner=None, **kwargs):
# 		super().__init__(name, info, base, **kwargs)
# 		self._name = name
# 		self._info = info
# 		self.base = base
# 		self.owner = owner
#
# 	@property
# 	def name(self):
# 		return self._name
#
# 	@property
# 	def info(self):
# 		return self._info
#
# 	@property
# 	def value(self):
# 		try:
# 			return self.info.get_value(self.base)
# 		except self.info.MissingValueError:
# 			return self.NoValue
#
# 	@property
# 	def is_default(self):
# 		return not self.info.is_cached(self.base)
#
# 	def _str_payload(self):
# 		name = self.name
# 		value = self.value
# 		payload = None if value is self.NoValue else repr(value)
# 		return name if payload is None else f'{name}={payload}'
#
# 	def __repr__(self):
# 		base = self.base.__name__ if isinstance(self.base, type) else self.base.__class__.__name__ + '()'
# 		return f'{self.__class__.__name__}<{base}>({self._str_payload()})'
# 		return self.__str__()


# class OldSpecBase(UserList, AbstractSpec):
# 	SpecItem = SpecItemBase
#
# 	@property
# 	def base(self):
# 		if len(self):
# 			return self[0].base
#
# 	def _derivative(self, *args, **kwargs):
# 		return self.__class__(*args, **kwargs)
# 	def __getitem__(self, item):
# 		if isinstance(item, str):
# 			return self.get(item)
# 		out = super().__getitem__(item)
# 		if isinstance(out, self.__class__):
# 			return self._derivative(out)
# 		return out
#
# 	def package(self, name, info, base, **kwargs):
# 		return self.SpecItem(name, info, base, owner=self, **kwargs)
#
# 	def _expand(self, base, hidden=False, non_default=False, **kwargs):
# 		for key, info in base.named_hyperparameters(hidden=hidden):
# 			item = self.package(key, info, base, **kwargs)
# 			if non_default and item.is_default:
# 				continue
# 			yield item
#
# 	@classmethod
# 	def expand(cls, base, hidden=False, non_default=False, **kwargs):
# 		return cls()._expand(base, hidden=hidden, non_default=non_default, **kwargs)
#
# 	def __str__(self):
# 		return f'{self.__class__.__name__}({", ".join(map(str, self))})'




# class MachineSpecItem(SpecItemBase):
# 	def __init__(self, name, info, base, *, parent=None, **kwargs):
# 		super().__init__(name, info, base, **kwargs)
# 		self._parent = parent
#
# 	@property
# 	def parent(self):
# 		return self._parent
# 	@parent.setter
# 	def parent(self, value):
# 		self._parent = value
#
# 	@property
# 	def name(self):
# 		if self._parent is None:
# 			return self._name
# 		return f'{self._parent.name}.{self._name}'
#
# 	@property
# 	def is_machine(self):
# 		return isinstance(self.info, AbstractMachine)
#
# 	def expand(self, include_machines=True, expand_machines=True, **kwargs):
# 		if self.owner is None:
# 			raise ValueError(f'{self} has no owner')
# 		return self.owner.expand_spec_item(self, include_machines=include_machines,
# 		                                   expand_machines=expand_machines, **kwargs)


# class MachineSpec(OldSpecBase):
# 	SpecItem = MachineSpecItem
#
# 	@property
# 	def parent(self):
# 		if len(self):
# 			return getattr(self[0].parent, 'owner', None)
#
# 	def _expand(self, base, include_machines=True, expand_machines=True, parent=None, **kwargs):
# 		for item in super()._expand(base, parent=parent, **kwargs):
# 			is_machine = item.is_machine
# 			if include_machines or not is_machine:
# 				yield item
# 			if is_machine and expand_machines:
# 				yield self.expand_spec_item(item, include_machines=include_machines,
# 				                           expand_machines=expand_machines, **kwargs)
#
# 	@classmethod
# 	def expand_spec_item(cls, item, include_machines=True, expand_machines=True, **kwargs):
# 		value = item.value
# 		if value is item.NoValue:
# 			builder = item.info.get_builder()
# 			if builder is not None:
# 				yield from cls.expand(builder, parent=item, include_machines=include_machines,
# 				                       expand_machines=expand_machines, **kwargs)
# 		else:
# 			yield from cls.expand(value, parent=item, include_machines=include_machines,
# 			                       expand_machines=expand_machines, **kwargs)














