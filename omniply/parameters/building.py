from typing import Dict, Tuple, Optional, Any, Callable, Type

import logging
from omnibelt import unspecified_argument, Class_Registry, agnostic, Modifiable, inject_modifiers, agnosticproperty
from omnibelt.tricks import auto_methods, dynamic_capture, extract_function_signature
import omnifig as fig

from ..tools.assessments import Signatured, AbstractSignature, SimpleSignature

from .abstract import AbstractBuilder, AbstractParameterized, AbstractArgumentBuilder, \
	AbstractMultiBuilder, AbstractRegistryBuilder
from .errors import NoProductFound, MissingBranchError
from .hyperparameters import HyperparameterBase
from .parameterized import ParameterizedBase
from ..structure import spaces

prt = logging.Logger('Building')
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(levelname)s: %(msg)s'))
ch.setLevel(0)
prt.addHandler(ch)



class BuilderBase(ParameterizedBase, AbstractBuilder):
	pass




class AdaptableBuilderBase(ParameterizedBase, AbstractBuilder):
	def __call__(self, *args, **kwargs):
		return self.copy(*args, **kwargs)



class AnalysisBuilder(AbstractBuilder):
	_Signature = SimpleSignature
	def product_signatures(self, *args, **kwargs):
		product = self.product(*args, **kwargs)
		yield from product.signatures()



# class SelfAware(BuildableBase):
# 	pass
# # 	# TODO: maybe replace with SpecBuilder (or at least standardize behavior for stateful builders)
# #
# # 	def _populate_existing(self, target, existing=None):
# # 		if existing is None:
# # 			existing = {}
# # 		for name, _ in target.named_hyperparameters(hidden=True):
# # 			if name not in existing:
# # 				try:
# # 					value = getattr(self, name, unspecified_argument)
# # 				except self.Hyperparameter.MissingValueError:
# # 					continue
# # 				if value is not unspecified_argument:
# # 					if isinstance(value, SelfAware):
# # 						value = value.build_replica()
# # 					existing[name] = value
# # 		return existing
# #
# #
# # 	def build_replica(self, *args, **kwargs):
# # 		product = self.product(*args, **kwargs)
# # 		fixed_args, necessary_kwargs, missing = extract_function_signature(product, args=args, kwargs=kwargs,
# # 		                                                               allow_positional=False, include_missing=True,
# # 		                                                               default_fn=self._find_missing_hparam(self))
# # 		assert not len(missing), f'Could not find values for {missing} in {self}'
# # 		fixed_kwargs = self._populate_existing(product, necessary_kwargs)
# # 		return product(*fixed_args, **fixed_kwargs)



class ConfigBuilder(BuilderBase, AbstractArgumentBuilder, fig.Configurable):
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
		return cls._config_builder_type(cls(), config, target_name=target_name, silent=silent)


	@classmethod
	def build_from_config(cls, config, args: Optional[Tuple] = None, kwargs: Optional[Dict[str, Any]] = None, *,
	                     silent: Optional[bool] = None) -> Any:
		if args is None:
			args = ()
		if kwargs is None:
			kwargs = {}
		return cls._config_builder(config, target_name='build', silent=silent).build(*args, **kwargs)


	def build(self, *args, **kwargs):
		product = self.product(*args, **kwargs)
		kwargs = self._build_kwargs(product, *args, **kwargs)
		config = self._my_config
		if config is not None and issubclass(product, fig.Configurable):
			return product.init_from_config(config, kwargs=kwargs)
		return product(**kwargs)



class ModifiableProduct(BuilderBase, AbstractArgumentBuilder):
	_product_mods = ()

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.__dict__['_product_mods'] = self._product_mods # save current product mods to instance.__dict__


	@staticmethod
	def _modify_product(product, *mods, name=None):
		if issubclass(product, Modifiable):
			return product.inject_mods(*mods, name=name)
		new = inject_modifiers(product, *mods, name=name)
		if new is not product and issubclass(new, ParameterizedBase):
			for src in reversed(new.__bases__):
				if issubclass(src, ParameterizedBase):
					new.inherit_hparams(*src.hyperparameter_names(hidden=True))
		return new


	def product_base(self, *args, **kwargs):
		raise NotImplementedError


	def modded(self, *mods):
		self._product_mods = [*self._product_mods, *mods]
		return self


	def vanilla(self):
		self._product_mods = ()
		return self


	def mods(self):
		yield from self._product_mods


	def product(self, *args, **kwargs) -> Type:
		return self._modify_product(self.product_base(*args, **kwargs), *self._product_mods)



