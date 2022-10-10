from typing import List, Dict, Tuple, Optional, Union, Any, Hashable, Sequence, Callable, Type, \
	Iterable, Iterator
import inspect
from collections import UserDict
from omnibelt import unspecified_argument, Class_Registry, extract_function_signature, agnostic, agnosticproperty
from omnibelt.tricks import auto_methods
from .hyperparameters import Parameterized, spaces, hparam, inherit_hparams, with_hparams, Hyperparameter


class Buildable:
	@agnosticmethod
	def full_spec(self, fmt='{}', fmt_rule='{parent}.{child}', include_machines=True):
		raise NotImplementedError

	pass


class Builder(Parameterized):
	@staticmethod
	def product(*args, **kwargs) -> Type:
		raise NotImplementedError

	@staticmethod
	def build(*args, **kwargs):
		raise NotImplementedError

	@staticmethod
	def plan(*args, **kwargs) -> Iterator[Tuple[str, Hyperparameter]]:
		raise NotImplementedError


	def my_build(self, *args, **kwargs):
		fixed_args, fixed_kwargs = self.fill_hparams(self.build, args=args, kwargs=kwargs)
		return self.build(*fixed_args, **fixed_kwargs)

	def my_plan(self, *args, **kwargs) -> Iterator[Tuple[str, Hyperparameter]]:
		fixed_args, fixed_kwargs = self.fill_hparams(self.plan, args=args, kwargs=kwargs)
		return self.plan(*fixed_args, **fixed_kwargs)



class AutoBuilder(Builder, auto_methods,
                  inheritable_auto_methods=['__init__', 'build', 'product', 'plan', 'my_build', 'my_plan']):

	class MissingArgumentsError(TypeError):
		def __init__(self, src, method, missing, *, msg=None):
			if msg is None:
				msg = f'{src.__name__}.{method.__name__}() missing {len(missing)} ' \
				      f'required arguments: {", ".join(missing)}'
			super().__init__(msg)
			self.missing = missing
			self.src = src
			self.method = method

	@classmethod
	def _auto_method_call(cls, self, src: Type, method: Callable, args: Tuple, kwargs: Dict[str, Any]):
		base = cls if self is None else self
		fixed_args, fixed_kwargs, missing = base.fill_hparams(method, args=args, kwargs=kwargs, include_missing=True)
		if len(missing):
			raise base.MissingArgumentsError(src, method, missing)
		return method(*fixed_args, **fixed_kwargs)



class OldBuilder(Parameterized):

	class NoProductFound(NotImplementedError):
		pass


	@agnostic
	def product(self, *args, **kwargs) -> Type:
		fixed_args, fixed_kwargs = self.fill_hparams(self._product, args, kwargs)
		return self._product(*fixed_args, **fixed_kwargs)

		
	@agnostic
	def _product(self, *args, **kwargs) -> Type:
		return self if type(self) == type else self.__class__

	
	@agnostic
	def plan(self, *args, **kwargs) -> Iterator[Tuple[str, Hyperparameter]]:
		fixed_args, fixed_kwargs = self.fill_hparams(self._plan, args, kwargs)
		return self._plan(*fixed_args, **fixed_kwargs)
		

	@agnostic
	def _plan(self, *args, **kwargs) -> Iterator[Tuple[str, Hyperparameter]]:
		product = self.product(*args, **kwargs)
		if issubclass(product, Parameterized):
			yield from product.named_hyperparameters()


	@agnostic
	def build(self, *args, **kwargs) -> Any:
		fixed_args, fixed_kwargs = self.fill_hparams(self._build, args, kwargs)
		return self._build(*fixed_args, **fixed_kwargs)
	
	
	@agnostic
	def _build(self, *args, **kwargs) -> Any:
		product = self.product(*args, **kwargs)
		return product(*args, **kwargs)


	# class Specification:
	# 	def find(self, key):
	# 		raise NotImplementedError
	#
	# 	def has(self, key):
	# 		raise NotImplementedError



builder_registry = Class_Registry()
register_builder = builder_registry.get_decorator()
get_builder = builder_registry.get_class


class ClassBuilder(Builder):
	ident = hparam(required=True)
	
	class IdentSpace(spaces.Selection):
		pass

	
	def __init_subclass__(cls, default_ident=unspecified_argument, register_ident=True, **kwargs):
		super().__init_subclass__(**kwargs)
		if register_ident:
			cls.register_hparam('ident', ref=cls.get_hparam('ident'), space=cls.IdentSpace(), default=default_ident)
		cls._update_ident_space()
	
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._update_ident_space()


	@agnostic
	def _update_ident_space(self):
		hparam = self.get_hparam('ident')
		ident_space = hparam.space
		if isinstance(ident_space, spaces.Selection):
			ident_space.replace(list(self.product_registry().keys()))
	

	@agnostic
	def _set_default_ident(self, default):
		self.get_hparam('ident').default_profile = default


	@agnostic
	def product_registry(self):
		return {}

	class NoProductFound(KeyError):
		pass

	@agnostic
	def product(self, ident):
		product = self.product_registry().get(ident, unspecified_argument)
		if product is unspecified_argument:
			raise self.NoProductFound(ident)
		return product

	# @agnostic
	# def plan(self, ident):
	# 	product = self.product(ident)
	# 	yield from product.named_hyperparameters()

	@agnostic
	def build(self, ident, *args, **kwargs):
		product = self.product(ident)
		return product(*args, **kwargs)


class RegistryBuilder(ClassBuilder):
	Product_Registry = Class_Registry
	_product_registry: Product_Registry = None
	_registration_node = None
	
	def __init_subclass__(cls, create_registry=True, register_ident=True,
	                      default_ident=unspecified_argument, **kwargs):
		super().__init_subclass__(register_ident=create_registry, default_ident=default_ident, **kwargs)
		if create_registry:
			cls._product_registry = cls.Product_Registry()
			cls._registration_node = cls
		if default_ident is not unspecified_argument:
			cls._set_default_ident(default_ident)


	def find_product(self, ident, default=unspecified_argument):
		return self.product_registry().find(ident, None)


	@agnostic
	def product(self, ident):
		entry = self.find_product(ident)
		return entry.cls
		product = super().product(ident)
		if isinstance(product, self._product_registry.entry_cls):
			return product.cls
		return product


class AutoClassBuilder(RegistryBuilder):
	'''Automatically register subclasses and add them to the product_registry.'''

	Product_Registry = Class_Registry
	_product_registry: Class_Registry = None
	_registration_node = None

	def __init_subclass__(cls, ident=None, create_registry=False, default=False,
	                      inherit_ident=False, default_ident=unspecified_argument, **kwargs):
		super().__init_subclass__(inherit_ident=create_registry, default_ident=default_ident, **kwargs)

		node = cls._registration_node
		if node is None or create_registry:
			registry = cls.Product_Registry()
			cls._product_registry = registry
			cls._registration_node = cls

		if ident is not None:
			cls.register_product(ident, cls, default=default)
			cls.inherit_hparams('ident')
			cls.register_hparam('ident', ref=cls.get_hparam('ident'), default=ident)


	@agnostic
	def _product(self, ident):
		product = super()._product(ident)
		if isinstance(product, self._product_registry.entry_cls):
			return product.cls
		return product


	@agnostic
	def product_registry(self):
		if self._product_registry is None:
			return {}
		return self._product_registry


	@agnostic
	def register_product(self, ident, product, default=False, **kwargs):
		ident_hparam = self._registration_node.get_hparam('ident')
		ident_hparam.space.append(ident)
		if default:
			self._set_default_ident(ident)
		self._product_registry.new(ident, product, **kwargs)








