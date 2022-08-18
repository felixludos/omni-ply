import inspect
from omnibelt import agnosticmethod, unspecified_argument, Class_Registry, extract_function_signature
from .hyperparameters import Parameterized, MachineParametrized, spaces, hparam, inherit_hparams, with_hparams


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
		return self.named_hyperparameters()


	@agnosticmethod
	def build(self, *args, **kwargs):
		fixed_args, fixed_kwargs = self.fill_hparams(self._build, args, kwargs)
		return self._build(*fixed_args, **fixed_kwargs)
	
	
	@agnosticmethod
	def _build(self, *args, **kwargs):
		product = self.product(*args, **kwargs)
		return product(*args, **kwargs)



builder_registry = Class_Registry()
register_builder = builder_registry.get_decorator()
get_builder = builder_registry.get_class



class ClassBuilder(Builder):
	ident = hparam(required=True, space=spaces.Selection())
	
	
	def __init_subclass__(cls, inherit_ident=True, default_ident=None, **kwargs):
		super().__init_subclass__(**kwargs)
		if inherit_ident:
			cls.inherit_hparams('ident')
		if default_ident is not None:
			cls._set_default_ident(default_ident)
		cls._update_ident_space()
	
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._update_ident_space()


	@agnosticmethod
	def _update_ident_space(self):
		ident_space = self.get_hparam('ident').space
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


	@agnosticmethod
	def _plan(self, ident=None, **kwargs):
		try:
			product = self.product(ident, **kwargs)
		except self.NoProductFound:
			pass
		else:
			me = self if type(self) == type else self.__class__
			if product is me or not isinstance(product, Parameterized):
				yield from super()._plan(ident=ident, **kwargs)
			elif isinstance(product, Parameterized):
				yield from product.named_hyperparameters()


	@agnosticmethod
	def _build(self, ident=None, *args, **kwargs):
		product = self.product(ident, **kwargs)
		return product(*args, **kwargs)
	


class AutoClassBuilder(ClassBuilder):
	'''Automatically register subclasses and add them to the product_registry.'''

	Class_Registry = Class_Registry
	_product_registry: Class_Registry = None
	_registration_node = None

	def __init_subclass__(cls, ident=None, create_registry=False, default=False,
	                      inherit_ident=False, default_ident=None, **kwargs):
		super().__init_subclass__(inherit_ident=inherit_ident, default_ident=default_ident, **kwargs)

		node = cls._registration_node
		if node is None or create_registry:
			registry = cls.Class_Registry()
			cls._product_registry = registry
			cls._registration_node = cls

		if ident is not None:
			cls.register_product(ident, cls, default=default)
			cls.ident = ident


	@agnosticmethod
	def product_registry(self):
		if self._product_registry is None:
			return {}
		return self._product_registry


	@agnosticmethod
	def register_product(self, ident, product, default=False):
		self._registration_node.get_hparam('ident').space.append(ident)
		if default:
			self._set_default_ident(ident)
		self._product_registry.new(ident, product)











