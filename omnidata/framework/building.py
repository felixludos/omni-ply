from typing import List, Dict, Tuple, Optional, Union, Any, Hashable, Sequence, Callable, Type, \
	Iterable, Iterator
import inspect

import logging
from collections import UserDict
from omnibelt import unspecified_argument, Class_Registry, extract_function_signature, agnostic, agnosticproperty
from omnibelt.nodes import AddressNode
from omnibelt.tricks import auto_methods
from .hyperparameters import Parameterized, spaces, hparam, inherit_hparams, with_hparams, Hyperparameter


prt = logging.Logger('Building')
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(levelname)s: %(msg)s'))
ch.setLevel(0)
prt.addHandler(ch)



class Builder(Parameterized):
	@staticmethod
	def validate(product, *args, **kwargs):
		return product

	@staticmethod
	def product(*args, **kwargs) -> Type:
		raise NotImplementedError

	@staticmethod
	def build(*args, **kwargs):
		raise NotImplementedError

	@staticmethod
	def plan(*args, **kwargs) -> Iterator[Tuple[str, Hyperparameter]]:
		raise NotImplementedError

	@agnostic
	def full_spec(self, spec=None):
		spec = super().full_spec(spec)
		spec.include(self.plan())
		return spec


class Buildable(Builder):
	@classmethod
	def product(cls, *args, **kwargs) -> Type:
		return cls

	@agnostic
	def build(self, *args, **kwargs):
		return self.product(*args, **kwargs)(*args, **kwargs)

	@agnostic
	def plan(self, *args, **kwargs) -> Iterator[Tuple[str, Hyperparameter]]:
		return self.full_spec()

	@agnostic
	def full_spec(self, spec=None):
		return super(Builder, self).full_spec(spec=spec)


class AutoBuilder(Builder, auto_methods,
                  inheritable_auto_methods=['__init__', 'build', 'product', 'plan', 'validate']):

	class MissingArgumentsError(TypeError):
		def __init__(self, src, method, missing, *, msg=None):
			if msg is None:
				msg = f'{src.__name__}.{method.__name__} missing {len(missing)} ' \
				      f'required arguments: {", ".join(missing)}'
			super().__init__(msg)
			self.missing = missing
			self.src = src
			self.method = method

	@classmethod
	def _auto_method_call(cls, self: Optional[auto_methods], src: Type, method: Callable,
	                      args: Tuple, kwargs: Dict[str, Any]):
		# base = (cls if method.__name__ == '__init__' else src) if self is None else self
		base = src if self is None else self
		fixed_args, fixed_kwargs, missing = base.fill_hparams(method, args=args, kwargs=kwargs, include_missing=True)
		if len(missing):
			raise base.MissingArgumentsError(src, method, missing)
		return method(*fixed_args, **fixed_kwargs)

	# def full_spec(self, spec=None):



	# class Specification:
	# 	def find(self, key):
	# 		raise NotImplementedError
	#
	# 	def has(self, key):
	# 		raise NotImplementedError



builder_registry = Class_Registry()
register_builder = builder_registry.get_decorator()
get_builder = builder_registry.get_class


class MultiBuilder(Builder):
	_IdentParameter = Hyperparameter

	def __init_subclass__(cls, _register_ident=False, **kwargs):
		super().__init_subclass__(**kwargs)
		if _register_ident:
			cls.register_hparam('ident', cls._IdentParameter(required=True))

	class NoProductFound(KeyError):
		pass

	@agnostic
	def available_products(self):
		return {}

	@agnostic
	def product(self, ident):
		product = self.available_products().get(ident, None)
		if product is None:
			raise self.NoProductFound(ident)
		return product

	@agnostic
	def plan(self, ident, *args, **kwargs):
		try:
			product = self.product(ident)
		except self.NoProductFound:
			product = None

		if isinstance(product, Builder):
			return product.plan(*args, **kwargs)
		elif isinstance(product, Parameterized):
			yield from product.named_hyperparameters()
		else:
			yield from self.named_hyperparameters()

	@agnostic
	def build(self, ident, *args, **kwargs):
		product = self.product(ident)
		if isinstance(product, Builder):
			return product.build(*args, **kwargs)
		return product(*args, **kwargs)

	@agnostic
	def validate(self, product):
		if isinstance(product, str):
			return self.build(product)
		return product


class RegistryBuilder(MultiBuilder):
	Product_Registry = Class_Registry
	_product_registry: Product_Registry = None
	_registration_node = None


	class _IdentParameter(MultiBuilder.Hyperparameter):
		def __init__(self, *, space=None, **kwargs):
			if space is None:
				space = spaces.Selection()
			super().__init__(space=space, **kwargs)

		def set_default_value(self, value):
			self.default = value
			if value not in self.values:
				self.values.append(value)
			return self


	def __init_subclass__(cls, create_registry=None, default_ident=unspecified_argument,
	                      _register_ident=None, **kwargs):
		if _register_ident is not None:
			prt.warning(f'`register_ident` should not be used with `RegistryBuilder`')
		prev_ident_hparam = None
		if create_registry is None:
			create_registry = cls._registration_node is None
			prev_ident_hparam = cls.get_hparam('ident', None)
		super().__init_subclass__(_register_ident=create_registry, **kwargs)
		if create_registry:
			ident_hparam = cls.get_hparam('ident', None)
			if ident_hparam is not None and prev_ident_hparam is not None:
				ident_hparam.values.extend(prev_ident_hparam.values)
			cls._product_registry = cls.Product_Registry()
			cls._registration_node = cls
		if default_ident is not unspecified_argument:
			cls._set_default_product(default_ident)


	@classmethod
	def _set_default_product(cls, ident):
		return cls._registration_node.get_hparam('ident').set_default_value(ident)

	def find_product_entry(self, ident, default=unspecified_argument):
		entry = self._registration_node._product_registry.find(ident, None)
		if entry is None:
			if default is not unspecified_argument:
				return default
			raise self.NoProductFound(ident)
		return entry

	@classmethod
	def register_product(cls, name, product, is_default=False, **kwargs):
		cls._registration_node._product_registry.new(name, product, **kwargs)
		if is_default:
			cls._set_default_product(name)

	@classmethod
	def get_product_registration_decorator(cls):
		return cls._registration_node._product_registry.get_decorator()


	@agnostic
	def available_products(self):
		return {ident: entry.cls for ident, entry in self._registration_node._product_registry.items()}

	@agnostic
	def product(self, ident):
		entry = self.find_product_entry(ident)
		return entry.cls



class AutoClassBuilder(RegistryBuilder):
	'''Automatically register subclasses and add them to the product_registry.'''

	def __init_subclass__(cls, ident=None, is_default=False, **kwargs):
		super().__init_subclass__(**kwargs)
		if ident is not None:
			cls.ident = ident
			cls.register_product(ident, cls, is_default=is_default)







