from typing import List, Dict, Tuple, Optional, Union, Any, Hashable, Sequence, Callable, Generator, Type, Iterable, \
	Iterator, NamedTuple, ContextManager
import logging
from functools import cached_property
from omnibelt import unspecified_argument, defaultproperty, autoproperty, referenceproperty

from .abstract import AbstractHyperparameter
from .errors import MissingValueError

prt = logging.Logger('Hyperparameters')
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(levelname)s: %(msg)s'))
ch.setLevel(0)
prt.addHandler(ch)


class IgnoreUpdateFlag(ValueError):
	pass



class DefaultProperty:
	_unknown = object()

	def __init__(self, default=unspecified_argument, *, fget=None, fset=None, fdel=None, fformat=None, cache=True,
	             attrname=None, **kwargs):
		if default is unspecified_argument:
			default = self._unknown
		fget, default = self._check_fget(fget, default)
		super().__init__(**kwargs)
		self.attrname = attrname
		# if not cache:
		# 	raise NotImplementedError('cache=False not implemented') # TODO: implement
		self.cache = cache
		self.default = default
		self.fget = fget
		self.fformat = fformat
		self.fset = fset
		self.fdel = fdel


	def _check_fget(self, fget=None, default=unspecified_argument):
		if fget is None:
			if callable(default) and not isinstance(default, type) and default.__qualname__ != default.__name__:
				return default, self._unknown  # decorator has no other args
			return None, default  # no fget provided (optionally can be added with __call__)
		return fget, default  # fget was specified as keyword argument


	def setup(self, owner: Type, name: str) -> 'method_decorator':
		if self.attrname is None:
			self.attrname = name
		elif name != self.attrname:
			raise TypeError(
				"Cannot assign the same cached_property to two different names "
				f"({self.attrname!r} and {name!r})."
			)
		return self


	def __set_name__(self, owner, name):
		self.setup(owner, name)


	_MissingValueError = MissingValueError


	def __get__(self, instance, owner=None):
		if instance is None:
			return self
		return self.get_value(instance, owner=owner)


	def is_missing(self, instance):
		return self.attrname not in instance.__dict__ and self.default is self._unknown and self.fget is None


	def is_cached(self, instance):
		return self.attrname in instance.__dict__


	def get_value(self, instance=None, owner=None):
		if instance is None:
			if self.default is self._unknown:
				raise self._MissingValueError(f'No default value for {self.attrname!r} (must include instance)')
			return self.default
		if self.attrname is None:
			raise TypeError(
				"Cannot use cached_property instance without calling __set_name__ on it.")
		try:
			cache = instance.__dict__
		except AttributeError:  # not all objects have __dict__ (e.g. class defines slots)
			msg = (
				f"No '__dict__' attribute on {type(instance).__name__!r} "
				f"instance to cache {self.attrname!r} property."
			)
			raise TypeError(msg) from None
		val = cache.get(self.attrname, self._unknown)
		if val is self._unknown: # TODO: make thread safe
			if self.fget is None:
				if self.default is self._unknown:
					raise self._MissingValueError(f'No value for {self.attrname!r} property')
				return self.default
			val = self.fget.__get__(instance, owner)()
			if self.cache:
				try:
					cache[self.attrname] = val
				except TypeError:
					msg = (
						f"The '__dict__' attribute on {type(instance).__name__!r} instance "
						f"does not support item assignment for caching {self.attrname!r} property."
					)
					raise TypeError(msg) from None
		return val


	def __set__(self, instance, value):
		self.update_value(instance, value)


	_IgnoreUpdateFlag = IgnoreUpdateFlag

	def update_value(self, instance, value):
		if self.fformat is not None:
			try:
				value = self.fformat.__get__(instance, type(instance))(value)
			except self._IgnoreUpdateFlag:
				return

		if self.fset is None:
			return instance.__dict__.setdefault(self.attrname, value)

		try:
			setter = self.fset.__get__(instance, type(instance))
		except AttributeError:
			setter = self.fset

		setter(value)


	def __delete__(self, instance):
		self.remove_value(instance)


	def remove_value(self, instance):
		if self.fdel is None:
			return delattr(instance, self.attrname)

		try:
			deleter = self.fdel.__get__(instance, type(instance))
		except AttributeError:
			deleter = self.fdel

		deleter()


	def __call__(self, fn):
		return self.getter(fn)


	def copy(self, **kwargs):
		return self.__class__(default=self.default,
		                      fget=self.fget, fset=self.fset, fdel=self.fdel, fformat=self.fformat,
		                      cache=self.cache, attrname=self.attrname, **kwargs)


	def getter(self, fget):
		new = self.copy()
		new.fget = fget
		return new


	def formatter(self, fformat):
		new = self.copy()
		new.fformat = fformat
		return new


	def setter(self, fset):
		new = self.copy()
		new.fset = fset
		return new


	def deleter(self, fdel):
		new = self.copy()
		new.fdel = fdel
		return new



# TODO: add 'help' option to include custom info about the hyperparameter

class HyperparameterBase(DefaultProperty, AbstractHyperparameter): # TODO: add 'cached' option
	def __init__(self, default=unspecified_argument, *, space=None, hidden=None, required=None, **kwargs):
		super().__init__(default=default, **kwargs)
		self.space = space
		self.hidden = hidden
		self.required = required


	def setup(self, owner, name):
		out = super().setup(owner, name)
		if self.hidden is None and self.attrname.startswith('_'):
			self.hidden = True
		return out



class InheritableHyperparameter(HyperparameterBase):
	def __init__(self, default=unspecified_argument, *, inherit=None, **kwargs):
		super().__init__(default=default, **kwargs)
		self.inherit = inherit

















