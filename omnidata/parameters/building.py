from typing import Dict, Tuple, Optional, Any, Callable, Type

import logging
from omnibelt import unspecified_argument, Class_Registry, agnostic, Modifiable, inject_modifiers
from omnibelt.tricks import auto_methods, dynamic_capture, extract_function_signature
import omnifig as fig

from .abstract import AbstractBuilder
from .hyperparameters import HyperparameterBase
from .parameterized import ParameterizedBase
from ..structure import spaces

prt = logging.Logger('Building')
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(levelname)s: %(msg)s'))
ch.setLevel(0)
prt.addHandler(ch)


class BuilderBase(AbstractBuilder, ParameterizedBase):
	pass


class BuildableBase(BuilderBase):
	@classmethod
	def product(cls, *args, **kwargs) -> Type:
		return cls

	@agnostic
	def build(self, *args, **kwargs):
		return self.product(*args, **kwargs)(*args, **kwargs)


class ConfigBuilder(BuilderBase, fig.Configurable):
	class _config_builder_type(fig.Configurable._config_builder_type):
		def __init__(self, product, config, *, target_name='__init__', silent=None):
			super().__init__(product, config, silent=silent)
			self.target_name = target_name

		def build(self, *args, **kwargs):
			init_capture = dynamic_capture(self.configurable_parents(self.product),
			                               self.fixer, self.target_name).activate()

			self.product._my_config = self.config

			target = self.product if self.target_name == '__init__' else getattr(self.product, self.target_name)
			obj = target(*args, **kwargs)

			del self.product._my_config
			obj._my_config = self.config

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


class ModifiableProduct(BuilderBase):
	_product_mods = ()

	@staticmethod
	def _modify_product(product, *mods, name=None):
		if issubclass(product, Modifiable):
			return product.inject_mods(*mods, name=name)
		return inject_modifiers(product, *mods, name=name)

	@agnostic
	def product_base(self, *args, **kwargs):
		raise NotImplementedError

	@agnostic
	def modded(self, *mods):
		self._product_mods = [*self._product_mods, *mods]
		return self

	@agnostic
	def vanilla(self):
		self._product_mods = ()
		return self

	@agnostic
	def mods(self):
		yield from self._product_mods

	@agnostic
	def product(self, *args, **kwargs) -> Type:
		return self._modify_product(self.product_base(*args, **kwargs), *self._product_mods)


# @fig.creator('build')
class BuildCreator(fig.ConfigNode.DefaultCreator): # creates using build() instead of __init__()
	@staticmethod
	def _modify_component(component, modifiers=()):
		if issubclass(component, ModifiableProduct):
			cls = component.cls
			mods = [mod.cls for mod in modifiers]
			return cls.modded(*mods)
		elif len(modifiers):
			raise NotImplementedError(f'Builders must subclass ModifiableProduct to use modifiers')
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

		if isinstance(cls, ModifiableProduct):
			cls.vanilla()

		config._trace = None
		return obj



class AutoBuilder(BuilderBase, auto_methods, wrap_mro_until=True,
                  inheritable_auto_methods=['build', 'product', 'validate']): # TODO: buildable should include __init__

	class MissingArgumentsError(TypeError):
		def __init__(self, src, method, missing, *, msg=None):
			if msg is None:
				msg = f'{src.__name__}.{method.__name__} missing {len(missing)} ' \
				      f'required arguments: {", ".join(map(str,missing))}'
			super().__init__(msg)
			self.missing = missing
			self.src = src
			self.method = method

	@classmethod
	def _auto_method_call(cls, self: Optional[auto_methods], src: Type, method: Callable,
	                      args: Tuple, kwargs: Dict[str, Any]):
		# base = (cls if method.__name__ == '__init__' else src) if self is None else self
		base = src if self is None else self
		fixed_args, fixed_kwargs, missing = extract_function_signature(method, args=args, kwargs=kwargs,
		                                                               allow_positional=True, include_missing=True,
		                                                               default_fn=base._find_missing_hparam(base))
		# fixed_args, fixed_kwargs, missing = base.fill_hparams(method, args=args, kwargs=kwargs, include_missing=True)
		if len(missing):
			raise base.MissingArgumentsError(src, method, missing)
		return method(*fixed_args, **fixed_kwargs)


builder_registry = Class_Registry()
register_builder = builder_registry.get_decorator()
get_builder = builder_registry.get_class


class MultiBuilderBase(BuilderBase):
	_IdentParameter = HyperparameterBase

	def __init_subclass__(cls, _register_ident=False, **kwargs):
		super().__init_subclass__(**kwargs)
		if _register_ident:
			cls._register_hparam('ident', cls._IdentParameter(name='ident', required=True))

	class NoProductFound(KeyError):
		pass

	@agnostic
	def available_products(self):
		return {}

	@agnostic
	def product(self, ident, **kwargs):
		product = self.available_products().get(ident, None)
		if product is None:
			raise self.NoProductFound(ident)
		return product

	@agnostic
	def build(self, ident, **kwargs):
		product = self.product(ident)
		if isinstance(product, AbstractBuilder):
			return product.build(**kwargs)
		return product(**kwargs)

	@agnostic
	def validate(self, product):
		if isinstance(product, str):
			return self.build(product)
		return product



class RegistryBuilderBase(MultiBuilderBase):
	Product_Registry = Class_Registry
	_product_registry: Product_Registry = None
	_registration_node = None

	def __init__(self, ident=None, **kwargs):
		if ident is None:
			ident = self.ident
		super().__init__(ident=ident, **kwargs)


	class _IdentParameter(MultiBuilderBase.Hyperparameter):
		IdentSpace = spaces.Selection

		def __init__(self, *, space=None, **kwargs):
			if space is None:
				space = self.IdentSpace()
			super().__init__(space=space, **kwargs)

		def set_default_value(self, value):
			self.default = value
			if value not in self.space.values:
				self.space.values.append(value)
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

	@classmethod
	def find_product_entry(cls, ident, default=unspecified_argument):
		entry = cls._registration_node._product_registry.find(ident, None)
		if entry is None:
			if default is not unspecified_argument:
				return default
			raise cls.NoProductFound(ident)
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
	def product(self, ident, **kwargs): # <------------------
		entry = self.find_product_entry(ident)
		return entry.cls



class ClassBuilderBase(RegistryBuilderBase):
	'''Automatically register subclasses and add them to the product_registry.'''

	_class_builder_delimiter = '/'
	_class_builder_terms = ()
	def __init_subclass__(cls, ident=None, is_default=False, as_branch=False, **kwargs):
		super().__init_subclass__(**kwargs)
		if ident is not None:
			if as_branch:
				cls._class_builder_terms = (*cls._class_builder_terms, ident)
			else:
				addr = cls._class_builder_delimiter.join((*cls._class_builder_terms, ident))
				cls.ident = addr
				cls.register_product(addr, cls, is_default=is_default)






