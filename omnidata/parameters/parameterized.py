
from typing import List, Dict, Tuple, Optional, Union, Any, Hashable, Sequence, Callable, Generator, Type, Iterable, \
	Iterator, NamedTuple, ContextManager
import types
import inspect
from pprint import pprint
import logging
from collections import OrderedDict
from omnibelt import split_dict, unspecified_argument, agnosticmethod, OrderedSet, \
	extract_function_signature, method_wrapper, agnostic, Modifiable

from .abstract import AbstractParameterized
from .hyperparameters import _hyperparameter_property, HyperparameterBase


class ParameterizedBase(AbstractParameterized):
	_registered_hparams = None
	def __init_subclass__(cls, skip_auto_registration=False, **kwargs):
		super().__init_subclass__(**kwargs)
		cls._registered_hparams = OrderedSet()
		if not skip_auto_registration:
			for key, val in cls.__dict__.items():
				if isinstance(val, _hyperparameter_property):
					val.register_with(cls, key)

	def __init__(self, *args, **kwargs):
		# self._registered_hparams = self._registered_hparams.copy()
		super().__init__(*args, **self._extract_hparams(kwargs))

	class _find_missing_hparam:
		def __init__(self, base, **kwargs):
			super().__init__(**kwargs)
			self.base = base

		def __call__(self, name, default=inspect.Parameter.empty):
			value = getattr(self.base, name, default)
			# if isinstance(value, HyperparameterBase):
			# 	value = value.get_value(self.base)
			if value is inspect.Parameter.empty:
				raise KeyError(name)
			return value

	@agnostic
	def fill_hparams(self, fn, args=None, kwargs=None, **finder_kwargs) -> Dict[str, Any]:
		params = extract_function_signature(fn, args=args, kwargs=kwargs, allow_positional=False,
		                                    default_fn=self._find_missing_hparam(self), **finder_kwargs)

		return params

	@agnostic
	def _extract_hparams(self, kwargs):
		for name, _ in self.named_hyperparameters():
			if name in kwargs:
				setattr(self, name, kwargs.pop(name))
		return kwargs

	Hyperparameter = HyperparameterBase

	@classmethod
	def _register_hparam(cls, name, param):
		if not getattr(param, 'hidden', False):
			cls._registered_hparams.add(name)
		assert name is not None, f'No name provided for {param}'
		setattr(cls, name, param)
		return param

	@classmethod
	def register_hparam(cls, name: Optional[str] = None, _instance: Optional[Hyperparameter] = None, *,
	                    default: Optional[Any] = unspecified_argument, **kwargs):
		_instance = cls.Hyperparameter(name=name, default=default, **kwargs) \
			if _instance is None else cls.Hyperparameter.extract_from(_instance)
		if name is None:
			name = _instance.name
		return cls._register_hparam(name, _instance)

	@agnostic
	def reset_hparams(self):
		for param in self.hyperparameters():
			param.reset()

	@agnostic
	def get_hparam(self, key, default=unspecified_argument):
		val = inspect.getattr_static(self, key, unspecified_argument)
		if val is unspecified_argument:
			if default is unspecified_argument:
				raise AttributeError(f'{self.__class__.__name__} has no attribute {key}')
			return default
		return val

	@agnostic
	def hyperparameters(self):
		for key, val in self.named_hyperparameters():
			yield val

	@agnostic
	def named_hyperparameters(self):
		for key in self._registered_hparams:
			val = inspect.getattr_static(self, key, None)
			if val is not None:
				yield key, val

	@classmethod
	def inherit_hparams(cls, *names):
		for name in reversed(names):
			cls.register_hparam(name, cls.get_hparam(name))
			cls._registered_hparams.discard(name)
			cls._registered_hparams.insert(0, name)


class ModifiableParameterized(ParameterizedBase, Modifiable):
	@classmethod
	def inject_mods(cls, *mods, name=None):
		product = super().inject_mods(*mods, name=name)
		product.inherit_hparams(*[key for src in [*reversed(mods), cls]
		                          for key, param in src.named_hyperparameters()])
		return product



class inherit_hparams:
	def __init__(self, *names: Union[str, ParameterizedBase], **kwargs):
		self.names = names
		self.kwargs = kwargs

	class OwnerNotParametrized(Exception):
		pass

	_inherit_fn_name = 'inherit_hparams'

	def __call__(self, cls):
		try:
			inherit_fn = getattr(cls, self._inherit_fn_name)
		except AttributeError:
			raise self.OwnerNotParametrized(f'{cls} must be a subclass of {ParameterizedBase}')
		else:
			inherit_fn(*self.names, **self.kwargs)
		return cls



class with_hparams(method_wrapper):
	@staticmethod
	def process_args(args, kwargs, owner, instance, fn):
		base = owner if instance is None else instance
		return base.fill_hparams(fn, args, kwargs)














