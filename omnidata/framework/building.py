import inspect
from omnibelt import agnosticmethod, unspecified_argument, Class_Registry, extract_function_signature
from .hyperparameters import Parametrized, MachineParametrized, spaces, \
	hparam, inherit_hparams, machine, inherit_machines


class Builder(Parametrized):

	@agnosticmethod
	def _fillin_hparam_args(self, fn, args, kwargs):
		def defaults(n):
			if n in self._registered_hparams:
				return getattr(self, n)
			raise KeyError(n)
		
		return extract_function_signature(fn, args, kwargs, defaults)


	class NoProductFound(NotImplementedError):
		pass


	@agnosticmethod
	def product(self, *args, **kwargs):
		fixed_args, fixed_kwargs = self._fillin_hparam_args(self._product, args, kwargs)
		return self._product(*fixed_args, **fixed_kwargs)

		
	@agnosticmethod
	def _product(self, *args, **kwargs):
		return self if type(self) == type else self.__class__

	
	@agnosticmethod
	def plan(self, *args, **kwargs):
		fixed_args, fixed_kwargs = self._fillin_hparam_args(self._plan, args, kwargs)
		return self._plan(*fixed_args, **fixed_kwargs)
		

	@agnosticmethod
	def _plan(self, *args, **kwargs):
		return self.named_hyperparameters()


	@agnosticmethod
	def build(self, *args, **kwargs):
		fixed_args, fixed_kwargs = self._fillin_hparam_args(self._build, args, kwargs)
		return self._build(*fixed_args, **fixed_kwargs)
	
	
	@agnosticmethod
	def _build(self, *args, **kwargs):
		product = self.product(*args, **kwargs)
		return product(*args, **kwargs)



class BuilderRegistry(Class_Registry):
	def get_builder(self, name):
		return self.find(name).cls
builder_registry = BuilderRegistry()
register_builder = builder_registry.get_decorator()
get_builder = builder_registry.get_builder



class ClassBuilder(Builder):
	ident = hparam(required=True)
	
	
	def __init_subclass__(cls, **kwargs):
		super().__init_subclass__(**kwargs)
		cls._update_ident_space()
	
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._update_ident_space()
	
	
	@agnosticmethod
	def _update_ident_space(self):
		ident_space = self.product_registry().get_hparam('ident').space
		if isinstance(ident_space, spaces.Categorical):
			ident_space.update(list(self.product_registry().keys()))
	
	
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
			if product is me:
				yield from super()._plan(ident=ident, **kwargs)
			elif isinstance(product, Parametrized):
				yield from product.hyperparameters()


	@agnosticmethod
	def _build(self, ident=None, *args, **kwargs):
		product = self.product(ident, **kwargs)
		return product(*args, **kwargs)
	


class AutoClassBuilder(ClassBuilder):
	'''Automatically register subclasses and add them to the product_registry.'''
	
	
	
	pass