# @fig.creator('build')
class BuildCreator(fig.Node.DefaultCreator): # creates using build() instead of __init__()
	@staticmethod
	def _modify_component(component, modifiers=()):
		component = component.cls
		if issubclass(component, ModifiableProduct):
			mods = [mod.cls for mod in modifiers]
			return component.modded(*mods)
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



# class BuildableBase(ModifiableProduct, BuilderBase, AbstractArgumentBuilder):
# 	@classmethod
# 	def product_base(cls, *args, **kwargs) -> Type:
# 		return cls



# class AutoBuilder(BuilderBase, auto_methods, wrap_mro_until=True, # TODO: buildable should include __init__
#                   inheritable_auto_methods=['build', 'product', 'validate']):
#
# 	class MissingArgumentsError(TypeError):
# 		def __init__(self, src, method, missing, *, msg=None):
# 			if msg is None:
# 				msg = f'{src.__name__}.{method.__name__} missing {len(missing)} ' \
# 				      f'required arguments: {", ".join(map(str,missing))}'
# 			super().__init__(msg)
# 			self.missing = missing
# 			self.src = src
# 			self.method = method
#
# 	@classmethod
# 	def _auto_method_call(cls, self: Optional['AutoBuilder'], src: Type, method: Callable,
# 	                      args: Tuple, kwargs: Dict[str, Any]):
# 		# base = (cls if method.__name__ == '__init__' else src) if self is None else self
# 		base = cls if self is None else self
#
# 		fixed_args, fixed_kwargs, missing = extract_function_signature(method, args=args, kwargs=kwargs,
#                                                            allow_positional=False, include_missing=True,
#                                                            default_fn=base._find_missing_hparam(base))
# 		# fixed_args, fixed_kwargs, missing = extract_function_signature(method, args=args, kwargs=kwargs,
# 		#                                                                allow_positional=True, include_missing=True,
# 		#                                                                default_fn=base._find_missing_hparam(base))
# 		# # fixed_args, fixed_kwargs, missing = base.fill_hparams(method, args=args, kwargs=kwargs, include_missing=True)
# 		if len(missing):
# 			raise base.MissingArgumentsError(src, method, missing)
#
# 		return method(*fixed_args, **fixed_kwargs)



builder_registry = Class_Registry()
register_builder = builder_registry.get_decorator()
get_builder = builder_registry.get_class



class IdentBuilder(AbstractMultiBuilder, AbstractArgumentBuilder):
	_IdentParameter = HyperparameterBase

	def __init_subclass__(cls, _register_ident=True, default_ident=None, **kwargs):
		super().__init_subclass__(**kwargs)
		if _register_ident:
			cls.ident = cls._IdentParameter(required=True).setup(cls, 'ident')
		# cls._register_hparam('ident', cls._IdentParameter(name='ident', required=True), prepend=True)


	def __init__(self, ident=unspecified_argument, **kwargs):
		super().__init__(**kwargs)
		if ident is not unspecified_argument:
			self.ident = ident


	def build(self, ident: Optional[str] = unspecified_argument, **kwargs):
		if ident is unspecified_argument:
			ident = self.ident
		return super().build(ident=ident, **kwargs)


	def _build_kwargs(self, product, ident=unspecified_argument, **kwargs):
		if ident is unspecified_argument:
			ident = self.ident
		return super()._build_kwargs(product, ident=ident, **kwargs)



