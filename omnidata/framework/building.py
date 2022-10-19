from typing import List, Dict, Tuple, Optional, Union, Any, Hashable, Sequence, Callable, Type, \
	Iterable, Iterator
import inspect

import logging
from collections import UserDict
from omnibelt import unspecified_argument, Class_Registry, extract_function_signature, agnostic, agnosticproperty, \
	Modifiable, inject_modifiers
from omnibelt.nodes import AddressNode
from omnibelt.tricks import auto_methods, dynamic_capture
import omnifig as fig

from .hyperparameters import HyperparameterBase
from .parameterized import Parameterized
from . import spaces

prt = logging.Logger('Building')
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(levelname)s: %(msg)s'))
ch.setLevel(0)
prt.addHandler(ch)


class AbstractBuilder(Parameterized):
	@staticmethod
	def validate(product, *args, **kwargs):
		return product

	@staticmethod
	def product(*args, **kwargs) -> Type:
		raise NotImplementedError

	@staticmethod
	def build(*args, **kwargs):
		raise NotImplementedError


class BuildableBase(AbstractBuilder):
	@classmethod
	def product(cls, *args, **kwargs) -> Type:
		return cls

	@agnostic
	def build(self, *args, **kwargs):
		return self.product(*args, **kwargs)(*args, **kwargs)


class ConfigBuilder(AbstractBuilder, fig.Configurable):
	class _config_builder_type(fig.Configurable._config_builder_type):
		def __init__(self, product, config, *, target_name='__init__', silent=None):
			super().__init__(product, config, silent=silent)
			self.target_name = target_name

		def build(self, *args, **kwargs):
			init_capture = dynamic_capture(self.configurable_parents(self.product),
			                               self.fixer, self.target_name).activate()

			obj = self.product(*args, **kwargs)

			init_capture.deactivate()
			return obj


	@classmethod
	def _config_builder(cls, config, silent=None, target_name='__init__'):
		return cls._config_builder_type(cls, config, target_name=target_name, silent=silent)

	@classmethod
	def build_from_config(cls, config, args: Optional[Tuple] = None, kwargs: Optional[Dict[str, Any]] = None, *,
	                     silent: Optional[bool] = None) -> Any:
		if args is None:
			args = ()
		if kwargs is None:
			kwargs = {}
		return cls._config_builder(config, target_name='build', silent=silent).build(*args, **kwargs)


class ModifiableProduct(AbstractBuilder):
	@staticmethod
	def _modify_product(product, *mods, name=None):
		if issubclass(product, Modifiable):
			return product.inject_mods(*mods, name=name)
		return inject_modifiers(product, *mods, name=name)

	@agnostic
	def product_base(self, *args, **kwargs):
		raise NotImplementedError

	@agnostic
	def product(self, *args, mods=None, **kwargs) -> Type:
		if mods is None:
			mods = []
		return self._modify_product(self.product_base(*args, **kwargs), *mods)


# @fig.creator('build')
class BuilderCreator(fig.ConfigNode.DefaultCreator):
	@staticmethod
	def _modify_component(component, modifiers=()):
		if issubclass(component, ModifiableProduct):
			return component._modify_product(component, *modifiers)
		return super()._modify_component(component, modifiers=modifiers)

	def _create_component(self, config, args: Tuple, kwargs: Dict[str, Any], silent: bool = None) -> Any:
		config.reporter.create_component(config, component_type=self.component_type, modifiers=self.modifiers,
		                                 creator_type=self._creator_name, silent=silent)

		cls = self._modify_component(self.component_entry,
		                             [self.project.find_artifact('modifier', mod) for mod in self.modifiers])

		if issubclass(cls, ConfigBuilder):
			obj = cls.build_from_config(config, args, kwargs, silent=silent)
		elif isinstance(cls, AbstractBuilder):
			settings = config.settings
			old_silent = settings.get('silent', None)
			settings['silent'] = silent
			obj = cls.build(*args, **kwargs)
			if old_silent is not None:
				settings['silent'] = old_silent
		else:
			raise NotImplementedError(f'Cannot create component of type {cls!r}')

		config._trace = None
		return obj


class AutoBuilder(AbstractBuilder, auto_methods,
                  inheritable_auto_methods=['__init__', 'build', 'product', 'validate']):

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


builder_registry = Class_Registry()
register_builder = builder_registry.get_decorator()
get_builder = builder_registry.get_class


class MultiBuilderBase(AbstractBuilder):
	_IdentParameter = HyperparameterBase

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
	def build(self, ident, *args, **kwargs):
		product = self.product(ident)
		if isinstance(product, AbstractBuilder):
			return product.build(*args, **kwargs)
		return product(*args, **kwargs)

	@agnostic
	def validate(self, product):
		if isinstance(product, str):
			return self.build(product)
		return product



class RegistryBuilderBase(MultiBuilderBase):
	Product_Registry = Class_Registry
	_product_registry: Product_Registry = None
	_registration_node = None


	class _IdentParameter(MultiBuilderBase.Hyperparameter):
		def __init__(self, *, space=None, **kwargs):
			if space is None:
				space = spaces.Selection()
			super().__init__(space=space, **kwargs)

		def set_default_value(self, value):
			self.default = value
			if value not in self.values:
				self.values.append(value)
			return self


	def __init_subclass__(cls, create_registry=None, products=None, default_ident=unspecified_argument,
	                      _register_ident=None, **kwargs):
		if _register_ident is not None:
			prt.warning(f'`register_ident` should not be used with `RegistryBuilder`')
		prev_ident_hparam = None
		if create_registry is None and products is not None:
			create_registry = True
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
		if products is not None:
			for name, product in products.items():
				cls.register_product(name, product)


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


class ClassBuilderBase(RegistryBuilderBase):
	'''Automatically register subclasses and add them to the product_registry.'''

	def __init_subclass__(cls, ident=None, is_default=False, **kwargs):
		super().__init_subclass__(**kwargs)
		if ident is not None:
			cls.ident = ident
			cls.register_product(ident, cls, is_default=is_default)



class BasicBuilder(ConfigBuilder, AutoBuilder): # not recommended as it can't handle modifiers
	pass

class Builder(ModifiableProduct, BasicBuilder, inheritable_auto_methods=['product_base']):
	pass

class Buildable(BuildableBase, Builder):
	pass


class MultiBuilder(Builder, MultiBuilderBase, wrap_existing=True):
	@agnostic
	def product_base(self, *args, **kwargs):
		return super(ModifiableProduct, self).product(*args, **kwargs)


class RegistryBuilder(MultiBuilder, RegistryBuilderBase):
	pass


class ClassBuilder(RegistryBuilder, ClassBuilderBase):
	pass




