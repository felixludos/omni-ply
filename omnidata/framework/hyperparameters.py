
from typing import List, Dict, Tuple, Optional, Union, Any, Hashable, Sequence, Callable, Generator, Type, Iterable, \
	Iterator, NamedTuple, ContextManager
import types
import inspect
from pprint import pprint
import logging
from collections import OrderedDict
from omnibelt import split_dict, unspecified_argument, agnosticmethod, OrderedSet, \
	extract_function_signature, method_wrapper, agnostic, agnosticproperty, \
	defaultproperty, autoproperty, referenceproperty, smartproperty, TrackSmart, Tracer


prt = logging.Logger('Hyperparameters')
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(levelname)s: %(msg)s'))
ch.setLevel(0)
prt.addHandler(ch)


class _hyperparameter_property(defaultproperty):
	def register_with(self, obj, name):
		raise NotImplementedError


# manual -> cache -> config -> (builder) -> fget -> default

class HyperparameterBase(_hyperparameter_property, autoproperty):
	# space = defaultproperty(None)
	# required = defaultproperty(False)
	# hidden = defaultproperty(False)
	# fixed = defaultproperty(False)

	@classmethod
	def extract_from(cls, param: 'HyperparameterBase', **kwargs):
		info = {
			'name': param.name,
			'src': param.src,
			'default': param.default,
			'hidden': param.hidden,
			'required': param.required,
			'space': param.space,
			'fixed': param.fixed,
			'cache': param.cache,
			'fget': param.fget,
			'fset': param.fset,
			'fdel': param.fdel,
		}
		info.update(kwargs)
		return cls(**info)

	def __init__(self, default=unspecified_argument, *, space=None, required=False, hidden=False, fixed=False,
	             **kwargs):
		# if space is unspecified_argument:
		# 	space = self.space
		# if hidden is unspecified_argument:
		# 	hidden = self.hidden
		# if required is unspecified_argument:
		# 	required = self.required
		# if fixed is unspecified_argument:
		# 	fixed = self.fixed
		super().__init__(default=default, **kwargs)
		self.space = space
		self.required = required
		self.hidden = hidden
		self.fixed = fixed


	def copy(self, *, space=unspecified_argument, hidden=unspecified_argument,
	         required=unspecified_argument, fixed=unspecified_argument,
	         **kwargs):
		if space is unspecified_argument:
			space = self.space
		if hidden is unspecified_argument:
			hidden = self.hidden
		if required is unspecified_argument:
			required = self.required
		if fixed is unspecified_argument:
			fixed = self.fixed
		return super().copy(space=space, hidden=hidden, required=required, fixed=fixed, **kwargs)

	def __str__(self):
		name = '' if self.name is None else self.name
		default = '' if self.default is self.unknown else f', default={self.default}'
		return f'{self.__class__.__name__}({name}{default})'

	def __repr__(self):
		name = f'{id(self)[-8:]}' if self.name is None else self.name
		return f'<{self.__class__.__name__}:{name}>'

	def register_with(self, obj, name, **kwargs):
		if name != self.name:
			self = self.copy(name=name, **kwargs)
		return obj.register_hparam(self.name, self)

	def validate_value(self, value):
		return value

	def create_value(self, base, owner=None): # TODO: maybe make thread-safe by using a lock
		return self.validate_value(super().create_value(base, owner=owner))
		
	def update_value(self, base, value):
		return super().update_value(base, self.validate_value(value))

	# def _get_cached_value(self, base):
	# 	if base is self.src:
	# 		return self.cached_value
	# 	return super()._get_cached_value(base)
	#
	# def _set_cached_value(self, base, value):
	# 	if base is self.src:
	# 		self.cached_value = value
	# 	else:
	# 		super()._set_cached_value(base, value)
	#
	# def _clear_cache(self, base):
	# 	if base is self.src:
	# 		self.cached_value = self.unknown
	# 	else:
	# 		super()._clear_cache(base)

	
class ConfigHyperparameter(HyperparameterBase):
	# aliases = defaultproperty(None)
	# silent = defaultproperty(None)

	def __init__(self, default=unspecified_argument, *, aliases=None, silent=None, **kwargs):
		# if aliases is unspecified_argument:
		# 	aliases = self.aliases
		# if silent is unspecified_argument:
		# 	silent = self.silent
		super().__init__(default=default, **kwargs)
		self.aliases = aliases
		self.silent = silent

	@classmethod
	def extract_from(cls, param: 'HyperparameterBase', **kwargs):
		return super().extract_from(param, aliases=getattr(param, 'aliases', None),
		                            silent=getattr(param, 'silent', None), **kwargs)
		
	def copy(self, *, aliases=unspecified_argument, silent=unspecified_argument, required=unspecified_argument,
	         **kwargs):
		if aliases is unspecified_argument:
			aliases = self.aliases
		if silent is unspecified_argument:
			silent = self.silent
		return super().copy(aliases=aliases, silent=silent, **kwargs)

	def _extract_from_config(self, config, name, aliases, default, silent):
		# can be changed to use peek or create for extra features
		return config.pulls(name, *aliases, default=default, silent=silent)

	def create_value(self, base, owner=None):  # TODO: maybe make thread-safe by using a lock
		if not isinstance(base, type): # base is and instance
			config = getattr(base, 'my_config', None)
			default = config._empty_default if (self.default is self.unknown or self.fget is not None) else self.default

			if config is not None:
				try:
					result = self._extract_from_config(config, self.name, self.aliases, default, self.silent)
				except config.SearchFailed:
					pass
				else:
					return self.validate_value(result)
		return super().create_value(base, owner=owner)


class RefHyperparameter(HyperparameterBase): # TODO: test, a lot
	name = referenceproperty('ref')
	default = referenceproperty('ref')
	cache = referenceproperty('ref')

	hidden = referenceproperty('ref')
	space = referenceproperty('ref')
	required = defaultproperty('ref')
	fixed = defaultproperty('ref')

	fget = referenceproperty('ref')
	fset = referenceproperty('ref')
	fdel = referenceproperty('ref')

	def __init__(self, ref=None, **kwargs):
		super().__init__(**kwargs)
		self.ref = ref

	def copy(self, *, ref=unspecified_argument, **kwargs):
		if ref is unspecified_argument:
			ref = None
		return super().copy(ref=ref, **kwargs)

	def register_with(self, obj, name):
		return super().register_with(obj, name, ref=self)


class hparam(_hyperparameter_property):
	def __init__(self, default=unspecified_argument, **info):
		assert 'name' not in info, 'Cannot manually set name in hparam'
		super().__init__(default=default)
		self.info = info

	_default_base = HyperparameterBase
	_registration_fn_name = 'register_hparam'


	def register_with(self, obj, name):
		reg_fn = getattr(obj, self._registration_fn_name)
		kwargs = self._get_registration_args()
		if reg_fn is None:
			if self._default_base is None:
				raise ValueError(f'No registration function found on {obj} and no default base set')
			setattr(obj, self.name, self._default_base(name, **kwargs))
		else:
			reg_fn(name, **kwargs)


	def _get_registration_args(self):
		kwargs = self.info.copy()
		if self.default is not self.unknown:
			kwargs['default'] = self.default
		kwargs['fget'] = self.fget
		kwargs['fset'] = self.fset
		kwargs['fdel'] = self.fdel
		kwargs['src'] = self.src
		return kwargs