class MultiBuilderBase(IdentBuilder, ModifiableProduct):
	@classmethod
	def available_products(cls):
		return {}


	@classmethod
	def named_products(cls):
		yield from cls.available_products().items()


	def product_base(self, ident: Optional[str] = unspecified_argument, **kwargs):
		if ident is None:
			ident = self.ident
		product = self.available_products().get(ident, None)
		if product is None:
			raise self._NoProductFound(ident)
		return product



class RegistryBuilderBase(IdentBuilder, ModifiableProduct):
	class _IdentParameter(IdentBuilder._IdentParameter):
		_IdentSpace = spaces.Selection
		def __init__(self, *, space=None, **kwargs):
			if space is None:
				space = self._IdentSpace()
			super().__init__(space=space, **kwargs)


		def add_value(self, value, is_default=False):
			if value not in self.space:
				self.space.append(value)
			if is_default:
				self.default = value
			return self


	class _product_registry_type(Class_Registry, components=['owner']): pass
	_product_registry_owner = None
	_product_registry = None

	_default_products = None # these are inherited when set (unless overridden in __init_subclass__)
	_default_ident = None

	ident: _IdentParameter


	def __init_subclass__(cls, create_registry=None, default_ident=None, products=None, **kwargs):
		if create_registry is None:
			create_registry = cls._product_registry is None
		if default_ident is None:
			default_ident = cls._default_ident
		if products is None:
			products = {}
		if cls._default_products is not None:
			products.update(cls._default_products)
		super().__init_subclass__(_register_ident=create_registry, **kwargs)
		if create_registry:
			cls._product_registry = cls._product_registry_type()
			cls._product_registry_owner = cls
			for name, prod in products.items():
				cls.register_product(name, prod)

			if default_ident is not None:
				cls._register_ident(default_ident, is_default=True)


	@property
	def default_ident(self):
		return self.get_hparam('ident').default


	@classmethod
	def _register_ident(cls, ident, *, is_default=False):
		return cls.ident.add_value(ident, is_default=is_default)


	@classmethod
	def register_product(cls, name, product, *, is_default=False, **kwargs):
		registry = getattr(cls, '_product_registry', None)
		if registry is None:
			registry_name = cls.__name__ if isinstance(cls, type) else cls.__class__.__name__
			raise NotImplementedError(f'{registry_name} doesnt have a product registry')
		cls._register_ident(name, is_default=is_default)
		return registry.new(name, product, owner=cls, **kwargs)


	@classmethod
	def named_products(cls):
		for key, entry in cls._product_registry.items():
			yield key, entry.cls


	class _product_registration_decorator:
		def __init__(self, registry, name, **kwargs):
			self.registry = registry
			self.name = name
			self.kwargs = kwargs


		def __call__(self, product):
			self.registry.register_product(self.name, product, **self.kwargs)
			return product


	@classmethod
	def registration_decorator(cls, name, is_default=False, **kwargs):
		return cls._product_registration_decorator(cls, name, is_default=is_default, **kwargs)


	@classmethod
	def find_product_entry(cls, ident, default=unspecified_argument):
		entry = cls._product_registry.find(ident, None)
		if entry is None:
			if default is not unspecified_argument:
				return default
			raise cls._NoProductFound(ident)
		return entry


	def product_base(self, ident: Optional[str] = unspecified_argument, **kwargs):
		if ident is unspecified_argument:
			ident = self.ident
		entry = self.find_product_entry(ident)
		return entry.cls



