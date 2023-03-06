from typing import List, Dict, Tuple, Optional, Union, Any, Hashable, Sequence, Callable, Generator, Type, Iterable, \
	Iterator, NamedTuple, ContextManager
from omnibelt import agnostic, unspecified_argument


class AbstractHyperparameter:
	def __get__(self, instance, owner):
		raise NotImplementedError



class AbstractParameterized:
	def fill_hparams(self, fn, args=None, kwargs=None, **finder_kwargs) -> Dict[str, Any]:
		raise NotImplementedError


	def _extract_hparams(self, kwargs):
		raise NotImplementedError


	def has_hparam(self, key):
		raise NotImplementedError


	def get_hparam(self, key, default=unspecified_argument):
		raise NotImplementedError


	@classmethod
	def hyperparameters(cls):
		raise NotImplementedError


	@classmethod
	def named_hyperparameters(cls):
		raise NotImplementedError


	@classmethod
	def inherit_hparams(cls, *names):
		raise NotImplementedError


	# def __setattr__(self, key, value):
	# 	if isinstance(value, AbstractHyperparameter):
	# 		raise ValueError('Hyperparameters must be set to the class (not an instance)')
	# 	super().__setattr__(key, value)



class AbstractBuilder(AbstractParameterized):
	@staticmethod
	def validate(product, *args, **kwargs):
		return product


	@staticmethod
	def product(*args, **kwargs) -> Type:
		raise NotImplementedError


	@staticmethod
	def build(*args, **kwargs):
		raise NotImplementedError



class AbstractSubmodule(AbstractHyperparameter):
	def get_builder(self) -> Optional[AbstractBuilder]:
		raise NotImplementedError


	def build_with(self, *args, **kwargs):
		raise NotImplementedError



class AbstractSpec(Iterable):
	def get(self, name, default=unspecified_argument) -> 'AbstractSpec':
		raise NotImplementedError

	@property
	def base(self):
		raise NotImplementedError

	@property
	def name(self):
		raise NotImplementedError

	@property
	def info(self):
		raise NotImplementedError

	@property
	def is_default(self):
		raise NotImplementedError



