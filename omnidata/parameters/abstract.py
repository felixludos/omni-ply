from typing import List, Dict, Tuple, Optional, Union, Any, Hashable, Sequence, Callable, Generator, Type, Iterable, \
	Iterator, NamedTuple, ContextManager
from omnibelt import agnostic, unspecified_argument

from .errors import MissingBuilderError, NoProductFound, InvalidProductError


class AbstractHyperparameter:
	def __get__(self, instance, owner):
		raise NotImplementedError


	def validate(self, instance: 'AbstractParameterized') -> Any:
		raise NotImplementedError



class AbstractParameterized:
	def fill_hparams(self, fn, args=None, kwargs=None, **finder_kwargs) -> Dict[str, Any]:
		raise NotImplementedError


	def _extract_hparams(self, kwargs):
		raise NotImplementedError


	def _existing_hparams(self, *, hidden=False):
		for key, param in self.named_hyperparameters(hidden=hidden):
			if param.is_missing(self):
				yield key, getattr(self, key)


	def has_hparam(self, key):
		raise NotImplementedError


	def get_hparam(self, key, default=unspecified_argument):
		raise NotImplementedError


	@classmethod
	def hyperparameters(cls, *, hidden=False):
		for key, val in cls.named_hyperparameters(hidden=hidden):
			yield val


	@classmethod
	def named_hyperparameters(cls, *, hidden=False):
		raise NotImplementedError


	@classmethod
	def hyperparameter_names(cls, *, hidden=False):
		for key, val in cls.named_hyperparameters(hidden=hidden):
			yield key


	@classmethod
	def inherit_hparams(cls, *names):
		raise NotImplementedError


	# def __setattr__(self, key, value):
	# 	if isinstance(value, AbstractHyperparameter):
	# 		raise ValueError('Hyperparameters must be set to the class (not an instance)')
	# 	super().__setattr__(key, value)



class AbstractBuilder(AbstractParameterized):
	@staticmethod
	def validate(product):
		return product


	@staticmethod
	def product(*args, **kwargs) -> Type:
		raise NotImplementedError


	@staticmethod
	def build(*args, **kwargs):
		raise NotImplementedError



class AbstractArgumentBuilder(AbstractBuilder):
	def build(self, *args, **kwargs):
		product = self.product(*args, **kwargs)
		kwargs = self._build_kwargs(product, *args, **kwargs)
		args = kwargs.pop(None) if None in kwargs else ()
		return product(*args, **kwargs)


	def _build_kwargs(self, product, *args, **kwargs):
		return kwargs.copy()



class AbstractMultiBuilder(AbstractArgumentBuilder, AbstractParameterized):
	ident = None
	_NoProductFound = NoProductFound


	@classmethod
	def product_names(cls):
		for name, product in cls.named_products():
			yield name


	@classmethod
	def products(cls):
		for name, product in cls.named_products():
			yield product


	@classmethod
	def named_products(cls):
		raise NotImplementedError


	def _build_kwargs(self, product, ident: Optional[str] = unspecified_argument, **kwargs):
		return super()._build_kwargs(product, **kwargs)


	_InvalidProductError = InvalidProductError
	def validate(self, product):
		if isinstance(product, str):
			# raise self._InvalidProductError(f'Expected product, got string: {product!r}')
			return self.build(product)
		return product



class AbstractRegistryBuilder(AbstractMultiBuilder):
	@classmethod
	def register_product(cls, name, product, *, is_default=False, **kwargs):
		raise NotImplementedError



class AbstractModular(AbstractParameterized):
	@classmethod
	def named_submodules(cls, *, hidden=False) -> Iterator[Tuple[str, 'AbstractSubmodule']]:
		for name, param in cls.named_hyperparameters(hidden=hidden):
			if isinstance(param, AbstractSubmodule):
				yield name, param


	@classmethod
	def submodules(cls, *, hidden=False) -> Iterator['AbstractSubmodule']:
		for name, param in cls.named_submodules(hidden=hidden):
			yield param


	@classmethod
	def submodule_names(cls, *, hidden=False) -> Iterator[str]:
		for name, param in cls.named_submodules(hidden=hidden):
			yield name



class AbstractSubmodule(AbstractHyperparameter):

	def init(self, instance):
		raise NotImplementedError


	# def get_builder(self, *args, **kwargs) -> Optional[AbstractBuilder]:
	# 	raise NotImplementedError


	# def validate(self, product, *, spec=None):
	# 	builder = self.get_builder() if spec is None else self.get_builder(blueprint=spec)
	# 	if builder is None:
	# 		return super().validate(product)
	# 	try:
	# 		return builder.validate(product)
	# 	except InvalidProductError:
	# 		return self.build_with(product) if spec is None else self.build_with_spec(product, spec=spec)


	# def build_with_spec(self, owner, spec=None): # TODO: --> architect
	# 	if spec is None:
	# 		spec = owner.as_spec()
	#
	# 	builder = self.get_builder()
	# 	if builder is None:
	# 		raise self._MissingBuilderError(f'No builder for {self}')
	# 	return builder.build(*args, **kwargs)



# class AbstractSpec(Iterable):
# 	def get(self, name, default=unspecified_argument) -> 'AbstractSpec':
# 		raise NotImplementedError
#
# 	@property
# 	def base(self):
# 		raise NotImplementedError
#
# 	@property
# 	def name(self):
# 		raise NotImplementedError
#
# 	@property
# 	def info(self):
# 		raise NotImplementedError
#
# 	@property
# 	def is_default(self):
# 		raise NotImplementedError