class HierarchyBuilderBase(RegistryBuilderBase, create_registry=False):
	_branch_registry_type = Class_Registry
	_branch_registries = None
	_branch_name = None
	_branch_parent_registries = None
	_branch_address_delimiter = '/'
	_MissingBranchError = MissingBranchError


	def __init_subclass__(cls, branch=None, create_registry=None, parents=None, **kwargs):
		if branch is None and parents is not None:
			raise ValueError(f'{cls.__name__} is a branch but has no branch name')
		if branch is not None:
			if parents is None:
				parents = cls._product_registry_owner
			create_registry = create_registry is None or create_registry
		super().__init_subclass__(create_registry=create_registry, **kwargs)
		cls._branch_parent_registries = []
		cls._branch_registries = cls._branch_registry_type()

		if branch is not None:
			cls._branch_name = branch

		if branch is not None and parents is None:
			for base in cls.__bases__:
				if issubclass(base, HierarchyBuilderBase):
					base._branch_registries.new(branch, cls)
					# cls._branch_parent_registries.append(base)
					
		if parents is not None:
			assert branch is not None
			if isinstance(parents, (str, type)):
				parents = [parents]
			for owner in parents:
				if isinstance(owner, str):
					owner = get_builder(owner)
				if issubclass(owner, HierarchyBuilderBase):
					owner._branch_registries.new(branch, cls)
					# cls._branch_parent_registries.append(owner)


	@classmethod
	def hierarchy_registry_address(cls):
		if len(cls._branch_parent_registries) == 0:
			return cls._branch_name
		return f'{cls._branch_parent_registries[0].hierarchy_registry_address()}' \
		       f'{cls._branch_address_delimiter}{cls._branch_name}'


	@classmethod
	def branch_registries(cls):
		for branch, entry in cls._branch_registries.items():
			yield branch, entry.cls


	@classmethod
	def registry_hierarchy(cls):
		yield cls
		for entry in cls._branch_registries.values():
			yield from entry.cls.registry_hierarchy()


	@classmethod
	def product_hierarchy(cls):
		yield from cls.named_products()
		for entry in cls._branch_registries.values():
			for name, product in entry.cls.product_hierarchy():
				yield f'{entry.name}{cls._branch_address_delimiter}{name}', product


	@classmethod
	def find_product_entry(cls, ident, default=unspecified_argument):
		try:
			return super().find_product_entry(ident, default=default)
		except cls._NoProductFound:
			terms = ident.split(cls._branch_address_delimiter, 1)
			if len(terms) > 1:
				branch, ident = terms
				if branch in cls._branch_registries:
					return cls._branch_registries.get_class(branch).find_product_entry(ident, default=default)
				raise cls._MissingBranchError(branch, ident) from None
			raise



class RegisteredProductBase:
	ident = None
	_owning_registry = None

	def __init_subclass__(cls, ident=None, registry=None, is_default=False, **kwargs):
		super().__init_subclass__(**kwargs)
		if ident is None:
			ident = getattr(cls, 'ident', None)
		else:
			setattr(cls, 'ident', ident)
		if registry is None:
			registry = getattr(cls, '_owning_registry', None)
		else:
			if isinstance(registry, str):
				registry = get_builder(registry) # TODO: better error handling
			setattr(cls, '_owning_registry', registry)
		if ident is not None and registry is not None:
			registry.register_product(ident, cls, is_default=is_default)
			cls._owning_registry = registry



# class BoundRegistryBuilderBase(RegistryBuilderBase): # TODO: future
# 	_parent_registries = None
# 	_child_registries = None
#
# 	def __init_subclass__(cls, **kwargs):
# 		super().__init_subclass__(**kwargs)
# 		for base in cls.__bases__: # TODO: test extensively!
# 			if isinstance(base, RegistryBuilderBase) and base._product_registry is not None:
# 				cls._parent_registries.append(base._product_registry)
# 			if isinstance(base, BoundRegistryBuilderBase):
# 				base._child_registries.append(cls)


