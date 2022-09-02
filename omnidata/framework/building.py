import inspect
from collections import UserDict
from omnibelt import agnosticmethod, unspecified_argument, Class_Registry, extract_function_signature
from .hyperparameters import Parameterized, spaces, hparam, inherit_hparams, with_hparams


class Buildable:
	@agnosticmethod
	def full_spec(self, fmt='{}', fmt_rule='{parent}.{child}', include_machines=True):
		raise NotImplementedError

	pass


class Builder(Parameterized):

	class NoProductFound(NotImplementedError):
		pass


	@agnosticmethod
	def product(self, *args, **kwargs):
		fixed_args, fixed_kwargs = self.fill_hparams(self._product, args, kwargs)
		return self._product(*fixed_args, **fixed_kwargs)

		
	@agnosticmethod
	def _product(self, *args, **kwargs):
		return self if type(self) == type else self.__class__

	
	@agnosticmethod
	def plan(self, *args, **kwargs):
		fixed_args, fixed_kwargs = self.fill_hparams(self._plan, args, kwargs)
		return self._plan(*fixed_args, **fixed_kwargs)
		

	@agnosticmethod
	def _plan(self, *args, **kwargs):
		product = self.product(*args, **kwargs)
		if issubclass(product, Parameterized):
			yield from product.full_spec()


	@agnosticmethod
	def build(self, *args, **kwargs):
		fixed_args, fixed_kwargs = self.fill_hparams(self._build, args, kwargs)
		return self._build(*fixed_args, **fixed_kwargs)
	
	
	@agnosticmethod
	def _build(self, *args, **kwargs):
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

	
	def __init_subclass__(cls, default_ident=unspecified_argument, inherit_ident=True, **kwargs):
		super().__init_subclass__(**kwargs)
		if inherit_ident:
			cls.inherit_hparams('ident')
			cls.register_hparam('ident', ref=cls.get_hparam('ident'), space=cls.IdentSpace(), default=default_ident)
		cls._update_ident_space()
	
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._update_ident_space()


	@agnosticmethod
	def _update_ident_space(self):
		hparam = self.get_hparam('ident')
		ident_space = hparam.space
		if isinstance(ident_space, spaces.Selection):
			ident_space.replace(list(self.product_registry().keys()))
	

	@agnosticmethod
	def _set_default_ident(self, default):
		self.get_hparam('ident').default = default


	@agnosticmethod
	def product_registry(self):
		return {}


	@agnosticmethod
	def _product(self, ident):
		product = self.product_registry().get(ident, unspecified_argument)
		if product is unspecified_argument:
			raise self.NoProductFound(ident)
		return product


	# @agnosticmethod
	# def _plan(self, ident=None, **kwargs):
	# 	try:
	# 		product = self.product(ident, **kwargs)
	# 	except self.NoProductFound:
	# 		pass
	# 	else:
	# 		me = self if type(self) == type else self.__class__
	# 		if product is me or not issubclass(product, Parameterized):
	# 			yield from super()._plan(ident=ident, **kwargs)
	# 		elif issubclass(product, Parameterized):
	# 			yield from product.named_hyperparameters()


	# @agnosticmethod
	# def _build(self, ident=None, *args, **kwargs):
	# 	product = self.product(ident, **kwargs)
	# 	return product(*args, **kwargs)
	


class AutoClassBuilder(ClassBuilder):
	'''Automatically register subclasses and add them to the product_registry.'''

	Class_Registry = Class_Registry
	_product_registry: Class_Registry = None
	_registration_node = None

	def __init_subclass__(cls, ident=None, create_registry=False, default=False,
	                      inherit_ident=False, default_ident=None, **kwargs):
		super().__init_subclass__(inherit_ident=create_registry, default_ident=None, **kwargs)

		node = cls._registration_node
		if node is None or create_registry:
			registry = cls.Class_Registry()
			# cls.get_hparam('ident').space =
			cls._product_registry = registry
			cls._registration_node = cls

		if ident is not None:
			cls.register_product(ident, cls, default=default)
			cls.inherit_hparams('ident')
			cls.register_hparam('ident', ref=cls.get_hparam('ident'), default=ident)


	@agnosticmethod
	def _product(self, ident):
		product = super()._product(ident)
		if isinstance(product, self._product_registry.entry_cls):
			return product.cls
		return product


	@agnosticmethod
	def product_registry(self):
		if self._product_registry is None:
			return {}
		return self._product_registry


	@agnosticmethod
	def register_product(self, ident, product, default=False):
		ident_hparam = self._registration_node.get_hparam('ident')
		ident_hparam.space.append(ident)
		if default:
			self._set_default_ident(ident)
		self._product_registry.new(ident, product)


class BuilderSpecification:
	def find(self, key):
		raise NotImplementedError

	def has(self, key):
		raise NotImplementedError


class MachineBuilder(Builder):
	class Specification(BuilderSpecification, UserDict):
		def find(self, key):
			return self[key]

		def has(self, key):
			return key in self


	def create_spec(self, *args, **kwargs):
		raise NotImplementedError

	def plan_from_spec(self, spec: BuilderSpecification):
		pass

	def build_from_spec(self, spec: BuilderSpecification):
		pass

	def product_from_spec(self, spec: BuilderSpecification):
		pass