# class AutoRegistryBuilderBase(MultiBuilderBase):
# 	'''
# 	Issue differentiating a "builder" instance and a "product" instance. Specifically,
# 	which hparams are for the builder, and which ones are for the product.
# 	Conclusion: for now, separate the registration class from the registered product classes
#
# 	Example:
#
# 	```python
#
# 	class MyModels(ClassBuilder, nn.Module, default_ident='b'):
# 		p1 = hparam(required=True)
# 		p2 = hparam(10)
# 		p3 = hparam('hello', inherit=True)
# 		p4 = hparam((1,2,3), hidden=True)
#
#
# 	@inherit_hparams('p1', 'p2')
# 	class ModelB(MyModels, ident='b'):
# 		pass
#
# 	builder = MyModels(p2=50)
# 	assert MyModels.p2 == 10
# 	assert builder.p2 == 50
# 	b = builder.build()
# 	assert b.p2 == 50
# 	```
#
# 	'''
#
# 	Product_Registry = Class_Registry
# 	_product_registry: Product_Registry = None
# 	_registration_node = None
#
# 	def __init__(self, ident=None, **kwargs):
# 		if self.has_hparam('ident'): # self still behaves as a builder (bit of a hack)
# 			if ident is None:
# 				ident = self.ident
# 			super().__init__(ident=ident, **kwargs)
# 		else:
# 			super().__init__(**kwargs)
#
# 	class _IdentParameter(MultiBuilderBase.Hyperparameter):
# 		IdentSpace = spaces.Selection
#
# 		def __init__(self, *, space=None, **kwargs):
# 			if space is None:
# 				space = self.IdentSpace()
# 			super().__init__(space=space, **kwargs)
#
# 		def set_default_value(self, value):
# 			self.default = value
# 			if value not in self.space.values:
# 				self.space.values.append(value)
# 			return self
#
#
# 	def __init_subclass__(cls, create_registry=None, products=None, default_ident=unspecified_argument,
# 	                      _register_ident=None, **kwargs):
# 		if _register_ident is not None:
# 			prt.warning(f'`register_ident` should not be used with `RegistryBuilder`')
# 		prev_ident_hparam = None
# 		if create_registry is None and products is not None:
# 			create_registry = True
# 		if create_registry is None:
# 			create_registry = cls._registration_node is None
# 			prev_ident_hparam = cls.get_hparam('ident', None)
# 		super().__init_subclass__(_register_ident=create_registry, **kwargs)
# 		if create_registry:
# 			ident_hparam = cls.get_hparam('ident', None)
# 			if ident_hparam is not None and prev_ident_hparam is not None:
# 				ident_hparam.values.extend(prev_ident_hparam.values)
# 			cls._product_registry = cls.Product_Registry()
# 			cls._registration_node = cls
# 		if default_ident is not unspecified_argument:
# 			cls._set_default_product(default_ident)
# 		if products is not None:
# 			for name, product in products.items():
# 				cls.register_product(name, product)
#
#
# 	@classmethod
# 	def _set_default_product(cls, ident):
# 		return cls._registration_node.get_hparam('ident').set_default_value(ident)
#
# 	@classmethod
# 	def find_product_entry(cls, ident, default=unspecified_argument):
# 		entry = cls._registration_node._product_registry.find(ident, None)
# 		if entry is None:
# 			if default is not unspecified_argument:
# 				return default
# 			raise cls.NoProductFound(ident)
# 		return entry
#
# 	@classmethod
# 	def register_product(cls, name, product, is_default=False, **kwargs):
# 		cls._registration_node._product_registry.new(name, product, **kwargs)
# 		if is_default:
# 			cls._set_default_product(name)
#
# 	@classmethod
# 	def get_product_registration_decorator(cls):
# 		return cls._registration_node._product_registry.get_decorator()
#
#
# 	@agnostic
# 	def available_products(self):
# 		return {ident: entry.cls for ident, entry in self._registration_node._product_registry.items()}
#
# 	@agnostic
# 	def product(self, ident, **kwargs): # <------------------
# 		entry = self.find_product_entry(ident)
# 		return entry.cls
#
#
#
# class ClassBuilderBaseAuto(AutoRegistryBuilderBase, create_registry=False):
# 	'''Automatically register subclasses and add them to the product_registry.'''
#
# 	_class_builder_delimiter = '/'
# 	_class_builder_terms = ()
# 	def __init_subclass__(cls, ident=None, is_default=False, as_branch=False, **kwargs):
# 		super().__init_subclass__(**kwargs)
# 		if ident is not None:
# 			if as_branch:
# 				cls._class_builder_terms = (*cls._class_builder_terms, ident)
# 			else:
# 				addr = cls._class_builder_delimiter.join((*cls._class_builder_terms, ident))
# 				cls.ident = addr
# 				cls.register_product(addr, cls, is_default=is_default)






